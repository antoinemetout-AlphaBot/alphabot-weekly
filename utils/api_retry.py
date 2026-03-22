"""Utilitaire de retry avec backoff exponentiel pour les appels API externes."""

import time
import functools
from utils.activity_logger import log_event


def retry_api(max_retries=3, base_delay=2, retryable_exceptions=(Exception,), agent_name="API"):
    """Décorateur de retry avec backoff exponentiel.

    Args:
        max_retries: Nombre max de tentatives (défaut: 3)
        base_delay: Délai initial en secondes (défaut: 2)
        retryable_exceptions: Tuple d'exceptions à retenter
        agent_name: Nom de l'agent pour le logging

    Example:
        @retry_api(max_retries=3, agent_name="Agent Veille")
        def fetch_data():
            return requests.get(url).json()
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        log_event(agent_name, "warning",
                            f"Tentative {attempt+1}/{max_retries} échouée: {str(e)[:100]}. Retry dans {delay}s...")
                        time.sleep(delay)
                    else:
                        log_event(agent_name, "error",
                            f"Échec après {max_retries} tentatives: {str(e)[:200]}")
            raise last_exception
        return wrapper
    return decorator


def safe_api_call(func, *args, max_retries=3, base_delay=2, agent_name="API", default=None, **kwargs):
    """Appel API sécurisé avec retry. Retourne default en cas d'échec total.

    Args:
        func: Fonction à appeler (ex: requests.get)
        *args: Arguments positionnels pour func
        max_retries: Nombre max de tentatives
        base_delay: Délai initial de retry en secondes
        agent_name: Nom de l'agent pour le logging
        default: Valeur par défaut en cas d'échec total
        **kwargs: Arguments nommés pour func

    Returns:
        Le résultat de func(), ou default si tous les retries échouent

    Example:
        response = safe_api_call(requests.get, url, timeout=10, agent_name="Agent Veille", default=None)
        if response is None:
            print("API call failed, using default behavior")
    """
    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                log_event(agent_name, "warning",
                    f"Tentative {attempt+1}/{max_retries} échouée: {str(e)[:100]}. Retry dans {delay}s...")
                time.sleep(delay)
            else:
                log_event(agent_name, "error",
                    f"Échec après {max_retries+1} tentatives: {str(e)[:200]}")

    if last_exception:
        log_event(agent_name, "warning", f"Utilisation de la valeur par défaut après échecs")

    return default
