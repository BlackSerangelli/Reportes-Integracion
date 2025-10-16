// Objeto 'utils' para encapsular toda la lógica de configuración
const utils = {
  // Elementos del DOM para la configuración
  protocolSelect: document.getElementById("protocolSelect"), //
  hostInput: document.getElementById("hostInput"), //
  portInput: document.getElementById("portInput"), //
  basePathInput: document.getElementById("basePathInput"), //
  statusEl: document.getElementById("connectionStatus"), //

  // Elementos informativos
  epTodos: document.getElementById("endpointTodos"), //
  epIsbn: document.getElementById("endpointIsbn"), //
  epFormat: document.getElementById("endpointFormat"), //
  epAuthor: document.getElementById("endpointAuthor"), //

  // URL base de la API, se actualizará dinámicamente
  BASE_URL: "", //

  /**
   * Actualiza la variable BASE_URL y los campos informativos
   */
  updateBaseUrl: function() { //
    const protocol = this.protocolSelect.value; //
    const host = this.hostInput.value.trim(); //
    const port = this.portInput.value.trim(); //
    const basePath = this.basePathInput.value.trim(); //

    // Construye la URL base para /books
    this.BASE_URL = `${protocol}://${host}:${port}${basePath}/books`; //

    // Actualiza los campos informativos con los placeholders
    this.epTodos.value = `${basePath}/books`; //
    this.epIsbn.value = `${basePath}/books/isbn/{isbn}`; //
    this.epFormat.value = `${basePath}/books/format/{formato}`; //
    this.epAuthor.value = `${basePath}/books/author/{autor}`; //

    console.log("Nueva URL Base:", this.BASE_URL); //
  },

  /**
   * Guarda la configuración actual en localStorage
   */
  saveConfig: function() { //
    localStorage.setItem("bookProtocol", this.protocolSelect.value); //
    localStorage.setItem("bookHost", this.hostInput.value.trim()); //
    localStorage.setItem("bookPort", this.portInput.value.trim()); //
    localStorage.setItem("bookBasePath", this.basePathInput.value.trim()); //

    this.updateBaseUrl(); //
    this.statusEl.textContent = "Configuración guardada."; //
    this.statusEl.style.color = "green"; //
  },

  /**
   * Carga la configuración desde localStorage o usa valores por defecto
   */
  loadConfig: function() { //
    this.protocolSelect.value = localStorage.getItem("bookProtocol") || "http"; //
    this.hostInput.value = localStorage.getItem("bookHost") || "34.133.201.117"; //
    this.portInput.value = localStorage.getItem("bookPort") || "5000"; //
    this.basePathInput.value = localStorage.getItem("bookBasePath") || "/api"; //

    this.updateBaseUrl(); //
  },

  /**
   * Resetea la configuración a los valores por defecto
   */
  resetConfig: function() { //
    localStorage.removeItem("bookProtocol"); //
    localStorage.removeItem("bookHost"); //
    localStorage.removeItem("bookPort"); //
    localStorage.removeItem("bookBasePath"); //

    this.loadConfig(); // Carga los valores por defecto
    this.statusEl.textContent = "Configuración reseteada."; //
    this.statusEl.style.color = "orange"; //
  },

  /**
   * Prueba la conexión con el endpoint principal
   */
  testConnection: async function() { //
    this.updateBaseUrl(); // Asegura que la URL esté actualizada
    this.statusEl.textContent = "Probando..."; //
    this.statusEl.style.color = "blue"; //
    try {
      // Usamos 'no-cors' para una prueba simple de que el host responde
      // NOTA: Esta prueba no funcionará ahora que el endpoint requiere token
      // Se podría adaptar para usar fetchProtected si fuera necesario
      this.statusEl.textContent = "Prueba de conexión deshabilitada (requiere token).";
      this.statusEl.style.color = "orange";
      // const res = await fetch(this.getBaseApiUrl(), { mode: 'no-cors' }); //
      // this.statusEl.textContent = "¡Conexión exitosa! (El servidor respondió)"; //
      // this.statusEl.style.color = "green"; //
    } catch (err) {
      this.statusEl.textContent = `Error: ${err.message}`; //
      this.statusEl.style.color = "red"; //
    }
  },

  /**
   * Devuelve la URL base actual (ej. http://host:port/api/books)
   */
  getBaseApiUrl: function() { //
    return this.BASE_URL; //
  },

  /**
   * Devuelve la URL raíz (ej. http://host:port/api)
   */
  getRootApiUrl: function() { //
    const protocol = this.protocolSelect.value; //
    const host = this.hostInput.value.trim(); //
    const port = this.portInput.value.trim(); //
    const basePath = this.basePathInput.value.trim(); //
    return `${protocol}://${host}:${port}${basePath}`; //
  }
};
