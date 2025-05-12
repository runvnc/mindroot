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
        print("Cache is empty, fetching service models...")
        service_models_cache = await get_service_models_from_providers()
    else:
        print("Using cached service models")
    return service_models_cache

async def get_service_models_from_providers(timeout: float = 500.0, context=None) -> Dict[str, Dict[str, List[str]]]:
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
    # Get all providers that implement get_service_models
    providers = []
    if 'get_service_models' in service_manager.functions:
        print("get_service_models function found in service_manager functions")
        providers = [provider_info['provider'] for provider_info in service_manager.functions['get_service_models']]
        print(f"Found {len(providers)} providers with get_service_models function: {providers}")
        print(providers)
    else:
        print("No providers found with get_service_models function")

    async def query_provider(provider_name: str) -> tuple[str, Dict[str, List[str]]]:
        try:
            # Set a timeout for each provider query
            result = await asyncio.wait_for(
                service_manager.exec_with_provider('get_service_models', provider_name, context=context),
                timeout=timeout
            )
            return provider_name, result
        except asyncio.TimeoutError:
            print(f"Timeout querying provider {provider_name} for service models")
            return provider_name, {}
        except Exception as e:
            print(f"Error querying provider {provider_name} for service models: {str(e)}")
            return provider_name, {}
    
    # Run all queries in parallel
    print(f"Querying {len(providers)} providers for service models...")
    provider_tasks = [query_provider(provider) for provider in providers]
    provider_results = await asyncio.gather(*provider_tasks)
    print(provider_results)
    # Organize results by service, then by provider
    service_models: Dict[str, Dict[str, List[str]]] = {}
    
    for provider_name, provider_data in provider_results:
        if not provider_data:
            continue
            
        for service_name, models in provider_data.items():
            if service_name not in service_models:
                service_models[service_name] = {}
            
            service_models[service_name][provider_name] = models
    
    return service_models
