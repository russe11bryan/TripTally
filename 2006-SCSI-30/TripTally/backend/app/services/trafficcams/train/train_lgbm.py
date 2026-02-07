"""
Traffic Congestion Prediction - LightGBM Training Script

This script trains a LightGBM model to predict future traffic congestion (CI values)
based on historical traffic camera data, time features, and lag features.

Usage:
    python train_lgbm.py [--data-path PATH] [--output-dir DIR] [--gpu]
"""

import argparse
import json
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from tqdm.auto import tqdm


class TqdmCallback:
    """Custom callback for tqdm progress bar during training"""
    def __init__(self, total_rounds):
        self.pbar = tqdm(total=total_rounds, desc="Training", unit="iter")
        self.best_iter = 0
        self.best_score = float('inf')
    
    def __call__(self, env):
        self.pbar.update(1)
        # Update description with latest score if available
        if env.evaluation_result_list:
            for data_name, metric_name, result, _ in env.evaluation_result_list:
                if data_name == 'valid' and metric_name == 'rmse':
                    self.pbar.set_postfix({'valid_rmse': f'{result:.4f}'})
                    if result < self.best_score:
                        self.best_score = result
                        self.best_iter = env.iteration
    
    def close(self):
        self.pbar.close()


def load_data(file_path):
    """Load processed training data from parquet file"""
    print(f"Loading data from: {file_path}")
    df = pd.read_parquet(file_path)
    print(f"Data shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    return df


def prepare_features(data):
    """Prepare features for training"""
    print("\nPreparing features...")
    
    # Define categorical and feature columns
    cat_feats = ['camera_id', 'res_class', 'dow_h']
    drop_cols = ['ts', 'y', 'error', 'CI']
    
    # Add y_logit if not exists (logit transformation of y)
    if 'y_logit' not in data.columns:
        print("Creating y_logit from y...")
        # Clip y to avoid log(0) or log(1)
        y_clipped = data['y'].clip(0.01, 0.99)
        data['y_logit'] = np.log(y_clipped / (1 - y_clipped))
        print(f"y_logit range: [{data['y_logit'].min():.4f}, {data['y_logit'].max():.4f}]")
    
    drop_cols.append('y_logit')  # Don't use as feature, only as target
    
    # Convert categorical features
    for c in cat_feats:
        if c in data.columns:
            data[c] = data[c].astype('category')
    
    # Get feature columns
    feature_cols = [c for c in data.columns if c not in drop_cols]
    num_cols = [c for c in feature_cols if c not in cat_feats]
    
    # Convert numeric columns to float32
    data[num_cols] = data[num_cols].apply(pd.to_numeric, errors='coerce').astype('float32')
    
    print(f"Categorical features: {cat_feats}")
    print(f"Total features: {len(feature_cols)}")
    
    return data, feature_cols, cat_feats


def split_data(data, split_ratio=0.95):
    """Split data into train and validation sets based on timestamp"""
    print(f"\nSplitting data at {split_ratio*100}% quantile...")
    
    cut = data['ts'].quantile(split_ratio)
    train = data[data['ts'] < cut].copy()
    valid = data[data['ts'] >= cut].copy()
    
    print(f"Train size: {len(train):,} rows")
    print(f"Valid size: {len(valid):,} rows")
    print(f"Split date: {cut}")
    
    return train, valid


def train_model(train, valid, feature_cols, cat_feats, 
                num_boost_round=2000, early_stopping_rounds=50, 
                use_gpu=False, learning_rate=0.02):
    """Train LightGBM model"""
    print("\nCreating LightGBM datasets...")
    
    # Create LightGBM datasets
    dtrain = lgb.Dataset(
        train[feature_cols], 
        label=train['y_logit'],
        categorical_feature=cat_feats, 
        free_raw_data=False
    )
    dvalid = lgb.Dataset(
        valid[feature_cols], 
        label=valid['y_logit'],
        categorical_feature=cat_feats, 
        reference=dtrain, 
        free_raw_data=False
    )
    
    # Define parameters
    params = {
        'objective': 'regression',          
        'metric': ['RMSE'],
        'learning_rate': learning_rate,
        'num_leaves': 255, 
        'max_depth': -1,
        'feature_fraction': 0.8,
        'bagging_fraction': 0.8, 
        'bagging_freq': 1,
        'min_data_in_leaf': 100,
        'max_bin': 127,
        'verbosity': -1
    }
    
    # Add GPU parameters if requested
    if use_gpu:
        params.update({
            'device_type': 'gpu',
            'gpu_platform_id': 0,
            'gpu_device_id': 0
        })
        print("\nTraining LightGBM regressor on GPU...")
    else:
        print("\nTraining LightGBM regressor on CPU...")
    
    print("="*60)
    print(f"Parameters: {params}")
    print(f"Number of boost rounds: {num_boost_round}")
    print(f"Early stopping rounds: {early_stopping_rounds}")
    print("="*60)
    
    # Initialize progress bar callback
    pbar_callback = TqdmCallback(total_rounds=num_boost_round)
    
    try:
        bst = lgb.train(
            params,
            dtrain,
            num_boost_round=num_boost_round,
            valid_sets=[dtrain, dvalid],
            valid_names=['train', 'valid'],
            callbacks=[
                lgb.early_stopping(stopping_rounds=early_stopping_rounds, verbose=False),
                lgb.log_evaluation(period=0),  # Disable default logging
                pbar_callback
            ]
        )
    finally:
        pbar_callback.close()
    
    print("="*60)
    print(f"✓ Training complete!")
    print(f"Best iteration: {bst.best_iteration}")
    print(f"Best score (RMSE): {bst.best_score['valid']['rmse']}")
    
    return bst, dtrain, dvalid, params


def evaluate_model(bst, valid, feature_cols):
    """Evaluate model on validation set"""
    print("\nGenerating predictions...")
    
    # Make predictions
    z_pred = bst.predict(valid[feature_cols], num_iteration=bst.best_iteration)
    
    # Convert z_pred (logit/raw prediction) to y_pred (CI values)
    y_pred = expit(z_pred)  # sigmoid transformation
    y_true = valid['y'].values
    
    print(f"z_pred range: [{z_pred.min():.4f}, {z_pred.max():.4f}]")
    print(f"y_pred range: [{y_pred.min():.4f}, {y_pred.max():.4f}]")
    print(f"y_true range: [{y_true.min():.4f}, {y_true.max():.4f}]")
    
    # Calculate metrics
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    
    print(f"\n=== Validation Metrics ===")
    print(f"MAE:  {mae:.4f}")
    print(f"RMSE: {rmse:.4f}")
    print(f"R²:   {r2:.4f}")
    
    return {
        'mae': mae,
        'rmse': rmse,
        'r2': r2,
        'z_pred': z_pred,
        'y_pred': y_pred,
        'y_true': y_true
    }


def save_model(bst, feature_cols, cat_feats, params, metrics=None, 
               version=None, outdir="models", dtrain=None, dvalid=None):
    """
    Save LightGBM booster + metadata + datasets for deterministic inference.
    
    Args:
        bst: Trained LightGBM booster
        feature_cols: List of feature column names in exact order
        cat_feats: List of categorical feature names
        params: Training parameters dictionary
        metrics: Dictionary of evaluation metrics
        version: Model version string (auto-generated if None)
        outdir: Output directory for model files
        dtrain: Training LightGBM Dataset (optional)
        dvalid: Validation LightGBM Dataset (optional)
    
    Returns:
        Tuple of (model_path, metadata_path)
    """
    Path(outdir).mkdir(parents=True, exist_ok=True)
    version = version or time.strftime("ci-lgbm-%Y%m%d_%H%M%S")
    model_path = Path(outdir) / f"{version}.txt"
    meta_path = Path(outdir) / f"{version}.meta.json"
    
    # Save model
    bst.save_model(str(model_path), num_iteration=bst.best_iteration)
    
    # Save datasets as binary (optional, for reproducibility)
    if dtrain is not None:
        train_bin_path = Path(outdir) / f"{version}.train.bin"
        dtrain.save_binary(str(train_bin_path))
        print(f"✓ Training dataset saved to: {train_bin_path}")
    
    if dvalid is not None:
        valid_bin_path = Path(outdir) / f"{version}.valid.bin"
        dvalid.save_binary(str(valid_bin_path))
        print(f"✓ Validation dataset saved to: {valid_bin_path}")
    
    # Save metadata
    meta = {
        "version": version,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "best_iteration": bst.best_iteration,
        "params": params,
        "feature_cols": list(feature_cols),
        "cat_feats": list(cat_feats),
        "target": "y_logit",
        "metrics": metrics or {},
    }
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    
    print(f"✓ Model saved to: {model_path}")
    print(f"✓ Metadata saved to: {meta_path}")
    return str(model_path), str(meta_path)


def main():
    """Main training pipeline"""
    parser = argparse.ArgumentParser(
        description='Train LightGBM model for traffic congestion prediction'
    )
    parser.add_argument(
        '--data-path', 
        type=str, 
        default='data/processed_training_data.parquet',
        help='Path to processed training data parquet file'
    )
    parser.add_argument(
        '--output-dir', 
        type=str, 
        default='models',
        help='Output directory for trained models'
    )
    parser.add_argument(
        '--gpu', 
        action='store_true',
        help='Use GPU for training (requires GPU-enabled LightGBM)'
    )
    parser.add_argument(
        '--num-rounds', 
        type=int, 
        default=2000,
        help='Number of boosting rounds'
    )
    parser.add_argument(
        '--early-stopping', 
        type=int, 
        default=50,
        help='Early stopping rounds'
    )
    parser.add_argument(
        '--learning-rate', 
        type=float, 
        default=0.02,
        help='Learning rate'
    )
    parser.add_argument(
        '--split-ratio', 
        type=float, 
        default=0.95,
        help='Train/validation split ratio (0-1)'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("Traffic Congestion Prediction - LightGBM Training Pipeline")
    print("="*60)
    
    # Load data
    data = load_data(args.data_path)
    
    # Prepare features
    data, feature_cols, cat_feats = prepare_features(data)
    
    # Split data
    train, valid = split_data(data, split_ratio=args.split_ratio)
    
    # Train model
    bst, dtrain, dvalid, params = train_model(
        train, 
        valid, 
        feature_cols, 
        cat_feats,
        num_boost_round=args.num_rounds,
        early_stopping_rounds=args.early_stopping,
        use_gpu=args.gpu,
        learning_rate=args.learning_rate
    )
    
    # Evaluate model
    results = evaluate_model(bst, valid, feature_cols)
    
    # Prepare metrics for saving
    metrics = {
        'valid_mae': float(results['mae']),
        'valid_rmse': float(results['rmse']),
        'valid_r2': float(results['r2'])
    }
    
    # Save model with metadata and datasets
    version = time.strftime("ci-lgbm-%Y%m%d_%H%M%S")
    model_path, meta_path = save_model(
        bst, 
        feature_cols, 
        cat_feats, 
        params, 
        metrics=metrics,
        version=version,
        outdir=args.output_dir,
        dtrain=dtrain,
        dvalid=dvalid
    )
    
    print("\n" + "="*60)
    print("Training pipeline completed successfully!")
    print(f"Model version: {version}")
    print(f"Model path: {model_path}")
    print(f"Metadata path: {meta_path}")
    print("="*60)
    
    return bst, results, version


if __name__ == "__main__":
    model, results, version = main()
