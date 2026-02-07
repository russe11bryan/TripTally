"""
Data Analysis Script
Analyzes the processed training data to understand structure and patterns
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

def analyze_data(data_path: str = "train/data/processed_training_data.parquet"):
    """Analyze training data"""
    
    print("=" * 80)
    print("TRAINING DATA ANALYSIS")
    print("=" * 80)
    
    # Load data
    data_path = Path(data_path)
    if not data_path.exists():
        print(f"ERROR: Data file not found at {data_path}")
        return
    
    print(f"\nLoading data from: {data_path}")
    df = pd.read_parquet(data_path)
    
    # Basic info
    print(f"\n{'='*80}")
    print("DATASET OVERVIEW")
    print(f"{'='*80}")
    print(f"Shape: {df.shape} (rows x columns)")
    print(f"Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    
    # Columns
    print(f"\n{'='*80}")
    print("COLUMNS")
    print(f"{'='*80}")
    for i, col in enumerate(df.columns, 1):
        dtype = df[col].dtype
        null_count = df[col].isnull().sum()
        null_pct = 100 * null_count / len(df)
        print(f"{i:2d}. {col:25s} - {str(dtype):10s} - {null_count:6d} nulls ({null_pct:.1f}%)")
    
    # Date range
    if 'ts' in df.columns:
        df['ts'] = pd.to_datetime(df['ts'])
        print(f"\n{'='*80}")
        print("TIME RANGE")
        print(f"{'='*80}")
        print(f"Start: {df['ts'].min()}")
        print(f"End:   {df['ts'].max()}")
        print(f"Duration: {df['ts'].max() - df['ts'].min()}")
        print(f"Samples per camera: {len(df) / df['camera_id'].nunique():.1f} on average")
    
    # Camera coverage
    if 'camera_id' in df.columns:
        print(f"\n{'='*80}")
        print("CAMERA COVERAGE")
        print(f"{'='*80}")
        print(f"Unique cameras: {df['camera_id'].nunique()}")
        
        cam_counts = df['camera_id'].value_counts()
        print(f"Min samples per camera: {cam_counts.min()}")
        print(f"Max samples per camera: {cam_counts.max()}")
        print(f"Mean samples per camera: {cam_counts.mean():.1f}")
        print(f"Median samples per camera: {cam_counts.median():.1f}")
    
    # CI statistics
    if 'CI' in df.columns:
        print(f"\n{'='*80}")
        print("CI DISTRIBUTION")
        print(f"{'='*80}")
        print(df['CI'].describe())
        
        print(f"\nCI Quartiles:")
        print(f"  0-25%:   {(df['CI'] <= 0.25).sum():6d} samples ({100*(df['CI'] <= 0.25).sum()/len(df):.1f}%)")
        print(f"  25-50%:  {((df['CI'] > 0.25) & (df['CI'] <= 0.5)).sum():6d} samples")
        print(f"  50-75%:  {((df['CI'] > 0.5) & (df['CI'] <= 0.75)).sum():6d} samples")
        print(f"  75-100%: {(df['CI'] > 0.75).sum():6d} samples ({100*(df['CI'] > 0.75).sum()/len(df):.1f}%)")
    
    # Feature statistics
    feature_cols = ['veh_count', 'veh_wcount', 'area_ratio', 'motion']
    available_features = [col for col in feature_cols if col in df.columns]
    
    if available_features:
        print(f"\n{'='*80}")
        print("FEATURE STATISTICS")
        print(f"{'='*80}")
        for col in available_features:
            print(f"\n{col}:")
            print(df[col].describe())
    
    # Temporal features
    temporal_cols = ['hour', 'day_of_week', 'is_weekend']
    available_temporal = [col for col in temporal_cols if col in df.columns]
    
    if available_temporal:
        print(f"\n{'='*80}")
        print("TEMPORAL FEATURES")
        print(f"{'='*80}")
        for col in available_temporal:
            print(f"\n{col}:")
            print(df[col].value_counts().sort_index())
    
    # Correlations with CI
    if 'CI' in df.columns:
        print(f"\n{'='*80}")
        print("CORRELATION WITH CI")
        print(f"{'='*80}")
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        correlations = df[numeric_cols].corrwith(df['CI']).sort_values(ascending=False)
        
        print("\nTop positive correlations:")
        for col, corr in correlations.head(10).items():
            if col != 'CI':
                print(f"  {col:25s}: {corr:6.3f}")
        
        print("\nTop negative correlations:")
        for col, corr in correlations.tail(10).items():
            if col != 'CI':
                print(f"  {col:25s}: {corr:6.3f}")
    
    # Missing data patterns
    print(f"\n{'='*80}")
    print("MISSING DATA SUMMARY")
    print(f"{'='*80}")
    missing = df.isnull().sum()
    missing = missing[missing > 0].sort_values(ascending=False)
    
    if len(missing) > 0:
        for col, count in missing.items():
            pct = 100 * count / len(df)
            print(f"  {col:25s}: {count:6d} ({pct:.1f}%)")
    else:
        print("  No missing data!")
    
    # Sample data
    print(f"\n{'='*80}")
    print("SAMPLE DATA (first 5 rows)")
    print(f"{'='*80}")
    print(df.head())
    
    print(f"\n{'='*80}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*80}\n")
    
    return df


if __name__ == "__main__":
    import sys
    
    data_path = "train/data/processed_training_data.parquet"
    if len(sys.argv) > 1:
        data_path = sys.argv[1]
    
    analyze_data(data_path)
