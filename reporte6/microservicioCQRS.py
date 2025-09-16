import xml.etree.ElementTree as ET
from flask import Flask, request, Response, render_template, send_from_directory
import MySQLdb
from flask_cors import CORS

# --- Configuración Flask ---
app = Flask(__name__)

CORS(
    app,
    resources={r"/api/*": {"origins": ["*"]}},
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)

# --- Configuración DB ---
DB_CONFIG = {
    'host': 'localhost',
    'user': 'libros_user',
    'passwd': '666',
    'db': 'Libros',
    'charset': 'utf8mb4'
}

def get_db_connection():
    try:
        return MySQLdb.connect(**DB_CONFIG)
    except MySQLdb.Error as e:
        print(f"Error DB: {e}")
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
    return send_from_directory('.', 'libros.xsl', mimetype='application/xml')

# --- Endpoints API ---
@app.route('/api/books', methods=['GET'])
def get_books():
    conn = get_db_connection()
    if not conn: return create_message_xml("Error DB", 500)
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
    return create_xml_response(rows)

@app.route('/api/books/isbn/<isbn>', methods=['GET'])
def get_book(isbn):
    conn = get_db_connection()
    if not conn: return create_message_xml("Error DB", 500)
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
    return create_xml_response([row]) if row else create_message_xml("No encontrado", 404)

@app.route('/api/books/author/<author>', methods=['GET'])
def get_books_by_author(author):
    conn = get_db_connection()
    if not conn: return create_message_xml("Error DB", 500)
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
    return create_xml_response(rows) if rows else create_message_xml("No se encontraron libros", 404)

@app.route('/api/books/format/<format>', methods=['GET'])
def get_books_by_format(format):
    conn = get_db_connection()
    if not conn: return create_message_xml("Error DB", 500)
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
    cur.execute(query, (format,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return create_xml_response(rows) if rows else create_message_xml("No se encontraron libros", 404)

@app.route('/api/books/insert', methods=['POST'])
def insert_book():
    data = request.get_json()
    if not data: return create_message_xml("Sin JSON", 400)
    required = ['isbn','title','year','price','stock','genre','format','authors']
    if not all(k in data for k in required):
        return create_message_xml("Faltan campos", 400)

    conn = get_db_connection()
    if not conn: return create_message_xml("Error DB", 500)
    cur = conn.cursor()
    try:
        # genre
        cur.execute("SELECT genre_id FROM genres WHERE name=%s", (data['genre'],))
        g = cur.fetchone()
        if not g: return create_message_xml("Género inválido", 400)
        # format
        cur.execute("SELECT format_id FROM formats WHERE name=%s", (data['format'],))
        f = cur.fetchone()
        if not f: return create_message_xml("Formato inválido", 400)

        cur.execute("INSERT INTO books (isbn,title,year,price,stock,genre_id,format_id) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (data['isbn'], data['title'], data['year'], data['price'], data['stock'], g[0], f[0]))

        for author_name in [a.strip() for a in data['authors'].split(',')]:
            cur.execute("SELECT author_id FROM authors WHERE name=%s", (author_name,))
            a = cur.fetchone()
            if not a: return create_message_xml(f"Autor {author_name} inválido", 400)
            cur.execute("INSERT INTO book_authors (isbn,author_id) VALUES (%s,%s)", (data['isbn'], a[0]))

        conn.commit()
        return create_message_xml("Libro insertado", 201)
    except MySQLdb.Error as e:
        conn.rollback()
        return create_message_xml(f"Error: {e}", 500)
    finally:
        cur.close(); conn.close()

@app.route('/api/books/update/<isbn>', methods=['PUT'])
def update_book(isbn):
    data = request.get_json()
    if not data: return create_message_xml("Sin JSON", 400)
    conn = get_db_connection()
    if not conn: return create_message_xml("Error DB", 500)
    cur = conn.cursor()
    try:
        fields, vals = [], []
        for k in ['title','year','price','stock']:
            if k in data:
                fields.append(f"{k}=%s")
                vals.append(data[k])
        if fields:
            sql = f"UPDATE books SET {', '.join(fields)} WHERE isbn=%s"
            vals.append(isbn)
            cur.execute(sql, vals)
            conn.commit()
        return create_message_xml("Libro actualizado", 200)
    except MySQLdb.Error as e:
        conn.rollback()
        return create_message_xml(f"Error: {e}", 500)
    finally:
        cur.close(); conn.close()

@app.route('/api/books/delete', methods=['DELETE'])
def delete_books():
    data = request.get_json()
    if not data or 'isbns' not in data: return create_message_xml("Formato incorrecto", 400)
    isbns = data['isbns']
    conn = get_db_connection()
    if not conn: return create_message_xml("Error DB", 500)
    cur = conn.cursor()
    try:
        format_str = ','.join(['%s']*len(isbns))
        cur.execute(f"DELETE FROM book_authors WHERE isbn IN ({format_str})", tuple(isbns))
        cur.execute(f"DELETE FROM books WHERE isbn IN ({format_str})", tuple(isbns))
        conn.commit()
        return create_message_xml("Libros borrados", 200)
    except MySQLdb.Error as e:
        conn.rollback()
        return create_message_xml(f"Error: {e}", 500)
    finally:
        cur.close(); conn.close()

# --- Página principal ---
@app.route('/')
def home():
    return render_template('index.html')

# --- Run ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
