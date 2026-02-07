"""
Factory Pattern for Creating Repositories and Forecasters
Provides easy switching between implementations
"""

from typing import Union
from enum import Enum

from .data_repository import DataRepository
from .forecasting_strategy import ForecastingStrategy
from .repository import RedisRepository
from .csv_repository import CSVRepository
from .sql_repository import SQLRepository
from .forecaster import SimpleForecaster
from .ml_forecaster import MLForecaster
from .config import Config
from .logger import get_logger

logger = get_logger("factory")


class RepositoryType(Enum):
    """Enum for repository types"""
    REDIS = "redis"
    CSV = "csv"
    SQL = "sql"
    SQLITE = "sqlite"


class ForecasterType(Enum):
    """Enum for forecaster types"""
    SIMPLE = "simple"
    ML = "ml"
    XGBOOST = "xgboost"
    AUTO = "auto"  # Auto-select based on availability


class RepositoryFactory:
    """Factory for creating data repository instances"""
    
    @staticmethod
    def create(repo_type: Union[RepositoryType, str], config: Config = None) -> DataRepository:
        """
        Create repository instance based on type
        
        Args:
            repo_type: Type of repository to create
            config: Configuration object
            
        Returns:
            DataRepository implementation
            
        Raises:
            ValueError: If repo_type is not supported
        """
        if isinstance(repo_type, str):
            repo_type = repo_type.lower()
            try:
                repo_type = RepositoryType(repo_type)
            except ValueError:
                raise ValueError(f"Unknown repository type: {repo_type}")
        
        logger.info(f"Creating {repo_type.value} repository")
        
        if repo_type == RepositoryType.REDIS:
            if config is None:
                config = Config.from_env()
            return RedisRepository(config.redis)
        
        elif repo_type == RepositoryType.CSV:
            data_dir = getattr(config.processing, 'data_dir', './data') if config else './data'
            return CSVRepository(base_dir=data_dir)
        
        elif repo_type in (RepositoryType.SQL, RepositoryType.SQLITE):
            db_path = getattr(config.processing, 'db_path', './data/traffic_ci.db') if config else './data/traffic_ci.db'
            return SQLRepository(db_path=db_path)
        
        else:
            raise ValueError(f"Unsupported repository type: {repo_type}")


class ForecasterFactory:
    """Factory for creating forecaster instances"""
    
    @staticmethod
    def create(forecaster_type: Union[ForecasterType, str], config: Config = None) -> ForecastingStrategy:
        """
        Create forecaster instance based on type
        
        Args:
            forecaster_type: Type of forecaster to create
            config: Configuration object
            
        Returns:
            ForecastingStrategy implementation
            
        Raises:
            ValueError: If forecaster_type is not supported
        """
        if isinstance(forecaster_type, str):
            forecaster_type = forecaster_type.lower()
            try:
                forecaster_type = ForecasterType(forecaster_type)
            except ValueError:
                raise ValueError(f"Unknown forecaster type: {forecaster_type}")
        
        logger.info(f"Creating {forecaster_type.value} forecaster")
        
        if forecaster_type == ForecasterType.AUTO:
            # Try ML first, fallback to simple
            try:
                model_dir = getattr(config.processing, 'model_dir', './models') if config else './models'
                ml_forecaster = MLForecaster(model_dir=model_dir)
                
                if ml_forecaster.is_available():
                    logger.info("ML forecaster is available, using ML")
                    return ml_forecaster
                else:
                    logger.info("ML forecaster not available, using simple forecaster")
                    max_history = config.processing.max_history if config else 60
                    return SimpleForecaster(max_history=max_history)
            except Exception as e:
                logger.warning(f"Failed to create ML forecaster: {e}, using simple")
                max_history = config.processing.max_history if config else 60
                return SimpleForecaster(max_history=max_history)
        
        elif forecaster_type == ForecasterType.SIMPLE:
            max_history = config.processing.max_history if config else 60
            return SimpleForecaster(max_history=max_history)
        
        elif forecaster_type in (ForecasterType.ML, ForecasterType.XGBOOST):
            model_dir = getattr(config.processing, 'model_dir', './models') if config else './models'
            return MLForecaster(model_dir=model_dir)
        
        else:
            raise ValueError(f"Unsupported forecaster type: {forecaster_type}")


class ServiceContext:
    """
    Context class that holds repository and forecaster strategies
    Allows easy switching between implementations
    """
    
    def __init__(
        self,
        repository: DataRepository,
        forecaster: ForecastingStrategy
    ):
        self.repository = repository
        self.forecaster = forecaster
        
        logger.info(
            f"Service context created with {repository.get_repository_name()} "
            f"repository and {forecaster.get_strategy_name()} forecaster"
        )
    
    @staticmethod
    def from_config(
        config: Config,
        repo_type: Union[RepositoryType, str] = None,
        forecaster_type: Union[ForecasterType, str] = None
    ) -> 'ServiceContext':
        """
        Create ServiceContext from configuration
        
        Args:
            config: Configuration object
            repo_type: Repository type (defaults to REDIS)
            forecaster_type: Forecaster type (defaults to AUTO)
            
        Returns:
            ServiceContext instance
        """
        # Get types from config or use defaults
        if repo_type is None:
            repo_type = getattr(config.processing, 'repository_type', 'redis')
        
        if forecaster_type is None:
            forecaster_type = getattr(config.processing, 'forecaster_type', 'auto')
        
        # Create instances
        repository = RepositoryFactory.create(repo_type, config)
        forecaster = ForecasterFactory.create(forecaster_type, config)
        
        return ServiceContext(repository, forecaster)
    
    def switch_repository(self, repo_type: Union[RepositoryType, str], config: Config = None):
        """Switch to a different repository implementation"""
        logger.info(f"Switching repository to {repo_type}")
        self.repository = RepositoryFactory.create(repo_type, config)
    
    def switch_forecaster(self, forecaster_type: Union[ForecasterType, str], config: Config = None):
        """Switch to a different forecaster implementation"""
        logger.info(f"Switching forecaster to {forecaster_type}")
        self.forecaster = ForecasterFactory.create(forecaster_type, config)
