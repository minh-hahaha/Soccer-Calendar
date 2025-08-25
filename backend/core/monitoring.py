"""
Health Monitoring System
"""
import logging
import time
import psutil
from datetime import datetime
from typing import Dict, Any
from .database import db_manager
from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class HealthMonitor:
    """System health monitoring"""
    
    def __init__(self):
        self.settings = settings
    
    async def comprehensive_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check"""
        start_time = time.time()
        
        checks = {
            'database': self._check_database(),
            'system_resources': self._check_system_resources(),
            'disk_space': self._check_disk_space(),
            'model_availability': self._check_model_availability(),
        }
        
        overall_healthy = all(check.get('healthy', False) for check in checks.values())
        check_duration = time.time() - start_time
        
        return {
            'timestamp': datetime.now().isoformat(),
            'healthy': overall_healthy,
            'duration_seconds': round(check_duration, 2),
            'checks': checks,
        }
    
    def _check_database(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            is_connected = db_manager.health_check()
            connection_info = db_manager.get_connection_info()
            
            return {
                'healthy': is_connected,
                'pool_info': connection_info,
            }
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resources"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            return {
                'healthy': cpu_percent < 80 and memory.percent < 85,
                'cpu_percent': round(cpu_percent, 1),
                'memory_percent': round(memory.percent, 1),
            }
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    def _check_disk_space(self) -> Dict[str, Any]:
        """Check disk space"""
        try:
            disk = psutil.disk_usage('/')
            free_gb = disk.free / (1024**3)
            
            return {
                'healthy': disk.percent < 90,
                'disk_usage_percent': round(disk.percent, 1),
                'free_space_gb': round(free_gb, 2),
            }
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    def _check_model_availability(self) -> Dict[str, Any]:
        """Check if ML models are available"""
        try:
            from pathlib import Path
            model_path = Path(settings.MODEL_PATH)
            model_files = list(model_path.glob("*.pkl")) if model_path.exists() else []
            
            return {
                'healthy': len(model_files) > 0,
                'models_found': len(model_files),
                'model_files': [f.name for f in model_files]
            }
        except Exception as e:
            return {'healthy': False, 'error': str(e)}


# Global health monitor
health_monitor = HealthMonitor()
