package com.cliente.libros;

import com.google.gson.Gson;
import com.google.gson.JsonObject;
import javafx.application.Platform;
import javafx.fxml.FXML;
import javafx.scene.control.*;
import javafx.scene.layout.GridPane;
import javafx.scene.paint.Color;
import javafx.scene.shape.Circle;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;

public class MainController {

    // --- Variables de la UI (conectadas con fx:id del FXML) ---
    @FXML private TextField loginUsernameField;
    @FXML private PasswordField loginPasswordField;
    @FXML private TextField regUsernameField;
    @FXML private TextField regEmailField;
    @FXML private PasswordField regPasswordField;
    @FXML private TextArea tokenArea;
    @FXML private TextArea logArea;
    @FXML private TextArea booksArea;
    @FXML private TextField isbnField;
    @FXML private Circle statusLight;
    @FXML private Label statusLabel;
    @FXML private GridPane insertGrid;
    @FXML private TextField updateIsbnField;
    @FXML private TextField updateNameField;
    @FXML private TextField updateValueField;
    @FXML private TextField deleteIsbnField;
    @FXML private TextField authIpField;
    @FXML private TextField authPortField;
    @FXML private TextField booksIpField;
    @FXML private TextField booksPortField;

    // --- Variables de estado y herramientas ---
    private String accessToken;
    private final HttpClient httpClient = HttpClient.newHttpClient();
    private final Gson gson = new Gson();
    private String authServiceUrl = "http://127.0.0.1:5002";
    private String booksServiceUrl = "http://127.0.0.1:5000";
    private final Map<String, TextField> insertFields = new HashMap<>();

    public void initialize() {
        // Rellena los campos de configuración con los valores por defecto
        authIpField.setText("127.0.0.1");
        authPortField.setText("5002");
        booksIpField.setText("127.0.0.1");
        booksPortField.setText("5000");

        // Genera dinámicamente los campos de texto para insertar libro
        String[] fieldNames = {"isbn", "title", "authors", "year", "price", "stock", "genre", "format"};
        for (int i = 0; i < fieldNames.length; i++) {
            Label label = new Label(fieldNames[i].substring(0, 1).toUpperCase() + fieldNames[i].substring(1) + ":");
            TextField textField = new TextField();
            textField.setPromptText(fieldNames[i]);
            insertGrid.add(label, 0, i);
            insertGrid.add(textField, 1, i);
            insertFields.put(fieldNames[i], textField);
        }
        Button insertButton = new Button("Insertar Libro");
        insertButton.setOnAction(event -> handleInsertBook());
        insertGrid.add(insertButton, 1, fieldNames.length);

        handleHealthCheck();
    }

    // --- Lógica de la Pestaña de Configuración ---
    @FXML
    protected void handleSaveConfig() {
        authServiceUrl = "http://" + authIpField.getText() + ":" + authPortField.getText();
        booksServiceUrl = "http://" + booksIpField.getText() + ":" + booksPortField.getText();
        log("URLs actualizadas.");
        log("Auth Service: " + authServiceUrl);
        log("Books Service: " + booksServiceUrl);
    }

    @FXML
    protected void handleHealthCheck() {
        log("Verificando estado del servicio...");
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(authServiceUrl + "/health"))
                .GET().build();

        sendAsyncRequest(request, (response) -> {
            if (response.statusCode() == 200) {
                 Platform.runLater(() -> {
                    log("✓ Servicio de autenticación activo.");
                    updateStatus(true, "Online");
                });
            } else {
                 Platform.runLater(() -> {
                    log("✗ Servicio de autenticación con errores.");
                    updateStatus(false, "Error");
                });
            }
        });
    }

    // --- Lógica de Autenticación y Libros ---
    @FXML
    protected void handleLogin() {
        String username = loginUsernameField.getText();
        String password = loginPasswordField.getText();
        if (username.isBlank() || password.isBlank()) { log("Usuario y contraseña son requeridos."); return; }

        log("Intentando login para " + username + "...");
        String jsonPayload = gson.toJson(Map.of("username", username, "password", password));

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(authServiceUrl + "/login"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(jsonPayload))
                .build();

        sendAsyncRequest(request, (response) -> {
            if (response.statusCode() == 200) {
                JsonObject body = gson.fromJson(response.body(), JsonObject.class);
                this.accessToken = body.get("access_token").getAsString();
                Platform.runLater(() -> {
                    log("✓ Login exitoso.");
                    tokenArea.setText(this.accessToken);
                    updateStatus(true, "Conectado");
                });
            } else {
                Platform.runLater(() -> {
                    log("✗ Login fallido: " + response.body());
                    updateStatus(false, "Error de Login");
                });
            }
        });
    }

    @FXML
    protected void handleRegister() {
        String username = regUsernameField.getText();
        String email = regEmailField.getText();
        String password = regPasswordField.getText();
        if (username.isBlank() || email.isBlank() || password.isBlank()) { log("Todos los campos son requeridos."); return; }

        log("Intentando registrar a " + username + "...");
        String jsonPayload = gson.toJson(Map.of("username", username, "email", email, "password", password));

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(authServiceUrl + "/register"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(jsonPayload))
                .build();

        sendAsyncRequest(request, (response) -> {
             if (response.statusCode() == 201) {
                 Platform.runLater(() -> log("✓ Usuario registrado exitosamente."));
             } else {
                 Platform.runLater(() -> log("✗ Registro fallido: " + response.body()));
             }
        });
    }

    @FXML
    protected void handleLogout() {
        this.accessToken = null;
        tokenArea.setText("Inicia sesión para obtener un token.");
        log("Sesión cerrada localmente.");
        updateStatus(false, "Desconectado");
    }

    @FXML
    protected void handleGetAllBooks() {
        if (!isLoggedIn()) return;

        log("Obteniendo todos los libros...");
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(booksServiceUrl + "/api/books"))
                .header("Authorization", "Bearer " + this.accessToken)
                .GET().build();

        sendAsyncRequest(request, (response) -> Platform.runLater(() -> {
            log("Respuesta del servidor de libros: " + response.statusCode());
            booksArea.setText(response.body());
        }));
    }

    @FXML
    protected void handleGetBookByIsbn() {
        if (!isLoggedIn()) return;

        String isbn = isbnField.getText();
        if (isbn == null || isbn.isBlank()) { log("Por favor, introduce un ISBN para buscar."); return; }

        log("Buscando libro con ISBN: " + isbn);
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(booksServiceUrl + "/api/books/isbn/" + isbn))
                .header("Authorization", "Bearer " + this.accessToken)
                .GET().build();

        sendAsyncRequest(request, (response) -> Platform.runLater(() -> {
            log("Respuesta del servidor de libros: " + response.statusCode());
            booksArea.setText(response.body());
        }));
    }

    @FXML
    protected void handleInsertBook() {
        if (!isLoggedIn()) return;
        log("Intentando insertar libro...");

        Map<String, String> payload = new HashMap<>();
        for (Map.Entry<String, TextField> entry : insertFields.entrySet()) {
            payload.put(entry.getKey(), entry.getValue().getText());
        }

        String jsonPayload = gson.toJson(payload);
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(booksServiceUrl + "/api/books/insert"))
                .header("Authorization", "Bearer " + this.accessToken)
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(jsonPayload))
                .build();

        sendAsyncRequest(request, (response) -> Platform.runLater(() -> log("Respuesta de inserción: " + response.statusCode() + " - " + response.body())));
    }

    @FXML
    protected void handleUpdateBook() {
        if (!isLoggedIn()) return;

        String isbn = updateIsbnField.getText();
        String field = updateNameField.getText();
        String value = updateValueField.getText();
        if (isbn.isBlank() || field.isBlank() || value.isBlank()) { log("Para actualizar se requiere ISBN, campo y valor."); return; }

        log(String.format("Actualizando libro %s: campo %s a valor %s", isbn, field, value));
        String jsonPayload = gson.toJson(Map.of(field, value));

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(booksServiceUrl + "/api/books/update/" + isbn))
                .header("Authorization", "Bearer " + this.accessToken)
                .header("Content-Type", "application/json")
                .PUT(HttpRequest.BodyPublishers.ofString(jsonPayload))
                .build();

        sendAsyncRequest(request, (response) -> Platform.runLater(() -> log("Respuesta de actualización: " + response.statusCode() + " - " + response.body())));
    }

    @FXML
    protected void handleDeleteBook() {
        if (!isLoggedIn()) return;

        String isbns = deleteIsbnField.getText();
        if (isbns.isBlank()) { log("Introduce al menos un ISBN para borrar."); return; }

        log("Intentando borrar libros: " + isbns);
        String[] isbnArray = isbns.split(",");
        String jsonPayload = gson.toJson(Map.of("isbns", isbnArray));

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(booksServiceUrl + "/api/books/delete"))
                .header("Authorization", "Bearer " + this.accessToken)
                .header("Content-Type", "application/json")
                .method("DELETE", HttpRequest.BodyPublishers.ofString(jsonPayload))
                .build();

        sendAsyncRequest(request, (response) -> Platform.runLater(() -> log("Respuesta de borrado: " + response.statusCode() + " - " + response.body())));
    }

    // --- Métodos de Ayuda ---
    private boolean isLoggedIn() {
        if (accessToken == null || accessToken.isEmpty()) {
            log("Error: Debes iniciar sesión primero.");
            return false;
        }
        return true;
    }

    private void sendAsyncRequest(HttpRequest request, java.util.function.Consumer<HttpResponse<String>> callback) {
        httpClient.sendAsync(request, HttpResponse.BodyHandlers.ofString())
            .thenAccept(callback)
            .exceptionally(e -> {
                Platform.runLater(() -> {
                    log("✗ Error de conexión: " + e.getMessage());
                    updateStatus(false, "Offline");
                });
                return null;
            });
    }

    private void log(String message) {
        String timestamp = new SimpleDateFormat("HH:mm:ss").format(new Date());
        Platform.runLater(() -> logArea.appendText(String.format("[%s] %s\n", timestamp, message)));
    }

    private void updateStatus(boolean isOnline, String text) {
        Platform.runLater(() -> {
            statusLight.setFill(isOnline ? Color.GREEN : Color.RED);
            statusLabel.setText(text);
        });
    }
}
