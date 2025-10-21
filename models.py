from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
import re

# ============================================================================
# Modelos de Archivos
# ============================================================================

class FileMetadata(BaseModel):
    id: Optional[int] = None
    nombre: str = Field(..., min_length=1, max_length=255)
    ruta: str = Field(..., max_length=1000)
    tamaño: int = Field(..., gt=0)
    tipo: str = Field(..., min_length=1, max_length=100)
    createdAt: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
    updatedAt: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

    @field_validator('nombre')
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """Valida que el nombre de archivo no contenga caracteres peligrosos"""
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError('Nombre de archivo inválido: no puede contener .. o separadores de ruta')
        if v.startswith('.') or v.endswith('.'):
            raise ValueError('Nombre de archivo inválido: no puede comenzar o terminar con punto')
        return v

    @field_validator('ruta')
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Valida que la ruta no contenga secuencias peligrosas"""
        if '..' in v:
            raise ValueError('Ruta inválida: no puede contener ..')
        return v

    @field_validator('createdAt', 'updatedAt')
    @classmethod
    def validate_datetime(cls, v: str) -> str:
        """Valida formato ISO 8601"""
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError(f'Fecha inválida: {v}. Debe tener formato ISO 8601')

    @field_validator('tipo')
    @classmethod
    def validate_mime_type(cls, v: str) -> str:
        """Valida formato básico de MIME type"""
        if '/' not in v or len(v.split('/')) != 2:
            raise ValueError('Tipo MIME inválido')
        return v.lower()


class FileUploadResponse(BaseModel):
    id: int
    nombre: str
    ruta: str
    tamaño: int
    tipo: str
    createdAt: str
    message: str = "Archivo subido exitosamente"


# ============================================================================
# Modelos de Carpetas
# ============================================================================

class FolderMetadata(BaseModel):
    id: Optional[int] = None
    nombre: str = Field(..., min_length=1, max_length=255)
    ruta: str = Field(..., max_length=1000)
    createdAt: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

    @field_validator('nombre')
    @classmethod
    def validate_foldername(cls, v: str) -> str:
        """Valida que el nombre de carpeta no contenga caracteres peligrosos"""
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError('Nombre de carpeta inválido: no puede contener .. o separadores de ruta')
        if v.startswith('.') or v.endswith('.'):
            raise ValueError('Nombre de carpeta inválido: no puede comenzar o terminar con punto')
        return v

    @field_validator('ruta')
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Valida que la ruta no contenga secuencias peligrosas"""
        if '..' in v:
            raise ValueError('Ruta inválida: no puede contener ..')
        return v

    @field_validator('createdAt')
    @classmethod
    def validate_datetime(cls, v: str) -> str:
        """Valida formato ISO 8601"""
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError(f'Fecha inválida: {v}. Debe tener formato ISO 8601')


class FolderCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=255)
    parentPath: str = Field(default="", max_length=1000)

    @field_validator('nombre')
    @classmethod
    def validate_foldername(cls, v: str) -> str:
        """Valida que el nombre de carpeta no contenga caracteres peligrosos"""
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError('Nombre de carpeta inválido: no puede contener .. o separadores de ruta')
        if v.startswith('.') or v.endswith('.'):
            raise ValueError('Nombre de carpeta inválido: no puede comenzar o terminar con punto')
        return v

    @field_validator('parentPath')
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Valida que la ruta padre no contenga secuencias peligrosas"""
        if '..' in v:
            raise ValueError('Ruta padre inválida: no puede contener ..')
        return v


class FolderRename(BaseModel):
    oldName: str = Field(..., min_length=1, max_length=255)
    newName: str = Field(..., min_length=1, max_length=255)
    parentPath: str = Field(default="", max_length=1000)

    @field_validator('oldName', 'newName')
    @classmethod
    def validate_foldername(cls, v: str) -> str:
        """Valida que el nombre de carpeta no contenga caracteres peligrosos"""
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError('Nombre de carpeta inválido: no puede contener .. o separadores de ruta')
        if v.startswith('.') or v.endswith('.'):
            raise ValueError('Nombre de carpeta inválido: no puede comenzar o terminar con punto')
        return v

    @field_validator('parentPath')
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Valida que la ruta padre no contenga secuencias peligrosas"""
        if '..' in v:
            raise ValueError('Ruta padre inválida: no puede contener ..')
        return v


# ============================================================================
# Modelos de Respuesta
# ============================================================================

class ListResponse(BaseModel):
    files: List[FileMetadata]
    folders: List[FolderMetadata]
    path: str = Field(default="", max_length=1000)

    @field_validator('path')
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Valida que la ruta no contenga secuencias peligrosas"""
        if '..' in v:
            raise ValueError('Ruta inválida: no puede contener ..')
        return v