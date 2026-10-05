"""
KIRAHT AI - Web HUD Server
FastAPI & WebSocket backend providing a local, futuristic JARVIS-style dashboard.
Runs locally at http://127.0.0.1:8000.
"""

import asyncio
import datetime
import json
import os
import sys
from typing import Dict, Any, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from core import (
    get_system_telemetry,
    load_memory,
    load_chat_history,
    save_chat_history,
    clear_chat_history,
    add_chat_history_message,
    process_user_message_stream,
    is_online,
)
from tools import execute_system_command

app = FastAPI(title="KIRAHT AI Web HUD", version="0.2.1")

# Allow localhost CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
GENERATED_DIR = os.path.join(STATIC_DIR, "generated")
SCREENSHOTS_DIR = os.path.join(os.path.expanduser("~"), "Pictures", "Screenshots")

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(GENERATED_DIR, exist_ok=True)

# Mount static folder
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if os.path.exists(SCREENSHOTS_DIR):
    app.mount("/screenshots", StaticFiles(directory=SCREENSHOTS_DIR), name="screenshots")


# Quick Action request schema
class QuickActionRequest(BaseModel):
    action: str


# REST Endpoints
@app.get("/")
async def get_index():
    """Serves the main futuristic Web HUD dashboard."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"status": "KIRAHT AI Web HUD", "message": "index.html loading..."})


@app.get("/api/telemetry")
async def get_telemetry():
    """Returns real-time system hardware telemetry."""
    return get_system_telemetry()


@app.get("/api/history")
async def get_history():
    """Returns conversation history."""
    return load_chat_history()


@app.post("/api/clear")
async def clear_history():
    """Clears conversation history."""
    clear_chat_history()
    return {"status": "success", "message": "Conversation history cleared."}


@app.post("/api/quick-action")
async def handle_quick_action(req: QuickActionRequest):
    """Executes predefined dashboard quick actions."""
    action = req.action.lower().strip()
    mem = load_memory()
    call_me = mem.get("call_me", "Sir")

    res_text = ""
    activity_action = ""
    meta_info: Dict[str, Any] = {
        "engine": "tool",
        "tool": action,
        "source_label": f"TOOL: {action.replace('_', ' ').upper()}",
    }

    if action == "system_status":
        telem = get_system_telemetry()
        res_text = (
            f"System Status Diagnostic:\n"
            f"- CPU: {telem['cpu']['percent']}% load ({telem['cpu']['cores']} cores @ {telem['cpu']['frequency']})\n"
            f"- RAM: {telem['ram']['percent']}% used ({telem['ram']['used_gb']} GB / {telem['ram']['total_gb']} GB)\n"
            f"- Battery: {telem['battery']['percent']}% ({telem['battery']['status']})\n"
            f"- Network: {telem['network']['status']} (SSID: {telem['network']['ssid']})\n"
            f"- Uptime: {telem['uptime']['system']} (Session: {telem['uptime']['session']})"
        )
        activity_action = "System Status Diagnostic"

    elif action == "open_chrome":
        _, res_text = execute_system_command("open chrome", call_me=call_me)
        activity_action = "Open Chrome"

    elif action == "open_vscode":
        _, res_text = execute_system_command("open vs code", call_me=call_me)
        activity_action = "Open VS Code"

    elif action == "screenshot":
        from system_tools import take_silent_screenshot
        shot_path = take_silent_screenshot()
        if shot_path and os.path.exists(shot_path):
            filename = os.path.basename(shot_path)
            res_text = f"{call_me}, screenshot captured and saved.\n![Screenshot](/screenshots/{filename})"
            meta_info["screenshot_url"] = f"/screenshots/{filename}"
            meta_info["tool"] = "screenshot"
            meta_info["source_label"] = "SCREENSHOT TOOL"
        else:
            from system_tools import take_screenshot
            res_text = take_screenshot(call_me=call_me)
            meta_info["tool"] = "screenshot"
            meta_info["source_label"] = "SCREENSHOT TOOL"
        activity_action = "Capture Screenshot"

    elif action == "file_manager":
        from tools import open_folder
        res_text = open_folder("d:\\KIRAHT AI", call_me=call_me)
        activity_action = "Open File Manager"

    elif action == "open_whatsapp":
        _, res_text = execute_system_command("open whatsapp", call_me=call_me)
        activity_action = "Open WhatsApp"

    elif action == "open_brave":
        _, res_text = execute_system_command("open brave", call_me=call_me)
        activity_action = "Open Brave"

    elif action == "open_task_manager":
        _, res_text = execute_system_command("open task manager", call_me=call_me)
        activity_action = "Open Task Manager"

    elif action == "clear_chat":
        clear_chat_history()
        res_text = f"{call_me}, chat history cleared."
        activity_action = "Clear Chat"

    else:
        handled, res_text = execute_system_command(action, call_me=call_me)
        if not handled:
            res_text = f"{call_me}, unknown action '{action}'."
        activity_action = action

    # Record message in chat history
    add_chat_history_message("assistant", res_text, meta=meta_info)

    return {
        "status": "success",
        "action": activity_action,
        "result": res_text,
        "meta": meta_info,
    }


# WebSocket Manager for Real-Time Streaming & Telemetry Push
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._locks: Dict[WebSocket, asyncio.Lock] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self._locks[websocket] = asyncio.Lock()

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        self._locks.pop(websocket, None)

    async def send_json(self, websocket: WebSocket, data: dict):
        lock = self._locks.get(websocket)
        if lock:
            async with lock:
                try:
                    await websocket.send_text(json.dumps(data, ensure_ascii=False))
                except Exception:
                    pass
        else:
            try:
                await websocket.send_text(json.dumps(data, ensure_ascii=False))
            except Exception:
                pass


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    # Initial payload on client connection
    try:
        # 1. Telemetry
        telem = await asyncio.to_thread(get_system_telemetry)
        await manager.send_json(websocket, {"type": "telemetry", "data": telem})

        # 2. Past Chat History
        history = load_chat_history()
        await manager.send_json(websocket, {"type": "chat_history", "messages": history})

        # 3. Status READY
        await manager.send_json(websocket, {
            "type": "status",
            "state": "READY",
            "detail": "KIRAHT AI Online",
        })
    except Exception as err:
        print(f"[!] WebSocket handshake error: {err}")

    # Background task to push live telemetry continuously every 1.5 seconds
    async def telemetry_pusher():
        while True:
            try:
                await asyncio.sleep(1.5)
                if websocket not in manager.active_connections:
                    break
                live_telem = await asyncio.to_thread(get_system_telemetry)
                await manager.send_json(websocket, {"type": "telemetry", "data": live_telem})
            except asyncio.CancelledError:
                break
            except Exception as push_err:
                await asyncio.sleep(1.0)

    push_task = asyncio.create_task(telemetry_pusher())

    try:
        while True:
            raw_data = await websocket.receive_text()
            if not raw_data:
                continue

            try:
                msg_obj = json.loads(raw_data)
            except Exception:
                msg_obj = {"type": "chat", "message": raw_data}

            msg_type = msg_obj.get("type", "chat")

            if msg_type == "ping":
                await manager.send_json(websocket, {"type": "pong"})
                continue

            if msg_type == "clear_chat":
                clear_chat_history()
                await manager.send_json(websocket, {"type": "chat_cleared"})
                await manager.send_json(websocket, {
                    "type": "activity",
                    "actor": "User",
                    "action": "Clear Chat",
                    "detail": "Conversation history reset"
                })
                continue

            if msg_type == "quick_action":
                act_name = msg_obj.get("action", "")
                await manager.send_json(websocket, {
                    "type": "activity",
                    "actor": "User",
                    "action": "Action Trigger",
                    "detail": act_name.replace("_", " ").upper(),
                })
                req_obj = QuickActionRequest(action=act_name)
                res = await handle_quick_action(req_obj)

                await manager.send_json(websocket, {
                    "type": "activity",
                    "actor": "Tool",
                    "action": res.get("action", act_name),
                    "detail": f"Execution complete ({res.get('meta', {}).get('source_label', 'TOOL')})",
                })
                await manager.send_json(websocket, {
                    "type": "chat_message",
                    "role": "assistant",
                    "content": res.get("result", ""),
                    "timestamp": datetime.datetime.now().strftime("%I:%M %p"),
                    "meta": res.get("meta", {}),
                })
                continue

            if msg_type == "chat":
                user_text = msg_obj.get("message", "").strip()
                if not user_text:
                    continue

                # Echo user message immediately to the frontend
                await manager.send_json(websocket, {
                    "type": "chat_message",
                    "role": "user",
                    "content": user_text,
                    "timestamp": datetime.datetime.now().strftime("%I:%M %p"),
                })

                # Stream response through core processing generator
                try:
                    async for event in process_user_message_stream(user_text):
                        event_type = event.get("type")

                        if event_type == "status":
                            await manager.send_json(websocket, {
                                "type": "status",
                                "state": event.get("state"),
                                "detail": event.get("detail", ""),
                            })

                        elif event_type == "activity":
                            await manager.send_json(websocket, {
                                "type": "activity",
                                "actor": event.get("actor", "System"),
                                "action": event.get("action", ""),
                                "detail": event.get("detail", ""),
                                "timestamp": datetime.datetime.now().strftime("%I:%M:%S %p"),
                            })

                        elif event_type == "chunk":
                            await manager.send_json(websocket, {
                                "type": "stream_chunk",
                                "chunk": event.get("text", ""),
                            })

                        elif event_type == "done":
                            await manager.send_json(websocket, {
                                "type": "stream_end",
                                "full_text": event.get("full_text", ""),
                                "meta": event.get("meta", {}),
                            })
                except Exception as stream_err:
                    err_msg = f"Sir, an error occurred while processing command: {stream_err}"
                    await manager.send_json(websocket, {
                        "type": "activity",
                        "actor": "System",
                        "action": "Execution Error",
                        "detail": str(stream_err)[:100],
                    })
                    await manager.send_json(websocket, {
                        "type": "stream_chunk",
                        "chunk": err_msg,
                    })
                    await manager.send_json(websocket, {
                        "type": "stream_end",
                        "full_text": err_msg,
                        "meta": {"engine": "system", "source_label": "SYSTEM ERROR"},
                    })

    except WebSocketDisconnect:
        pass
    except Exception as err:
        pass
    finally:
        manager.disconnect(websocket)
        push_task.cancel()


def free_port(port: int = 8000) -> None:
    """
    Checks if the specified port is occupied by a stale process and frees it.
    """
    try:
        import subprocess
        import time
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", f"(Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue).OwningProcess"],
            capture_output=True,
            text=True,
            timeout=3
        )
        pids = [p.strip() for p in res.stdout.split() if p.strip().isdigit()]
        current_pid = str(os.getpid())
        for pid in pids:
            if pid != current_pid and pid != "0":
                print(f"[*] Reclaiming port {port} from stale process (PID {pid})...")
                subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True, timeout=2)
                time.sleep(0.5)
    except Exception:
        pass


def _auto_open_browser(url: str, delay: float = 1.0) -> None:
    """Opens the Web HUD in default browser after server initializes."""
    import time
    import webbrowser
    time.sleep(delay)
    try:
        webbrowser.open(url)
    except Exception:
        pass


def run_server(host: str = "127.0.0.1", port: int = 8000):
    """Starts the FastAPI Web HUD local server with auto-port conflict resolution."""
    free_port(port)
    url = f"http://{host}:{port}"
    print("=" * 64)
    print("  ⚡ KIRAHT AI - Web HUD Server")
    print(f"  🌐 Running locally on: {url}")
    print(f"  🔌 WebSocket Stream   : ws://{host}:{port}/ws")
    print(f"  🛡️ Security Mode      : Localhost-Only")
    print("=" * 64)
    import threading
    try:
        from global_hotkeys import start_global_hotkeys
        start_global_hotkeys()
    except Exception as hk_err:
        print(f"[!] Global hotkeys warning: {hk_err}")
    threading.Thread(target=_auto_open_browser, args=(url,), daemon=True).start()
    try:
        uvicorn.run(app, host=host, port=port, log_level="warning")
    except OSError as err:
        if "10048" in str(err):
            print(f"\n[!] Port {port} is occupied. Attempting cleanup and retry...")
            free_port(port)
            uvicorn.run(app, host=host, port=port, log_level="warning")
        else:
            raise err


if __name__ == "__main__":
    run_server()
