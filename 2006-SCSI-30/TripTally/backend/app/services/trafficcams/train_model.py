"""
ML Model Trainer for CI Forecasting
Trains LSTM and XGBoost models on historical data
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
import joblib
import json

# ML libraries
try:
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    import xgboost as xgb
except ImportError as e:
    print(f"Warning: Some ML libraries not installed: {e}")

from .logger import get_logger

logger = get_logger("ml_trainer")


class CIModelTrainer:
    """Train ML models for CI forecasting"""
    
    def __init__(self, data_path: str, output_dir: str = "./models"):
        self.data_path = Path(data_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.scaler = StandardScaler()
        self.models = {}
        
    def load_data(self) -> pd.DataFrame:
        """Load and validate training data"""
        logger.info(f"Loading data from {self.data_path}")
        
        if not self.data_path.exists():
            raise FileNotFoundError(f"Training data not found: {self.data_path}")
        
        df = pd.read_parquet(self.data_path)
        logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
        
        # Show data info
        logger.info(f"Columns: {list(df.columns)}")
        logger.info(f"Date range: {df['ts'].min()} to {df['ts'].max()}")
        
        return df
    
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer features for ML"""
        logger.info("Creating features...")
        
        df = df.copy()
        
        # Sort by camera and time
        df = df.sort_values(['camera_id', 'ts'])
        
        # Temporal features (if not already present)
        if 'hour' not in df.columns:
            df['hour'] = pd.to_datetime(df['ts']).dt.hour
        if 'day_of_week' not in df.columns:
            df['day_of_week'] = pd.to_datetime(df['ts']).dt.dayofweek
        if 'minute_of_day' not in df.columns:
            df['minute_of_day'] = (
                pd.to_datetime(df['ts']).dt.hour * 60 + 
                pd.to_datetime(df['ts']).dt.minute
            )
        
        # Cyclical encoding
        if 'sin_t_h' not in df.columns:
            df['sin_t_h'] = np.sin(2 * np.pi * df['hour'] / 24)
        if 'cos_t_h' not in df.columns:
            df['cos_t_h'] = np.cos(2 * np.pi * df['hour'] / 24)
        
        # Lag features per camera
        for lag in [1, 2, 3, 6, 12]:
            col_name = f'CI_lag_{lag}'
            if col_name not in df.columns:
                df[col_name] = df.groupby('camera_id')['CI'].shift(lag)
        
        # Rolling statistics per camera
        for window in [6, 12, 30]:
            col_name = f'CI_roll_mean_{window}'
            if col_name not in df.columns:
                df[col_name] = (
                    df.groupby('camera_id')['CI']
                    .rolling(window=window, min_periods=1)
                    .mean()
                    .reset_index(level=0, drop=True)
                )
        
        # Rate of change
        if 'CI_diff' not in df.columns:
            df['CI_diff'] = df.groupby('camera_id')['CI'].diff()
        
        logger.info(f"Created features, shape: {df.shape}")
        return df
    
    def prepare_training_data(self, df: pd.DataFrame, horizons: list = [2, 5, 10, 15, 30, 60, 120]):
        """Prepare X, y for multiple forecast horizons"""
        logger.info("Preparing training data for multiple horizons...")
        
        # Feature columns
        feature_cols = [
            'veh_count', 'veh_wcount', 'area_ratio', 'motion',
            'hour', 'day_of_week', 'minute_of_day', 'is_weekend',
            'sin_t_h', 'cos_t_h',
            'CI_lag_1', 'CI_lag_2', 'CI_lag_3', 'CI_lag_6', 'CI_lag_12',
            'CI_roll_mean_6', 'CI_roll_mean_12', 'CI_roll_mean_30',
            'CI_diff'
        ]
        
        # Filter to available columns
        feature_cols = [c for c in feature_cols if c in df.columns]
        logger.info(f"Using {len(feature_cols)} features: {feature_cols}")
        
        # Create target variables for each horizon
        df = df.sort_values(['camera_id', 'ts'])
        
        for h in horizons:
            # Shift CI backwards by h steps (2-minute intervals)
            df[f'CI_target_{h}'] = df.groupby('camera_id')['CI'].shift(-h)
        
        # Drop rows with missing targets
        df = df.dropna(subset=[f'CI_target_{h}' for h in horizons])
        
        # Drop rows with missing features
        df = df.dropna(subset=feature_cols)
        
        logger.info(f"Training data ready: {len(df)} samples")
        
        return df, feature_cols, horizons
    
    def train_xgboost_models(self, df: pd.DataFrame, feature_cols: list, horizons: list):
        """Train separate XGBoost model for each horizon"""
        logger.info("Training XGBoost models...")
        
        X = df[feature_cols].values
        
        # Standardize features
        X_scaled = self.scaler.fit_transform(X)
        
        models = {}
        metrics = {}
        
        for horizon in horizons:
            logger.info(f"Training model for {horizon}-minute horizon...")
            
            y = df[f'CI_target_{horizon}'].values
            
            # Time series split
            tscv = TimeSeriesSplit(n_splits=3)
            
            best_model = None
            best_score = float('inf')
            
            for train_idx, val_idx in tscv.split(X_scaled):
                X_train, X_val = X_scaled[train_idx], X_scaled[val_idx]
                y_train, y_val = y[train_idx], y[val_idx]
                
                # Train XGBoost
                model = xgb.XGBRegressor(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                    n_jobs=-1
                )
                
                model.fit(
                    X_train, y_train,
                    eval_set=[(X_val, y_val)],
                    early_stopping_rounds=10,
                    verbose=False
                )
                
                # Evaluate
                y_pred = model.predict(X_val)
                mse = mean_squared_error(y_val, y_pred)
                
                if mse < best_score:
                    best_score = mse
                    best_model = model
            
            # Final evaluation on last fold
            y_pred = best_model.predict(X_val)
            
            metrics[horizon] = {
                'mse': mean_squared_error(y_val, y_pred),
                'rmse': np.sqrt(mean_squared_error(y_val, y_pred)),
                'mae': mean_absolute_error(y_val, y_pred),
                'r2': r2_score(y_val, y_pred)
            }
            
            logger.info(
                f"  {horizon}min - RMSE: {metrics[horizon]['rmse']:.4f}, "
                f"MAE: {metrics[horizon]['mae']:.4f}, R²: {metrics[horizon]['r2']:.4f}"
            )
            
            models[f'xgb_{horizon}'] = best_model
        
        return models, metrics
    
    def save_models(self, models: dict, feature_cols: list, metrics: dict):
        """Save trained models and metadata"""
        logger.info("Saving models...")
        
        # Save scaler
        scaler_path = self.output_dir / "ci_scaler.pkl"
        joblib.dump(self.scaler, scaler_path)
        logger.info(f"Saved scaler to {scaler_path}")
        
        # Save each model
        for name, model in models.items():
            model_path = self.output_dir / f"ci_model_{name}.pkl"
            joblib.dump(model, model_path)
            logger.info(f"Saved {name} to {model_path}")
        
        # Save metadata
        metadata = {
            'trained_at': datetime.now().isoformat(),
            'feature_columns': feature_cols,
            'horizons': [int(k.split('_')[1]) for k in models.keys()],
            'metrics': {k: {mk: float(mv) for mk, mv in v.items()} 
                       for k, v in metrics.items()},
            'model_type': 'xgboost',
            'scaler': 'StandardScaler'
        }
        
        metadata_path = self.output_dir / "ci_model_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Saved metadata to {metadata_path}")
    
    def train(self):
        """Full training pipeline"""
        logger.info("=" * 60)
        logger.info("Starting CI ML Model Training")
        logger.info("=" * 60)
        
        # Load data
        df = self.load_data()
        
        # Engineer features
        df = self.create_features(df)
        
        # Prepare training data
        horizons = [2, 5, 10, 15, 30, 60, 120]
        df, feature_cols, horizons = self.prepare_training_data(df, horizons)
        
        # Train models
        models, metrics = self.train_xgboost_models(df, feature_cols, horizons)
        
        # Save everything
        self.save_models(models, feature_cols, metrics)
        
        logger.info("=" * 60)
        logger.info("Training Complete!")
        logger.info("=" * 60)
        
        return models, metrics


def main():
    """Run training"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Train CI forecasting models')
    parser.add_argument(
        '--data',
        default='train/data/processed_training_data.parquet',
        help='Path to training data'
    )
    parser.add_argument(
        '--output',
        default='./models',
        help='Output directory for models'
    )
    
    args = parser.parse_args()
    
    trainer = CIModelTrainer(args.data, args.output)
    trainer.train()


if __name__ == "__main__":
    main()
