from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
from flask_cors import CORS
import bcrypt, datetime
import jwt as pyjwt   # aseguramos usar PyJWT (no el paquete jwt malo)

app = Flask(__name__)
CORS(
    app,
    origins="*", # Permite peticiones de cualquier origen
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "Authorization"] # Permite los headers
    )

# ============================
# Configuración de la DB
# ============================
app.config['MYSQL_HOST'] = "localhost"
app.config['MYSQL_USER'] = "libros_user"
app.config['MYSQL_PASSWORD'] = "666"
app.config['MYSQL_DB'] = "Libros"
app.config['MYSQL_CURSORCLASS'] = "DictCursor"

mysql = MySQL(app)

# ============================
# Clave secreta JWT
# ============================
SECRET_KEY = "mi_super_clave_secreta"

# ============================
# Helper: Crear Access y Refresh Tokens
# ============================
def generate_tokens(user_id):
    access_token = pyjwt.encode(
        {"user_id": user_id,
         "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=5)},
        SECRET_KEY, algorithm="HS256"
    )
    refresh_token = pyjwt.encode(
        {"user_id": user_id,
         "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)},
        SECRET_KEY, algorithm="HS256"
    )
    print(f"[DEBUG] Access Token generado: {access_token}")
    print(f"[DEBUG] Refresh Token generado: {refresh_token}")

    # Guardar refresh token en BD
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO refresh_tokens (user_id, token, expires_at) VALUES (%s,%s,%s)",
                (user_id, refresh_token,
                 datetime.datetime.utcnow() + datetime.timedelta(days=7)))
    mysql.connection.commit()
    cur.close()

    return access_token, refresh_token

# ============================
# Endpoint Health
# ============================
@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok", "message": "Microservicio JWT corriendo"}, 200

# ============================
# Registro de usuarios
# ============================
@app.route("/auth/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        username = data["username"]
        email = data["email"]
        password = data["password"]

        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username,email,password_hash) VALUES (%s,%s,%s)",
                    (username, email, hashed))
        mysql.connection.commit()
        cur.close()

        print(f"[DEBUG] Usuario registrado: {username}, {email}")
        return jsonify({"msg": "Usuario registrado"}), 201
    except Exception as e:
        print(f"[ERROR] Fallo en register: {e}")
        return jsonify({"error": str(e)}), 500

# ============================
# Login de usuarios
# ============================
@app.route("/auth/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        email = data["email"]
        password = data["password"]

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", [email])
        user = cur.fetchone()
        cur.close()

        if not user or not bcrypt.checkpw(password.encode("utf-8"),
                                          user["password_hash"].encode("utf-8")):
            return jsonify({"error": "Credenciales inválidas"}), 401

        print(f"[DEBUG] Login exitoso de {user['username']} ({email})")

        access, refresh = generate_tokens(user["id"])
        return jsonify({"access_token": access, "refresh_token": refresh})
    except Exception as e:
        print(f"[ERROR] Fallo en login: {e}")
        return jsonify({"error": str(e)}), 500

# ============================
# Refresh Token
# ============================
@app.route("/auth/refresh", methods=["POST"])
def refresh():
    data = request.get_json()
    token = data.get("refresh_token")

    try:
        payload = pyjwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        print(f"[DEBUG] Refresh token válido: {payload}")
        new_access, _ = generate_tokens(payload["user_id"])
        return jsonify({"access_token": new_access})
    except pyjwt.ExpiredSignatureError:
        return jsonify({"error": "Refresh token expirado"}), 401
    except pyjwt.InvalidTokenError:
        return jsonify({"error": "Token inválido"}), 401

# ============================
# Endpoint protegido /api/profile
# ============================
@app.route("/api/profile", methods=["GET"])
def profile():
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"error": "Token requerido"}), 401

    try:
        payload = pyjwt.decode(token.split(" ")[1], SECRET_KEY, algorithms=["HS256"])
        print(f"[DEBUG] Perfil solicitado por user_id={payload['user_id']}")
        cur = mysql.connection.cursor()
        cur.execute("SELECT id,username,email FROM users WHERE id=%s", [payload["user_id"]])
        user = cur.fetchone()
        cur.close()
        return jsonify(user)
    except pyjwt.ExpiredSignatureError:
        return jsonify({"error": "Access token expirado"}), 401
    except pyjwt.InvalidTokenError:
        return jsonify({"error": "Token inválido"}), 401

# ============================
# Endpoint protegido /api/items
# ============================
@app.route("/api/items", methods=["GET","POST"])
def items():
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"error": "Token requerido"}), 401

    try:
        payload = pyjwt.decode(token.split(" ")[1], SECRET_KEY, algorithms=["HS256"])
        user_id = payload["user_id"]
        print(f"[DEBUG] Items consultados/creados por user_id={user_id}")

        cur = mysql.connection.cursor()

        if request.method == "POST":
            name = request.json["name"]
            cur.execute("INSERT INTO items (user_id,name) VALUES (%s,%s)", (user_id, name))
            mysql.connection.commit()
            cur.close()
            return jsonify({"msg": "Item creado"}), 201

        cur.execute("SELECT * FROM items WHERE user_id=%s", [user_id])
        items = cur.fetchall()
        cur.close()
        return jsonify(items)
    except pyjwt.ExpiredSignatureError:
        return jsonify({"error": "Access token expirado"}), 401
    except pyjwt.InvalidTokenError:
        return jsonify({"error": "Token inválido"}), 401

# ============================
# Run en puerto 5002
# ============================
if __name__ == "__main__":
    app.run(debug=True, port=5002)
