import csv
import requests
import time

# URL del endpoint de registro de tu microservicio
REGISTER_URL = 'http://4.246.170.83:5001/auth/register'

def register_users_from_csv(file_path='users.csv'):
    """
    Lee un archivo CSV y registra a los usuarios
    enviando una petición POST al endpoint de registro.
    """
    try:
        with open(file_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Datos del usuario a registrar
                user_data = {
                    "username": row['username'],
                    "email": row['email'],
                    "password": row['password']
                }

                try:
                    # Envía la petición POST
                    response = requests.post(REGISTER_URL, json=user_data)

                    # Imprime el resultado
                    if response.status_code == 201:
                        print(f"✅ Usuario '{user_data['username']}' registrado exitosamente.")
                    else:
                        print(f"❌ Error al registrar a '{user_data['username']}': {response.status_code} - {response.text}")

                except requests.exceptions.ConnectionError as e:
                    print(f"🚨 Error de conexión. Asegúrate de que el microservicio esté corriendo en {REGISTER_URL}.")
                    return

                # Pequeña pausa para no saturar el servicio
                time.sleep(0.1)

    except FileNotFoundError:
        print(f"🚨 Error: El archivo '{file_path}' no fue encontrado.")

if __name__ == "__main__":
    print("Iniciando el registro masivo de usuarios...")
    register_users_from_csv()
    print("Proceso de registro finalizado.")