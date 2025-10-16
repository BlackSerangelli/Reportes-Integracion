import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
import json
import threading
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom
import queue # El sistema de "buzón"

# ==============================================================================
#  CLASE PRINCIPAL DE LA APLICACIÓN TKINTER
# ==============================================================================
class LibrosAppClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Cliente para Microservicios de Libros y Autenticación")
        self.root.geometry("1200x850")

        # --- Variables de estado ---
        self.base_url_auth = "http://127.0.0.1:5002"
        self.base_url_books = "http://127.0.0.1:5000"
        self.access_token = None
        self.refresh_token = None

        # --- El "buzón" para la comunicación entre hilos ---
        self.result_queue = queue.Queue()

        self.create_gui()
        self.process_queue() # Inicia el procesador del buzón
        self.check_service_health()

    # Método que revisa el buzón y actualiza la UI
    def process_queue(self):
        try:
            message = self.result_queue.get_nowait()
            identifier, data = message

            if identifier == "log":
                self._log_message_ui(data)
            elif identifier == "traffic_light":
                status, text = data
                self._update_traffic_light_ui(status, text)
            elif identifier == "login_success":
                self.access_token, self.refresh_token = data
                self._log_message_ui("✓ Login exitoso.")
                self.update_token_display()
                self._update_traffic_light_ui('green', 'Conectado')
                messagebox.showinfo("Éxito", "Login correcto.")
            elif identifier == "login_fail":
                self._log_message_ui(f"✗ Login fallido: {data}")
                self._update_traffic_light_ui('red', 'Error de Login')
                messagebox.showerror("Error de Login", data)
            elif identifier == "register_success":
                self._log_message_ui(f"✓ Usuario registrado correctamente.")
                messagebox.showinfo("Éxito", "Usuario registrado.")
            elif identifier == "register_fail":
                self._log_message_ui(f"✗ Registro fallido: {data}")
                messagebox.showerror("Error de Registro", data)
            elif identifier == "book_results":
                self.update_results_display(data)
            elif identifier == "book_op_success":
                self._log_message_ui(f"✓ Operación de libro exitosa: {data}")
                messagebox.showinfo("Éxito", data)
            elif identifier == "request_error":
                self._log_message_ui(f"✗ Error de red/petición: {data}")
                messagebox.showerror("Error de Petición", data)

        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_queue)

    # --- Creación de la GUI ---
    def create_gui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 10))
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side='right', fill='y')
        self.notebook = ttk.Notebook(left_panel)
        self.notebook.pack(fill='both', expand=True)
        self.create_auth_tab()
        self.create_books_tab()
        self.create_config_tab()
        self.create_log_area(right_panel)
        self.create_traffic_light(right_panel)

    def create_auth_tab(self):
        auth_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(auth_frame, text="🔑 Autenticación")
        login_frame = ttk.LabelFrame(auth_frame, text="Iniciar Sesión", padding=10)
        login_frame.pack(fill='x', pady=5)
        ttk.Label(login_frame, text="Usuario:").grid(row=0, column=0, sticky='w', pady=2)
        self.login_username_entry = ttk.Entry(login_frame, width=40)
        self.login_username_entry.grid(row=0, column=1, padx=5, pady=2)
        ttk.Label(login_frame, text="Contraseña:").grid(row=1, column=0, sticky='w', pady=2)
        self.login_password_entry = ttk.Entry(login_frame, width=40, show="*")
        self.login_password_entry.grid(row=1, column=1, padx=5, pady=2)
        ttk.Button(login_frame, text="Login", command=self.login, style='Accent.TButton').grid(row=2, column=0, columnspan=2, pady=10)
        reg_frame = ttk.LabelFrame(auth_frame, text="Registrar Nuevo Usuario", padding=10)
        reg_frame.pack(fill='x', pady=5)
        ttk.Label(reg_frame, text="Username:").grid(row=0, column=0, sticky='w', pady=2)
        self.reg_username_entry = ttk.Entry(reg_frame, width=40)
        self.reg_username_entry.grid(row=0, column=1, padx=5, pady=2)
        ttk.Label(reg_frame, text="Email:").grid(row=1, column=0, sticky='w', pady=2)
        self.reg_email_entry = ttk.Entry(reg_frame, width=40)
        self.reg_email_entry.grid(row=1, column=1, padx=5, pady=2)
        ttk.Label(reg_frame, text="Contraseña:").grid(row=2, column=0, sticky='w', pady=2)
        self.reg_password_entry = ttk.Entry(reg_frame, width=40, show="*")
        self.reg_password_entry.grid(row=2, column=1, padx=5, pady=2)
        ttk.Button(reg_frame, text="Registrar", command=self.register_user).grid(row=3, column=0, columnspan=2, pady=10)
        token_frame = ttk.LabelFrame(auth_frame, text="Token de Acceso (JWT)", padding=10)
        token_frame.pack(fill='both', expand=True, pady=5)
        self.token_display = scrolledtext.ScrolledText(token_frame, height=5, wrap='word')
        self.token_display.pack(fill='both', expand=True)
        self.token_display.insert('1.0', "Inicia sesión para obtener un token.")
        self.token_display.config(state='disabled')
        ttk.Button(token_frame, text="Logout", command=self.logout).pack(pady=5)

    def create_books_tab(self):
        books_main_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(books_main_frame, text="📚 Gestión de Libros")

        cqrs_notebook = ttk.Notebook(books_main_frame)
        cqrs_notebook.pack(fill='both', expand=True)

        # --- Pestaña de Consultas (Queries) ---
        query_frame = ttk.Frame(cqrs_notebook, padding=10)
        cqrs_notebook.add(query_frame, text="🔍 Consultas (Queries)")

        query_controls_frame = ttk.Frame(query_frame)
        query_controls_frame.pack(fill='x', pady=(0, 10))

        ttk.Button(query_controls_frame, text="Obtener Todos", command=self.get_all_books, style='Accent.TButton').pack(side='left', padx=5)
        self.isbn_entry = ttk.Entry(query_controls_frame, width=20)
        self.isbn_entry.pack(side='left', padx=5)
        self.isbn_entry.insert(0, "ISBN...")
        ttk.Button(query_controls_frame, text="Buscar por ISBN", command=self.get_book_by_isbn).pack(side='left', padx=5)

        self.results_text = scrolledtext.ScrolledText(query_frame, height=20, wrap='none')
        self.results_text.pack(fill='both', expand=True)
        self.results_text.insert('1.0', "Aquí se mostrarán los resultados de las consultas en formato XML...")
        self.results_text.config(state='disabled')

        # --- Pestaña de Comandos (Commands) ---
        command_frame = ttk.Frame(cqrs_notebook, padding=10)
        cqrs_notebook.add(command_frame, text="✏️ Comandos (C/U/D)")

        # --- Insertar Libro ---
        insert_frame = ttk.LabelFrame(command_frame, text="Añadir Nuevo Libro", padding=10)
        insert_frame.pack(fill='x', pady=5)

        fields = ["isbn", "title", "authors", "year", "price", "stock", "genre", "format"]
        self.insert_entries = {}
        for i, field in enumerate(fields):
            ttk.Label(insert_frame, text=f"{field.title()}:").grid(row=i, column=0, sticky='w', padx=5, pady=2)
            entry = ttk.Entry(insert_frame, width=50)
            entry.grid(row=i, column=1, sticky='ew', padx=5, pady=2)
            self.insert_entries[field] = entry
        ttk.Button(insert_frame, text="Insertar Libro", command=self.insert_book, style='Accent.TButton').grid(row=len(fields), column=0, columnspan=2, pady=10)

        # --- Actualizar Libro ---
        update_frame = ttk.LabelFrame(command_frame, text="Actualizar Libro", padding=10)
        update_frame.pack(fill='x', pady=5)

        ttk.Label(update_frame, text="ISBN del libro a actualizar:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.update_isbn_entry = ttk.Entry(update_frame, width=40)
        self.update_isbn_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=2)

        ttk.Label(update_frame, text="Campo a cambiar (ej: price, stock):").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.update_field_entry = ttk.Entry(update_frame, width=40)
        self.update_field_entry.grid(row=1, column=1, sticky='ew', padx=5, pady=2)

        ttk.Label(update_frame, text="Nuevo valor:").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.update_value_entry = ttk.Entry(update_frame, width=40)
        self.update_value_entry.grid(row=2, column=1, sticky='ew', padx=5, pady=2)

        ttk.Button(update_frame, text="Actualizar", command=self.update_book).grid(row=3, column=0, columnspan=2, pady=10)

        # --- Borrar Libro ---
        delete_frame = ttk.LabelFrame(command_frame, text="Borrar Libro(s)", padding=10)
        delete_frame.pack(fill='x', pady=5)
        ttk.Label(delete_frame, text="ISBN(s) a borrar (separados por coma):").pack(side='left', padx=5)
        self.delete_isbn_entry = ttk.Entry(delete_frame, width=40)
        self.delete_isbn_entry.pack(side='left', fill='x', expand=True, padx=5)
        ttk.Button(delete_frame, text="Borrar", command=self.delete_book).pack(side='left', padx=5)

    def create_config_tab(self):
        config_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(config_frame, text="⚙️ Configuración")
        auth_settings = ttk.LabelFrame(config_frame, text="Microservicio de Autenticación (JWT)", padding=10)
        auth_settings.pack(fill='x', pady=5)
        ttk.Label(auth_settings, text="IP:").grid(row=0, column=0, sticky='w')
        self.ip_auth_var = tk.StringVar(value="127.0.0.1")
        ttk.Entry(auth_settings, textvariable=self.ip_auth_var).grid(row=0, column=1, padx=5)
        ttk.Label(auth_settings, text="Puerto:").grid(row=0, column=2, sticky='w', padx=5)
        self.port_auth_var = tk.StringVar(value="5002")
        ttk.Entry(auth_settings, textvariable=self.port_auth_var).grid(row=0, column=3, padx=5)
        books_settings = ttk.LabelFrame(config_frame, text="Microservicio de Libros (CQRS)", padding=10)
        books_settings.pack(fill='x', pady=5)
        ttk.Label(books_settings, text="IP:").grid(row=0, column=0, sticky='w')
        self.ip_books_var = tk.StringVar(value="127.0.0.1")
        ttk.Entry(books_settings, textvariable=self.ip_books_var).grid(row=0, column=1, padx=5)
        ttk.Label(books_settings, text="Puerto:").grid(row=0, column=2, sticky='w', padx=5)
        self.port_books_var = tk.StringVar(value="5000")
        ttk.Entry(books_settings, textvariable=self.port_books_var).grid(row=0, column=3, padx=5)
        ttk.Button(config_frame, text="Probar Conexión", command=self.check_service_health, style='Accent.TButton').pack(pady=10)

    def create_log_area(self, parent):
        log_frame = ttk.LabelFrame(parent, text="Log de Actividad", padding=10)
        log_frame.pack(fill='both', expand=True, pady=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, width=50, wrap='word')
        self.log_text.pack(fill='both', expand=True)
        self.log_text.config(state='disabled')

    def create_traffic_light(self, parent):
        light_frame = ttk.LabelFrame(parent, text="Estado Auth Service", padding=10)
        light_frame.pack(fill='x', pady=5)
        self.light_canvas = tk.Canvas(light_frame, width=50, height=30, highlightthickness=0)
        self.light_canvas.pack()
        self.traffic_light = self.light_canvas.create_oval(10, 5, 40, 25, fill='red', outline='black')
        self.light_label = ttk.Label(light_frame, text="Desconectado")
        self.light_label.pack()

    # --- Funciones que actualizan la UI (solo se llaman desde el hilo principal) ---
    def _log_message_ui(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.config(state='normal')
        self.log_text.insert('end', log_entry)
        self.log_text.see('end')
        self.log_text.config(state='disabled')

    def _update_traffic_light_ui(self, status, text):
        self.light_canvas.itemconfig(self.traffic_light, fill=status)
        self.light_label.config(text=text)

    def _update_base_urls(self):
        self.base_url_auth = f"http://{self.ip_auth_var.get()}:{self.port_auth_var.get()}"
        self.base_url_books = f"http://{self.ip_books_var.get()}:{self.port_books_var.get()}"

    def _pretty_xml(self, xml_string):
        try:
            dom = minidom.parseString(xml_string)
            return dom.toprettyxml(indent="  ")
        except Exception:
            return xml_string

    # --- Métodos que INICIAN hilos ---
    def check_service_health(self):
        self._update_base_urls()
        threading.Thread(target=self._health_check_thread, args=(self.result_queue,), daemon=True).start()

    def login(self):
        username = self.login_username_entry.get()
        password = self.login_password_entry.get()
        if not username or not password:
            messagebox.showerror("Error", "Usuario y contraseña son requeridos.")
            return
        threading.Thread(target=self._login_thread, args=(username, password, self.result_queue), daemon=True).start()

    def register_user(self):
        username = self.reg_username_entry.get()
        email = self.reg_email_entry.get()
        password = self.reg_password_entry.get()
        if not all([username, email, password]):
            messagebox.showerror("Error", "Todos los campos son requeridos.")
            return
        threading.Thread(target=self._register_thread, args=(username, email, password, self.result_queue), daemon=True).start()

    def logout(self):
        self.access_token = None
        self.refresh_token = None
        self._log_message_ui("Sesión cerrada localmente.")
        self.update_token_display()
        self._update_traffic_light_ui('red', 'Desconectado')
        messagebox.showinfo("Logout", "Has cerrado sesión.")

    def update_token_display(self):
        self.token_display.config(state='normal')
        self.token_display.delete('1.0', 'end')
        if self.access_token:
            self.token_display.insert('1.0', self.access_token)
        else:
            self.token_display.insert('1.0', "Inicia sesión para obtener un token.")
        self.token_display.config(state='disabled')

    def _make_book_request(self, method, endpoint, json_payload=None):
        if not self.access_token:
            messagebox.showerror("No autenticado", "Debes iniciar sesión.")
            return
        threading.Thread(target=self._book_request_thread, args=(method, endpoint, json_payload, self.result_queue), daemon=True).start()

    def get_all_books(self):
        self._make_book_request('GET', '/api/books')

    def get_book_by_isbn(self):
        isbn = self.isbn_entry.get()
        if not isbn or isbn == "ISBN...":
            messagebox.showwarning("Entrada requerida", "Por favor, introduce un ISBN.")
            return
        self._make_book_request('GET', f'/api/books/isbn/{isbn}')

    def insert_book(self):
        try:
            payload = {field: entry.get() for field, entry in self.insert_entries.items()}
            payload['year'] = int(payload['year'])
            payload['price'] = float(payload['price'])
            payload['stock'] = int(payload['stock'])
            self._make_book_request('POST', '/api/books/insert', json_payload=payload)
        except ValueError as e: messagebox.showerror("Error de formato", f"Campo numérico inválido: {e}")
        except Exception as e: messagebox.showerror("Error", f"Error preparando los datos: {e}")

    def update_book(self):
        isbn = self.update_isbn_entry.get()
        field = self.update_field_entry.get()
        value = self.update_value_entry.get()
        if not all([isbn, field, value]):
            messagebox.showwarning("Entrada requerida", "Se requieren el ISBN, el campo a cambiar y el nuevo valor.")
            return
        payload = {field: value}
        self._make_book_request('PUT', f'/api/books/update/{isbn}', json_payload=payload)

    def delete_book(self):
        isbns_str = self.delete_isbn_entry.get()
        if not isbns_str:
            messagebox.showwarning("Entrada requerida", "Introduce al menos un ISBN para borrar.")
            return
        isbns_list = [isbn.strip() for isbn in isbns_str.split(',')]
        payload = {"isbns": isbns_list}
        self._make_book_request('DELETE', '/api/books/delete', json_payload=payload)

    def update_results_display(self, content):
        self.results_text.config(state='normal')
        self.results_text.delete('1.0', 'end')
        self.results_text.insert('1.0', content)
        self.results_text.config(state='disabled')

    # --- FUNCIONES DE HILO (WORKER THREADS) ---
    def _health_check_thread(self, q):
        q.put(("log", "Verificando estado del microservicio de autenticación..."))
        q.put(("traffic_light", ('orange', 'Probando...')))
        try:
            response = requests.get(f"{self.base_url_auth}/health", timeout=3)
            if response.status_code == 200:
                q.put(("traffic_light", ('green', 'Online')))
                q.put(("log", "✓ Microservicio Auth está activo."))
            else:
                q.put(("traffic_light", ('red', 'Error')))
                q.put(("log", f"✗ Auth respondió con error: {response.status_code}"))
        except Exception as e:
            q.put(("traffic_light", ('red', 'Offline')))
            q.put(("log", f"✗ No se puede conectar a Auth: {e}"))

    def _login_thread(self, username, password, q):
        q.put(("log", f"Intentando login para {username}..."))
        try:
            payload = {"username": username, "password": password}
            response = requests.post(f"{self.base_url_auth}/login", json=payload)
            if response.status_code == 200:
                data = response.json()
                access = data.get('access_token')
                refresh = data.get('refresh_token')
                q.put(("login_success", (access, refresh)))
            else:
                error = response.json().get('msg', 'Error desconocido')
                q.put(("login_fail", error))
        except Exception as e:
            q.put(("request_error", str(e)))

    def _register_thread(self, username, email, password, q):
        q.put(("log", f"Intentando registrar a {username}..."))
        payload = {"username": username, "email": email, "password": password}
        try:
            response = requests.post(f"{self.base_url_auth}/register", json=payload)
            if response.status_code == 201:
                q.put(("register_success", None))
            else:
                error = response.json().get('msg', 'Error desconocido')
                q.put(("register_fail", error))
        except Exception as e:
            q.put(("request_error", str(e)))

    def _book_request_thread(self, method, endpoint, json_payload, q):
        q.put(("log", f"Petición: {method.upper()} {self.base_url_books}{endpoint}"))
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            response = requests.request(method, f"{self.base_url_books}{endpoint}", headers=headers, json=json_payload, timeout=10)
            q.put(("log", f"Respuesta: {response.status_code}"))

            if response.ok:
                content_type = response.headers.get('Content-Type', '')
                if 'application/xml' in content_type:
                    try:
                        root = ET.fromstring(response.content)
                        msg = root.find('message').text
                        q.put(("book_op_success", msg))
                    except (ET.ParseError, AttributeError):
                        pretty_xml = self._pretty_xml(response.text)
                        q.put(("book_results", pretty_xml))
            else:
                q.put(("request_error", f"Error {response.status_code}: {response.text}"))
        except Exception as e:
            q.put(("request_error", str(e)))


# ==============================================================================
#  FUNCIÓN PRINCIPAL PARA EJECUTAR LA APP
# ==============================================================================
def main():
    root = tk.Tk()
    style = ttk.Style()
    try:
        style.theme_use('clam')
        style.configure('Accent.TButton', foreground='white', background='#0078D7')
    except tk.TclError:
        print("Tema 'clam' no disponible, usando el predeterminado.")

    app = LibrosAppClient(root)
    root.mainloop()

if __name__ == "__main__":
    main()
