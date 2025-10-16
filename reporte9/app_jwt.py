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

# -----------------------------------------------------
# CONFIGURACIÓN BASE
# -----------------------------------------------------
app = Flask(__name__)

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
mysql_conn = pymysql.connect(
    host="localhost",
    user="libros_user",
    password="666",
    database="Libros",
    cursorclass=pymysql.cursors.DictCursor,
    autocommit=True
)

# -----------------------------------------------------
# MANEJADORES DE ERRORES JWT
# -----------------------------------------------------
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({"error": "token_expired", "msg": "Your session has expired. Please log in again."}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({"error": "invalid_token", "msg": "Invalid token. Please log in again."}), 422

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({"error": "authorization_required", "msg": "Authorization header missing or malformed."}), 401

@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    return jsonify({"error": "token_revoked", "msg": "This token has been revoked. Please log in again."}), 401


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

    if not username or not email or not password:
        return jsonify({"msg": "Username, email, and password are required"}), 400

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    try:
        with mysql_conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE username=%s OR email=%s", (username, email))
            if cursor.fetchone():
                return jsonify({"msg": "User already exists"}), 400
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                (username, email, hashed)
            )
        return jsonify({"msg": "User registered successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------------
# ENDPOINT: Login (Access + Refresh)
# -----------------------------------------------------
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"msg": "Username and password required"}), 400

    try:
        with mysql_conn.cursor() as cursor:
            cursor.execute("SELECT id, password_hash FROM users WHERE username=%s", (username,))
            user = cursor.fetchone()

        if not user or not bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
            return jsonify({"msg": "Invalid credentials"}), 401

        user_id = user["id"]
        access_token = create_access_token(identity=str(user_id))
        refresh_token = create_refresh_token(identity=str(user_id))

        # Guardar access_token en Redis
        if r:
            decoded_access = decode_token(access_token)
            jti_access = decoded_access["jti"]
            r.setex(f"token:{jti_access}", timedelta(hours=1), "active")

        # Guardar refresh_token en MariaDB
        with mysql_conn.cursor() as cursor:
            expires_at = datetime.utcnow() + timedelta(days=7)
            cursor.execute(
                "INSERT INTO refresh_tokens (user_id, token, expires_at) VALUES (%s, %s, %s)",
                (user_id, refresh_token, expires_at)
            )

        return jsonify(access_token=access_token, refresh_token=refresh_token), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------------
# ENDPOINT: Refresh (usa token de MariaDB)
# -----------------------------------------------------
@app.route("/refresh", methods=["POST"])
def refresh():
    data = request.get_json()
    refresh_token = data.get("refresh_token")

    if not refresh_token:
        return jsonify({"msg": "Refresh token required"}), 400

    try:
        decoded = decode_token(refresh_token)
        user_id = decoded["sub"]

        # Validar que el refresh token esté guardado y no haya expirado
        with mysql_conn.cursor() as cursor:
            cursor.execute("SELECT * FROM refresh_tokens WHERE user_id=%s AND token=%s", (user_id, refresh_token))
            row = cursor.fetchone()

            if not row:
                return jsonify({"msg": "Invalid or revoked refresh token"}), 401
            if row["expires_at"] < datetime.utcnow():
                return jsonify({"msg": "Refresh token expired"}), 401

        # Crear nuevo access token
        new_access = create_access_token(identity=user_id)
        decoded_new = decode_token(new_access)
        jti_new = decoded_new["jti"]
        if r:
            r.setex(f"token:{jti_new}", timedelta(hours=1), "active")

        return jsonify(access_token=new_access), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------------
# ENDPOINT: Protected (requiere access token)
# -----------------------------------------------------
@app.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    user_id = get_jwt_identity()
    jti = get_jwt().get("jti")

    token_status = None
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
    user_id = get_jwt_identity()
    jti = get_jwt()["jti"]

    if r:
        r.set(f"token:{jti}", "revoked")

    try:
        with mysql_conn.cursor() as cursor:
            cursor.execute("DELETE FROM refresh_tokens WHERE user_id=%s", (user_id,))
        return jsonify(msg="Logged out successfully, tokens revoked"), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------------
# EJECUCIÓN DEL SERVIDOR
# -----------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=False, threaded=True)
