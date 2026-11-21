Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\hsn10\.gemini\antigravity\scratch\pinterest-video-auto"
WshShell.Run "pythonw app.py", 0, False
WScript.Echo "Pinterest Video Otomasyonu arka planda (gizli) baslatildi!" & vbCrLf & "Tarayicinizdan http://localhost:8080 adresine girebilirsiniz."
