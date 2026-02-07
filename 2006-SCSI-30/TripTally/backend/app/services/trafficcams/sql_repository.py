"""
SQL Repository Implementation
Implements DataRepository interface for SQL database storage (PostgreSQL/SQLite)
"""

import sqlite3
import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from threading import Lock

from .data_repository import DataRepository
from .models import CIState, CIForecast, Camera
from .logger import get_logger

logger = get_logger("sql_repo")


class SQLRepository(DataRepository):
    """SQL implementation of DataRepository (SQLite for now)"""
    
    def __init__(self, db_path: str = "./data/traffic_ci.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.lock = Lock()
        
        # Initialize database
        self._initialize_db()
        
        logger.info(f"SQL Repository initialized at {self.db_path}")
    
    def _get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row  # Return rows as dicts
        return conn
    
    def _initialize_db(self):
        """Create tables if they don't exist"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # CI states table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ci_states (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    camera_id TEXT NOT NULL,
                    ci REAL NOT NULL,
                    vehicle_count INTEGER,
                    weighted_count REAL,
                    area_ratio REAL,
                    motion_score REAL,
                    img_width INTEGER,
                    img_height INTEGER,
                    minute_of_day INTEGER,
                    hour INTEGER,
                    day_of_week INTEGER,
                    is_weekend INTEGER,
                    sin_t_h REAL,
                    cos_t_h REAL,
                    model_version TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Index on camera_id and timestamp
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_ci_states_camera_ts 
                ON ci_states(camera_id, timestamp DESC)
            ''')
            
            # Forecasts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS forecasts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    camera_id TEXT NOT NULL,
                    current_ci REAL NOT NULL,
                    forecast_time TEXT NOT NULL,
                    forecasts_json TEXT NOT NULL,
                    model_version TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Index on camera_id and timestamp
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_forecasts_camera_ts 
                ON forecasts(camera_id, timestamp DESC)
            ''')
            
            # Cameras table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cameras (
                    camera_id TEXT PRIMARY KEY,
                    latitude REAL,
                    longitude REAL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
    
    def save_ci_state(self, state: CIState) -> bool:
        """Save current CI state"""
        try:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO ci_states (
                        timestamp, camera_id, ci, vehicle_count, weighted_count,
                        area_ratio, motion_score, img_width, img_height,
                        minute_of_day, hour, day_of_week, is_weekend,
                        sin_t_h, cos_t_h, model_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    state.timestamp.isoformat(),
                    state.camera_id,
                    state.ci,
                    state.vehicle_count,
                    state.weighted_count,
                    state.area_ratio,
                    state.motion_score,
                    state.img_width,
                    state.img_height,
                    state.minute_of_day,
                    state.hour,
                    state.day_of_week,
                    state.is_weekend,
                    state.sin_t_h,
                    state.cos_t_h,
                    state.model_version
                ))
                
                conn.commit()
                conn.close()
            
            logger.debug(f"Saved CI state for camera {state.camera_id} to SQL")
            return True
        except Exception as e:
            logger.error(f"Failed to save CI state to SQL: {e}")
            return False
    
    def get_ci_state(self, camera_id: str) -> Optional[CIState]:
        """Retrieve latest CI state for camera"""
        try:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM ci_states 
                    WHERE camera_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                ''', (camera_id,))
                
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    return dict(row)  # Return as dict for now
                return None
        except Exception as e:
            logger.error(f"Failed to get CI state from SQL: {e}")
            return None
    
    def save_forecast(self, forecast: CIForecast) -> bool:
        """Save forecast"""
        try:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                forecasts_json = json.dumps([
                    {
                        'minutes_ahead': f.horizon_minutes,
                        'forecast_ci': f.predicted_ci,
                        'confidence': f.confidence,
                        'forecast_time': f.forecast_time.isoformat() if f.forecast_time else None
                    }
                    for f in forecast.horizons
                ])
                
                cursor.execute('''
                    INSERT INTO forecasts (
                        timestamp, camera_id, current_ci, forecast_time,
                        forecasts_json, model_version
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    forecast.camera_id,
                    forecast.current_ci,
                    forecast.forecast_time.isoformat(),
                    forecasts_json,
                    forecast.model_version
                ))
                
                conn.commit()
                conn.close()
            
            logger.debug(f"Saved forecast for camera {forecast.camera_id} to SQL")
            return True
        except Exception as e:
            logger.error(f"Failed to save forecast to SQL: {e}")
            return False
    
    def get_forecast(self, camera_id: str) -> Optional[CIForecast]:
        """Retrieve latest forecast for camera"""
        try:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM forecasts 
                    WHERE camera_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                ''', (camera_id,))
                
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    return dict(row)  # Return as dict for now
                return None
        except Exception as e:
            logger.error(f"Failed to get forecast from SQL: {e}")
            return None
    
    def save_camera_metadata(self, camera: Camera) -> bool:
        """Save camera metadata"""
        try:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO cameras (camera_id, latitude, longitude, updated_at)
                    VALUES (?, ?, ?, ?)
                ''', (
                    camera.camera_id,
                    camera.latitude,
                    camera.longitude,
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                conn.close()
            
            logger.debug(f"Saved camera metadata for {camera.camera_id} to SQL")
            return True
        except Exception as e:
            logger.error(f"Failed to save camera metadata to SQL: {e}")
            return False
    
    def get_camera_metadata(self, camera_id: str) -> Optional[Camera]:
        """Retrieve camera metadata"""
        try:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM cameras WHERE camera_id = ?
                ''', (camera_id,))
                
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    return dict(row)  # Return as dict for now
                return None
        except Exception as e:
            logger.error(f"Failed to get camera metadata from SQL: {e}")
            return None
    
    def list_cameras(self) -> List[str]:
        """List all camera IDs"""
        try:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('SELECT camera_id FROM cameras')
                rows = cursor.fetchall()
                conn.close()
                
                return [row['camera_id'] for row in rows]
        except Exception as e:
            logger.error(f"Failed to list cameras from SQL: {e}")
            return []
    
    def health_check(self) -> bool:
        """Check if repository is healthy"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            conn.close()
            return True
        except Exception as e:
            logger.error(f"SQL health check failed: {e}")
            return False
    
    def get_repository_name(self) -> str:
        """Return name of the repository implementation"""
        return "SQLite"
