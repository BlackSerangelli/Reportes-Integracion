from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt, decode_token
)
from datetime import datetime, timedelta
import redis
import pymysql
import bcrypt
import traceback

# -----------------------------------------------------
# CONFIGURACIÓN BASE
# -----------------------------------------------------
app = Flask(__name__)
CORS(app)

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

# -----------------------------------------------------
# CONEXIÓN A MARIADB
# -----------------------------------------------------
try:
    mysql_conn = pymysql.connect(
        host="localhost",
        user="libros_user",
        password="666",
        database="Libros",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )
    print("✅ MariaDB conectado correctamente")
except pymysql.Error as e:
    print(f"⚠️ Error al conectar a MariaDB: {e}")
    exit()

# -----------------------------------------------------
# MANEJADORES DE ERRORES JWT PERSONALIZADOS
# -----------------------------------------------------
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({"error": "token_expired", "msg": "El token ha expirado. Por favor, inicia sesión de nuevo."}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({"error": "invalid_token", "msg": "Token inválido. Por favor, inicia sesión de nuevo."}), 422

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({"error": "authorization_required", "msg": "Falta la cabecera de autorización."}), 401

@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    return jsonify({"error": "token_revoked", "msg": "Este token ha sido revocado (sesión cerrada)."}), 401


# -----------------------------------------------------
# ENDPOINT: Health Check
# -----------------------------------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify(status="ok"), 200


# -----------------------------------------------------
# ENDPOINT: Registro de usuario
# -----------------------------------------------------
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not all([username, email, password]):
        return jsonify({"msg": "Se requiere nombre de usuario, email y contraseña"}), 400

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    try:
        with mysql_conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE username=%s OR email=%s", (username, email))
            if cursor.fetchone():
                return jsonify({"msg": "El usuario o email ya existe"}), 409
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                (username, email, hashed)
            )
        return jsonify({"msg": "Usuario registrado exitosamente"}), 201
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Error interno del servidor"}), 500


# -----------------------------------------------------
# ENDPOINT: Login (crea Access + Refresh tokens)
# -----------------------------------------------------
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"msg": "Se requiere nombre de usuario y contraseña"}), 400

    try:
        with mysql_conn.cursor() as cursor:
            cursor.execute("SELECT id, password_hash FROM users WHERE username=%s", (username,))
            user = cursor.fetchone()

        if not user or not bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
            return jsonify({"msg": "Credenciales inválidas"}), 401

        # Usamos el username como 'identity' para que aparezca en la UI
        user_identity = username
        access_token = create_access_token(identity=user_identity)
        refresh_token = create_refresh_token(identity=user_identity)

        if r:
            decoded_token = decode_token(access_token)
            jti_access = decoded_token["jti"]
            r.setex(f"token:{jti_access}", app.config["JWT_ACCESS_TOKEN_EXPIRES"], "active")

        with mysql_conn.cursor() as cursor:
            expires_at = datetime.utcnow() + app.config["JWT_REFRESH_TOKEN_EXPIRES"]
            cursor.execute(
                "INSERT INTO refresh_tokens (user_id, token, expires_at) VALUES (%s, %s, %s)",
                (user['id'], refresh_token, expires_at)
            )

        return jsonify(access_token=access_token, refresh_token=refresh_token), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Error interno del servidor"}), 500


# -----------------------------------------------------
# ENDPOINT: Refresh
# -----------------------------------------------------
@app.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    try:
        user_identity = get_jwt_identity()
        new_access_token = create_access_token(identity=user_identity)

        if r:
            decoded_token = decode_token(new_access_token)
            new_jti = decoded_token["jti"]
            r.setex(f"token:{new_jti}", app.config["JWT_ACCESS_TOKEN_EXPIRES"], "active")

        return jsonify(access_token=new_access_token), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Error interno del servidor"}), 500


# -----------------------------------------------------
# ENDPOINT: Protected (para validar tokens)
# -----------------------------------------------------
@app.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    jti = get_jwt().get("jti")
    if r:
        token_status = r.get(f"token:{jti}")
        if token_status != "active":
            return jsonify({"msg": "El token ha sido revocado o ya no es válido"}), 401

    user_identity = get_jwt_identity()
    return jsonify({"msg": f"Acceso concedido al usuario {user_identity}"}), 200


# -----------------------------------------------------
# ENDPOINT: Logout
# -----------------------------------------------------
@app.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]

    # Obtenemos el ID de usuario desde el token para borrar el refresh token correcto
    # (El 'sub' en un refresh token es el mismo que el 'identity')
    decoded_token = get_jwt()
    username = decoded_token.get('sub') # En refresh, la identidad está en 'sub'
    user_id = None
    try:
        with mysql_conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            if user:
                user_id = user['id']
    except Exception as e:
        print(f"Error buscando usuario para logout: {e}")

    if r:
        r.setex(f"token:{jti}", app.config["JWT_ACCESS_TOKEN_EXPIRES"], "revoked")

    try:
        if user_id:
            with mysql_conn.cursor() as cursor:
                cursor.execute("DELETE FROM refresh_tokens WHERE user_id=%s", (user_id,))
        return jsonify(msg="Sesión cerrada exitosamente, tokens revocados"), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Error interno del servidor al cerrar sesión"}), 500

# -----------------------------------------------------
# ENDPOINT: (MEJORADO) Verificar estado de un token en Redis (Introspect)
# -----------------------------------------------------
@app.route("/token/status", methods=["GET"])
@jwt_required()
def token_status():
    decoded_token = get_jwt()
    jti = decoded_token.get("jti")
    username = get_jwt_identity()

    # Preparamos la respuesta detallada como la de la imagen
    response_data = {
        "decoded": {
            "exp": decoded_token.get("exp"),
            "iat": decoded_token.get("iat"),
            "jti": jti,
            "sub": decoded_token.get("sub"),
            "type": decoded_token.get("type"),
            "username": username
        },
        "exp_utc": datetime.utcfromtimestamp(decoded_token.get('exp')).isoformat() + 'Z',
        "is_revoked": True, # Asumimos revocado por defecto
        "redis_state": "not_found_or_expired",
        "allowlist": False,
        "blacklist": True
    }

    if r:
        token_in_redis = r.get(f"token:{jti}")
        if token_in_redis:
            response_data["redis_state"] = token_in_redis
            if token_in_redis == "active":
                response_data["is_revoked"] = False

    return jsonify(response_data), 200


# -----------------------------------------------------
# EJECUCIÓN DEL SERVIDOR
# -----------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=False, threaded=True)
