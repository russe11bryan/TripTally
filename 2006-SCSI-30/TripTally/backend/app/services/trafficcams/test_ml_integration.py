"""
ML Integration Test Script
Verifies that ML components are properly integrated
"""

import sys
from pathlib import Path


def test_imports():
    """Test that all ML modules can be imported"""
    print("Testing imports...")
    
    try:
        import train_model
        print("  ✓ train_model")
    except ImportError as e:
        print(f"  ✗ train_model: {e}")
        return False
    
    try:
        import ml_forecaster
        print("  ✓ ml_forecaster")
    except ImportError as e:
        print(f"  ✗ ml_forecaster: {e}")
        return False
    
    try:
        import analyze_data
        print("  ✓ analyze_data")
    except ImportError as e:
        print(f"  ✗ analyze_data: {e}")
        return False
    
    try:
        import quick_train
        print("  ✓ quick_train")
    except ImportError as e:
        print(f"  ✗ quick_train: {e}")
        return False
    
    return True


def test_ml_libraries():
    """Test that required ML libraries are installed"""
    print("\nTesting ML libraries...")
    
    libs = {
        'sklearn': 'scikit-learn',
        'xgboost': 'xgboost',
        'joblib': 'joblib',
        'pandas': 'pandas',
        'numpy': 'numpy'
    }
    
    all_ok = True
    for module, name in libs.items():
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name} (run: pip install {name})")
            all_ok = False
    
    return all_ok


def test_ml_forecaster_instantiation():
    """Test that MLForecaster can be instantiated"""
    print("\nTesting MLForecaster instantiation...")
    
    try:
        from ml_forecaster import MLForecaster
        forecaster = MLForecaster(model_dir="./models")
        
        if forecaster.models:
            print(f"  ✓ MLForecaster loaded {len(forecaster.models)} models")
        else:
            print("  ⚠ MLForecaster instantiated but no models loaded")
            print("    (This is OK if you haven't trained models yet)")
        
        return True
    except Exception as e:
        print(f"  ✗ MLForecaster instantiation failed: {e}")
        return False


def test_service_integration():
    """Test that service.py uses MLForecaster"""
    print("\nTesting service integration...")
    
    try:
        with open('service.py', 'r') as f:
            content = f.read()
        
        if 'from ml_forecaster import MLForecaster' in content:
            print("  ✓ service.py imports MLForecaster")
        else:
            print("  ✗ service.py does not import MLForecaster")
            return False
        
        if 'MLForecaster(model_dir=' in content or 'MLForecaster(' in content:
            print("  ✓ service.py instantiates MLForecaster")
        else:
            print("  ✗ service.py does not instantiate MLForecaster")
            return False
        
        return True
    except Exception as e:
        print(f"  ✗ Error reading service.py: {e}")
        return False


def test_training_data_path():
    """Test if training data exists"""
    print("\nTesting training data...")
    
    data_path = Path("train/data/processed_training_data.parquet")
    
    if data_path.exists():
        size = data_path.stat().st_size / (1024 * 1024)
        print(f"  ✓ Training data found ({size:.2f} MB)")
        return True
    else:
        print(f"  ⚠ Training data not found at {data_path}")
        print("    (You can still run the service with fallback forecasting)")
        return None  # Not an error, just info


def test_models_directory():
    """Test if models directory exists and has models"""
    print("\nTesting models directory...")
    
    models_dir = Path("./models")
    
    if not models_dir.exists():
        print("  ⚠ Models directory does not exist")
        print("    (Run 'make train' or 'python quick_train.py' to create)")
        return None
    
    print(f"  ✓ Models directory exists")
    
    # Check for expected files
    expected = [
        "ci_scaler.pkl",
        "ci_model_metadata.json",
        "ci_model_xgb_2.pkl",
        "ci_model_xgb_5.pkl",
        "ci_model_xgb_10.pkl",
        "ci_model_xgb_15.pkl",
        "ci_model_xgb_30.pkl",
        "ci_model_xgb_60.pkl",
        "ci_model_xgb_120.pkl"
    ]
    
    found = 0
    for fname in expected:
        if (models_dir / fname).exists():
            found += 1
    
    if found == len(expected):
        print(f"  ✓ All {found} model files found")
        return True
    elif found > 0:
        print(f"  ⚠ Only {found}/{len(expected)} model files found")
        return None
    else:
        print("  ⚠ No model files found")
        print("    (Run 'make train' or 'python quick_train.py' to train)")
        return None


def main():
    """Run all tests"""
    print("=" * 80)
    print("ML INTEGRATION TEST")
    print("=" * 80)
    
    results = []
    
    # Critical tests
    results.append(("Imports", test_imports()))
    results.append(("ML Libraries", test_ml_libraries()))
    results.append(("MLForecaster", test_ml_forecaster_instantiation()))
    results.append(("Service Integration", test_service_integration()))
    
    # Informational tests
    results.append(("Training Data", test_training_data_path()))
    results.append(("Models", test_models_directory()))
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    critical_pass = all(r[1] == True for r in results[:4])
    
    print("\nCritical checks:")
    for name, result in results[:4]:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print("\nOptional checks:")
    for name, result in results[4:]:
        if result == True:
            status = "✓ OK"
        elif result == None:
            status = "⚠ INFO"
        else:
            status = "✗ FAIL"
        print(f"  {status}: {name}")
    
    print("\n" + "=" * 80)
    
    if critical_pass:
        print("✅ ML INTEGRATION WORKING!")
        print("\nYour system is ready to use ML forecasting.")
        print("\nNext steps:")
        print("  1. If you have training data: run 'make train' or '.\train.ps1'")
        print("  2. Start service: python main.py")
        print("  3. Check logs for 'Successfully loaded N ML models'")
        print("\nWithout training data, the system will use fallback forecasting.")
        return 0
    else:
        print("❌ INTEGRATION ISSUES DETECTED")
        print("\nPlease fix the failed checks above.")
        print("\nCommon fixes:")
        print("  - Install dependencies: pip install -r requirements.txt")
        print("  - Check that all new files exist")
        print("  - Verify service.py was updated correctly")
        return 1


if __name__ == "__main__":
    sys.exit(main())
