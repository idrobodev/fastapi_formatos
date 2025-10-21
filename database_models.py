from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Optional
from datetime import datetime
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:Nalufis28++@corporacion-corporaciondb-4z75xa:5432/corporacion_db")
print(f"🔍 DATABASE_URL: {DATABASE_URL}")

engine = create_engine(DATABASE_URL)  # Remove echo=True for production
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# ============================================================================
# Modelos SQLAlchemy
# ============================================================================

class FileModel(Base):
    """Modelo SQLAlchemy para File"""
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    ruta = Column(String(1000), nullable=True)
    tamaño = Column(BigInteger, nullable=False)
    tipo = Column(String(100), nullable=False)
    categoria = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FolderModel(Base):
    """Modelo SQLAlchemy para Folder"""
    __tablename__ = "folders"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    ruta = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# Crear las tablas
Base.metadata.create_all(bind=engine)

# ============================================================================
# Servicio de Base de Datos
# ============================================================================

class DatabaseService:
    """Servicio de base de datos usando SQLAlchemy"""

    def __init__(self):
        self.initialize_default_data()

    def get_db(self) -> Session:
        """Obtener sesión de base de datos"""
        return SessionLocal()

    def initialize_default_data(self):
        """Inicializar datos por defecto"""
        db = self.get_db()
        try:
            # Verificar si ya existen datos
            if db.query(FolderModel).count() > 0:
                return

            # Crear carpetas por defecto
            folders_data = [
                {
                    "id": 1,
                    "nombre": "Documentos",
                    "ruta": "",
                    "created_at": datetime.fromisoformat("2024-01-15T10:00:00")
                },
                {
                    "id": 2,
                    "nombre": "Imágenes",
                    "ruta": "",
                    "created_at": datetime.fromisoformat("2024-01-16T11:00:00")
                },
                {
                    "id": 3,
                    "nombre": "Reportes",
                    "ruta": "Documentos/",
                    "created_at": datetime.fromisoformat("2024-01-17T12:00:00")
                }
            ]

            for folder_data in folders_data:
                folder = FolderModel(**folder_data)
                db.add(folder)

            # Crear archivos por defecto
            files_data = [
                {
                    "id": 1,
                    "nombre": "manual_usuario.pdf",
                    "ruta": "Documentos/",
                    "tamaño": 2048000,
                    "tipo": "application/pdf",
                    "categoria": "documento",
                    "created_at": datetime.fromisoformat("2024-01-15T10:30:00"),
                    "updated_at": datetime.fromisoformat("2024-01-15T10:30:00")
                },
                {
                    "id": 2,
                    "nombre": "logo.png",
                    "ruta": "Imágenes/",
                    "tamaño": 512000,
                    "tipo": "image/png",
                    "categoria": "imagen",
                    "created_at": datetime.fromisoformat("2024-01-16T11:15:00"),
                    "updated_at": datetime.fromisoformat("2024-01-16T11:15:00")
                },
                {
                    "id": 3,
                    "nombre": "datos.xlsx",
                    "ruta": "Documentos/",
                    "tamaño": 1024000,
                    "tipo": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "categoria": "documento",
                    "created_at": datetime.fromisoformat("2024-01-17T12:30:00"),
                    "updated_at": datetime.fromisoformat("2024-01-17T12:30:00")
                },
                {
                    "id": 4,
                    "nombre": "reporte_mensual.docx",
                    "ruta": "Documentos/Reportes/",
                    "tamaño": 1536000,
                    "tipo": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "categoria": "documento",
                    "created_at": datetime.fromisoformat("2024-01-18T13:00:00"),
                    "updated_at": datetime.fromisoformat("2024-01-18T13:00:00")
                },
                {
                    "id": 5,
                    "nombre": "banner.jpg",
                    "ruta": "Imágenes/",
                    "tamaño": 768000,
                    "tipo": "image/jpeg",
                    "categoria": "imagen",
                    "created_at": datetime.fromisoformat("2024-01-19T14:00:00"),
                    "updated_at": datetime.fromisoformat("2024-01-19T14:00:00")
                }
            ]

            for file_data in files_data:
                file_record = FileModel(**file_data)
                db.add(file_record)

            db.commit()
            print("✅ Datos por defecto inicializados en PostgreSQL para formatos")

        except Exception as e:
            db.rollback()
            print(f"❌ Error inicializando datos por defecto: {e}")
        finally:
            db.close()

# Instancia global del servicio de base de datos
db_service = DatabaseService()