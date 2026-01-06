import asyncio
from typing import Dict, List, Any, Optional
from lib.providers.services import service_manager
service_models_cache: Dict[str, Dict[str, List[str]]] = {}

async def cached_get_service_models():
    """
    Retrieve service models from the cache or fetch them if not available.
    Returns:
        Dictionary mapping services to providers to models:
        {
            "service_name": {
                "provider_name": ["model1", "model2", ...],
                ...
            },
            ...
        }
    """
    global service_models_cache
    if not service_models_cache:
        service_models_cache = await get_service_models_from_providers()
    return service_models_cache

async def get_service_models_from_providers(timeout: float=500.0, context=None) -> Dict[str, Dict[str, List[str]]]:
    """
    Gather service models from all providers.
    
    Args:
        timeout: Maximum time in seconds to wait for each provider response
        
    Returns:
        Dictionary mapping services to providers to models:
        {
            "service_name": {
                "provider_name": ["model1", "model2", ...],
                ...
            },
            ...
        }
    """
    providers = []
    if 'get_service_models' in service_manager.functions:
        providers = [provider_info['provider'] for provider_info in service_manager.functions['get_service_models']]

    async def query_provider(provider_name: str) -> tuple[str, Dict[str, List[str]]]:
        try:
            result = await asyncio.wait_for(service_manager.exec_with_provider('get_service_models', provider_name, context=context), timeout=timeout)
            return (provider_name, result)
        except asyncio.TimeoutError:
            return (provider_name, {})
        except Exception as e:
            return (provider_name, {})
    provider_tasks = [query_provider(provider) for provider in providers]
    provider_results = await asyncio.gather(*provider_tasks)
    service_models: Dict[str, Dict[str, List[str]]] = {}
    for provider_name, provider_data in provider_results:
        if not provider_data:
            continue
        for service_name, models in provider_data.items():
            if service_name not in service_models:
                service_models[service_name] = {}
            service_models[service_name][provider_name] = models
    return service_models