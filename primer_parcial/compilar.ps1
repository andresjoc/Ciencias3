# Script PowerShell para compilar la aplicación a binario ejecutable (.exe)
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " Compilando SimulaAutomata.exe con PyInstaller" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

python -m PyInstaller --noconfirm --clean --onefile --windowed --name SimulaAutomata --paths . src/main.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n======================================================================" -ForegroundColor Green
    Write-Host " [OK] Binario generado exitosamente en: dist\SimulaAutomata.exe" -ForegroundColor Green
    Write-Host "======================================================================" -ForegroundColor Green
} else {
    Write-Host "`n======================================================================" -ForegroundColor Red
    Write-Host " [ERROR] La compilación falló. Revise los mensajes anteriores." -ForegroundColor Red
    Write-Host "======================================================================" -ForegroundColor Red
}
