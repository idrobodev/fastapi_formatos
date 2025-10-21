"""
Utilidades generales para el sistema de gestión de formatos.
Funciones auxiliares para manejo de archivos, directorios y fechas.
"""

import os
from datetime import datetime
from pathlib import Path

# ============================================================================
# Funciones de Directorios
# ============================================================================

def ensure_storage_directory() -> None:
    """
    Asegura que el directorio de almacenamiento storage/formatos/ exista.
    Crea el directorio si no existe y crea las carpetas por defecto.
    """
    storage_path = Path("storage/formatos")
    storage_path.mkdir(parents=True, exist_ok=True)

    # Crear carpetas por defecto
    default_folders = ["Documentos", "Imágenes"]
    for folder_name in default_folders:
        folder_path = storage_path / folder_name
        folder_path.mkdir(exist_ok=True)

    print(f"✅ Directorio de almacenamiento verificado: {storage_path.absolute()}")
    print(f"✅ Carpetas por defecto creadas: {', '.join(default_folders)}")


# ============================================================================
# Funciones de Archivos
# ============================================================================

def get_file_size(file_path: str) -> int:
    """
    Obtiene el tamaño de un archivo en bytes.

    Args:
        file_path: Ruta del archivo

    Returns:
        Tamaño del archivo en bytes, o 0 si no existe o hay error
    """
    try:
        return os.path.getsize(file_path)
    except (OSError, FileNotFoundError):
        return 0


# ============================================================================
# Funciones de Fechas
# ============================================================================

def format_datetime(dt: datetime) -> str:
    """
    Formatea un objeto datetime a string ISO 8601 con zona horaria UTC.

    Args:
        dt: Objeto datetime a formatear

    Returns:
        String en formato ISO 8601 (ej: 2024-01-15T10:30:00Z)
    """
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")