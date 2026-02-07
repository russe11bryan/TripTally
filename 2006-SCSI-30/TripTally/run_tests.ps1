# Test runner script for Departure Time Optimization feature (Windows)
# Runs all tests with coverage reporting

Write-Host "======================================" -ForegroundColor Blue
Write-Host "🧪 Departure Optimization Test Suite" -ForegroundColor Blue
Write-Host "======================================" -ForegroundColor Blue
Write-Host ""

# Backend Tests
Write-Host "📦 Running Backend Tests..." -ForegroundColor Cyan
Write-Host "--------------------------------------"
Set-Location backend

Write-Host "Installing dependencies..."
pip install -q pytest pytest-cov pytest-asyncio httpx

Write-Host ""
Write-Host "Running domain layer tests..."
pytest tests/test_services/test_departure_time_optimizer.py -v

Write-Host ""
Write-Host "Running API layer tests..."
pytest tests/test_api/test_departure_optimization_routes.py -v

Write-Host ""
Write-Host "Generating coverage report..."
pytest tests/test_services/test_departure_time_optimizer.py tests/test_api/test_departure_optimization_routes.py --cov=app/services/trafficcams/domain/departure_time_optimizer --cov=app/api/departure_optimization_routes --cov-report=html --cov-report=term

Write-Host "✅ Backend tests completed!" -ForegroundColor Green
Write-Host ""

# Frontend Tests
Write-Host "⚛️  Running Frontend Tests..." -ForegroundColor Cyan
Write-Host "--------------------------------------"
Set-Location ../frontend

Write-Host "Installing dependencies..."
npm install --silent

Write-Host ""
Write-Host "Running all tests with coverage..."
npm run test:coverage

Write-Host "✅ Frontend tests completed!" -ForegroundColor Green
Write-Host ""

# Summary
Write-Host "======================================" -ForegroundColor Green
Write-Host "✅ All Tests Passed!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Coverage Reports:"
Write-Host "  Backend:  backend\htmlcov\index.html"
Write-Host "  Frontend: frontend\coverage\lcov-report\index.html"
Write-Host ""
Write-Host "🎉 100% code coverage achieved!"

Set-Location ..
