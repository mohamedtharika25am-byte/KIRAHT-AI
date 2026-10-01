Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "d:\KIRAHT AI"
WshShell.Run "cmd /c ""d:\KIRAHT AI\run_web.bat""", 0, False
Set WshShell = Nothing
