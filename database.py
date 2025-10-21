"""
Base de datos PostgreSQL para el sistema de gestión de formatos.
Usa SQLAlchemy para interactuar con PostgreSQL.
"""

from database_models import db_service, FileModel, FolderModel
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import os

# ============================================================================
# Funciones de compatibilidad con la API existente
# ============================================================================

def format_datetime(dt: datetime) -> str:
    """Formatea datetime a ISO 8601 string"""
    return dt.isoformat() + "Z"


# ============================================================================
# Funciones de gestión de archivos
# ============================================================================

def get_file_by_id(file_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene un archivo por ID"""
    db = db_service.get_db()
    try:
        file_record = db.query(FileModel).filter(FileModel.id == file_id).first()
        if not file_record:
            return None

        return {
            "id": file_record.id,
            "nombre": file_record.nombre,
            "ruta": file_record.ruta or "",
            "tamaño": file_record.tamaño,
            "tipo": file_record.tipo,
            "categoria": file_record.categoria,
            "createdAt": format_datetime(file_record.created_at),
            "updatedAt": format_datetime(file_record.updated_at)
        }
    finally:
        db.close()


def get_files_by_path(path: str) -> List[Dict[str, Any]]:
    """Obtiene archivos por ruta"""
    db = db_service.get_db()
    try:
        files = db.query(FileModel).filter(FileModel.ruta == path).all()
        return [{
            "id": f.id,
            "nombre": f.nombre,
            "ruta": f.ruta or "",
            "tamaño": f.tamaño,
            "tipo": f.tipo,
            "categoria": f.categoria,
            "createdAt": format_datetime(f.created_at),
            "updatedAt": format_datetime(f.updated_at)
        } for f in files]
    finally:
        db.close()


def create_file_record(nombre: str, ruta: str, tamaño: int, tipo: str, categoria: str = None) -> int:
    """Crea un registro de archivo"""
    db = db_service.get_db()
    try:
        now = datetime.utcnow()
        file_record = FileModel(
            nombre=nombre,
            ruta=ruta,
            tamaño=tamaño,
            tipo=tipo,
            categoria=categoria,
            created_at=now,
            updated_at=now
        )
        db.add(file_record)
        db.commit()
        db.refresh(file_record)
        return file_record.id
    finally:
        db.close()


def delete_file_record(file_id: int) -> bool:
    """Elimina un registro de archivo"""
    db = db_service.get_db()
    try:
        file_record = db.query(FileModel).filter(FileModel.id == file_id).first()
        if file_record:
            db.delete(file_record)
            db.commit()
            return True
        return False
    finally:
        db.close()


# ============================================================================
# Funciones de gestión de carpetas
# ============================================================================

def get_folder_by_id(folder_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene una carpeta por ID"""
    db = db_service.get_db()
    try:
        folder = db.query(FolderModel).filter(FolderModel.id == folder_id).first()
        if not folder:
            return None

        return {
            "id": folder.id,
            "nombre": folder.nombre,
            "ruta": folder.ruta or "",
            "createdAt": format_datetime(folder.created_at)
        }
    finally:
        db.close()


def get_folders_by_path(path: str) -> List[Dict[str, Any]]:
    """Obtiene carpetas por ruta padre"""
    db = db_service.get_db()
    try:
        folders = db.query(FolderModel).filter(FolderModel.ruta == path).all()
        return [{
            "id": f.id,
            "nombre": f.nombre,
            "ruta": f.ruta or "",
            "createdAt": format_datetime(f.created_at)
        } for f in folders]
    finally:
        db.close()


def create_folder_record(nombre: str, ruta: str) -> int:
    """Crea un registro de carpeta"""
    db = db_service.get_db()
    try:
        now = datetime.utcnow()
        folder = FolderModel(
            nombre=nombre,
            ruta=ruta,
            created_at=now
        )
        db.add(folder)
        db.commit()
        db.refresh(folder)
        return folder.id
    finally:
        db.close()


def delete_folder_record(folder_id: int) -> bool:
    """Elimina un registro de carpeta"""
    db = db_service.get_db()
    try:
        folder = db.query(FolderModel).filter(FolderModel.id == folder_id).first()
        if folder:
            db.delete(folder)
            db.commit()
            return True
        return False
    finally:
        db.close()


def update_file_paths(old_path: str, new_path: str):
    """Actualiza rutas de archivos después de renombrar carpeta"""
    db = db_service.get_db()
    try:
        # Actualizar archivos
        files_to_update = db.query(FileModel).filter(FileModel.ruta.startswith(old_path)).all()
        for file_record in files_to_update:
            file_record.ruta = file_record.ruta.replace(old_path, new_path, 1)
            file_record.updated_at = datetime.utcnow()

        # Actualizar subcarpetas
        folders_to_update = db.query(FolderModel).filter(FolderModel.ruta.startswith(old_path)).all()
        for folder in folders_to_update:
            folder.ruta = folder.ruta.replace(old_path, new_path, 1)

        db.commit()
    finally:
        db.close()


def check_folder_name_exists(nombre: str, parent_path: str, exclude_id: Optional[int] = None) -> bool:
    """Verifica si ya existe una carpeta con el mismo nombre en la misma ruta"""
    db = db_service.get_db()
    try:
        query = db.query(FolderModel).filter(
            FolderModel.nombre == nombre,
            FolderModel.ruta == parent_path
        )
        if exclude_id:
            query = query.filter(FolderModel.id != exclude_id)
        return query.first() is not None
    finally:
        db.close()


# ============================================================================
# Funciones de compatibilidad (legacy)
# ============================================================================

# Mantener referencias para compatibilidad con código existente
files_db = {}
folders_db = {}
counters = {"files": 0, "folders": 0}


def initialize_database():
    """Función de compatibilidad - la inicialización se hace en database_models.py"""
    pass