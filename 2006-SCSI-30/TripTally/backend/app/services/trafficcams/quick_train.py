"""
Quick Training Script
Runs the complete training pipeline with one command
"""

import sys
from pathlib import Path

def main():
    """Run training pipeline"""
    
    print("=" * 80)
    print("CI FORECASTING MODEL TRAINING PIPELINE")
    print("=" * 80)
    
    # Default paths
    data_path = "train/data/processed_training_data.parquet"
    output_dir = "./models"
    
    # Parse args
    if len(sys.argv) > 1:
        data_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    
    print(f"\nConfiguration:")
    print(f"  Data: {data_path}")
    print(f"  Output: {output_dir}")
    
    # Check data exists
    if not Path(data_path).exists():
        print(f"\n❌ ERROR: Training data not found at {data_path}")
        print("\nPlease provide the correct path:")
        print(f"  python quick_train.py <path_to_data> [output_dir]")
        sys.exit(1)
    
    # Step 1: Analyze data
    print("\n" + "=" * 80)
    print("STEP 1: Analyzing Training Data")
    print("=" * 80)
    
    try:
        from analyze_data import analyze_data
        df = analyze_data(data_path)
        
        if df is None or len(df) == 0:
            print("\n❌ ERROR: No data loaded")
            sys.exit(1)
        
        print("\n✅ Data analysis complete")
        
    except Exception as e:
        print(f"\n❌ ERROR during data analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Step 2: Train models
    print("\n" + "=" * 80)
    print("STEP 2: Training ML Models")
    print("=" * 80)
    
    try:
        from train_model import CIModelTrainer
        
        trainer = CIModelTrainer(data_path, output_dir)
        models, metrics = trainer.train()
        
        print("\n✅ Model training complete")
        
    except Exception as e:
        print(f"\n❌ ERROR during training: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Step 3: Verify models
    print("\n" + "=" * 80)
    print("STEP 3: Verifying Models")
    print("=" * 80)
    
    try:
        output_path = Path(output_dir)
        
        # Check files
        files_to_check = [
            "ci_scaler.pkl",
            "ci_model_metadata.json"
        ]
        
        for horizon in [2, 5, 10, 15, 30, 60, 120]:
            files_to_check.append(f"ci_model_xgb_{horizon}.pkl")
        
        print("\nChecking output files:")
        all_good = True
        for fname in files_to_check:
            fpath = output_path / fname
            if fpath.exists():
                size = fpath.stat().st_size / 1024
                print(f"  ✓ {fname:35s} ({size:8.1f} KB)")
            else:
                print(f"  ✗ {fname:35s} (MISSING)")
                all_good = False
        
        if not all_good:
            print("\n⚠️  WARNING: Some files missing")
        else:
            print("\n✅ All model files present")
        
    except Exception as e:
        print(f"\n❌ ERROR during verification: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 4: Summary
    print("\n" + "=" * 80)
    print("TRAINING SUMMARY")
    print("=" * 80)
    
    print(f"\n✅ Training complete!")
    print(f"\nModel files saved to: {output_dir}")
    print(f"\nTo use the models:")
    print(f"  1. Copy models to deployment: cp -r {output_dir} /path/to/deployment/")
    print(f"  2. Start service: python main.py")
    print(f"  3. Or rebuild Docker: docker-compose build && docker-compose up")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
