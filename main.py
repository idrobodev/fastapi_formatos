from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from utils import ensure_storage_directory, format_datetime
from database import initialize_database, files_db, counters, folders_db
from models import FileUploadResponse, FolderCreate, FolderRename
from services import validate_path, validate_file_type, sanitize_filename, get_unique_filename, get_mime_type, delete_folder_recursive, get_file_category, ensure_category_folder

# ============================================================================
# Configuración de lifespan para inicialización
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja los eventos de startup y shutdown de la aplicación"""
    # Startup
    ensure_storage_directory()
    initialize_database()

    yield

    # Shutdown (si es necesario en el futuro)
    pass

# ============================================================================
# Configuración de la aplicación FastAPI
# ============================================================================

app = FastAPI(
    title="Formatos API - Corporación Todo por un Alma",
    description="API REST para gestión de archivos y formatos",
    version="1.0.0",
    lifespan=lifespan
)

# ============================================================================
# Configuración de CORS
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Endpoints de Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    """Endpoint de health check para verificar que el servidor está funcionando"""
    return {
        "status": "ok",
        "message": "Formatos API is running",
        "service": "Formatos API - Corporación Todo por un Alma",
        "version": "1.0.0"
    }

# ============================================================================
# Endpoints de Archivos
# ============================================================================

@app.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...)):
    """
    Sube un archivo al sistema de gestión de formatos.
    Los archivos se organizan automáticamente en carpetas por tipo.

    - **file**: Archivo a subir
    """
    try:
        # Validar tamaño del archivo (100MB máximo)
        MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
        file_content = await file.read()
        file_size = len(file_content)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Archivo demasiado grande. Tamaño máximo: 100MB, tamaño recibido: {file_size} bytes"
            )

        # Validar tipo de archivo
        temp_file_path = f"/tmp/{file.filename}"
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(file_content)

        if not validate_file_type(temp_file_path):
            # Limpiar archivo temporal
            Path(temp_file_path).unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de archivo no permitido"
            )

        # Determinar categoría del archivo y asegurar que la carpeta existe
        category = get_file_category(file.filename)
        category_folder = ensure_category_folder(category)

        # Sanitizar nombre de archivo
        sanitized_name = sanitize_filename(file.filename)

        # Generar nombre único en la carpeta de categoría
        unique_name = get_unique_filename(category_folder, sanitized_name)

        # Crear directorio de destino
        storage_path = Path("storage/formatos")
        dest_dir = storage_path / category_folder
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Guardar archivo
        file_path = dest_dir / unique_name
        with open(file_path, "wb") as dest_file:
            dest_file.write(file_content)

        # Limpiar archivo temporal
        Path(temp_file_path).unlink(missing_ok=True)

        # Crear registro en base de datos
        new_id = counters["files"] + 1
        counters["files"] = new_id

        now = datetime.utcnow()
        now_iso = format_datetime(now)

        mime_type = get_mime_type(unique_name)

        file_record = {
            "id": new_id,
            "nombre": unique_name,
            "ruta": category_folder,
            "tamaño": file_size,
            "tipo": mime_type,
            "categoria": category,
            "createdAt": now_iso,
            "updatedAt": now_iso
        }

        files_db[new_id] = file_record

        # Retornar respuesta
        return FileUploadResponse(
            id=new_id,
            nombre=unique_name,
            ruta=category_folder,
            tamaño=file_size,
            tipo=mime_type,
            createdAt=now_iso,
        )

    except HTTPException:
        raise
    except Exception as e:
        # Limpiar archivo temporal en caso de error
        temp_file_path = f"/tmp/{file.filename}"
        Path(temp_file_path).unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al subir archivo: {str(e)}"
        )


@app.get("/download/{file_id}")
async def download_file(file_id: int):
    """
    Descarga un archivo por su ID.

    - **file_id**: ID del archivo a descargar
    """
    # Buscar archivo en base de datos
    file_record = files_db.get(file_id)
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo no encontrado"
        )

    # Construir ruta del archivo físico
    storage_path = Path("storage/formatos")
    if file_record['ruta']:
        file_path = storage_path / file_record['ruta'].lstrip('/') / file_record['nombre']
    else:
        file_path = storage_path / file_record['nombre']

    # Verificar que el archivo físico exista
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Archivo físico no encontrado en el servidor"
        )

    # Retornar archivo con headers apropiados
    return FileResponse(
        path=file_path,
        filename=file_record['nombre'],
        media_type=file_record['tipo']
    )


@app.get("/list")
async def list_files(path: str = ""):
    """
    Lista archivos y carpetas en una ruta específica.

    - **path**: Ruta a listar (opcional, default="")
    """
    try:
        # Validar ruta
        if not validate_path(path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ruta inválida"
            )

        # Filtrar archivos por ruta
        filtered_files = []
        for file_data in files_db.values():
            if file_data['ruta'] == path:
                filtered_files.append(file_data)

        # Filtrar carpetas por ruta padre
        filtered_folders = []
        for folder_data in folders_db.values():
            if folder_data['ruta'] == path:
                filtered_folders.append(folder_data)

        return {
            "files": filtered_files,
            "folders": filtered_folders,
            "path": path
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar archivos: {str(e)}"
        )


@app.delete("/{file_id}")
async def delete_file(file_id: int):
    """
    Elimina un archivo por su ID.

    - **file_id**: ID del archivo a eliminar
    """
    # Buscar archivo en base de datos
    file_record = files_db.get(file_id)
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo no encontrado"
        )

    # Construir ruta del archivo físico
    storage_path = Path("storage/formatos")
    if file_record['ruta']:
        file_path = storage_path / file_record['ruta'].lstrip('/') / file_record['nombre']
    else:
        file_path = storage_path / file_record['nombre']

    # Intentar eliminar archivo físico
    physical_file_deleted = True
    warning_message = None

    try:
        if file_path.exists():
            file_path.unlink()
        else:
            physical_file_deleted = False
            warning_message = "El archivo físico no existía en el sistema de archivos"
    except Exception as e:
        physical_file_deleted = False
        warning_message = f"Error al eliminar archivo físico: {str(e)}"

    # Eliminar registro de base de datos
    del files_db[file_id]

    # Preparar mensaje de respuesta
    message = "Archivo eliminado exitosamente"
    if warning_message:
        message += f". Advertencia: {warning_message}"

    return {
        "message": message,
        "id": file_id,
        "physical_file_deleted": physical_file_deleted
    }


# ============================================================================
# Endpoints de Carpetas
# ============================================================================

@app.post("/folders/create", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_folder(folder: FolderCreate):
    """
    Crea una nueva carpeta.

    - **folder**: Datos de la carpeta a crear (nombre, parentPath)
    """
    try:
        # Validar nombre de carpeta (usando la validación del modelo)
        # La validación ya se hace automáticamente por Pydantic

        # Verificar que no exista una carpeta con el mismo nombre en la misma ruta
        parent_path = folder.parentPath or ""
        for existing_folder in folders_db.values():
            if existing_folder['nombre'] == folder.nombre and existing_folder['ruta'] == parent_path:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Ya existe una carpeta con el nombre '{folder.nombre}' en esta ubicación"
                )

        # Crear directorio físico
        storage_path = Path("storage/formatos")
        if parent_path:
            folder_path = storage_path / parent_path.lstrip('/') / folder.nombre
        else:
            folder_path = storage_path / folder.nombre

        folder_path.mkdir(parents=True, exist_ok=True)

        # Crear registro en base de datos
        new_id = counters["folders"] + 1
        counters["folders"] = new_id

        now = datetime.utcnow()
        now_iso = format_datetime(now)

        folder_record = {
            "id": new_id,
            "nombre": folder.nombre,
            "ruta": parent_path,
            "createdAt": now_iso
        }

        folders_db[new_id] = folder_record

        return folder_record

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear carpeta: {str(e)}"
        )


@app.put("/folders/rename")
async def rename_folder(folder_rename: FolderRename):
    """
    Renombra una carpeta existente.

    - **folder_rename**: Datos para renombrar (oldName, newName, parentPath)
    """
    try:
        # Buscar carpeta por nombre y ruta padre
        parent_path = folder_rename.parentPath or ""
        folder_to_rename = None
        folder_id = None

        for fid, folder in folders_db.items():
            if folder['nombre'] == folder_rename.oldName and folder['ruta'] == parent_path:
                folder_to_rename = folder
                folder_id = fid
                break

        if not folder_to_rename:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontró la carpeta '{folder_rename.oldName}' en la ruta especificada"
            )

        # Verificar que no exista una carpeta con el nuevo nombre en la misma ruta
        for folder in folders_db.values():
            if (folder['nombre'] == folder_rename.newName and
                folder['ruta'] == parent_path and
                folder['id'] != folder_id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Ya existe una carpeta con el nombre '{folder_rename.newName}' en esta ubicación"
                )

        # Renombrar directorio físico
        storage_path = Path("storage/formatos")
        if parent_path:
            old_path = storage_path / parent_path.lstrip('/') / folder_rename.oldName
            new_path = storage_path / parent_path.lstrip('/') / folder_rename.newName
        else:
            old_path = storage_path / folder_rename.oldName
            new_path = storage_path / folder_rename.newName

        if old_path.exists():
            old_path.rename(new_path)

        # Actualizar registro en base de datos
        folder_to_rename['nombre'] = folder_rename.newName
        folders_db[folder_id] = folder_to_rename

        # Actualizar rutas de archivos y subcarpetas
        old_folder_path = parent_path + folder_rename.oldName + '/' if parent_path else folder_rename.oldName + '/'
        new_folder_path = parent_path + folder_rename.newName + '/' if parent_path else folder_rename.newName + '/'

        # Actualizar rutas de archivos
        for file_data in files_db.values():
            if file_data['ruta'].startswith(old_folder_path):
                file_data['ruta'] = file_data['ruta'].replace(old_folder_path, new_folder_path, 1)

        # Actualizar rutas de subcarpetas
        for sub_folder in folders_db.values():
            if sub_folder['ruta'].startswith(old_folder_path):
                sub_folder['ruta'] = sub_folder['ruta'].replace(old_folder_path, new_folder_path, 1)

        return {
            "message": f"Carpeta renombrada de '{folder_rename.oldName}' a '{folder_rename.newName}' exitosamente",
            "oldName": folder_rename.oldName,
            "newName": folder_rename.newName,
            "parentPath": parent_path
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al renombrar carpeta: {str(e)}"
        )


@app.delete("/folders/{folder_id}")
async def delete_folder(folder_id: int):
    """
    Elimina una carpeta y todo su contenido recursivamente.

    - **folder_id**: ID de la carpeta a eliminar
    """
    try:
        # Verificar que la carpeta exista
        if folder_id not in folders_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Carpeta no encontrada"
            )

        # Llamar a la función de eliminación recursiva
        success = delete_folder_recursive(folder_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al eliminar la carpeta"
            )

        return {
            "message": "Carpeta eliminada exitosamente",
            "id": folder_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar carpeta: {str(e)}"
        )