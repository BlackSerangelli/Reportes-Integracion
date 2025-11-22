# Microservicio de Gestión de Imágenes (GCP + Flask)

Este microservicio permite subir, listar y visualizar imágenes almacenadas en un bucket de Google Cloud Storage, con registro de metadatos en una base de datos MariaDB.

La API está protegida por un token Bearer y ofrece respuestas en XML (default) y JSON.

## 1. Configuración del Entorno

El servicio se configura completamente a través de variables de entorno.

### Variables de Entorno Requeridas

**Autenticación del Servicio (Token):**
* `API_TOKEN`: Tu token secreto para autenticar las solicitudes (ej: `super_secret_token_123`).

**Conexión a Google Cloud Storage:**
* `GCS_BUCKET_NAME`: El nombre de tu bucket en GCS (ej: `microservicio-libros`).
* `GCS_PROJECT_ID`: El ID de tu proyecto en Google Cloud Platform.
* `GOOGLE_APPLICATION_CREDENTIALS`: Ruta completa al archivo JSON de credenciales de tu Service Account (ej: `/ruta/a/service-account-key.json`).

**Conexión a MariaDB:**
* `DB_HOST`: La dirección del servidor de MariaDB (ej: `localhost` o una IP).
* `DB_USER`: El usuario de la base de datos.
* `DB_PASSWORD`: La contraseña del usuario de la base de datos.
* `DB_NAME`: El nombre de la base de datos donde está la tabla `images`.

## 2. Instalación

1.  Clona este repositorio (o copia los archivos).
2.  Crea un entorno virtual:
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    ```
3.  Instala las dependencias:
    ```bash
    pip install -r requirements.txt
    ```
4.  Ejecuta el script `init.sql` en tu base de datos MariaDB para crear la tabla.
5.  Crea un bucket en Google Cloud Storage y una Service Account con permisos de "Storage Admin" o "Storage Object Admin".
6.  Descarga el archivo JSON de credenciales de la Service Account.

## 3. Ejecución

1.  Exporta todas las variables de entorno listadas arriba (o usa un archivo `.env`).
    ```bash
    # Ejemplo en Linux/macOS
    export API_TOKEN="tu_token_secreto"
    export GCS_BUCKET_NAME="microservicio-libros"
    export GCS_PROJECT_ID="tu-proyecto-id"
    export GOOGLE_APPLICATION_CREDENTIALS="/ruta/a/service-account-key.json"
    export DB_HOST="localhost"
    export DB_USER="root"
    export DB_PASSWORD="tu_db_pass"
    export DB_NAME="nombre_de_tu_db"
    ```

    **Alternativa con archivo `.env`:**
    ```bash
    cp .env.example .env
    # Edita .env con tus valores reales
    ```
2.  Inicia la aplicación Flask:
    ```bash
    flask run
    # O para producción:
    # gunicorn --bind 0.0.0.0:5000 app:app
    ```

## 4. Ejemplos de Uso (curl)

Asegúrate de reemplazar `tu_token_secreto` con el valor de tu `API_TOKEN`.

### Subir una imagen

```bash
curl -X POST [http://127.0.0.1:5000/upload](http://127.0.0.1:5000/upload) \
     -H "Authorization: Bearer tu_token_secreto" \
     -F "image=@/ruta/a/tu/imagen.jpg"
