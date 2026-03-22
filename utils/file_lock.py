"""Verrouillage de fichiers pour éviter les corruptions lors d'accès concurrents."""

import os
import time
import contextlib

@contextlib.contextmanager
def file_lock(filepath, timeout=10, poll_interval=0.2):
    """Context manager pour verrouiller un fichier pendant l'écriture.

    Usage:
        with file_lock("data/subscribers.csv"):
            # lire et écrire le fichier en toute sécurité
            ...

    Args:
        filepath: Chemin du fichier à verrouiller
        timeout: Temps max d'attente en secondes (défaut: 10)
        poll_interval: Intervalle de vérification en secondes
    """
    lock_path = filepath + ".lock"
    start = time.time()

    while True:
        try:
            # Création atomique du fichier lock (échoue si existe déjà)
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            break
        except FileExistsError:
            # Vérifier si le lock est périmé (> 60 secondes = probablement crash)
            try:
                lock_age = time.time() - os.path.getmtime(lock_path)
                if lock_age > 60:
                    os.remove(lock_path)
                    continue
            except OSError:
                pass

            if time.time() - start > timeout:
                raise TimeoutError(f"Impossible de verrouiller {filepath} après {timeout}s. "
                                   f"Supprimez {lock_path} si le problème persiste.")
            time.sleep(poll_interval)

    try:
        yield
    finally:
        try:
            os.remove(lock_path)
        except OSError:
            pass
