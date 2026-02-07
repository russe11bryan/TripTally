# ML Model Training for Windows PowerShell
# Quick training script

param(
    [string]$DataPath = "train\data\processed_training_data.parquet",
    [string]$OutputDir = ".\models"
)

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "CI FORECASTING MODEL TRAINING" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan

Write-Host "`nConfiguration:" -ForegroundColor Yellow
Write-Host "  Data Path:   $DataPath"
Write-Host "  Output Dir:  $OutputDir"

# Check if data exists
if (-not (Test-Path $DataPath)) {
    Write-Host "`n❌ ERROR: Training data not found at $DataPath" -ForegroundColor Red
    Write-Host "`nUsage:" -ForegroundColor Yellow
    Write-Host "  .\train.ps1 -DataPath <path> -OutputDir <output>"
    exit 1
}

Write-Host "`n✓ Training data found" -ForegroundColor Green

# Step 1: Analyze data
Write-Host "`n" -NoNewline
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "STEP 1: Analyzing Training Data" -ForegroundColor Yellow
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan

python analyze_data.py $DataPath

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Data analysis failed" -ForegroundColor Red
    exit 1
}

Write-Host "`n✓ Data analysis complete" -ForegroundColor Green

# Step 2: Train models
Write-Host "`n" -NoNewline
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "STEP 2: Training ML Models" -ForegroundColor Yellow
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan

python train_model.py --data $DataPath --output $OutputDir

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Model training failed" -ForegroundColor Red
    exit 1
}

Write-Host "`n✓ Model training complete" -ForegroundColor Green

# Step 3: Verify
Write-Host "`n" -NoNewline
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "STEP 3: Verifying Models" -ForegroundColor Yellow
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan

$expectedFiles = @(
    "ci_scaler.pkl",
    "ci_model_metadata.json",
    "ci_model_xgb_2.pkl",
    "ci_model_xgb_5.pkl",
    "ci_model_xgb_10.pkl",
    "ci_model_xgb_15.pkl",
    "ci_model_xgb_30.pkl",
    "ci_model_xgb_60.pkl",
    "ci_model_xgb_120.pkl"
)

Write-Host "`nChecking output files:" -ForegroundColor Yellow
$allGood = $true

foreach ($file in $expectedFiles) {
    $fullPath = Join-Path $OutputDir $file
    if (Test-Path $fullPath) {
        $size = (Get-Item $fullPath).Length / 1KB
        Write-Host "  ✓ $file" -NoNewline -ForegroundColor Green
        Write-Host " ($([math]::Round($size, 1)) KB)"
    } else {
        Write-Host "  ✗ $file (MISSING)" -ForegroundColor Red
        $allGood = $false
    }
}

if (-not $allGood) {
    Write-Host "`n⚠️  WARNING: Some files missing" -ForegroundColor Yellow
} else {
    Write-Host "`n✓ All model files present" -ForegroundColor Green
}

# Summary
Write-Host "`n" -NoNewline
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "TRAINING SUMMARY" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan

Write-Host "`n✅ Training complete!" -ForegroundColor Green
Write-Host "`nModel files saved to: $OutputDir" -ForegroundColor Yellow

Write-Host "`nTo use the models:" -ForegroundColor Yellow
Write-Host "  1. Start service: python main.py"
Write-Host "  2. Or rebuild Docker: docker-compose build; docker-compose up"

Write-Host "`n" -NoNewline
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
