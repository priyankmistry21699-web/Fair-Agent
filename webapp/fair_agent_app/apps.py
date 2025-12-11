"""
Django app configuration for FAIR-Agent application
"""

from django.apps import AppConfig


class FairAgentAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'fair_agent_app'
    verbose_name = 'FAIR-Agent Application'
    
    def ready(self):
        """
        Initialize FAIR-Agent system when Django starts
        NOTE: Lazy initialization - agents will be loaded on first query
        """
        # Skip initialization here to avoid concurrent model loading issues
        # Agents will be initialized lazily on first query via FairAgentService.process_query()
        import logging
        logger = logging.getLogger(__name__)
        logger.info("FAIR-Agent app ready (lazy initialization mode)")