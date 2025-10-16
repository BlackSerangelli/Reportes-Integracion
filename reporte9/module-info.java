module com.cliente.libros {
    requires javafx.controls;
    requires javafx.fxml;
    requires java.net.http; // Para el cliente HTTP
    requires com.google.gson; // Para JSON

    opens com.cliente.libros to javafx.fxml;
    exports com.cliente.libros;
}
