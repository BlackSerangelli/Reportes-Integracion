import time
import redis
import pymysql

# ---------------------------
# Configuración de conexiones
# ---------------------------

# Redis
r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# MariaDB/MySQL
mysql_conn = pymysql.connect(
    host="localhost",
    user="libros_user",
    password="666",
    database="Libros",
    cursorclass=pymysql.cursors.DictCursor
)


while True:
    # ---------------------------
    # Entrada de datos del usuario
    # ---------------------------
    username = input("\nIngrese su username (o escriba 'ya' para terminar): ")
    if username.lower() == "ya":
        break

    email = input("Ingrese su email: ")
    password_hash = input("Ingrese su password_hash: ")

    # ---------------------------
    # Inserción en Redis
    # ---------------------------
    print("\n--- Redis ---")
    user_key = f"user:{username}"

    start_time = time.time()
    r.hset(user_key, mapping={
        "username": username,
        "email": email,
        "password_hash": password_hash
    })
    redis_insert_time = time.time() - start_time
    print(f"[Redis CMD] HSET {user_key} username {username} email {email} password_hash {password_hash}")
    print(f"Inserción en Redis completada en {redis_insert_time:.6f} segundos.")

    # Lectura en Redis
    start_time = time.time()
    user_data_redis = r.hgetall(user_key)
    redis_read_time = time.time() - start_time
    print(f"[Redis CMD] HGETALL {user_key}")
    print(f"Lectura en Redis completada en {redis_read_time:.6f} segundos.")
    print("Datos en Redis:", user_data_redis)

    # ---------------------------
    # Inserción en MySQL/MariaDB
    # ---------------------------
    print("\n--- MariaDB ---")
    with mysql_conn.cursor() as cursor:
        start_time = time.time()
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
            (username, email, password_hash)
        )
        mysql_conn.commit()
        mysql_insert_time = time.time() - start_time
        print(f"[MariaDB CMD] INSERT INTO users (username, email, password_hash) VALUES ('{username}', '{email}', '{password_hash}')")
        print(f"Inserción en MariaDB completada en {mysql_insert_time:.6f} segundos.")

        # Lectura en MySQL
        start_time = time.time()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user_data_mysql = cursor.fetchone()
        mysql_read_time = time.time() - start_time
        print(f"[MariaDB CMD] SELECT * FROM users WHERE username = '{username}'")
        print(f"Lectura en MariaDB completada en {mysql_read_time:.6f} segundos.")
        print("Datos en MariaDB:", user_data_mysql)

    # ---------------------------
    # Comparación de tiempos
    # ---------------------------
    print("\n--- Comparación ---")
    insert_ratio = mysql_insert_time / redis_insert_time if redis_insert_time > 0 else float("inf")
    read_ratio = mysql_read_time / redis_read_time if redis_read_time > 0 else float("inf")

    print(f"Inserción: MySQL fue {insert_ratio:.2f} veces más lento que Redis.")
    print(f"Lectura:   MySQL fue {read_ratio:.2f} veces más lento que Redis.")


mysql_conn.close()
print("\nConexiones cerradas.")
