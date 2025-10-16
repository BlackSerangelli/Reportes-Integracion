from flask import Flask, request, jsonify
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt, decode_token
)
from datetime import datetime, timedelta
import redis
import pymysql
import bcrypt
import traceback
from flasgger import Swagger  # <-- 1. Importar Swagger

# -----------------------------------------------------
# CONFIGURACIÓN BASE
# -----------------------------------------------------
app = Flask(__name__)

# --- CONFIGURACIÓN DE SWAGGER ---
app.config['SWAGGER'] = {
    'title': 'API de Autenticación de Libros',
    'uiversion': 3,
    'securityDefinitions': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': "Token de autorización JWT. Formato: Bearer [token]"
        }
    },
    'security': [
        {'Bearer': []}
    ]
}
swagger = Swagger(app)  # <-- 2. Inicializar Swagger

# --- CONFIGURACIÓN DE JWT ---
app.config["JWT_SECRET_KEY"] = "super-secret-key"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=7)
jwt = JWTManager(app)

# -----------------------------------------------------
# CONEXIÓN A REDIS
# -----------------------------------------------------
try:
    r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
    r.ping()
    print("✅ Redis conectado correctamente")
except redis.ConnectionError:
    print("⚠️ Redis no disponible, el servicio seguirá sin cache")
    r = None

# --- FUNCIÓN PARA OBTENER CONEXIONES A LA DB ---
def get_db_connection():
    return pymysql.connect(
        host="localhost", user="libros_user", password="666",
        database="Libros", cursorclass=pymysql.cursors.DictCursor, autocommit=True
    )

# -----------------------------------------------------
# MANEJADORES DE ERRORES JWT
# -----------------------------------------------------
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({"error": "token_expired", "msg": "Your session has expired. Please log in again."}), 401
# ... (los demás manejadores sin cambios)

# -----------------------------------------------------
# ENDPOINT: Health Check
# -----------------------------------------------------
@app.route("/health", methods=["GET"])
def health():
    """
    Verifica el estado de salud del microservicio.
    ---
    tags:
      - Health
    responses:
      200:
        description: El servicio está funcionando correctamente.
    """
    return jsonify(status="ok"), 200

# -----------------------------------------------------
# ENDPOINT: Registro de usuario
# -----------------------------------------------------
@app.route("/register", methods=["POST"])
def register():
    """
    Registra un nuevo usuario en el sistema.
    ---
    tags:
      - Autenticación
    parameters:
      - name: body
        in: body
        required: true
        schema:
          id: RegisterUser
          required: [username, email, password]
          properties:
            username:
              type: string
              description: Nombre de usuario único.
              example: "usuario_prueba"
            email:
              type: string
              description: Correo electrónico único.
              example: "prueba@ejemplo.com"
            password:
              type: string
              description: Contraseña del usuario.
              example: "password123"
    responses:
      201:
        description: Usuario registrado exitosamente.
      400:
        description: Datos incompletos o el usuario ya existe.
    """
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not all([username, email, password]):
        return jsonify({"msg": "Username, email, and password are required"}), 400

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE username=%s OR email=%s", (username, email))
            if cursor.fetchone():
                return jsonify({"msg": "User already exists"}), 400
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                (username, email, hashed)
            )
        return jsonify({"msg": "User registered successfully"}), 201
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# -----------------------------------------------------
# ENDPOINT: Login (Access + Refresh)
# -----------------------------------------------------
@app.route("/login", methods=["POST"])
def login():
    """
    Inicia sesión de un usuario y devuelve tokens.
    ---
    tags:
      - Autenticación
    parameters:
      - name: body
        in: body
        required: true
        schema:
          id: LoginUser
          required: [username, password]
          properties:
            username:
              type: string
              description: El nombre de usuario para iniciar sesión.
              example: "jorge"
            password:
              type: string
              description: La contraseña del usuario.
              example: "123456"
    responses:
      200:
        description: Login exitoso. Devuelve los tokens.
        schema:
          properties:
            access_token: {type: string}
            refresh_token: {type: string}
      401:
        description: Credenciales inválidas.
    """
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"msg": "Username and password required"}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, password_hash FROM users WHERE username=%s", (username,))
            user = cursor.fetchone()

        if not user or not bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
            return jsonify({"msg": "Invalid credentials"}), 401

        user_id = user["id"]
        access_token = create_access_token(identity=str(user_id))
        refresh_token = create_refresh_token(identity=str(user_id))

        if r:
            decoded_access = decode_token(access_token)
            jti_access = decoded_access["jti"]
            r.setex(f"token:{jti_access}", timedelta(hours=1), "active")

        with conn.cursor() as cursor:
            expires_at = datetime.utcnow() + timedelta(days=7)
            cursor.execute(
                "INSERT INTO refresh_tokens (user_id, token, expires_at) VALUES (%s, %s, %s)",
                (user_id, refresh_token, expires_at)
            )

        return jsonify(access_token=access_token, refresh_token=refresh_token), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# -----------------------------------------------------
# ENDPOINT: Refresh (usa token de MariaDB)
# -----------------------------------------------------
@app.route("/refresh", methods=["POST"])
def refresh():
    """
    Refresca un token de acceso usando un token de refresco.
    ---
    tags:
      - Autenticación
    parameters:
      - name: body
        in: body
        required: true
        schema:
          properties:
            refresh_token:
              type: string
              description: El token de refresco obtenido durante el login.
    responses:
      200:
        description: Token de acceso refrescado exitosamente.
      401:
        description: El token de refresco es inválido o ha expirado.
    """
    data = request.get_json()
    refresh_token = data.get("refresh_token")

    if not refresh_token:
        return jsonify({"msg": "Refresh token required"}), 400

    conn = get_db_connection()
    try:
        decoded = decode_token(refresh_token)
        user_id = decoded["sub"]

        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM refresh_tokens WHERE user_id=%s AND token=%s", (user_id, refresh_token))
            row = cursor.fetchone()

            if not row or row["expires_at"] < datetime.utcnow():
                return jsonify({"msg": "Invalid or expired refresh token"}), 401

        new_access = create_access_token(identity=user_id)
        if r:
            jti_new = decode_token(new_access)["jti"]
            r.setex(f"token:{jti_new}", timedelta(hours=1), "active")

        return jsonify(access_token=new_access), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# -----------------------------------------------------
# ENDPOINT: Protected (requiere access token)
# -----------------------------------------------------
@app.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    """
    Endpoint protegido que requiere un token de acceso válido.
    ---
    tags:
      - Rutas Protegidas
    security:
      - Bearer: []
    responses:
      200:
        description: Acceso concedido.
      401:
        description: Token inválido, expirado o revocado.
    """
    user_id = get_jwt_identity()
    jti = get_jwt().get("jti")

    if r:
        token_status = r.get(f"token:{jti}")
        if token_status != "active":
            return jsonify({"msg": "Access token expired or revoked"}), 401

    return jsonify({"msg": f"Access granted to user {user_id}"}), 200

# -----------------------------------------------------
# ENDPOINT: Logout (revoca access y refresh)
# -----------------------------------------------------
@app.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """
    Cierra la sesión del usuario revocando sus tokens.
    ---
    tags:
      - Autenticación
    security:
      - Bearer: []
    responses:
      200:
        description: Sesión cerrada y tokens revocados.
      401:
        description: Token inválido o expirado.
    """
    user_id = get_jwt_identity()
    jti = get_jwt()["jti"]

    if r:
        r.set(f"token:{jti}", "revoked")

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM refresh_tokens WHERE user_id=%s", (user_id,))
        return jsonify(msg="Logged out successfully, tokens revoked"), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# -----------------------------------------------------
# EJECUCIÓN DEL SERVIDOR
# -----------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=False)
