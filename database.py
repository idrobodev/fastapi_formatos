"""
Base de datos en memoria para el sistema de gestión de formatos.
Simula una base de datos usando diccionarios de Python.
"""

# ============================================================================
# Contadores para IDs autoincrementales
# ============================================================================

counters = {
    "files": 0,
    "folders": 0
}

# ============================================================================
# Almacenamiento en memoria
# ============================================================================

# Estructura files_db:
# {
#     id: {
#         "id": int,
#         "nombre": str,
#         "ruta": str,
#         "tamaño": int,
#         "tipo": str,
#         "createdAt": str (ISO 8601),
#         "updatedAt": str (ISO 8601)
#     }
# }
files_db = {}

# Estructura folders_db:
# {
#     id: {
#         "id": int,
#         "nombre": str,
#         "ruta": str,
#         "createdAt": str (ISO 8601)
#     }
# }
folders_db = {}

# ============================================================================
# Funciones de inicialización de datos
# ============================================================================

def init_folders():
    """Inicializa datos de ejemplo para carpetas"""
    global folders_db
    folders_db = {
        1: {
            "id": 1,
            "nombre": "Documentos",
            "ruta": "",
            "createdAt": "2024-01-15T10:00:00Z"
        },
        2: {
            "id": 2,
            "nombre": "Imágenes",
            "ruta": "",
            "createdAt": "2024-01-16T11:00:00Z"
        },
        3: {
            "id": 3,
            "nombre": "Reportes",
            "ruta": "Documentos/",
            "createdAt": "2024-01-17T12:00:00Z"
        }
    }


def init_files():
    """Inicializa datos de ejemplo para archivos"""
    global files_db
    files_db = {
        1: {
            "id": 1,
            "nombre": "manual_usuario.pdf",
            "ruta": "Documentos/",
            "tamaño": 2048000,
            "tipo": "application/pdf",
            "createdAt": "2024-01-15T10:30:00Z",
            "updatedAt": "2024-01-15T10:30:00Z"
        },
        2: {
            "id": 2,
            "nombre": "logo.png",
            "ruta": "Imágenes/",
            "tamaño": 512000,
            "tipo": "image/png",
            "createdAt": "2024-01-16T11:15:00Z",
            "updatedAt": "2024-01-16T11:15:00Z"
        },
        3: {
            "id": 3,
            "nombre": "datos.xlsx",
            "ruta": "Documentos/",
            "tamaño": 1024000,
            "tipo": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "createdAt": "2024-01-17T12:30:00Z",
            "updatedAt": "2024-01-17T12:30:00Z"
        },
        4: {
            "id": 4,
            "nombre": "reporte_mensual.docx",
            "ruta": "Documentos/Reportes/",
            "tamaño": 1536000,
            "tipo": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "createdAt": "2024-01-18T13:00:00Z",
            "updatedAt": "2024-01-18T13:00:00Z"
        },
        5: {
            "id": 5,
            "nombre": "banner.jpg",
            "ruta": "Imágenes/",
            "tamaño": 768000,
            "tipo": "image/jpeg",
            "createdAt": "2024-01-19T14:00:00Z",
            "updatedAt": "2024-01-19T14:00:00Z"
        }
    }


def initialize_database():
    """Inicializa toda la base de datos con datos de ejemplo"""
    init_folders()
    init_files()
    # Actualizar contadores
    counters["folders"] = len(folders_db)
    counters["files"] = len(files_db)
    print("✅ Base de datos inicializada con datos de ejemplo")
    print(f"   - {len(folders_db)} carpetas")
    print(f"   - {len(files_db)} archivos")


# Inicializar la base de datos al importar el módulo
initialize_database()