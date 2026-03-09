# Creates a desktop shortcut for SCP Tool
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$desktopPath = [Environment]::GetFolderPath("Desktop")

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut("$desktopPath\SCP Tool.lnk")
$shortcut.TargetPath = "$scriptDir\backend\venv\Scripts\pythonw.exe"
$shortcut.Arguments = "`"$scriptDir\launch.pyw`""
$shortcut.WorkingDirectory = $scriptDir
$shortcut.IconLocation = "$scriptDir\icon.ico, 0"
$shortcut.Description = "SCP Tool - Secure file transfers"
$shortcut.Save()

Write-Host "Shortcut created on your Desktop!" -ForegroundColor Green
