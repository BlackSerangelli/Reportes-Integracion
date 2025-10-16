
# Proyecto de Microservicios: Libros con Autenticación JWT y Redis

Este proyecto implementa una arquitectura de microservicios para gestionar un catálogo de libros. Consiste en un servicio de autenticación centralizado que utiliza **JWT** para la seguridad y un servicio de negocio para las operaciones **CRUD** de los libros. La revocación de tokens se maneja a través de una **blacklist en Redis**, y la persistencia de datos se realiza en **MariaDB**.

## 🚀 Arquitectura

El sistema se compone de los siguientes servicios independientes:

  * **Cliente Web (PC):** Una interfaz de usuario (HTML, CSS, JS) que consume los microservicios.
  * **Microservicio de Libros (Puerto 5000):** Una API REST en Flask que maneja toda la lógica de negocio relacionada con los libros (CRUD). Delega la seguridad al servicio de autenticación.
  * **Microservicio de Autenticación (Puerto 5002):** Una API REST en Flask que gestiona el registro, login y ciclo de vida de los tokens JWT (creación, refresco, revocación).
  * **MariaDB:** Base de datos SQL para almacenar información persistente como usuarios, libros y refresh tokens.
  * **Redis:** Base de datos en memoria utilizada como blacklist para la revocación instantánea de access tokens.

<!-- end list -->

```
+-------------+         +----------------------------+         +----------------+
|             |--(A)--> | Microservicio Libros (5000)| --(C)-->|                |
| Cliente Web |         +----------------------------+         |     MariaDB    |
|             |                   |                            |                |
+-------------+                   | (B)                        +----------------+
      |                         |                                      ^
      |                         v                                      | (E)
      |         +-----------------------------+                        |
      +--(D)--> | Microservicio Auth (5002)   | --(F)--> +-----------------+
                +-----------------------------+          | Redis (blacklist)|
                                                         +-----------------+
```

  * **(A)** Peticiones a la API de libros (ej. `GET /api/books`).
  * **(B)** El servicio de libros delega la validación del token al servicio de Auth.
  * **(C)** El servicio de libros consulta o modifica datos en la base de datos principal.
  * **(D)** Peticiones de Login, Registro, Logout y Refresh.
  * **(E)** El servicio de Auth consulta usuarios y guarda refresh tokens en MariaDB.
  * **(F)** El servicio de Auth añade tokens a la blacklist de Redis durante el logout.

-----

## 🛠️ Prerrequisitos

Para desplegar este proyecto en un servidor (ej. una VM en GCP), necesitas tener instalado:

  * Python 3.9+ y Pip
  * Git
  * Servidor de MariaDB (o MySQL)
  * Servidor de Redis

-----

## ⚙️ Instalación y Configuración

Sigue estos pasos en la terminal de tu servidor.

### 1\. Clonar el Repositorio

```bash
git clone <URL_DE_TU_REPOSITORIO>
cd <NOMBRE_DEL_PROYECTO>
```

### 2\. Configurar MariaDB

Asegúrate de que el servicio de MariaDB esté corriendo. Luego, crea la base de datos, el usuario e importa tu esquema.

```sql
-- Inicia sesión como root en MariaDB
sudo mysql -u root -p

-- Ejecuta los siguientes comandos SQL:
CREATE DATABASE Libros;
CREATE USER 'libros_user'@'localhost' IDENTIFIED BY '666';
GRANT ALL PRIVILEGES ON Libros.* TO 'libros_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

Después, importa la estructura y datos de tus tablas (asumiendo que tienes un archivo `schema.sql`):

```bash
mysql -u libros_user -p Libros < schema.sql
```

### 3\. Configurar Redis

Simplemente asegúrate de que el servidor de Redis esté corriendo en su puerto por defecto (6379).

```bash
sudo systemctl status redis-server
# Si no está activo: sudo systemctl start redis-server
```

### 4\. Instalar Dependencias de Python

Es una buena práctica usar entornos virtuales para cada microservicio.

**Para el Microservicio de Autenticación:**

```bash
cd microAuth/
python3 -m venv venv
source venv/bin/activate
pip install Flask Flask-JWT-Extended PyMySQL bcrypt redis Flask-Cors
```

**Para el Microservicio de Libros:**

```bash
cd ../microLibros/  # Sube un nivel y entra a la otra carpeta
python3 -m venv venv
source venv/bin/activate
pip install Flask MySQL-python Flask-Cors requests
```

-----

## ▶️ Despliegue y Ejecución

Debes ejecutar cada microservicio en su propia terminal.

### 1\. Iniciar el Microservicio de Autenticación

Abre una terminal, navega a la carpeta `microAuth` y ejecuta:

```bash
# Activa el entorno virtual si no está activo
source venv/bin/activate

# Exporta la variable de entorno de Flask
export FLASK_APP=app_jwt.py  # O el nombre de tu archivo principal

# Ejecuta el servidor
flask run --host=0.0.0.0 --port=5002
```

> **Nota:** `host=0.0.0.0` es **crucial** para que el servicio sea accesible desde fuera de la máquina virtual.

### 2\. Iniciar el Microservicio de Libros

Abre una **segunda terminal**, navega a la carpeta `microLibros` y ejecuta:

```bash
# Activa el entorno virtual
source venv/bin/activate

# Exporta la variable de entorno de Flask
export FLASK_APP=microservicioCQRS.py

# Ejecuta el servidor
flask run --host=0.0.0.0 --port=5000
```

### 3\. Acceder al Cliente Web

Con ambos servicios corriendo, abre tu navegador y ve a la siguiente dirección:

```
http://<TU_IP_PUBLICA_DE_GCP>:5000
```

La interfaz web que creaste debería cargar y estar lista para usarse.

-----

## 🧪 Pruebas con cURL

Puedes probar la API directamente desde la terminal para verificar su funcionamiento.

```bash
# Define la IP de tu servidor
export SERVER_IP="35.225.153.19"

# 1. Registrar un usuario
curl -X POST http://$SERVER_IP:5002/register \
-H "Content-Type: application/json" \
-d '{"username": "test_curl", "email": "curl@test.com", "password": "123"}'

# 2. Iniciar sesión
curl -X POST http://$SERVER_IP:5002/login \
-H "Content-Type: application/json" \
-d '{"username": "test_curl", "password": "123"}'

# 3. Acceder a un recurso protegido (debería fallar, necesitas el token real)
curl -i -X GET http://$SERVER_IP:5000/api/books \
-H "Authorization: Bearer <PEGA_TU_ACCESS_TOKEN_AQUI>"
```
