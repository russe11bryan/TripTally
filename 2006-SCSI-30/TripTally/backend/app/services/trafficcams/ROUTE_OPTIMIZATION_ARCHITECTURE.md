# Route Optimization Service Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend / Client                        │
│         (React, Mobile App, or any HTTP client)                  │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP/JSON
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                      FastAPI Application                         │
│                     (app/main.py)                                │
│                                                                   │
│  Routers:                                                         │
│  ├─ /api/traffic/route/optimize                                  │
│  ├─ /api/traffic/route/cameras-along-route                       │
│  └─ /api/traffic/route/health                                    │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│              API Layer (Presentation)                            │
│        api/route_optimization_routes.py                          │
│                                                                   │
│  Responsibilities:                                                │
│  ├─ HTTP request validation (Pydantic)                           │
│  ├─ Response serialization                                       │
│  ├─ Error handling                                               │
│  └─ Dependency injection (get_optimizer_service)                 │
└─────────────────────┬───────────────────────┬───────────────────┘
                      │                       │
        ┌─────────────▼──────────┐   ┌────────▼──────────┐
        │ RouteOptimizationService│   │ GeospatialService │
        │  (Business Logic)       │   │  (Domain Service) │
        │                         │   │                   │
        │ domain/route_optimizer.py│   │ domain/geospatial│
        │                         │   │    _service.py    │
        │ Responsibilities:       │   │                   │
        │ ├─ Departure analysis   │   │ Responsibilities: │
        │ ├─ Traffic estimation   │   │ ├─ Distance calc  │
        │ ├─ Time optimization    │   │ ├─ Route matching │
        │ └─ Confidence scoring   │   │ └─ Length calc    │
        └─────────────┬───────────┘   └───────────────────┘
                      │
         ┌────────────▼─────────────┐
         │    ServiceContext        │
         │    (Factory Pattern)     │
         │                          │
         │  Provides:               │
         │  ├─ Repository instance  │
         │  └─ Forecaster instance  │
         └────────────┬─────────────┘
                      │
         ┌────────────▼─────────────┐
         │   DataRepository         │
         │   (Interface/Pattern)    │
         │                          │
         │  Implementations:        │
         │  ├─ RedisRepository      │
         │  ├─ CSVRepository        │
         │  └─ SQLRepository        │
         │                          │
         │  Methods:                │
         │  ├─ get_camera_metadata()│
         │  ├─ get_ci_state()       │
         │  ├─ get_forecast()       │
         │  └─ list_cameras()       │
         └──────────────────────────┘
```

## Component Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                       Domain Layer                            │
│                    (Pure Business Logic)                      │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐  │
│  │             Domain Models (route_models.py)            │  │
│  │                                                          │  │
│  │  • Point                  • DepartureOption            │  │
│  │  • LineString             • RouteOptimizationResult    │  │
│  │  • RouteCameraInfo        • TrafficLevel (Enum)        │  │
│  │  • CameraTrafficInfo                                   │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌──────────────────────┐    ┌────────────────────────────┐  │
│  │  GeospatialService   │    │ RouteOptimizationService   │  │
│  │  (geospatial_service │    │   (route_optimizer.py)     │  │
│  │        .py)          │    │                            │  │
│  │                      │    │  Uses:                     │  │
│  │  • haversine_distance│    │  • GeospatialService       │  │
│  │  • point_to_line     │────▶  • DataRepository          │  │
│  │  • find_cameras      │    │                            │  │
│  │  • calculate_length  │    │  Produces:                 │  │
│  │                      │    │  • DepartureOption         │  │
│  │  (No dependencies)   │    │  • RouteOptimizationResult │  │
│  └──────────────────────┘    └────────────────────────────┘  │
│                                                                │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                    Application Layer                          │
│                   (Orchestration & API)                       │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐  │
│  │         API Routes (route_optimization_routes.py)      │  │
│  │                                                          │  │
│  │  • POST /optimize                                       │  │
│  │  • GET /cameras-along-route                            │  │
│  │  • GET /health                                          │  │
│  │                                                          │  │
│  │  Pydantic Models:                                       │  │
│  │  • RouteOptimizationRequest                            │  │
│  │  • RouteOptimizationResponse                           │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                                │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                   Infrastructure Layer                        │
│                (Storage & External Services)                  │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐    │
│  │           DataRepository (Interface)                 │    │
│  └──────────┬────────────┬─────────────┬────────────────┘    │
│             │            │             │                      │
│    ┌────────▼──────┐ ┌──▼──────────┐ ┌▼──────────────┐      │
│    │ Redis         │ │ CSV         │ │ SQL           │      │
│    │ Repository    │ │ Repository  │ │ Repository    │      │
│    │               │ │             │ │               │      │
│    │ (In-memory)   │ │ (File-based)│ │ (Database)    │      │
│    └───────────────┘ └─────────────┘ └───────────────┘      │
│                                                                │
└──────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
┌─────────┐
│ Client  │
└────┬────┘
     │ 1. POST /optimize
     │    {route_points, eta}
     ▼
┌────────────────┐
│  API Router    │
└────┬───────────┘
     │ 2. Validate & parse request
     ▼
┌──────────────────────────┐
│ get_optimizer_service()  │ (Singleton pattern)
│                          │
│ Creates:                 │
│ ├─ ServiceContext        │
│ ├─ GeospatialService     │
│ └─ RouteOptimizationSvc  │
└────┬─────────────────────┘
     │ 3. Call optimizer.optimize_route()
     ▼
┌───────────────────────────────────────────┐
│  RouteOptimizationService.optimize_route()│
└────┬─────┬────────────┬───────────────────┘
     │     │            │
     │ 4a. │            │ 4b. Get camera data
     │ Get │            │     from repository
     │ all │            ▼
     │ cams│     ┌──────────────┐
     │     │     │ Repository   │
     │     │     │ ├─ list()    │
     │     │     │ ├─ get_meta()│
     │     │     │ ├─ get_state()│
     │     │     │ └─ get_forecast()│
     │     │     └──────────────┘
     │     │            │
     │     │ 5. Match   │ 6. Return data
     │     │    cameras │
     │     │    to route│
     │     ▼            ▼
     │ ┌───────────────────┐
     │ │ GeospatialService │
     │ │ find_cameras_     │
     │ │ along_route()     │
     │ └───────────────────┘
     │          │
     │ 7. For each time horizon (0, 10, 20...120):
     │    ├─ Get forecast CI
     │    ├─ Calculate avg CI
     │    ├─ Estimate travel time
     │    └─ Calculate confidence
     │
     │ 8. Select best departure (lowest CI)
     │
     ▼
┌────────────────────────┐
│ RouteOptimizationResult│
│ ├─ best_departure      │
│ ├─ alternatives        │
│ └─ route_cameras       │
└────┬───────────────────┘
     │ 9. Convert to response format
     ▼
┌────────────────────┐
│ API Response       │
│ (JSON)             │
│                    │
│ {                  │
│   "success": true, │
│   "best_departure":│
│   {                │
│     "minutes_from_ │
│      now": 30,     │
│     ...            │
│   }                │
│ }                  │
└────┬───────────────┘
     │ 10. Return to client
     ▼
┌─────────┐
│ Client  │
└─────────┘
```

## Dependency Graph

```
route_optimization_routes.py
    │
    ├─ Depends on: RouteOptimizationService
    │   │
    │   ├─ Depends on: DataRepository (interface)
    │   │   │
    │   │   └─ Implemented by:
    │   │       ├─ RedisRepository
    │   │       ├─ CSVRepository
    │   │       └─ SQLRepository
    │   │
    │   └─ Depends on: GeospatialService
    │       │
    │       └─ No dependencies (pure math)
    │
    ├─ Depends on: Domain Models
    │   │
    │   └─ route_models.py (pure data)
    │
    └─ Depends on: ServiceContext (factory)
        │
        └─ Creates repository instances
```

## Sequence Diagram: Optimize Route

```
Client          API Router      Optimizer       Geospatial      Repository
  │                 │               │                │               │
  │ POST /optimize  │               │                │               │
  ├────────────────>│               │                │               │
  │                 │               │                │               │
  │           validate & parse      │                │               │
  │                 │               │                │               │
  │                 │ optimize()    │                │               │
  │                 ├──────────────>│                │               │
  │                 │               │ list_cameras() │               │
  │                 │               ├───────────────────────────────>│
  │                 │               │                │    [cam IDs]  │
  │                 │               │<───────────────────────────────┤
  │                 │               │                │               │
  │                 │               │ get_metadata() │               │
  │                 │               ├───────────────────────────────>│
  │                 │               │                │  [Camera obj] │
  │                 │               │<───────────────────────────────┤
  │                 │               │                │               │
  │                 │               │ find_cameras() │               │
  │                 │               ├───────────────>│               │
  │                 │               │  [RouteCameraInfo list]        │
  │                 │               │<───────────────┤               │
  │                 │               │                │               │
  │                 │               │ get_forecast() │               │
  │                 │               ├───────────────────────────────>│
  │                 │               │                │  [CIForecast] │
  │                 │               │<───────────────────────────────┤
  │                 │               │                │               │
  │                 │               │ (for each time horizon)        │
  │                 │               │ - calc avg CI                  │
  │                 │               │ - estimate time                │
  │                 │               │ - calc confidence              │
  │                 │               │                │               │
  │                 │ [Result]      │                │               │
  │                 │<──────────────┤                │               │
  │                 │               │                │               │
  │           format response       │                │               │
  │                 │               │                │               │
  │    [JSON]       │               │                │               │
  │<────────────────┤               │                │               │
  │                 │               │                │               │
```

## Class Diagram

```
┌──────────────────────────┐
│     <<interface>>        │
│   DataRepository         │
├──────────────────────────┤
│ + save_ci_state()        │
│ + get_ci_state()         │
│ + save_forecast()        │
│ + get_forecast()         │
│ + get_camera_metadata()  │
│ + list_cameras()         │
│ + health_check()         │
└────────▲─────────────────┘
         │ implements
         │
    ┌────┴────┬─────────┐
    │         │         │
┌───┴────┐ ┌──┴──┐ ┌────┴────┐
│ Redis  │ │ CSV │ │  SQL    │
│ Repo   │ │ Repo│ │  Repo   │
└────────┘ └─────┘ └─────────┘

┌──────────────────────────────┐
│   GeospatialService          │
├──────────────────────────────┤
│ + haversine_distance()       │
│ + point_to_line_distance()   │
│ + find_cameras_along_route() │
│ + calculate_route_length()   │
└──────────────────────────────┘

┌──────────────────────────────────┐
│  RouteOptimizationService        │
├──────────────────────────────────┤
│ - repository: DataRepository     │
│ - geo_service: GeospatialService │
├──────────────────────────────────┤
│ + optimize_route()               │
│ - _get_speed_factor()            │
│ - _estimate_travel_time()        │
│ - _get_forecast_at_horizon()     │
│ - _calculate_confidence()        │
└──────────────────────────────────┘
         │ uses
         │
    ┌────▼────┐
    │ Domain  │
    │ Models  │
    └─────────┘
```

---

**Key Design Patterns:**

1. **Repository Pattern**: DataRepository abstraction
2. **Factory Pattern**: ServiceContext creates instances
3. **Singleton Pattern**: Service instances cached
4. **Dependency Injection**: Services receive dependencies via constructor
5. **Strategy Pattern**: Different repository implementations
6. **Domain-Driven Design**: Clear domain/application/infrastructure layers
