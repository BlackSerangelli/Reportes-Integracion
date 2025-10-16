from locust import HttpUser, task, between
import random
import json
import time

class MicroserviceUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Login inicial"""
        self.username = f"user{random.randint(1, 10000)}"
        self.password = "123456"
        self.token = None
        self.refresh_token = None

        # Registrar usuario
        self.client.post("/register", json={
            "username": self.username,
            "email": f"{self.username}@test.com",
            "password": self.password
        })

        # Login inicial
        self.login()

    # -----------------------------
    # Funciones auxiliares
    # -----------------------------
    def login(self):
        """Realiza login y guarda tokens"""
        with self.client.post("/login",
                              json={"username": self.username, "password": self.password},
                              catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")
                response.success()
            else:
                response.failure(f"Login failed: {response.status_code}")
                self.token = None

    def refresh(self):
        """Usa refresh_token desde MariaDB"""
        if not self.refresh_token:
            return self.login()
        with self.client.post("/refresh",
                              json={"refresh_token": self.refresh_token},
                              catch_response=True) as response:
            if response.status_code == 200:
                self.token = response.json().get("access_token")
                response.success()
            else:
                # Si el refresh falla, fuerza login
                self.login()

    def relogin(self):
        """Vuelve a loguear si el access token expiró"""
        print(f"🔄 Token expired for {self.username}, reauthenticating...")
        self.login()

    def auth_headers(self):
        """Encabezados con token si existe"""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    # -----------------------------
    # Tareas
    # -----------------------------
    @task(2)
    def health(self):
        self.client.get("/health")

    @task(3)
    def protected(self):
        """Prueba endpoint protegido, maneja expiración"""
        with self.client.get("/protected", headers=self.auth_headers(), catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                # Token expirado o inválido → relogin
                response.success()  # No marcarlo como fallo técnico
                self.relogin()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)
    def refresh_token(self):
        """Simula refresh periódico"""
        if self.refresh_token:
            with self.client.post("/refresh",
                                  json={"refresh_token": self.refresh_token},
                                  catch_response=True) as response:
                if response.status_code == 200:
                    self.token = response.json().get("access_token")
                    response.success()
                elif response.status_code == 401:
                    # Refresh expirado → login de nuevo
                    response.success()
                    self.relogin()
                else:
                    response.failure(f"Unexpected response: {response.status_code}")

    @task(1)
    def logout(self):
        """Simula logout aleatorio"""
        if random.random() < 0.2 and self.token:  # 20% de los usuarios hacen logout
            with self.client.post("/logout", headers=self.auth_headers(), catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                    self.token = None
                    self.refresh_token = None
                else:
                    response.failure("Logout failed")
