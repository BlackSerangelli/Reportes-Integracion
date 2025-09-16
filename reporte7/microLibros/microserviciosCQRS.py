import xml.etree.ElementTree as ET
from flask import Flask, request, Response, render_template, send_from_directory, jsonify
import MySQLdb
from flask_cors import CORS
import jwt as pyjwt  # Importar PyJWT
from functools import wraps # Importar wraps

# --- Configuración Flask ---
app = Flask(__name__, template_folder='templates', static_folder='static')

CORS(
    app,
    resources={r"/api/*": {"origins": ["*"]}},
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "Authorization"], # <-- AÑADIR "Authorization"
)

# ============================
# Clave secreta JWT
# ¡¡DEBE SER IDÉNTICA A LA DE app_jwt.py!!
# ============================
SECRET_KEY = "mi_super_clave_secreta"

# ==============================================================================
# --- DECORADOR DE VALIDACIÓN DE TOKEN ---
# ==============================================================================

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Buscar el token en el header 'Authorization'
        if 'Authorization' in request.headers:
            token_header = request.headers['Authorization']
            if token_header.startswith('Bearer '):
                token = token_header.split(" ")[1]

        if not token:
            # Usamos create_message_xml para ser consistentes
            return create_message_xml("Token es requerido", 401)

        try:
            # Decodificar el token usando la clave secreta
            data = pyjwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            # Podríamos buscar el current_user en la BD si quisiéramos
            # current_user_id = data['user_id']
        except pyjwt.ExpiredSignatureError:
            return create_message_xml("Token ha expirado", 401)
        except pyjwt.InvalidTokenError:
            return create_message_xml("Token inválido", 401)

        # Si el token es válido, ejecuta la ruta
        return f(*args, **kwargs)
    return decorated

# ==============================================================================
# --- INICIO DE IMPLEMENTACIÓN CQRS ---
# ==============================================================================

# --- Configuración DB (Separada para Queries y Commands) ---
DB_CONFIG_QUERY = {
    'host': 'localhost',
    'user': 'libros_user',
    'passwd': '666',
    'db': 'Libros',
    'charset': 'utf8mb4'
}
DB_CONFIG_COMMAND = {
    'host': 'localhost',
    'user': 'libros_user',
    'passwd': '666',
    'db': 'Libros',
    'charset': 'utf8mb4'
}

# --- Conexiones de Base de Datos ---
def get_db_connection_query():
    """Obtiene una conexión de BD para operaciones de LECTURA (Queries)."""
    try:
        return MySQLdb.connect(**DB_CONFIG_QUERY)
    except MySQLdb.Error as e:
        print(f"Error DB (Query): {e}")
        return None

def get_db_connection_command():
    """Obtiene una conexión de BD para operaciones de ESCRITURA (Commands)."""
    try:
        return MySQLdb.connect(**DB_CONFIG_COMMAND)
    except MySQLdb.Error as e:
        print(f"Error DB (Command): {e}")
        return None

# --- Helpers XML ---
def create_xml_response(books_data):
    catalog = ET.Element('catalog')
    for book_dict in books_data:
        book = ET.SubElement(catalog, 'book', isbn=str(book_dict.get('isbn', '')))
        ET.SubElement(book, 'title').text = book_dict.get('title', '')
        ET.SubElement(book, 'author').text = book_dict.get('authors', '')
        ET.SubElement(book, 'year').text = str(book_dict.get('year', ''))
        ET.SubElement(book, 'genre').text = book_dict.get('genre', '')
        ET.SubElement(book, 'price').text = str(book_dict.get('price', ''))
        ET.SubElement(book, 'stock').text = str(book_dict.get('stock', ''))
        ET.SubElement(book, 'format').text = book_dict.get('format', '')
    return Response(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<?xml-stylesheet type="text/xsl" href="/libros.xsl"?>\n' +
        ET.tostring(catalog, encoding='UTF-8').decode('utf-8'),
        mimetype='application/xml'
    )

def create_message_xml(message, status_code=200):
    root = ET.Element('response')
    ET.SubElement(root, 'message').text = message
    ET.SubElement(root, 'status').text = str(status_code)
    return Response(ET.tostring(root, encoding='UTF-8', xml_declaration=True).decode('utf-8'),
                    mimetype='application/xml', status=status_code)

# --- Endpoint para servir el XSL ---
@app.route('/libros.xsl')
def get_xsl():
    # Asume que libros.xsl está en el mismo directorio que este script
    return send_from_directory('.', 'libros.xsl', mimetype='application/xml')

# ==============================================================================
# --- SECCIÓN DE QUERIES (Lecturas) ---
# ==============================================================================

def handle_get_all_books_query():
    """Lógica de negocio para obtener todos los libros."""
    conn = get_db_connection_query()
    if not conn: return None
    cur = conn.cursor(MySQLdb.cursors.DictCursor)
    query = """
    SELECT b.isbn, b.title, b.year, b.price, b.stock,
           g.name AS genre, f.name AS format,
           GROUP_CONCAT(a.name SEPARATOR ', ') AS authors
    FROM books b
    LEFT JOIN genres g ON b.genre_id = g.genre_id
    LEFT JOIN formats f ON b.format_id = f.format_id
    LEFT JOIN book_authors ba ON b.isbn = ba.isbn
    LEFT JOIN authors a ON ba.author_id = a.author_id
    GROUP BY b.isbn
    ORDER BY b.title;
    """
    cur.execute(query)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def handle_get_book_by_isbn_query(isbn):
    """Lógica de negocio para obtener un libro por ISBN."""
    conn = get_db_connection_query()
    if not conn: return None
    cur = conn.cursor(MySQLdb.cursors.DictCursor)
    query = """
    SELECT b.isbn, b.title, b.year, b.price, b.stock,
           g.name AS genre, f.name AS format,
           GROUP_CONCAT(a.name SEPARATOR ', ') AS authors
    FROM books b
    LEFT JOIN genres g ON b.genre_id = g.genre_id
    LEFT JOIN formats f ON b.format_id = f.format_id
    LEFT JOIN book_authors ba ON b.isbn = ba.isbn
    LEFT JOIN authors a ON ba.author_id = a.author_id
    WHERE b.isbn=%s GROUP BY b.isbn;
    """
    cur.execute(query, (isbn,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return [row] if row else []

def handle_get_books_by_author_query(author):
    """Lógica de negocio para obtener libros por autor."""
    conn = get_db_connection_query()
    if not conn: return None
    cur = conn.cursor(MySQLdb.cursors.DictCursor)
    query = """
    SELECT b.isbn, b.title, b.year, b.price, b.stock,
           g.name AS genre, f.name AS format,
           GROUP_CONCAT(a.name SEPARATOR ', ') AS authors
    FROM books b
    JOIN book_authors ba ON b.isbn = ba.isbn
    JOIN authors a ON ba.author_id = a.author_id
    LEFT JOIN genres g ON b.genre_id = g.genre_id
    LEFT JOIN formats f ON b.format_id = f.format_id
    WHERE a.name=%s GROUP BY b.isbn;
    """
    cur.execute(query, (author,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def handle_get_books_by_format_query(format_name):
    """Lógica de negocio para obtener libros por formato."""
    conn = get_db_connection_query()
    if not conn: return None
    cur = conn.cursor(MySQLdb.cursors.DictCursor)
    query = """
    SELECT b.isbn, b.title, b.year, b.price, b.stock,
           g.name AS genre, f.name AS format,
           GROUP_CONCAT(a.name SEPARATOR ', ') AS authors
    FROM books b
    LEFT JOIN genres g ON b.genre_id = g.genre_id
    LEFT JOIN formats f ON b.format_id = f.format_id
    LEFT JOIN book_authors ba ON b.isbn = ba.isbn
    LEFT JOIN authors a ON ba.author_id = a.author_id
    WHERE f.name=%s GROUP BY b.isbn;
    """
    cur.execute(query, (format_name,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

# --- Endpoints de la API (Queries) ---

@app.route('/api/books', methods=['GET'])
@token_required
def get_books():
    rows = handle_get_all_books_query()
    if rows is None: return create_message_xml("Error DB (Query)", 500)
    return create_xml_response(rows)

@app.route('/api/books/isbn/<isbn>', methods=['GET'])
@token_required
def get_book(isbn):
    rows = handle_get_book_by_isbn_query(isbn)
    if rows is None: return create_message_xml("Error DB (Query)", 500)
    if not rows: return create_message_xml("No encontrado", 404)
    return create_xml_response(rows)

@app.route('/api/books/author/<author>', methods=['GET'])
@token_required
def get_books_by_author(author):
    rows = handle_get_books_by_author_query(author)
    if rows is None: return create_message_xml("Error DB (Query)", 500)
    if not rows: return create_message_xml("No se encontraron libros", 404)
    return create_xml_response(rows)

@app.route('/api/books/format/<format>', methods=['GET'])
@token_required
def get_books_by_format(format):
    rows = handle_get_books_by_format_query(format)
    if rows is None: return create_message_xml("Error DB (Query)", 500)
    if not rows: return create_message_xml("No se encontraron libros", 404)
    return create_xml_response(rows)

# ==============================================================================
# --- SECCIÓN DE COMMANDS (Escrituras) ---
# ==============================================================================

class CommandError(Exception):
    """Excepción personalizada para errores de lógica de negocio en comandos."""
    def __init__(self, message, status_code=400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

def handle_insert_book_command(data):
    """Lógica de negocio para insertar un libro."""
    conn = get_db_connection_command()
    if not conn: raise CommandError("Error DB (Command)", 500)
    cur = conn.cursor()
    try:
        cur.execute("SELECT genre_id FROM genres WHERE name=%s", (data['genre'],))
        g = cur.fetchone()
        if not g: raise CommandError("Género inválido")

        cur.execute("SELECT format_id FROM formats WHERE name=%s", (data['format'],))
        f = cur.fetchone()
        if not f: raise CommandError("Formato inválido")

        cur.execute("INSERT INTO books (isbn,title,year,price,stock,genre_id,format_id) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (data['isbn'], data['title'], data['year'], data['price'], data['stock'], g[0], f[0]))

        for author_name in [a.strip() for a in data['authors'].split(',')]:
            cur.execute("SELECT author_id FROM authors WHERE name=%s", (author_name,))
            a = cur.fetchone()
            if not a: raise CommandError(f"Autor {author_name} inválido")
            cur.execute("INSERT INTO book_authors (isbn,author_id) VALUES (%s,%s)", (data['isbn'], a[0]))

        conn.commit()
    except MySQLdb.Error as e:
        conn.rollback()
        if e.args[0] == 1062:
            raise CommandError(f"Error: Ya existe un libro con el ISBN {data['isbn']}", 409)
        raise CommandError(f"Error MySQL: {e}", 500)
    finally:
        cur.close(); conn.close()

def handle_update_book_command(isbn, data):
    """Lógica de negocio para actualizar un libro."""
    conn = get_db_connection_command()
    if not conn: raise CommandError("Error DB (Command)", 500)
    cur = conn.cursor()
    try:
        fields, vals = [], []
        for k in ['title','year','price','stock']:
            if k in data:
                fields.append(f"{k}=%s")
                vals.append(data[k])

        if not fields: raise CommandError("No hay campos para actualizar", 400)

        sql = f"UPDATE books SET {', '.join(fields)} WHERE isbn=%s"
        vals.append(isbn)
        cur.execute(sql, vals)

        if cur.rowcount == 0:
            raise CommandError(f"No se encontró ningún libro con el ISBN {isbn} para actualizar", 404)

        conn.commit()
    except MySQLdb.Error as e:
        conn.rollback()
        raise CommandError(f"Error MySQL: {e}", 500)
    finally:
        cur.close(); conn.close()

def handle_delete_books_command(isbns):
    """Lógica de negocio para borrar libros."""
    conn = get_db_connection_command()
    if not conn: raise CommandError("Error DB (Command)", 500)
    cur = conn.cursor()
    try:
        format_str = ','.join(['%s']*len(isbns))
        cur.execute(f"DELETE FROM book_authors WHERE isbn IN ({format_str})", tuple(isbns))
        cur.execute(f"DELETE FROM books WHERE isbn IN ({format_str})", tuple(isbns))

        if cur.rowcount == 0:
             raise CommandError("No se encontraron libros con esos ISBNs para borrar", 404)

        conn.commit()
    except MySQLdb.Error as e:
        conn.rollback()
        raise CommandError(f"Error MySQL: {e}", 500)
    finally:
        cur.close(); conn.close()

# --- Endpoints de la API (Commands) ---

@app.route('/api/books/insert', methods=['POST'])
@token_required
def insert_book():
    data = request.get_json()
    if not data: return create_message_xml("Sin JSON", 400)
    required = ['isbn','title','year','price','stock','genre','format','authors']
    if not all(k in data for k in required):
        return create_message_xml("Faltan campos", 400)

    try:
        handle_insert_book_command(data)
        return create_message_xml("Libro insertado", 201)
    except CommandError as e:
        return create_message_xml(e.message, e.status_code)

@app.route('/api/books/update/<isbn>', methods=['PUT'])
@token_required
def update_book(isbn):
    data = request.get_json()
    if not data: return create_message_xml("Sin JSON", 400)

    try:
        handle_update_book_command(isbn, data)
        return create_message_xml("Libro actualizado", 200)
    except CommandError as e:
        return create_message_xml(e.message, e.status_code)

@app.route('/api/books/delete', methods=['DELETE'])
@token_required
def delete_books():
    data = request.get_json()
    if not data or 'isbns' not in data or not data['isbns']:
        return create_message_xml("Formato incorrecto o lista de ISBNs vacía", 400)

    try:
        handle_delete_books_command(data['isbns'])
        return create_message_xml("Libros borrados", 200)
    except CommandError as e:
        return create_message_xml(e.message, e.status_code)

# ==============================================================================
# --- FIN DE IMPLEMENTACIÓN CQRS ---
# ==============================================================================

# --- Página principal ---
@app.route('/')
def home():
    # Asume que index.html está en una carpeta 'templates'
    return render_template('index.html')

# --- Run ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
