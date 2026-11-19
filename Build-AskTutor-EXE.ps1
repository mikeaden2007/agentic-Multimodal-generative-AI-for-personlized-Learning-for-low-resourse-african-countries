# Optional: builds a tiny Windows launcher from the working batch file.
# Run from Windows PowerShell: powershell -ExecutionPolicy Bypass -File .\Build-AskTutor-EXE.ps1
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $MyInvocation.MyCommand.Path
$exe=Join-Path $root 'Open AskTutor.exe'
$source=@'
using System;
using System.Diagnostics;
using System.IO;
public class Launcher {
  public static void Main() {
    string dir=AppDomain.CurrentDomain.BaseDirectory;
    string bat=Path.Combine(dir,"Open-AskTutor.bat");
    if(!File.Exists(bat)){Console.WriteLine("Open-AskTutor.bat is missing.");Console.ReadKey();return;}
    Process.Start(new ProcessStartInfo("cmd.exe", "/c \""+bat+"\"") {WorkingDirectory=dir, UseShellExecute=true});
  }
}
'@
Add-Type -TypeDefinition $source -Language CSharp -OutputAssembly $exe -OutputType ConsoleApplication
Write-Host "Created: $exe" -ForegroundColor Green
