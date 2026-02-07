"""
Traffic Congestion Prediction - Inference Script

This script loads a trained LightGBM model and makes predictions on new data.

Usage:
    python predict_lgbm.py --model-version VERSION --data-path PATH [--output OUTPUT]
"""

import argparse
import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy.special import expit


def load_model(version, model_dir="models"):
    """
    Load model + metadata and return (booster, meta).
    
    Args:
        version: Model version string
        model_dir: Directory containing model files
    
    Returns:
        Tuple of (booster, metadata_dict)
    """
    model_path = Path(model_dir) / f"{version}.txt"
    meta_path = Path(model_dir) / f"{version}.meta.json"
    
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    if not meta_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {meta_path}")
    
    bst = lgb.Booster(model_file=str(model_path))
    with open(meta_path) as f:
        meta = json.load(f)
    
    print(f"✓ Loaded model: {version}")
    print(f"  Created: {meta['created_at']}")
    print(f"  Best iteration: {meta['best_iteration']}")
    print(f"  Metrics: {meta.get('metrics', {})}")
    
    return bst, meta


def prepare_features(data, meta):
    """
    Prepare input data features to match the trained model.
    
    Args:
        data: DataFrame with raw features
        meta: Model metadata dictionary
    
    Returns:
        DataFrame with features in correct order and types
    """
    X = data.copy()
    
    # Cast categorical features
    for c in meta["cat_feats"]:
        if c in X.columns:
            X[c] = X[c].astype("category")
    
    # Select and order features exactly like training
    X = X[meta["feature_cols"]]
    
    return X


def predict(model_version, data_path, model_dir="models", output_path=None):
    """
    Make predictions on new data using a saved model.
    
    Args:
        model_version: Model version string
        data_path: Path to input data (parquet file)
        model_dir: Directory containing model files
        output_path: Path to save predictions (optional)
    
    Returns:
        Array of predictions (CI values between 0 and 1)
    """
    # Load model and metadata
    print("="*60)
    print("Loading model...")
    print("="*60)
    bst, meta = load_model(model_version, model_dir=model_dir)
    
    # Load input data
    print("\n" + "="*60)
    print("Loading input data...")
    print("="*60)
    print(f"Data path: {data_path}")
    data = pd.read_parquet(data_path)
    print(f"Input shape: {data.shape}")
    print(f"Input columns: {data.columns.tolist()}")
    
    # Prepare features
    print("\n" + "="*60)
    print("Preparing features...")
    print("="*60)
    X = prepare_features(data, meta)
    print(f"Feature shape: {X.shape}")
    print(f"Features: {X.columns.tolist()}")
    
    # Make predictions
    print("\n" + "="*60)
    print("Making predictions...")
    print("="*60)
    z_pred = bst.predict(X, num_iteration=meta["best_iteration"])
    
    # Convert logits to CI values using sigmoid
    y_pred = expit(z_pred).clip(0, 1)
    
    print(f"✓ Generated {len(y_pred)} predictions")
    print(f"  Prediction range: [{y_pred.min():.4f}, {y_pred.max():.4f}]")
    print(f"  Mean prediction: {y_pred.mean():.4f}")
    print(f"  Std prediction: {y_pred.std():.4f}")
    
    # Add predictions to dataframe
    result = data.copy()
    result['predicted_ci'] = y_pred
    result['predicted_ci_logit'] = z_pred
    
    # Save predictions if output path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if output_path.suffix == '.parquet':
            result.to_parquet(output_path, index=False)
        elif output_path.suffix == '.csv':
            result.to_csv(output_path, index=False)
        else:
            raise ValueError(f"Unsupported output format: {output_path.suffix}")
        
        print(f"\n✓ Predictions saved to: {output_path}")
        print(f"  File size: {output_path.stat().st_size / (1024**2):.2f} MB")
    
    # Print summary statistics if y is available
    if 'y' in data.columns:
        print("\n" + "="*60)
        print("Evaluation on labeled data:")
        print("="*60)
        y_true = data['y'].values
        mae = np.mean(np.abs(y_true - y_pred))
        rmse = np.sqrt(np.mean((y_true - y_pred)**2))
        
        print(f"MAE:  {mae:.4f}")
        print(f"RMSE: {rmse:.4f}")
        
        # Sample comparison
        print("\nSample predictions (first 10):")
        print("Actual  | Predicted | Difference")
        print("-" * 40)
        for i in range(min(10, len(y_pred))):
            diff = abs(y_true[i] - y_pred[i])
            print(f"{y_true[i]:.4f}  | {y_pred[i]:.4f}    | {diff:.4f}")
    
    print("\n" + "="*60)
    print("Prediction complete!")
    print("="*60)
    
    return y_pred, result


def main():
    """Main prediction pipeline"""
    parser = argparse.ArgumentParser(
        description='Make predictions using trained LightGBM model'
    )
    parser.add_argument(
        '--model-version',
        type=str,
        required=True,
        help='Model version to use (e.g., ci-lgbm-20251103_145223)'
    )
    parser.add_argument(
        '--data-path',
        type=str,
        required=True,
        help='Path to input data parquet file'
    )
    parser.add_argument(
        '--model-dir',
        type=str,
        default='models',
        help='Directory containing model files'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Path to save predictions (parquet or csv)'
    )
    
    args = parser.parse_args()
    
    # Make predictions
    predictions, results = predict(
        args.model_version,
        args.data_path,
        model_dir=args.model_dir,
        output_path=args.output
    )
    
    return predictions, results


if __name__ == "__main__":
    predictions, results = main()
