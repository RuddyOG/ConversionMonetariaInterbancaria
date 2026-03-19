param(
  [string]$TipoCambio = "6.96",
  [int]$LimitPorBanco = 200,
  [int]$Workers = 8,
  [switch]$ResetASFI = $false
)

$ErrorActionPreference = "Stop"

$ProjectRoot = "d:\DISCO (D)\UNIVALLE\7°mo Semestre\Sistemas Distribuidos\Practica2\ConversionMonetariaInterbancaria"
$RelacionalDir = Join-Path $ProjectRoot "BackendRelacional"
$SeedNoRel = Join-Path $ProjectRoot "app\db\seed(datos)\seed_non_relational.py"

Write-Host "[1/8] Instalando dependencias..."
python -m pip install -r (Join-Path $ProjectRoot "requirements.txt") | Out-Null

Write-Host "[2/8] Levantando BD relacionales (BackendRelacional)..."
Push-Location $RelacionalDir
docker compose up -d
python load_1pct_relacionales.py
Pop-Location

Write-Host "[3/8] Levantando BD no relacionales (Mongo/Redis)..."
Push-Location $ProjectRoot
docker compose up -d
python "$SeedNoRel"
Pop-Location

Write-Host "[4/8] Iniciando API bancos en background..."
$apiArgs = @("-m", "uvicorn", "app.banks_api.server:app", "--host", "0.0.0.0", "--port", "9000")
$apiProc = Start-Process -FilePath "python" -ArgumentList $apiArgs -PassThru -WorkingDirectory $ProjectRoot

Start-Sleep -Seconds 4

try {
  Write-Host "[5/8] Verificando /health..."
  $health = Invoke-RestMethod -Method Get -Uri "http://localhost:9000/health"
  Write-Host "API OK => $($health | ConvertTo-Json -Compress)"

  Write-Host "[6/8] Ejecutando runner ASFI 1..14 en paralelo..."
  $truncate = if ($ResetASFI) { "True" } else { "False" }
  $cmd = "from app.asfi.run_asfi_14banks import run; run(limit_per_bank=$LimitPorBanco, max_workers=$Workers, truncate_asfi=$truncate, currency_rate='$TipoCambio')"
  Push-Location $ProjectRoot
  python -c $cmd
  Pop-Location

  Write-Host "[7/8] Verificando conteo ASFI central..."
  docker exec -it db_asfi_pg psql -U admin -d asfi_central -c "SELECT COUNT(*) FROM cuentas_asfi;"

  Write-Host "[8/8] Listo. Revisa logs/auditoria.csv"
}
finally {
  if ($apiProc -and -not $apiProc.HasExited) {
    Write-Host "Apagando API bancos..."
    Stop-Process -Id $apiProc.Id -Force
  }
}
