"""
Network Configuration Manager for FAIR-Agent
Handles dynamic discovery of services and ports
"""

import os
import requests
import socket
from typing import Dict, Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)

class NetworkConfig:
    """Dynamic network configuration manager"""
    
    DEFAULT_PORTS = {
        'ollama': 11435,
        'django': 8000,
        'redis': 6379,
        'webapp': 3000
    }
    
    DEFAULT_HOSTS = {
        'ollama': 'localhost',
        'django': '127.0.0.1', 
        'redis': '127.0.0.1',
        'webapp': 'localhost'
    }
    
    @classmethod
    def discover_ollama_endpoint(cls) -> str:
        """Discover available Ollama endpoint"""
        possible_endpoints = [
            "http://localhost:11435",
            "http://127.0.0.1:11435",
            "http://0.0.0.0:11435",
            "http://host.docker.internal:11435"  # Docker environment
        ]
        
        for endpoint in possible_endpoints:
            try:
                response = requests.get(f"{endpoint}/api/tags", timeout=2)
                if response.status_code == 200:
                    logger.info(f"✅ Found Ollama at: {endpoint}")
                    return endpoint
            except Exception:
                continue
        
        # Fallback to default
        logger.warning("⚠️ Ollama not found, using default endpoint")
        return "http://localhost:11435"
    
    @classmethod
    def discover_redis_endpoint(cls) -> Tuple[str, int]:
        """Discover Redis endpoint"""
        redis_host = os.environ.get('REDIS_HOST', cls.DEFAULT_HOSTS['redis'])
        redis_port = int(os.environ.get('REDIS_PORT', cls.DEFAULT_PORTS['redis']))
        
        # Test if Redis is available
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((redis_host, redis_port))
            sock.close()
            
            if result == 0:
                logger.info(f"✅ Found Redis at: {redis_host}:{redis_port}")
                return redis_host, redis_port
        except Exception:
            pass
        
        logger.warning("⚠️ Redis not found, using default configuration")
        return redis_host, redis_port
    
    @classmethod
    def get_web_host_port(cls) -> Tuple[str, int]:
        """Get web interface host and port configuration"""
        # Check environment variables first
        host = os.environ.get('DJANGO_HOST', os.environ.get('WEB_HOST', cls.DEFAULT_HOSTS['django']))
        port = int(os.environ.get('DJANGO_PORT', os.environ.get('WEB_PORT', cls.DEFAULT_PORTS['django'])))
        
        # In Docker/container environments, use 0.0.0.0
        if os.environ.get('CONTAINER_ENV') == 'true' or os.path.exists('/.dockerenv'):
            host = '0.0.0.0'
        
        return host, port
    
    @classmethod
    def get_allowed_hosts(cls) -> List[str]:
        """Get dynamically configured allowed hosts"""
        allowed_hosts = []
        
        # Add environment-specified hosts
        env_hosts = os.environ.get('DJANGO_ALLOWED_HOSTS', '')
        if env_hosts:
            allowed_hosts.extend([h.strip() for h in env_hosts.split(',') if h.strip()])
        
        # Add default hosts
        default_hosts = ['localhost', '127.0.0.1', '0.0.0.0']
        
        # Add discovered local IP
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            default_hosts.append(local_ip)
        except Exception:
            pass
        
        # Combine and deduplicate
        all_hosts = list(set(allowed_hosts + default_hosts))
        
        logger.info(f"📡 Configured allowed hosts: {all_hosts}")
        return all_hosts
    
    @classmethod
    def get_cors_origins(cls) -> List[str]:
        """Get dynamically configured CORS origins"""
        origins = []
        
        # Environment-specified origins
        env_origins = os.environ.get('CORS_ORIGINS', '')
        if env_origins:
            origins.extend([o.strip() for o in env_origins.split(',') if o.strip()])
        
        # Default development origins
        host, port = cls.get_web_host_port()
        default_origins = [
            f"http://localhost:{port}",
            f"http://127.0.0.1:{port}",
            f"http://{host}:{port}",
            "http://localhost:3000",  # React dev server
            "http://127.0.0.1:3000"
        ]
        
        # Combine and deduplicate
        all_origins = list(set(origins + default_origins))
        
        logger.info(f"🌐 Configured CORS origins: {all_origins}")
        return all_origins
    
    @classmethod
    def get_service_url(cls, service: str, path: str = "") -> str:
        """Get full service URL"""
        if service == 'ollama':
            base_url = cls.discover_ollama_endpoint()
        elif service == 'webapp':
            host, port = cls.get_web_host_port()
            base_url = f"http://{host}:{port}"
        else:
            host = cls.DEFAULT_HOSTS.get(service, 'localhost')
            port = cls.DEFAULT_PORTS.get(service, 8000)
            base_url = f"http://{host}:{port}"
        
        return f"{base_url}/{path}".rstrip('/')
    
    @classmethod
    def validate_configuration(cls) -> Dict[str, bool]:
        """Validate network configuration"""
        validation_results = {}
        
        # Test Ollama connection
        try:
            ollama_url = cls.discover_ollama_endpoint()
            response = requests.get(f"{ollama_url}/api/tags", timeout=5)
            validation_results['ollama'] = response.status_code == 200
        except Exception:
            validation_results['ollama'] = False
        
        # Test Redis connection
        try:
            redis_host, redis_port = cls.discover_redis_endpoint()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((redis_host, redis_port))
            sock.close()
            validation_results['redis'] = result == 0
        except Exception:
            validation_results['redis'] = False
        
        return validation_results