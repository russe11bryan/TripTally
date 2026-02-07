"""
Design Patterns Example Script
Demonstrates how to use the factory pattern to switch between implementations
"""

import os
import sys
from datetime import datetime

# Set up environment for testing
os.environ['REDIS_HOST'] = 'localhost'
os.environ['REPOSITORY_TYPE'] = 'csv'  # Start with CSV
os.environ['FORECASTER_TYPE'] = 'auto'  # Auto-select

from .config import Config
from .factory import RepositoryFactory, ForecasterFactory, ServiceContext, RepositoryType, ForecasterType
from .models import CIState, Camera


def print_section(title: str):
    """Print section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def demo_repository_pattern():
    """Demonstrate repository pattern"""
    print_section("REPOSITORY PATTERN DEMO")
    
    config = Config.from_env()
    
    # Create a sample CI state
    state = CIState(
        camera_id="1001",
        timestamp=datetime.now(),
        ci_value=0.65,
        vehicle_count=15,
        weighted_count=18.5,
        area_ratio=0.12,
        motion_score=0.45,
        img_width=640,
        img_height=480,
        minute_of_day=630,
        hour=10,
        day_of_week=1,
        is_weekend=0,
        sin_t_h=0.5,
        cos_t_h=0.866,
        model_version="yolov8n"
    )
    
    print("Created sample CI state:")
    print(f"  Camera: {state.camera_id}")
    print(f"  CI: {state.ci_value}")
    print(f"  Vehicles: {state.vehicle_count}")
    
    # Test each repository
    repositories = {
        "CSV": RepositoryType.CSV,
        "SQL": RepositoryType.SQL,
        "Redis": RepositoryType.REDIS
    }
    
    for name, repo_type in repositories.items():
        print(f"\n--- Testing {name} Repository ---")
        
        try:
            repo = RepositoryFactory.create(repo_type, config)
            print(f"✓ Created {repo.get_repository_name()} repository")
            
            # Health check
            if repo.health_check():
                print(f"✓ Health check passed")
            else:
                print(f"⚠ Health check failed (may need {name} running)")
                continue
            
            # Save state
            if repo.save_ci_state(state):
                print(f"✓ Saved CI state")
            
            # Retrieve state
            retrieved = repo.get_ci_state(state.camera_id)
            if retrieved:
                print(f"✓ Retrieved CI state")
            
        except Exception as e:
            print(f"✗ Error with {name}: {e}")


def demo_forecasting_pattern():
    """Demonstrate forecasting strategy pattern"""
    print_section("FORECASTING STRATEGY PATTERN DEMO")
    
    config = Config.from_env()
    
    # Create a sample CI state
    state = CIState(
        camera_id="1001",
        timestamp=datetime.now(),
        ci_value=0.55,
        vehicle_count=12,
        weighted_count=14.5,
        area_ratio=0.10,
        motion_score=0.35,
        img_width=640,
        img_height=480,
        minute_of_day=630,
        hour=10,
        day_of_week=1,
        is_weekend=0,
        sin_t_h=0.5,
        cos_t_h=0.866,
        model_version="yolov8n"
    )
    
    print("Created sample CI state for forecasting:")
    print(f"  Camera: {state.camera_id}")
    print(f"  Current CI: {state.ci_value}")
    
    # Test each forecaster
    forecasters = {
        "Simple": ForecasterType.SIMPLE,
        "ML": ForecasterType.ML,
        "Auto": ForecasterType.AUTO
    }
    
    for name, forecaster_type in forecasters.items():
        print(f"\n--- Testing {name} Forecaster ---")
        
        try:
            forecaster = ForecasterFactory.create(forecaster_type, config)
            print(f"✓ Created {forecaster.get_strategy_name()} forecaster")
            
            # Check availability
            if forecaster.is_available():
                print(f"✓ Forecaster is available")
                
                # Generate forecast
                forecast = forecaster.generate_forecast(state)
                print(f"✓ Generated forecast with {len(forecast.forecasts)} horizons")
                print(f"  Model version: {forecast.model_version}")
                
                # Show first few predictions
                print(f"\n  Sample predictions:")
                for i, f in enumerate(forecast.horizons[:5]):
                    print(f"    {f.horizon_minutes:3d} min: CI={f.predicted_ci:.3f}, confidence={f.confidence:.2f}")
            else:
                print(f"⚠ Forecaster not available (may need trained models)")
                
        except Exception as e:
            print(f"✗ Error with {name}: {e}")


def demo_service_context():
    """Demonstrate ServiceContext"""
    print_section("SERVICE CONTEXT DEMO")
    
    config = Config.from_env()
    
    print("Creating ServiceContext with auto-configuration...")
    context = ServiceContext.from_config(config)
    
    print(f"✓ Created context with:")
    print(f"  Repository: {context.repository.get_repository_name()}")
    print(f"  Forecaster: {context.forecaster.get_strategy_name()}")
    
    print("\n--- Switching Implementations ---")
    
    # Switch repository
    print("\nSwitching to CSV repository...")
    context.switch_repository("csv", config)
    print(f"✓ Now using: {context.repository.get_repository_name()}")
    
    # Switch forecaster
    print("\nSwitching to Simple forecaster...")
    context.switch_forecaster("simple", config)
    print(f"✓ Now using: {context.forecaster.get_strategy_name()}")
    
    # Switch back
    print("\nSwitching to SQL repository...")
    context.switch_repository("sql", config)
    print(f"✓ Now using: {context.repository.get_repository_name()}")
    
    print("\n✓ Runtime switching works!")


def demo_configuration():
    """Demonstrate configuration options"""
    print_section("CONFIGURATION DEMO")
    
    print("Current configuration from environment:")
    config = Config.from_env()
    
    print(f"\nRepository Settings:")
    print(f"  Type: {config.processing.repository_type}")
    print(f"  Data dir: {config.processing.data_dir}")
    print(f"  DB path: {config.processing.db_path}")
    
    print(f"\nForecaster Settings:")
    print(f"  Type: {config.processing.forecaster_type}")
    print(f"  Model dir: {config.processing.model_dir}")
    print(f"  Max history: {config.processing.max_history}")
    
    print(f"\nTo change configuration, set environment variables:")
    print(f"  export REPOSITORY_TYPE=redis    # redis, csv, sql")
    print(f"  export FORECASTER_TYPE=ml       # simple, ml, auto")
    print(f"  export MODEL_DIR=./my_models")
    print(f"  export DATA_DIR=./my_data")


def main():
    """Run all demos"""
    print("\n" + "=" * 80)
    print("  DESIGN PATTERNS DEMONSTRATION")
    print("  CI Forecasting System")
    print("=" * 80)
    
    try:
        # Run demos
        demo_configuration()
        demo_repository_pattern()
        demo_forecasting_pattern()
        demo_service_context()
        
        # Summary
        print_section("SUMMARY")
        print("✓ Repository Pattern: Tested CSV, SQL, Redis implementations")
        print("✓ Strategy Pattern: Tested Simple, ML, Auto forecasters")
        print("✓ Factory Pattern: Created instances dynamically")
        print("✓ Service Context: Switched implementations at runtime")
        
        print("\nKey Takeaways:")
        print("1. Easy to switch between implementations")
        print("2. Configure via environment variables")
        print("3. Runtime switching supported")
        print("4. Testable without dependencies")
        print("5. Extensible for new implementations")
        
        print("\n" + "=" * 80)
        print("  DEMO COMPLETE!")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
