# 🚀 Deployment Guide

## Prerequisites
- Docker and Docker Compose installed
- YOLO model file (`models/yolov8n.pt`)
- (Optional) LTA API key for higher rate limits

## Steps

### 1. Verify Model File
```bash
ls -lh models/yolov8n.pt
```
✅ File should exist and be ~6MB

### 2. (Optional) Configure API Key
```bash
# Create .env file
echo "X_API_KEY=your_api_key_here" > .env
```

### 3. Start Services
```bash
# Using Make (recommended)
make up

# Or using docker-compose directly
docker-compose up -d
```

### 4. Verify Deployment
```bash
# Check if containers are running
make ps
# or
docker-compose ps

# Should show:
# triptally-redis        Up (healthy)
# triptally-ci-service   Up
```

### 5. View Logs
```bash
# Follow logs
make logs

# You should see:
# [INFO] TripTally CI Processing Service
# [INFO] Loading YOLO model...
# [INFO] YOLO model loaded successfully
# [INFO] Redis connection OK
# [INFO] Starting processing loop...
```

### 6. Test Redis Data
```bash
# Wait 2-3 minutes for first iteration to complete
# Then check Redis:
make redis-keys

# You should see keys like:
# ci:now:1001
# ci:now:1002
# ci:fcst:1001
# cameras:meta
```

### 7. Query Data
```bash
# Check current CI for camera
docker-compose exec redis redis-cli HGETALL ci:now:1001

# Check forecast
docker-compose exec redis redis-cli HGETALL ci:fcst:1001
```

## ✅ Success Indicators

1. **Containers Running**
   ```bash
   docker-compose ps
   # Both services show "Up"
   ```

2. **Logs Show Processing**
   ```bash
   docker-compose logs ci-service | tail -20
   # Should show camera processing messages
   ```

3. **Redis Has Data**
   ```bash
   docker-compose exec redis redis-cli DBSIZE
   # Should return > 0
   ```

4. **No Errors in Logs**
   ```bash
   docker-compose logs ci-service | grep ERROR
   # Should be empty or minimal
   ```

## 🔧 Troubleshooting

### Redis Not Starting
```bash
# Check logs
docker-compose logs redis

# Restart
make restart
```

### CI Service Not Starting
```bash
# Check logs
docker-compose logs ci-service

# Common issues:
# - Model file missing
# - Redis not healthy
# - Configuration error

# Rebuild and restart
make rebuild
```

### No Data in Redis After 5 Minutes
```bash
# Check if API is accessible
curl "https://api.data.gov.sg/v1/transport/traffic-images"

# Check service logs for API errors
docker-compose logs ci-service | grep -i api
```

### High CPU Usage
```bash
# Reduce image size in docker-compose.yml:
# IMG_SIZE=416  # instead of 640

# Restart
make restart
```

## 📊 Production Deployment

### 1. Update Configuration
Edit `docker-compose.yml`:
```yaml
environment:
  - LOG_LEVEL=WARNING  # Reduce log verbosity
  - X_API_KEY=${X_API_KEY}  # Use real API key
  - REDIS_PASSWORD=${REDIS_PASSWORD}  # Enable auth
```

### 2. Add Redis Password
```bash
# In docker-compose.yml, update Redis service:
redis:
  command: redis-server --requirepass ${REDIS_PASSWORD}
  
# In ci-service environment:
  - REDIS_PASSWORD=${REDIS_PASSWORD}
```

### 3. Set Resource Limits
```yaml
ci-service:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 2G
      reservations:
        memory: 512M
```

### 4. Enable Monitoring
```bash
# Add Prometheus exporter (future enhancement)
# Add health check endpoint
# Set up alerting
```

### 5. Deploy
```bash
# Pull latest code
git pull

# Build and start
make rebuild

# Verify
make health
```

## 🛡️ Security Checklist

- [ ] Use strong Redis password
- [ ] Don't commit secrets to git
- [ ] Use environment variables for sensitive data
- [ ] Run containers as non-root (already configured)
- [ ] Enable Redis persistence
- [ ] Set up log rotation
- [ ] Use HTTPS for API if available
- [ ] Monitor for suspicious activity

## 🔄 Updating

### Update Code
```bash
git pull
make rebuild
```

### Update Model
```bash
# Replace model file
cp new-model.pt models/yolov8n.pt

# Restart service
make restart
```

### Update Dependencies
```bash
# Edit requirements.txt
# Rebuild image
make rebuild
```

## 📱 Monitoring Commands

```bash
# View real-time logs
make logs

# Check container status
make ps

# Monitor Redis operations
make redis-monitor

# View all Redis keys
make redis-keys

# Check disk usage
docker system df

# View resource usage
docker stats
```

## 🆘 Emergency Commands

### Stop Everything
```bash
make down
```

### Full Reset
```bash
make clean-all
```

### Backup Data
```bash
make backup-redis
```

### View Container Errors
```bash
docker-compose logs ci-service --tail=100 | grep -i error
```

## 📞 Support

If issues persist:
1. Check logs: `make logs`
2. Verify configuration
3. Test Redis connection manually
4. Check API accessibility
5. Review GitHub issues

---

**Need Help?** Open an issue on GitHub with:
- Docker version
- OS information  
- Full error logs
- Steps to reproduce
