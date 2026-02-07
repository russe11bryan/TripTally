# CI Service Permission Error Fix

## Problem
The CI service container was failing with:
```
PermissionError: [Errno 13] Permission denied: '/app/cache/prev_frames'
```

## Root Cause
The Dockerfile was creating directories as root before switching to the `appuser` non-root user. When the application tried to create the `/app/cache/prev_frames` subdirectory at runtime, it didn't have the necessary permissions.

## Solution Applied

### 1. **Dockerfile Changes**
- Moved directory creation to **after** switching to the `appuser` user
- This ensures all directories are created with proper ownership and permissions
- Added explicit creation of the `prev_frames` subdirectory

**Before:**
```dockerfile
# Create necessary directories
RUN mkdir -p /app/cache /app/logs /app/models

# Run as non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser
```

**After:**
```dockerfile
# Run as non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Create necessary directories with proper permissions (as appuser)
RUN mkdir -p /app/cache/prev_frames /app/logs /app/models
```

### 2. **Motion Detector Improvements**
Enhanced error handling in `motion_detector.py` to provide clearer error messages if permission issues occur.

## How to Apply the Fix

### Step 1: Rebuild the Docker Image
```powershell
cd "c:\NTU Stuffs\Modules\Y2S1\SC2006\triptally\TripTally\backend\app\services\trafficcams"
docker-compose build --no-cache ci-service
```

### Step 2: Stop Existing Containers
```powershell
docker-compose down
```

### Step 3: Start the Services
```powershell
docker-compose up -d
```

### Step 4: Verify the Fix
Check the logs to ensure no permission errors:
```powershell
docker logs triptally-ci-service
```

You should see:
```
[INFO] ci_service: TripTally CI Processing Service
[INFO] ci_service.ci_service: Initializing CI Processing Service
[INFO] motion_detector: Motion detector cache directory created: /app/cache/prev_frames
```

### Step 5: Monitor the Service
```powershell
# Follow logs in real-time
docker logs -f triptally-ci-service

# Check container status
docker ps | Select-String triptally-ci-service
```

## Alternative: Manual Permission Fix (If Needed)

If you need a quick fix without rebuilding:

```powershell
# Stop the service
docker-compose stop ci-service

# Remove the container
docker-compose rm -f ci-service

# Create the directory with proper permissions on the host
mkdir -p .\cache\prev_frames

# Start the service
docker-compose up -d ci-service
```

## Verification Checklist

- [ ] Container starts without permission errors
- [ ] `/app/cache/prev_frames` directory is accessible
- [ ] Motion detection is working
- [ ] CI calculations are being stored in Redis
- [ ] No permission-related errors in logs

## Related Files
- `Dockerfile` - Fixed directory creation order
- `motion_detector.py` - Added better error handling
- `docker-compose.yml` - Volume mounts configuration
- `service.py` - Service initialization (line 42)

## Notes
- The volume mount in `docker-compose.yml` (`./cache:/app/cache`) ensures data persists between container restarts
- The `appuser` has UID 1000, which is standard for non-root Docker users
- All directories are now created with proper ownership from the start
