# Run on the teacher's Windows PC, once and then every time before a class:
#     powershell -ExecutionPolicy Bypass -File .\setup-teacher.ps1
# It starts the teacher page. Keep this window open while you teach. Close it to stop the page.
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$py = $null
foreach ($c in @('py', 'python', 'python3')) {
    if (Get-Command $c -ErrorAction SilentlyContinue) {
        try { & $c -c "import sys; assert sys.version_info >= (3, 8)" 2>$null; if ($LASTEXITCODE -eq 0) { $py = $c; break } } catch {}
    }
}
if (-not $py) {
    Write-Host "Python 3 is not installed. Install it with:  winget install Python.Python.3.12"
    Write-Host "(or from python.org). Then run this script again."
    exit 1
}
# Windows Firewall: the Jetsons must reach port 8800 of this PC
if (-not (Get-NetFirewallRule -DisplayName "Myduino teacher" -ErrorAction SilentlyContinue)) {
    try {
        New-NetFirewallRule -DisplayName "Myduino teacher" -Direction Inbound -Protocol TCP -LocalPort 8800 -Action Allow -Profile Any -ErrorAction Stop | Out-Null
        Write-Host "Port 8800 is open in Windows Firewall."
    } catch {
        Write-Host "Could not open port 8800 in Windows Firewall. Run PowerShell as Administrator once, or choose Allow when Windows asks."
    }
}
if ($py -eq 'py') { & py -3 "$here\labs\teacher_server.py" } else { & $py "$here\labs\teacher_server.py" }
