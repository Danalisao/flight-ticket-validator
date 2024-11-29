import json
import logging
import time
from datetime import timedelta
from functools import wraps
from threading import Lock

class InMemoryCache:
    def __init__(self):
        self._cache = {}
        self._lock = Lock()
        self.logger = logging.getLogger(__name__)

    def get(self, key):
        """Récupère une valeur du cache"""
        with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]
                if expiry > time.time():
                    return value
                else:
                    del self._cache[key]
        return None

    def set(self, key, value, expire_in_seconds=3600):
        """Stocke une valeur dans le cache avec une durée d'expiration"""
        with self._lock:
            expiry = time.time() + expire_in_seconds
            self._cache[key] = (value, expiry)
            return True

    def delete(self, key):
        """Supprime une valeur du cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
        return False

    def cleanup(self):
        """Nettoie les entrées expirées du cache"""
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, (_, expiry) in self._cache.items()
                if expiry <= current_time
            ]
            for key in expired_keys:
                del self._cache[key]

class CacheService:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        """Implémentation Singleton thread-safe"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(CacheService, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialise le service de cache"""
        if not self._initialized:
            self.cache = InMemoryCache()
            self.logger = logging.getLogger(__name__)
            self._initialized = True

    def cache_key(self, prefix, *args):
        """Génère une clé de cache unique basée sur les arguments"""
        return f"{prefix}:{':'.join(str(arg) for arg in args)}"

    def get(self, key):
        """Récupère une valeur du cache"""
        try:
            value = self.cache.get(key)
            if value is not None:
                self.logger.debug(f"Cache hit pour la clé: {key}")
                return json.loads(value)
            self.logger.debug(f"Cache miss pour la clé: {key}")
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération du cache: {str(e)}")
        return None

    def set(self, key, value, expire_in_seconds=3600):
        """Stocke une valeur dans le cache avec une durée d'expiration"""
        try:
            success = self.cache.set(
                key,
                json.dumps(value),
                expire_in_seconds
            )
            if success:
                self.logger.debug(f"Valeur mise en cache pour la clé: {key}")
            return success
        except Exception as e:
            self.logger.error(f"Erreur lors de la mise en cache: {str(e)}")
            return False

    def delete(self, key):
        """Supprime une valeur du cache"""
        try:
            success = self.cache.delete(key)
            if success:
                self.logger.debug(f"Valeur supprimée du cache pour la clé: {key}")
            return success
        except Exception as e:
            self.logger.error(f"Erreur lors de la suppression du cache: {str(e)}")
            return False

def cached(prefix, expire_in_seconds=3600):
    """
    Décorateur pour mettre en cache le résultat d'une fonction
    
    :param prefix: Préfixe pour la clé de cache
    :param expire_in_seconds: Durée de validité du cache en secondes
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Créer une instance du service de cache
            cache = CacheService()
            
            # Générer la clé de cache
            cache_key = cache.cache_key(prefix, *args)
            
            # Vérifier si le résultat est en cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Exécuter la fonction et mettre en cache le résultat
            result = func(self, *args, **kwargs)
            cache.set(cache_key, result, expire_in_seconds)
            
            return result
        return wrapper
    return decorator
