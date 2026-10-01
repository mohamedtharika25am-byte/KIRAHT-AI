"""
Creates a Windows Desktop Shortcut for KIRAHT AI Tactical Web HUD.
Handles OneDrive and standard desktop folder locations automatically.
"""

import os
import sys
import subprocess

def create_shortcut():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Icon path
    icon_path = os.path.join(project_dir, "static", "img", "kiraht_ai_logo.ico")
    if not os.path.exists(icon_path):
        from PIL import Image
        png_path = os.path.join(project_dir, "static", "img", "kiraht_ai_logo.png")
        img = Image.open(png_path)
        img.save(icon_path, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])

    vbs_script = os.path.join(project_dir, "launch_web.vbs")

    ps_script = f"""
$DesktopPath = [Environment]::GetFolderPath('Desktop')
$ShortcutPath = Join-Path $DesktopPath 'KIRAHT AI.lnk'
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = 'wscript.exe'
$Shortcut.Arguments = '"{vbs_script}"'
$Shortcut.WorkingDirectory = '{project_dir}'
$Shortcut.IconLocation = '{icon_path},0'
$Shortcut.Description = 'KIRAHT AI - Tactical Web HUD'
$Shortcut.Save()
Write-Host "Created shortcut at: $ShortcutPath"
"""
    result = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("Error:", result.stderr)

if __name__ == "__main__":
    create_shortcut()
