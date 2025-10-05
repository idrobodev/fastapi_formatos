"""
Servicios y validaciones para el sistema de gestión de formatos.
Contiene funciones de validación, sanitización y lógica de negocio.
"""

import os
import re
import mimetypes
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import datetime

from database import files_db, folders_db, counters
from models import FileMetadata, FolderMetadata

# ============================================================================
# Validaciones de Seguridad
# ============================================================================

def validate_filename(filename: str) -> bool:
    """
    Valida que un nombre de archivo sea seguro.

    Args:
        filename: Nombre del archivo a validar

    Returns:
        True si es válido, False en caso contrario
    """
    if not filename or len(filename) > 255:
        return False

    # No permitir caracteres peligrosos
    dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\x00']
    if any(char in filename for char in dangerous_chars):
        return False

    # No permitir secuencias de directorio
    if '..' in filename or '/' in filename or '\\' in filename:
        return False

    # No permitir archivos que empiecen o terminen con punto
    if filename.startswith('.') or filename.endswith('.'):
        return False

    return True


def validate_path(path: str) -> bool:
    """
    Valida que una ruta no contenga secuencias peligrosas.

    Args:
        path: Ruta a validar

    Returns:
        True si es válida, False en caso contrario
    """
    if not path:
        return True  # Ruta vacía es válida

    # No permitir path traversal
    if '..' in path:
        return False

    # Validar caracteres permitidos en rutas
    if any(char in path for char in ['<', '>', ':', '"', '|', '?', '*', '\x00']):
        return False

    return True


def validate_file_type(file_path: str) -> bool:
    """
    Valida que el tipo de archivo sea seguro (no ejecutable).

    Args:
        file_path: Ruta del archivo a validar

    Returns:
        True si es seguro, False en caso contrario
    """
    try:
        mime_type, _ = mimetypes.guess_type(file_path)

        if not mime_type:
            return False

        # Rechazar tipos ejecutables
        dangerous_types = [
            'application/x-executable',
            'application/x-msdownload',
            'application/x-msdos-program',
            'application/octet-stream'
        ]

        # Rechazar archivos con extensiones peligrosas
        dangerous_extensions = ['.exe', '.bat', '.cmd', '.com', '.scr', '.pif', '.vbs', '.js']

        if mime_type in dangerous_types:
            return False

        file_ext = Path(file_path).suffix.lower()
        if file_ext in dangerous_extensions:
            return False

        return True

    except Exception:
        return False


# ============================================================================
# Funciones de Sanitización
# ============================================================================

def sanitize_filename(filename: str) -> str:
    """
    Limpia y sanitiza un nombre de archivo.

    Args:
        filename: Nombre original del archivo

    Returns:
        Nombre sanitizado
    """
    if not filename:
        return "archivo_sin_nombre"

    # Remover caracteres peligrosos
    sanitized = re.sub(r'[<>:"|?*\x00]', '', filename)

    # Reemplazar espacios y caracteres especiales con guiones
    sanitized = re.sub(r'[^\w\.-]', '_', sanitized)

    # Remover puntos al inicio y final
    sanitized = sanitized.strip('.')

    # Limitar longitud
    if len(sanitized) > 255:
        name_part, ext = os.path.splitext(sanitized)
        name_part = name_part[:255-len(ext)]
        sanitized = name_part + ext

    # Asegurar que no esté vacío
    if not sanitized:
        sanitized = "archivo_sin_nombre"

    return sanitized


# ============================================================================
# Funciones de Tipo MIME
# ============================================================================

def get_mime_type(filename: str) -> str:
    """
    Detecta el tipo MIME de un archivo por su extensión.

    Args:
        filename: Nombre del archivo

    Returns:
        Tipo MIME detectado o 'application/octet-stream' si no se detecta
    """
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream'


# ============================================================================
# Funciones de Categorización de Archivos
# ============================================================================

def get_file_category(filename: str) -> str:
    """
    Determina la categoría de un archivo basado en su extensión.

    Args:
        filename: Nombre del archivo

    Returns:
        Categoría del archivo ('document', 'image', 'video', 'audio', 'archive', 'code', 'other')
    """
    if not filename:
        return 'other'

    extension = Path(filename).suffix.lower().lstrip('.')

    # Documentos
    document_extensions = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt']
    if extension in document_extensions:
        return 'document'

    # Imágenes
    image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp']
    if extension in image_extensions:
        return 'image'

    # Videos
    video_extensions = ['mp4', 'avi', 'mov', 'wmv']
    if extension in video_extensions:
        return 'video'

    # Audio
    audio_extensions = ['mp3', 'wav', 'flac']
    if extension in audio_extensions:
        return 'audio'

    # Archivos comprimidos
    archive_extensions = ['zip', 'rar', '7z']
    if extension in archive_extensions:
        return 'archive'

    # Código
    code_extensions = ['js', 'html', 'css', 'json']
    if extension in code_extensions:
        return 'code'

    return 'other'


def ensure_category_folder(category: str) -> str:
    """
    Asegura que exista la carpeta de categoría y la crea si no existe.

    Args:
        category: Categoría del archivo

    Returns:
        Nombre de la carpeta de categoría
    """
    # Mapear categorías a nombres de carpeta en español
    category_names = {
        'document': 'Documentos',
        'image': 'Imágenes',
        'video': 'Videos',
        'audio': 'Audio',
        'archive': 'Archivos',
        'code': 'Código',
        'other': 'Otros'
    }

    folder_name = category_names.get(category, 'Otros')

    # Verificar si la carpeta ya existe en la base de datos
    for folder_data in folders_db.values():
        if folder_data['nombre'] == folder_name and folder_data['ruta'] == '':
            return folder_name

    # Crear la carpeta si no existe
    from database import counters
    new_id = counters["folders"] + 1
    counters["folders"] = new_id

    from utils import format_datetime
    from datetime import datetime

    now = datetime.utcnow()
    now_iso = format_datetime(now)

    folder_record = {
        "id": new_id,
        "nombre": folder_name,
        "ruta": "",
        "createdAt": now_iso
    }

    folders_db[new_id] = folder_record

    # Crear directorio físico
    storage_path = Path("storage/formatos") / folder_name
    storage_path.mkdir(parents=True, exist_ok=True)

    return folder_name


# ============================================================================
# Funciones de Lógica de Negocio
# ============================================================================

def get_unique_filename(path: str, filename: str) -> str:
    """
    Genera un nombre de archivo único para evitar sobrescritura.

    Args:
        path: Ruta donde se guardará el archivo
        filename: Nombre original del archivo

    Returns:
        Nombre único para el archivo
    """
    if not filename:
        filename = "archivo_sin_nombre"

    base_name, extension = os.path.splitext(filename)
    counter = 1
    unique_name = filename

    # Verificar en la base de datos si ya existe
    while any(
        file_data['ruta'] == path and file_data['nombre'] == unique_name
        for file_data in files_db.values()
    ):
        unique_name = f"{base_name}_{counter}{extension}"
        counter += 1

    return unique_name


def get_file_by_id(file_id: int) -> Optional[dict]:
    """
    Busca un archivo en la base de datos por ID.

    Args:
        file_id: ID del archivo

    Returns:
        Datos del archivo o None si no existe
    """
    return files_db.get(file_id)


def get_folder_by_id(folder_id: int) -> Optional[dict]:
    """
    Busca una carpeta en la base de datos por ID.

    Args:
        folder_id: ID de la carpeta

    Returns:
        Datos de la carpeta o None si no existe
    """
    return folders_db.get(folder_id)


def list_files_in_path(path: str) -> Tuple[List[dict], List[dict]]:
    """
    Lista archivos y carpetas en una ruta específica.

    Args:
        path: Ruta a listar (vacío para raíz)

    Returns:
        Tupla con (lista de archivos, lista de carpetas)
    """
    # Normalizar path
    if path and not path.endswith('/'):
        path += '/'

    files = []
    folders = []

    # Buscar archivos en la ruta
    for file_data in files_db.values():
        if file_data['ruta'] == path:
            files.append(file_data)

    # Buscar carpetas en la ruta
    for folder_data in folders_db.values():
        if folder_data['ruta'] == path:
            folders.append(folder_data)

    # Ordenar por fecha de creación (más reciente primero)
    files.sort(key=lambda x: x['createdAt'], reverse=True)
    folders.sort(key=lambda x: x['createdAt'], reverse=True)

    return files, folders


def delete_folder_recursive(folder_id: int) -> bool:
    """
    Elimina una carpeta y todo su contenido recursivamente.

    Args:
        folder_id: ID de la carpeta a eliminar

    Returns:
        True si se eliminó correctamente, False en caso contrario
    """
    folder = get_folder_by_id(folder_id)
    if not folder:
        return False

    folder_path = folder['ruta'] + folder['nombre'] + '/'

    # Encontrar y eliminar archivos en la carpeta
    files_to_delete = []
    for file_id, file_data in files_db.items():
        if file_data['ruta'].startswith(folder_path):
            files_to_delete.append(file_id)

    for file_id in files_to_delete:
        del files_db[file_id]

    # Encontrar y eliminar subcarpetas recursivamente
    subfolders_to_delete = []
    for sub_id, sub_data in folders_db.items():
        if sub_data['ruta'].startswith(folder_path):
            subfolders_to_delete.append(sub_id)

    for sub_id in subfolders_to_delete:
        delete_folder_recursive(sub_id)

    # Eliminar la carpeta principal
    del folders_db[folder_id]

    # Eliminar archivos físicos si existen
    try:
        full_path = Path("storage/formatos") / folder_path.rstrip('/')
        if full_path.exists():
            import shutil
            shutil.rmtree(full_path)
    except Exception:
        pass  # Ignorar errores al eliminar archivos físicos

    return True