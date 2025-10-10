FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV DATABASE_URL=postgresql://postgres:Nalufis28++@corporacion-corporaciondb-4z75xa:5432/corporacion_db
ENV HOST=0.0.0.0
ENV PORT=8082
ENV ALLOWED_ORIGINS=https://todoporunalma.org,https://www.todoporunalma.org,http://localhost:3001,http://localhost:3001

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Crear directorio para storage
RUN mkdir -p storage/formatos

# Exponer puerto
EXPOSE 8082

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=40s \
    CMD python -c "import requests; requests.get('http://localhost:8082/api/health')"

# Comando para ejecutar la aplicación
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8082"]