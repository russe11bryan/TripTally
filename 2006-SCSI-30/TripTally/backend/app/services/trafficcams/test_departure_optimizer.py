"""
Test Departure Time Optimizer

Run this to verify the departure optimization feature works
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from domain.route_models import Point
from domain.geospatial_service import GeospatialService
from domain.departure_time_optimizer import DepartureTimeOptimizer, ETACalculationStrategy
from domain.camera_loader import get_camera_loader
from .factory import ServiceContext
from .config import Config


def test_departure_optimizer():
    """Test the departure optimizer with a sample route"""
    print("=" * 60)
    print("Testing Departure Time Optimizer")
    print("=" * 60)
    
    # Sample route: Orchard Road to NUS
    route_points = [
        Point(latitude=1.3521, longitude=103.8198),  # Orchard Road
        Point(latitude=1.3200, longitude=103.8000),  # Middle point
        Point(latitude=1.2966, longitude=103.7764),  # NUS
    ]
    
    original_eta = 25  # 25 minutes
    
    print(f"\n📍 Route: {len(route_points)} points")
    print(f"🕐 Original ETA: {original_eta} minutes")
    print(f"🔍 Search radius: 0.5 km")
    print(f"⏰ Forecast horizon: 120 minutes")
    
    # Setup dependencies
    config = Config()
    repository = ServiceContext.get_repository(config)
    geospatial = GeospatialService()
    camera_loader = get_camera_loader()
    
    # Create optimizer
    optimizer = DepartureTimeOptimizer(
        repository=repository,
        geospatial_service=geospatial,
        camera_loader=camera_loader
    )
    
    try:
        print("\n🔄 Analyzing traffic conditions...")
        
        # Find optimal departure time
        result = optimizer.find_optimal_departure(
            route_points=route_points,
            original_eta_minutes=original_eta,
            search_radius_km=0.5,
            forecast_horizon_minutes=120,
            time_interval_minutes=2
        )
        
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)
        
        print(f"\n📊 Analysis Summary:")
        print(f"  • Cameras analyzed: {result.cameras_analyzed}")
        print(f"  • Confidence score: {result.confidence_score:.0%}")
        
        print(f"\n🚦 Traffic Conditions:")
        print(f"  • Current average CI: {result.current_average_ci:.2f}")
        print(f"  • Optimal average CI: {result.optimal_average_ci:.2f}")
        
        print(f"\n⏱️ Recommended Departure:")
        print(f"  • Best time to leave: +{result.best_time_minutes_from_now} minutes from now")
        print(f"  • Departure time: {result.best_departure_time.strftime('%I:%M %p')}")
        
        print(f"\n🚗 ETA Comparison:")
        print(f"  • Original ETA: {result.original_eta_minutes} min")
        
        # Calculate current ETA
        eta_calc = ETACalculationStrategy()
        current_eta = eta_calc.calculate_eta_from_ci(
            original_eta,
            result.current_average_ci
        )
        print(f"  • If leaving now: {current_eta} min")
        print(f"  • If leaving at optimal time: {result.optimized_eta_minutes} min")
        print(f"  • Time saved: {result.time_saved_minutes} min")
        
        print(f"\n💡 Recommendation:")
        if result.best_time_minutes_from_now == 0:
            print("  ✅ Leave now! Traffic is good.")
        elif result.time_saved_minutes > 5:
            print(f"  ⏰ Wait {result.best_time_minutes_from_now} minutes")
            print(f"     You'll save {result.time_saved_minutes} minutes!")
        elif result.time_saved_minutes > 0:
            print(f"  ⚖️ Slight benefit to wait {result.best_time_minutes_from_now} minutes")
            print(f"     Could save {result.time_saved_minutes} minutes")
        else:
            print("  ➡️ Traffic is similar now and later")
        
        print("\n" + "=" * 60)
        print("✅ Test completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = test_departure_optimizer()
    sys.exit(0 if success else 1)
