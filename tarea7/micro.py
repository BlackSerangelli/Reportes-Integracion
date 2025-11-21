import os, uuid, io
import datetime as dt
from flask import Flask, request, Response, g, jsonify, make_response
import MySQLdb, jwt, redis
from flask_cors import CORS
from functools import wraps
from urllib.parse import urlparse
from flasgger import Swagger, swag_from
from werkzeug.utils import secure_filename

# --- Carga de variables de entorno (.env) ---
from dotenv import load_dotenv
load_dotenv()

# =========================
# App & Config
# =========================
app = Flask(__name__)

# --- INICIO DE LA CORRECCIÓN DE SWAGGER ---

# 1. Elimina el bloque app.config['SWAGGER'] que tenías aquí.

# 2. Define UN ÚNICO TEMPLATE que tiene TODO: info, definiciones Y seguridad.
SWAGGER_TEMPLATE = {
    'swagger': '2.0',
    'info': {
        'title': '📚 Microservicio de Gestión de Biblioteca Digital',
        'description': 'Sistema avanzado de administración de libros con almacenamiento en Azure',
        'version': '2.5.0',
        'contact': {
            'name': 'Equipo de Desarrollo',
            'email': 'dev@biblioteca.com'
        }
    },
    'schemes': ['http', 'https'],
    'securityDefinitions': {
        'bearerAuth': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': "🔐 Token JWT de autenticación (sin prefijo 'Bearer'). Ejemplo: eyJhbGci..."
        }
    },
    'security': [{'bearerAuth': []}], # Aplica seguridad global
    'definitions': {
        'BookWithImages': {
            'type': 'object',
            'description': 'Modelo completo de libro con imágenes',
            'properties': {
                'id_libro': {'type': 'integer', 'description': '🆔 Identificador único del libro'},
                'isbn': {'type': 'string', 'description': '📖 Código ISBN estándar'},
                'titulo': {'type': 'string', 'description': '📝 Título del libro'},
                'anio_publicacion': {'type': 'integer', 'description': '📅 Año de publicación'},
                'precio': {'type': 'number', 'format': 'float', 'description': '💰 Precio en moneda local'},
                'stock': {'type': 'integer', 'description': '📦 Cantidad disponible'},
                'genero': {'type': 'string', 'description': '🎭 Género literario'},
                'formato': {'type': 'string', 'description': '📄 Formato físico (tapa dura, blanda, etc.)'},
                'autor': {'type': 'string', 'description': '✍️ Autores (separados por coma)'},
                'imagenes': {
                    'type': 'array',
                    'items': {'type': 'string', 'format': 'uri'},
                    'description': '🖼️ URLs de imágenes almacenadas en Azure'
                }
            }
        },
        'BookList': {
            'type': 'array',
            'description': 'Colección de libros',
            'items': {'$ref': '#/definitions/BookWithImages'}
        }
    }
}
# 3. Inicia Swagger con el template corregido y configuración personalizada
swagger = Swagger(app, template=SWAGGER_TEMPLATE, config={
    'docExpansion': 'list',
    'defaultModelsExpandDepth': 3,
    'syntaxHighlight.theme': 'monokai'
})

# 4. CSS personalizado para la interfaz de Swagger
@app.route('/swagger-ui-custom.css')
def swagger_ui_css():
    custom_css = """
    .swagger-ui .topbar {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        border-bottom: 4px solid #4facfe;
    }
    .swagger-ui .info .title {
        color: #f5576c;
        font-size: 44px;
        font-weight: 900;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .swagger-ui .info .description {
        color: #2d3748;
        font-size: 17px;
        line-height: 1.6;
    }
    .swagger-ui .opblock-tag {
        font-size: 30px;
        font-weight: 800;
        color: #f5576c;
        border-bottom: 4px solid #4facfe;
        padding: 15px 0;
    }
    .swagger-ui .opblock.opblock-post {
        background: rgba(245, 87, 108, 0.12);
        border-color: #f5576c;
        border-left: 5px solid #f5576c;
    }
    .swagger-ui .opblock.opblock-post .opblock-summary-method {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        font-weight: 700;
    }
    .swagger-ui .opblock.opblock-get {
        background: rgba(79, 172, 254, 0.12);
        border-color: #4facfe;
        border-left: 5px solid #4facfe;
    }
    .swagger-ui .opblock.opblock-get .opblock-summary-method {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        font-weight: 700;
    }
    .swagger-ui .opblock.opblock-put {
        background: rgba(250, 173, 20, 0.12);
        border-color: #faad14;
        border-left: 5px solid #faad14;
    }
    .swagger-ui .opblock.opblock-put .opblock-summary-method {
        background: linear-gradient(135deg, #faad14 0%, #ffa940 100%);
        font-weight: 700;
    }
    .swagger-ui .opblock.opblock-delete {
        background: rgba(255, 77, 79, 0.12);
        border-color: #ff4d4f;
        border-left: 5px solid #ff4d4f;
    }
    .swagger-ui .opblock.opblock-delete .opblock-summary-method {
        background: linear-gradient(135deg, #ff4d4f 0%, #cf1322 100%);
        font-weight: 700;
    }
    .swagger-ui .btn.authorize {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        border-color: #f5576c;
        color: white;
        font-weight: 700;
        box-shadow: 0 2px 8px rgba(245, 87, 108, 0.3);
    }
    .swagger-ui .btn.execute {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        border-color: #4facfe;
        font-weight: 700;
        box-shadow: 0 2px 8px rgba(79, 172, 254, 0.3);
    }
    .swagger-ui .scheme-container {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    .swagger-ui .opblock-summary-description {
        font-weight: 600;
        font-size: 15px;
    }
    .swagger-ui .model-box {
        background: rgba(79, 172, 254, 0.05);
        border-radius: 8px;
    }
    """
    return Response(custom_css, mimetype='text/css')

# --- FIN DE LA CORRECCIÓN DE SWAGGER ---


# --- CORS y Manejador de Pre-flight (OPTIONS) ---
CORS(app)
@app.before_request
def handle_preflight():
    """Maneja las solicitudes OPTIONS (pre-flight) de CORS."""
    if request.method == "OPTIONS":
        res = make_response()
        res.headers.add("Access-Control-Allow-Origin", "*")
        res.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
        res.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        return res, 200

# --- DB Config ---
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST','localhost'),
    'user': os.getenv('MYSQL_USER','libros_user'),
    'passwd': os.getenv('MYSQL_PASSWORD','666'),
    'db': os.getenv('MYSQL_DB','Libros'),
    'charset': 'utf8mb4',
    'autocommit': False # IMPORTANTE para transacciones
}

# --- JWT + Redis Config ---
JWT_SECRET = os.getenv('JWT_SECRET','cambia-esto-en-produccion')
JWT_ALG = 'HS256'
REDIS_URL = os.getenv('REDIS_URL','redis://127.0.0.1:6379/0')
rconf = urlparse(REDIS_URL)
r = redis.Redis(host=rconf.hostname, port=rconf.port or 6379, db=int((rconf.path or '/0')[1:] or 0), password=rconf.password, decode_responses=True)

# --- Azure Blob Storage Config ---
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

ACCOUNT_URL = os.getenv("AZURE_STORAGE_ACCOUNT_URL", "https://imagenesintegracion.blob.core.windows.net")
CONTAINER_NAME = os.getenv("CONTAINER_NAME", "microservicio-libros")

try:
    credential = DefaultAzureCredential()
    blob_service_client = BlobServiceClient(account_url=ACCOUNT_URL, credential=credential)
    container_client = blob_service_client.get_container_client(CONTAINER_NAME)
    print("Azure Blob Storage conectado exitosamente.")
except Exception as e:
    print(f"Error al conectar con Azure Blob Storage: {e}")
    blob_service_client = None

# --- Configuración de Archivos Multimedia ---
ALLOWED_IMAGE_TYPES = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MAXIMUM_IMAGES_PER_BOOK = 8
IMAGE_QUALITY_THRESHOLD = 'high'

def validate_image_file(filename):
    """Valida que el archivo tenga una extensión de imagen válida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_TYPES

def create_error_response(error_message, http_status):
    """Genera una respuesta de error estandarizada en formato JSON."""
    return make_response(jsonify({
        "success": False,
        "error_message": error_message,
        "status_code": http_status,
        "timestamp": dt.datetime.utcnow().isoformat() + "Z"
    }), http_status)

# =========================
# DB & Auth
# =========================
def get_database_connection():
    """Establece y retorna una conexión a la base de datos por request."""
    if 'database_conn' not in g:
        try:
            g.database_conn = MySQLdb.connect(**DB_CONFIG)
            print("✅ Conexión a base de datos establecida")
        except MySQLdb.Error as db_error:
            print(f"❌ Error al conectar con la base de datos: {db_error}")
            g.database_conn = None
    return g.database_conn

@app.teardown_appcontext
def cleanup_database_connection(exception):
    """Limpia y cierra la conexión de base de datos al finalizar la request."""
    database_conn = g.pop('database_conn', None)
    if database_conn is not None:
        if exception:
            database_conn.rollback()
            print("⚠️ Rollback ejecutado debido a excepción")
        else:
            database_conn.commit()
            print("✅ Commit exitoso")
        database_conn.close()
        print("🔒 Conexión cerrada")

def jwt_required(fn):
    """Decorador de autenticación JWT - Valida tokens de acceso."""
    @wraps(fn)
    def wrapper_function(*args, **kwargs):
        authorization_header = request.headers.get('Authorization', '')
        if not authorization_header.startswith('Bearer '):
            return create_error_response("🔐 Token de autorización requerido", 401)

        access_token = authorization_header.split(' ', 1)[1].strip()
        try:
            token_payload = jwt.decode(access_token, JWT_SECRET, algorithms=[JWT_ALG])

            if token_payload.get('type') != 'access':
                return create_error_response("🚫 Tipo de token inválido", 401)

            token_jti = token_payload.get('jti')
            if not token_jti or not r.exists(f"access:session:{token_jti}"):
                return create_error_response("⛔ Token revocado o inválido", 401)

            g.current_user_id = int(token_payload['sub'])
            g.current_username = token_payload.get('username')

        except jwt.ExpiredSignatureError:
            return create_error_response("⏰ Token expirado - Por favor inicia sesión nuevamente", 401)
        except jwt.InvalidTokenError:
            return create_error_response("❌ Token inválido o corrupto", 401)

        return fn(*args, **kwargs)
    return wrapper_function

# =========================
# Azure Blob Helpers
# =========================
def upload_to_azure_storage(file_storage):
    """Procesa y sube una imagen a Azure Blob Storage.
    Retorna: (url_publica, nombre_blob)
    """
    if not blob_service_client:
        raise Exception("❌ Cliente de Azure Blob Storage no disponible")

    secure_name = secure_filename(file_storage.filename)
    file_extension = secure_name.rsplit('.', 1)[1].lower()
    unique_identifier = str(uuid.uuid4())
    blob_path = f"biblioteca/imagenes/{unique_identifier}.{file_extension}"

    try:
        azure_blob_client = container_client.get_blob_client(blob_path)
        azure_blob_client.upload_blob(file_storage.stream, overwrite=True)

        public_image_url = f"{ACCOUNT_URL}/{CONTAINER_NAME}/{blob_path}"
        print(f"✅ Imagen subida exitosamente: {blob_path}")

        return public_image_url, blob_path

    except Exception as upload_error:
        print(f"❌ Error durante la subida a Azure: {upload_error}")
        raise Exception(f"No se pudo subir la imagen: {upload_error}")

def remove_blob_from_azure(blob_identifier):
    """Elimina permanentemente un blob de Azure Blob Storage."""
    if not blob_service_client or not blob_identifier:
        print("⚠️ No se puede eliminar: Cliente o identificador no disponible")
        return

    try:
        azure_blob_client = container_client.get_blob_client(blob_identifier)
        azure_blob_client.delete_blob(delete_snapshots="include")
        print(f"🗑️ Blob eliminado correctamente: {blob_identifier}")
    except Exception as delete_error:
        print(f"⚠️ Error al eliminar blob {blob_identifier}: {delete_error}")

# =========================
# Endpoints de Libros
# =========================

@app.get('/')
def home():
    """Endpoint de bienvenida con información del servicio"""
    return jsonify({
        "message":"📚 Bienvenido a la API de Gestión de Biblioteca Digital v2.5.0",
        "documentation":"/apidocs/",
        "version":"2.5.0",
        "theme":"Pink & Blue Gradient Theme 💗💙",
        "features":[
            "📖 Gestión completa de libros",
            "🖼️ Almacenamiento de imágenes en Azure",
            "🔍 Búsqueda y filtros avanzados",
            "🔐 Autenticación JWT"
        ],
        "endpoints":{
            "list":"/api/books",
            "get":"/api/books/{id}",
            "create":"/api/books",
            "update":"/api/books/{id}",
            "delete":"/api/books/{id}"
        }
    }), 200

@app.get('/api/books')
@jwt_required
@swag_from({
    'tags': ['📚 Catálogo de Libros'],
    'summary': '📋 Listar Todos los Libros',
    'description': 'Obtiene el catálogo completo con filtros avanzados de búsqueda, género, formato y autor',

    'security': [{'bearerAuth': []}],

    'parameters': [
        {'in': 'query', 'name': 'q', 'type': 'string', 'description': '🔍 Búsqueda por título o ISBN'},
        {'in': 'query', 'name': 'genero', 'type': 'string', 'description': '🎭 Filtrar por género literario'},
        {'in': 'query', 'name': 'formato', 'type': 'string', 'description': '📄 Filtrar por formato físico'},
        {'in': 'query', 'name': 'autor', 'type': 'string', 'description': '✍️ Filtrar por nombre del autor'}
    ],
    'responses': {
        200: {'description': '✅ Lista de libros obtenida', 'schema': {'$ref': '#/definitions/BookList'}}
    }
})
def get_all_books():
    database_connection = get_database_connection()
    if not database_connection:
        return create_error_response("💔 No se pudo establecer conexión con la base de datos", 500)

    database_cursor = database_connection.cursor(MySQLdb.cursors.DictCursor)

    query = """
    SELECT
        l.id_libro, l.isbn, l.titulo, l.anio_publicacion, l.precio, l.stock,
        g.nombre AS genero, f.nombre AS formato,
        (SELECT GROUP_CONCAT(a.nombre SEPARATOR ', ')
         FROM autores a JOIN libro_autor la ON a.id_autor = la.id_autor
         WHERE la.id_libro = l.id_libro) AS autor,
        (SELECT GROUP_CONCAT(li.url SEPARATOR '||')
         FROM libro_imagenes li
         WHERE li.id_libro = l.id_libro ORDER BY li.orden) AS imagenes
    FROM libros l
    LEFT JOIN genero g ON l.id_genero = g.id_genero
    LEFT JOIN formato f ON l.id_formato = f.id_formato
    """

    where_clauses = []
    params = []

    q = request.args.get('q')
    if q:
        where_clauses.append("(l.titulo LIKE %s OR l.isbn LIKE %s)")
        params.extend([f"%{q}%", f"%{q}%"])

    genero = request.args.get('genero')
    if genero:
        where_clauses.append("g.nombre = %s")
        params.append(genero)

    formato = request.args.get('formato')
    if formato:
        where_clauses.append("f.nombre = %s")
        params.append(formato)

    autor = request.args.get('autor')
    if autor:
        query += """
        JOIN libro_autor la_filt ON l.id_libro = la_filt.id_libro
        JOIN autores a_filt ON la_filt.id_autor = a_filt.id_autor
        """
        where_clauses.append("a_filt.nombre = %s")
        params.append(autor)

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    query += " GROUP BY l.id_libro ORDER BY l.titulo ASC"

    database_cursor.execute(query, tuple(params))
    books_collection = database_cursor.fetchall()
    database_cursor.close()

    # Procesar imágenes para cada libro
    for libro in books_collection:
        if libro.get('imagenes'):
            libro['imagenes'] = libro['imagenes'].split('||')
        else:
            libro['imagenes'] = []

    return jsonify({
        "success": True,
        "total_books": len(books_collection),
        "data": books_collection
    }), 200

# --- Endpoint para obtener un solo libro ---
@app.get('/api/books/<int:id_libro>')
@jwt_required
@swag_from({
    'tags': ['📚 Catálogo de Libros'],
    'summary': '🔎 Obtener Libro Específico',
    'description': 'Recupera los detalles completos de un libro por su ID único',

    'security': [{'bearerAuth': []}],

    'parameters': [
        {'in': 'path', 'name': 'id_libro', 'type': 'integer', 'required': True, 'description': '🆔 ID del libro'}
    ],
    'responses': {
        200: {'description': '✅ Libro encontrado', 'schema': {'$ref': '#/definitions/BookWithImages'}},
        404: {'description': '❌ Libro no existe'}
    }
})
def get_book_by_id(id_libro):
    database_connection = get_database_connection()
    if not database_connection:
        return create_error_response("💔 Error de conexión con el servidor de base de datos", 500)

    database_cursor = database_connection.cursor(MySQLdb.cursors.DictCursor)

    query = """
    SELECT
        l.id_libro, l.isbn, l.titulo, l.anio_publicacion, l.precio, l.stock,
        g.nombre AS genero, f.nombre AS formato,
        (SELECT GROUP_CONCAT(a.nombre SEPARATOR ', ')
         FROM autores a JOIN libro_autor la ON a.id_autor = la.id_autor
         WHERE la.id_libro = l.id_libro) AS autor,
        (SELECT GROUP_CONCAT(li.url SEPARATOR '||')
         FROM libro_imagenes li
         WHERE li.id_libro = l.id_libro ORDER BY li.orden) AS imagenes
    FROM libros l
    LEFT JOIN genero g ON l.id_genero = g.id_genero
    LEFT JOIN formato f ON l.id_formato = f.id_formato
    WHERE l.id_libro = %s
    GROUP BY l.id_libro
    """
    database_cursor.execute(query, (id_libro,))
    book_data = database_cursor.fetchone()
    database_cursor.close()

    if not book_data:
        return create_error_response(f"📚 No se encontró el libro con ID {id_libro}", 404)

    # Procesar imágenes
    if book_data.get('imagenes'):
        book_data['imagenes'] = book_data['imagenes'].split('||')
    else:
        book_data['imagenes'] = []

    return jsonify({
        "success": True,
        "data": book_data
    }), 200


@app.post('/api/books')
@jwt_required
@swag_from({
    'tags': ['📚 Catálogo de Libros'],
    'summary': '➕ Agregar Nuevo Libro',
    'description': 'Registra un nuevo libro en el catálogo con imágenes. Acepta multipart/form-data con campos de formulario para datos y archivos de imagen.',
    'consumes': ['multipart/form-data'],

    'security': [{'bearerAuth': []}],

    'parameters': [
        {'in': 'formData', 'name': 'isbn', 'type': 'string', 'required': True, 'description': '📖 Código ISBN'},
        {'in': 'formData', 'name': 'titulo', 'type': 'string', 'required': True, 'description': '📝 Título del libro'},
        {'in': 'formData', 'name': 'anio_publicacion', 'type': 'integer', 'required': True, 'description': '📅 Año de publicación'},
        {'in': 'formData', 'name': 'precio', 'type': 'number', 'required': True, 'description': '💰 Precio'},
        {'in': 'formData', 'name': 'stock', 'type': 'integer', 'required': True, 'description': '📦 Cantidad en stock'},
        {'in': 'formData', 'name': 'autor', 'type': 'string', 'description': '✍️ Nombre del autor principal', 'required': True},
        {'in': 'formData', 'name': 'genero', 'type': 'string', 'required': True, 'description': '🎭 Género literario'},
        {'in': 'formData', 'name': 'formato', 'type': 'string', 'required': True, 'description': '📄 Formato físico'},
        {
            'in': 'formData',
            'name': 'images',
            'type': 'file',
            'description': f'🖼️ Imágenes del libro (Máx {MAXIMUM_IMAGES_PER_BOOK} archivos, {MAX_UPLOAD_SIZE_BYTES//1024//1024}MB cada uno, formatos: {ALLOWED_IMAGE_TYPES})'
        }
    ],
    'responses': {
        201: {'description': '✅ Libro creado exitosamente'},
        400: {'description': '⚠️ Error de validación en los datos'}
    }
})
def insert_book():
    database_connection = get_database_connection()
    if not database_connection:
        return create_error_response("💔 Error al conectar con la base de datos", 500)

    try:
        form_data = request.form
        uploaded_images = request.files.getlist('images')

        if len(uploaded_images) > MAXIMUM_IMAGES_PER_BOOK:
            return create_error_response(
                f"🖼️ Límite excedido: máximo {MAXIMUM_IMAGES_PER_BOOK} imágenes por libro", 400)

        validated_images = []
        for image_file in uploaded_images:
            if image_file and validate_image_file(image_file.filename):
                image_file.seek(0, os.SEEK_END)
                size_in_bytes = image_file.tell()
                image_file.seek(0)

                if size_in_bytes > MAX_UPLOAD_SIZE_BYTES:
                    return create_error_response(
                        f"📦 El archivo '{image_file.filename}' es demasiado grande. Máximo: {MAX_UPLOAD_SIZE_BYTES//1024//1024}MB", 400)

                validated_images.append(image_file)
            elif image_file.filename != '':
                return create_error_response(
                    f"⚠️ Formato no soportado: '{image_file.filename}'. Usa: {ALLOWED_IMAGE_TYPES}", 400)

        db_cursor = database_connection.cursor(MySQLdb.cursors.DictCursor)

        # Obtener ID de género
        db_cursor.execute("SELECT id_genero FROM genero WHERE nombre=%s", (form_data.get('genero'),))
        genero_row = db_cursor.fetchone()
        genre_id = genero_row['id_genero'] if genero_row else 1

        # Obtener ID de formato
        db_cursor.execute("SELECT id_formato FROM formato WHERE nombre=%s", (form_data.get('formato'),))
        formato_row = db_cursor.fetchone()
        format_id = formato_row['id_formato'] if formato_row else 1

        # Obtener ID de autor (primer autor)
        author_name = form_data.get('autor', '').split(',')[0].strip()
        db_cursor.execute("SELECT id_autor FROM autores WHERE nombre=%s", (author_name,))
        autor_row = db_cursor.fetchone()
        author_id = autor_row['id_autor'] if autor_row else 1
        # Insertar libro en la base de datos
        insert_book_query = """
        INSERT INTO libros (isbn, titulo, anio_publicacion, precio, stock, id_genero, id_formato)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        db_cursor.execute(insert_book_query, (
            form_data.get('isbn'),
            form_data.get('titulo'),
            form_data.get('anio_publicacion'),
            form_data.get('precio'),
            form_data.get('stock'),
            genre_id,
            format_id
        ))
        new_book_id = db_cursor.lastrowid

        # Asociar autor con el libro
        db_cursor.execute(
            "INSERT INTO libro_autor (id_libro, id_autor) VALUES (%s, %s)",
            (new_book_id, author_id)
        )

        # Subir imágenes a Azure y guardar referencias
        uploaded_image_urls = []
        for index, image_file in enumerate(validated_images):
            try:
                public_url, blob_identifier = upload_to_azure_storage(image_file)
                insert_image_query = "INSERT INTO libro_imagenes (id_libro, url, blob_name, orden) VALUES (%s, %s, %s, %s)"
                db_cursor.execute(insert_image_query, (new_book_id, public_url, blob_identifier, index))
                uploaded_image_urls.append(public_url)
            except Exception as upload_exception:
                database_connection.rollback()
                return create_error_response(f"📸 Error al procesar imagen: {upload_exception}", 500)

        db_cursor.close()

        return jsonify({
            "success": True,
            "message": "✅ Libro creado exitosamente en el catálogo",
            "book_id": new_book_id,
            "uploaded_images": uploaded_image_urls,
            "total_images": len(uploaded_image_urls)
        }), 201

    except MySQLdb.Error as database_error:
        database_connection.rollback()
        return create_error_response(f"📊 Error en la base de datos: {database_error}", 500)
    except Exception as general_error:
        database_connection.rollback()
        return create_error_response(f"⚠️ Error inesperado: {general_error}", 500)

# --- Endpoint para actualizar un libro ---
@app.put('/api/books/<int:id_libro>')
@jwt_required
@swag_from({
    'tags': ['📚 Catálogo de Libros'],
    'summary': '✏️ Modificar Libro Existente',
    'description': 'Actualiza la información de un libro. Si se envían nuevas imágenes, las antiguas serán reemplazadas automáticamente.',
    'consumes': ['multipart/form-data'],

    'security': [{'bearerAuth': []}],

    'parameters': [
        {'in': 'path', 'name': 'id_libro', 'type': 'integer', 'required': True, 'description': '🆔 ID del libro a actualizar'},
        {'in': 'formData', 'name': 'isbn', 'type': 'string', 'required': True, 'description': '📖 Nuevo código ISBN'},
        {'in': 'formData', 'name': 'titulo', 'type': 'string', 'required': True, 'description': '📝 Nuevo título'},
        {'in': 'formData', 'name': 'anio_publicacion', 'type': 'integer', 'required': True, 'description': '📅 Nuevo año'},
        {'in': 'formData', 'name': 'precio', 'type': 'number', 'required': True, 'description': '💰 Nuevo precio'},
        {'in': 'formData', 'name': 'stock', 'type': 'integer', 'required': True, 'description': '📦 Nueva cantidad'},
        {'in': 'formData', 'name': 'autor', 'type': 'string', 'description': '✍️ Nuevo autor principal', 'required': True},
        {'in': 'formData', 'name': 'genero', 'type': 'string', 'required': True, 'description': '🎭 Nuevo género'},
        {'in': 'formData', 'name': 'formato', 'type': 'string', 'required': True, 'description': '📄 Nuevo formato'},
        {
            'in': 'formData',
            'name': 'images',
            'type': 'file',
            'description': '🖼️ Nuevas imágenes (reemplazarán completamente las anteriores)'
        }
    ],
    'responses': {
        200: {'description': '✅ Libro actualizado correctamente'},
        404: {'description': '❌ Libro no encontrado en el catálogo'}
    }
})
def update_book(id_libro):
    database_connection = get_database_connection()
    if not database_connection:
        return create_error_response("💔 Error al conectar con la base de datos", 500)

    db_cursor = database_connection.cursor(MySQLdb.cursors.DictCursor)

    # Verificar que el libro existe
    db_cursor.execute("SELECT id_libro FROM libros WHERE id_libro = %s", (id_libro,))
    if not db_cursor.fetchone():
        db_cursor.close()
        return create_error_response(f"📕 No se encontró libro con ID {id_libro}", 404)

    try:
        form_data = request.form
        uploaded_images = request.files.getlist('images')

        blobs_for_deletion = []

        # Si hay nuevas imágenes, reemplazar las antiguas
        if uploaded_images and uploaded_images[0].filename != '':
            if len(uploaded_images) > MAXIMUM_IMAGES_PER_BOOK:
                return create_error_response(
                    f"🖼️ No puedes subir más de {MAXIMUM_IMAGES_PER_BOOK} imágenes", 400)

            validated_images = []
            for image_file in uploaded_images:
                if image_file and validate_image_file(image_file.filename):
                    image_file.seek(0, os.SEEK_END)
                    size_in_bytes = image_file.tell()
                    image_file.seek(0)

                    if size_in_bytes > MAX_UPLOAD_SIZE_BYTES:
                        return create_error_response(
                            f"📦 Archivo '{image_file.filename}' demasiado grande. Máximo {MAX_UPLOAD_SIZE_BYTES//1024//1024}MB", 400)

                    validated_images.append(image_file)
                elif image_file.filename != '':
                    return create_error_response(
                        f"⚠️ Formato inválido: '{image_file.filename}'", 400)

            # Obtener blobs antiguos para eliminarlos después
            db_cursor.execute("SELECT blob_name FROM libro_imagenes WHERE id_libro = %s", (id_libro,))
            blobs_for_deletion = [row['blob_name'] for row in db_cursor.fetchall()]

            # Eliminar registros de imágenes antiguas
            db_cursor.execute("DELETE FROM libro_imagenes WHERE id_libro = %s", (id_libro,))

            # Subir nuevas imágenes
            for index, image_file in enumerate(validated_images):
                public_url, blob_identifier = upload_to_azure_storage(image_file)
                insert_image_query = "INSERT INTO libro_imagenes (id_libro, url, blob_name, orden) VALUES (%s, %s, %s, %s)"
                db_cursor.execute(insert_image_query, (id_libro, public_url, blob_identifier, index))

        # Obtener IDs de género, formato y autor
        db_cursor.execute("SELECT id_genero FROM genero WHERE nombre=%s", (form_data.get('genero'),))
        genero_row = db_cursor.fetchone()
        genre_id = genero_row['id_genero'] if genero_row else 1

        db_cursor.execute("SELECT id_formato FROM formato WHERE nombre=%s", (form_data.get('formato'),))
        formato_row = db_cursor.fetchone()
        format_id = formato_row['id_formato'] if formato_row else 1

        author_name = form_data.get('autor', '').split(',')[0].strip()
        db_cursor.execute("SELECT id_autor FROM autores WHERE nombre=%s", (author_name,))
        autor_row = db_cursor.fetchone()
        author_id = autor_row['id_autor'] if autor_row else 1

        # Actualizar datos del libro
        update_book_query = """
        UPDATE libros SET
            isbn = %s, titulo = %s, anio_publicacion = %s, precio = %s,
            stock = %s, id_genero = %s, id_formato = %s
        WHERE id_libro = %s
        """
        db_cursor.execute(update_book_query, (
            form_data.get('isbn'),
            form_data.get('titulo'),
            form_data.get('anio_publicacion'),
            form_data.get('precio'),
            form_data.get('stock'),
            genre_id,
            format_id,
            id_libro
        ))

        # Actualizar autor
        db_cursor.execute("DELETE FROM libro_autor WHERE id_libro = %s", (id_libro,))
        db_cursor.execute(
            "INSERT INTO libro_autor (id_libro, id_autor) VALUES (%s, %s)",
            (id_libro, author_id)
        )

        db_cursor.close()

        # Eliminar blobs antiguos de Azure
        for blob_name in blobs_for_deletion:
            remove_blob_from_azure(blob_name)

        return jsonify({
            "success": True,
            "message": f"✅ Libro {id_libro} actualizado correctamente",
            "book_id": id_libro
        }), 200

    except Exception as update_error:
        database_connection.rollback()
        print(f"❌ Error en update_book: {update_error}")
        return create_error_response(f"⚠️ Error al actualizar: {update_error}", 500)

# --- Endpoint para eliminar un libro ---
@app.delete('/api/books/<int:id_libro>')
@jwt_required
@swag_from({
    'tags': ['📚 Catálogo de Libros'],
    'summary': '🗑️ Eliminar Libro del Catálogo',
    'description': 'Elimina permanentemente un libro y todas sus imágenes asociadas del sistema',

    'security': [{'bearerAuth': []}],

    'parameters': [
        {'in': 'path', 'name': 'id_libro', 'type': 'integer', 'required': True, 'description': '🆔 ID del libro a eliminar'}
    ],
    'responses': {
        200: {'description': '✅ Libro eliminado exitosamente'},
        404: {'description': '❌ Libro no encontrado'}
    }
})
def delete_book(id_libro):
    database_connection = get_database_connection()
    if not database_connection:
        return create_error_response("💔 Error de conexión con la base de datos", 500)

    db_cursor = database_connection.cursor(MySQLdb.cursors.DictCursor)

    try:
        # Obtener blobs para eliminar de Azure
        db_cursor.execute("SELECT blob_name FROM libro_imagenes WHERE id_libro = %s", (id_libro,))
        blobs_for_deletion = [row['blob_name'] for row in db_cursor.fetchall()]

        # Verificar que el libro existe
        db_cursor.execute("SELECT id_libro FROM libros WHERE id_libro = %s", (id_libro,))
        if not db_cursor.fetchone():
            db_cursor.close()
            return create_error_response(f"📕 No existe libro con ID {id_libro}", 404)

        # Eliminar libro (cascade eliminará relaciones)
        db_cursor.execute("DELETE FROM libros WHERE id_libro = %s", (id_libro,))

        db_cursor.close()

        # Eliminar blobs de Azure
        for blob_name in blobs_for_deletion:
            remove_blob_from_azure(blob_name)

        return jsonify({
            "success": True,
            "message": f"🗑️ Libro {id_libro} eliminado permanentemente del catálogo",
            "deleted_book_id": id_libro,
            "deleted_images": len(blobs_for_deletion)
        }), 200

    except Exception as delete_error:
        database_connection.rollback()
        return create_error_response(f"⚠️ Error al eliminar: {delete_error}", 500)


if __name__ == '__main__':
    if not blob_service_client:
        print("\n" + "="*70)
        print("⚠️  ADVERTENCIA: Azure Blob Storage no disponible")
        print("="*70)
        print("🔧 Asegúrate de configurar las variables de entorno:")
        print("   - AZURE_CLIENT_ID")
        print("   - AZURE_TENANT_ID")
        print("   - AZURE_CLIENT_SECRET")
        print("   - AZURE_STORAGE_ACCOUNT_URL")
        print("="*70 + "\n")
    else:
        print("\n" + "="*70)
        print("✅ API de Biblioteca Digital v2.5.0 iniciada correctamente")
        print("📚 Tema: Pink & Blue Gradient")
        print("🌐 Documentación disponible en: http://localhost:5000/apidocs/")
        print("="*70 + "\n")

    app.run(host='0.0.0.0', port=5000, debug=True)
