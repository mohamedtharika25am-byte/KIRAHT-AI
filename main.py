"""
KIRAHT AI - Version 0.1 (Local Ollama Edition)
A beginner-friendly, terminal-based AI assistant powered locally by Ollama.

Scope:
- Terminal text interaction only.
- In-memory conversation history for multi-turn context.
- 100% local inference with native Ollama Python package.
- Default model: qwen3:8b running locally at http://localhost:11434.
- No OpenAI API key or cloud API required.
- Graceful error handling for offline Ollama or unavailable models.
"""

import os
import sys
from dotenv import load_dotenv
import httpx
import ollama

# Configure UTF-8 output encoding on Windows terminals to support emojis and unicode
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def get_client_and_model():
    """
    Loads configuration from environment / .env file and initializes the Ollama client.
    Defaults to host http://localhost:11434 and model qwen3:8b.
    """
    load_dotenv()

    host = os.getenv("OLLAMA_HOST", "http://localhost:11434").strip() or "http://localhost:11434"
    model = os.getenv("AI_MODEL", "qwen3:8b").strip() or "qwen3:8b"

    client = ollama.Client(host=host)
    return client, model, host


def verify_ollama_status(client: ollama.Client, model: str, host: str) -> None:
    """
    Verifies that the local Ollama daemon is running and that the requested model exists.
    Exits gracefully with actionable guidance if Ollama is unreachable or model is missing.
    """
    try:
        response = client.list()
        # Extract model names from response
        available_models = []
        for item in response.models:
            name = getattr(item, "model", None) or getattr(item, "name", None)
            if name:
                available_models.append(name)

        # Check if the requested model or model tag is in available models (e.g. qwen3:8b or qwen3:8b:latest)
        model_found = any(
            m == model or m.startswith(f"{model}:") or model.startswith(f"{m}:")
            for m in available_models
        )

        if not model_found:
            print(f"\n[!] Model Error: Model '{model}' was not found in your local Ollama library.")
            print("    Available models:")
            if available_models:
                for m in available_models:
                    print(f"      - {m}")
            else:
                print("      (No models found)")
            print(f"\n    To fix this:")
            print(f"    Run the following command in your terminal to download the model:")
            print(f"       ollama pull {model}")
            print("    Then restart KIRAHT AI.\n")
            sys.exit(1)

    except (httpx.ConnectError, ConnectionRefusedError, ConnectionError, ollama.RequestError):
        print(f"\n[!] Connection Error: Unable to connect to Ollama at {host}.")
        print("    To fix this:")
        print("    1. Ensure Ollama is installed on your machine (https://ollama.com).")
        print("    2. Start Ollama by running 'ollama serve' in a terminal or opening the Ollama app.")
        print(f"    3. Verify that Ollama is accessible at {host}.\n")
        sys.exit(1)
    except Exception as err:
        print(f"\n[!] Unexpected Error while checking Ollama status: {err}\n")
        sys.exit(1)


def run_chat_loop(client: ollama.Client, model: str) -> None:
    """
    Runs the interactive terminal chat loop with conversation history.
    """
    print("Type 'exit' to quit.")

    # Initialize conversation history with a helpful system prompt
    messages = [
        {
            "role": "system",
            "content": "You are KIRAHT AI, a helpful, polite, and concise AI assistant.",
        }
    ]

    while True:
        try:
            # Prompt user for input
            user_input = input("\nYou: ").strip()

            # Ignore empty inputs
            if not user_input:
                continue

            # Check for exit command (case-insensitive)
            if user_input.lower() in ("exit", "quit", "bye"):
                print("\nGoodbye!")
                break

            # Append the user's message to conversation history
            messages.append({"role": "user", "content": user_input})

            # Send conversation history to the model
            try:
                response = client.chat(
                    model=model,
                    messages=messages,
                )

                # Extract the assistant's reply text
                ai_response = response.message.content or ""

                # Display the AI's response in the terminal
                print(f"\nkiraht AI: {ai_response}")

                # Save the assistant's response to history to remember previous context
                messages.append({"role": "assistant", "content": ai_response})

            except ollama.ResponseError as err:
                messages.pop()
                print(f"\nkiraht AI: [Ollama Error {err.status_code}] {err.error}")

            except (httpx.ConnectError, ConnectionRefusedError, ConnectionError, ollama.RequestError):
                messages.pop()
                print("\nkiraht AI: [Connection Error] Connection to local Ollama lost. Please ensure Ollama is running.")

            except Exception as err:
                messages.pop()
                print(f"\nkiraht AI: [Error] An unexpected error occurred: {err}")

        except (KeyboardInterrupt, EOFError):
            # Gracefully handle Ctrl+C or Ctrl+D/Z
            print("\nGoodbye!")
            break


def main() -> None:
    """
    Main entry point for KIRAHT AI V0.1 Local Edition.
    """
    # 1. Load configuration and initialize Ollama client
    client, model, host = get_client_and_model()

    # 2. Verify local Ollama is running and model is available
    verify_ollama_status(client, model, host)

    # 3. Start the interactive chat loop
    run_chat_loop(client, model)


if __name__ == "__main__":
    main()

