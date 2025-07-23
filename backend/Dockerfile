FROM python:3.9-slim

WORKDIR /app/

# Actualizar pip
RUN pip install --no-cache-dir --upgrade pip

# Copiar los archivos de requisitos primero para aprovechar la caché de Docker
COPY ./requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . /app/

# Crear directorios necesarios
RUN mkdir -p /app/app/ml/models
RUN mkdir -p /app/app/ml/training/data

# Crear archivos __init__.py necesarios
RUN touch /app/app/__init__.py
RUN touch /app/app/api/__init__.py
RUN touch /app/app/api/v1/__init__.py
RUN touch /app/app/api/v1/endpoints/__init__.py
RUN touch /app/app/core/__init__.py
RUN touch /app/app/crud/__init__.py
RUN touch /app/app/ml/__init__.py
RUN touch /app/app/ml/models/__init__.py
RUN touch /app/app/schemas/__init__.py

# Comando para ejecutar la aplicación
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]