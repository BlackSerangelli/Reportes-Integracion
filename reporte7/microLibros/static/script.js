// Espera a que el DOM esté cargado
document.addEventListener("DOMContentLoaded", () => {

  // ==== Variables de Autenticación ====
  let accessToken = null;
  let refreshToken = null;
  const AUTH_SERVICE_URL = "http://34.133.201.117:5002"; // URL de tu servicio JWT

  // Referencias a paneles
  const loginPanel = document.getElementById("login-panel");
  const mainContainer = document.getElementById("main-container");
  const authStatus = document.getElementById("auth-status");

  // Referencias a form de login
  const loginBtn = document.getElementById("loginBtn");
  const loginEmail = document.getElementById("loginEmail");
  const loginPassword = document.getElementById("loginPassword");
  const loginStatus = document.getElementById("loginStatus");

  // --- Referencias a Elementos (Configuración) ---
  const saveConfigBtn = document.getElementById("saveConfigBtn");
  const testConfigBtn = document.getElementById("testConfigBtn");
  const resetConfigBtn = document.getElementById("resetConfigBtn");

  // --- Referencias a Elementos (Consultas) ---
  const getAllBtn = document.getElementById("getAllBtn");
  const toggleResultsBtn = document.getElementById("toggleResultsBtn");
  const isbnInput = document.getElementById("isbnInput");
  const getByIsbnBtn = document.getElementById("getByIsbnBtn");
  const authorSelect = document.getElementById("authorSelect");
  const getByAuthorBtn = document.getElementById("getByAuthorBtn");
  const formatSelect = document.getElementById("formatSelect");
  const getByFormatBtn = document.getElementById("getByFormatBtn");

  // --- Referencias a Elementos (Resultados) ---
  const resultsContainer = document.getElementById("resultsContainer");
  const resultsFrame = document.getElementById("resultsFrame");
  const xmlSource = document.getElementById("xmlSource");
  const statusInfo = document.getElementById("statusInfo");
  const loadStatus = document.getElementById("loadStatus");
  const bookCount = document.getElementById("bookCount");

  // --- Referencias a Elementos (Operaciones) ---
  const insertBtn = document.getElementById("insertBtn");
  const insertIsbn = document.getElementById("insertIsbn");
  const insertTitle = document.getElementById("insertTitle");
  const insertYear = document.getElementById("insertYear");
  const insertPrice = document.getElementById("insertPrice");
  const insertStock = document.getElementById("insertStock");
  const insertGenre = document.getElementById("insertGenre");
  const insertFormat = document.getElementById("insertFormat");
  const insertAuthors = document.getElementById("insertAuthors");
  const insertStatus = document.getElementById("insertStatus");
  const updateBtn = document.getElementById("updateBtn");
  const updateIsbnTarget = document.getElementById("updateIsbnTarget");
  const updateTitle = document.getElementById("updateTitle");
  const updatePrice = document.getElementById("updatePrice");
  const updateStock = document.getElementById("updateStock");
  const updateStatus = document.getElementById("updateStatus");
  const deleteBtn = document.getElementById("deleteBtn");
  const deleteIsbns = document.getElementById("deleteIsbns");
  const deleteStatus = document.getElementById("deleteStatus");

  // =======================================================
  // ==== Lógica de Autenticación
  // =======================================================

  /**
   * Maneja el clic en el botón de Login
   */
  async function handleLogin() {
    const email = loginEmail.value;
    const password = loginPassword.value;
    if (!email || !password) {
      loginStatus.textContent = "Email y contraseña requeridos.";
      loginStatus.style.color = "red";
      return;
    }
    loginStatus.textContent = "Iniciando sesión...";
    loginStatus.style.color = "blue";

    try {
      const response = await fetch(`${AUTH_SERVICE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email, password: password })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Error al iniciar sesión");
      }

      // ¡Éxito! Guarda los tokens
      accessToken = data.access_token;
      refreshToken = data.refresh_token;
      localStorage.setItem("refreshToken", refreshToken); // Guardamos el refresh token

      // Oculta login, muestra app
      loginPanel.style.display = "none";
      mainContainer.style.display = "flex";
      authStatus.textContent = `Autenticado como: ${email}`;

      // Carga la app
      initializeApp();

    } catch (err) {
      loginStatus.textContent = err.message;
      loginStatus.style.color = "red";
    }
  }

  /**
   * Intenta refrescar el token de acceso si está expirado
   */
  async function getNewAccessToken() {
    // Busca el token en la variable local, o si no, en localStorage
    const tokenToUse = refreshToken || localStorage.getItem("refreshToken");

    if (!tokenToUse) {
      console.log("No hay refresh token para re-autenticar.");
      return false;
    }

    try {
      const response = await fetch(`${AUTH_SERVICE_URL}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: tokenToUse })
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.error);

      accessToken = data.access_token; // Actualiza el token de acceso
      refreshToken = tokenToUse; // Asegura que la variable local esté seteada

      console.log("Token refrescado exitosamente.");
      return true; // Éxito

    } catch (err) {
      console.error("No se pudo refrescar el token:", err.message);
      // Falla el refresh, forzar logout
      accessToken = null;
      refreshToken = null;
      localStorage.removeItem("refreshToken");
      return false; // Fracaso
    }
  }

  // --- Lógica de Inicialización ---
  async function initializeApp() {
    utils.loadConfig();
    try {
      authorSelect.innerHTML = '<option value="">-- Selecciona Autor --</option>';
      formatSelect.innerHTML = '<option value="">-- Selecciona Formato --</option>';

      const url = utils.getBaseApiUrl();
      const res = await fetchProtected(url);

      if (!res.ok) {
        const xmlText = await res.text();
        const parser = new DOMParser();
        const errorDoc = parser.parseFromString(xmlText, "application/xml");
        const message = errorDoc.getElementsByTagName("message")[0]?.textContent || `Error ${res.status}`;
        throw new Error(message);
      }

      const xml = await res.text();

      const parser = new DOMParser();
      const xmlDoc = parser.parseFromString(xml, "application/xml");
      const authors = new Set();
      const formats = new Set();
      for (let book of xmlDoc.getElementsByTagName("book")) {
        const authorNode = book.getElementsByTagName("author")[0];
        const formatNode = book.getElementsByTagName("format")[0];
        if (authorNode && authorNode.textContent) {
          authorNode.textContent.split(',').forEach(a => authors.add(a.trim()));
        }
        if (formatNode && formatNode.textContent) {
          formats.add(formatNode.textContent);
        }
      }
      const sortedAuthors = [...authors].sort();
      const sortedFormats = [...formats].sort();
      sortedAuthors.forEach(a => {
        const opt = document.createElement("option");
        opt.value = a;
        opt.textContent = a;
        authorSelect.appendChild(opt);
      });
      sortedFormats.forEach(f => {
        const opt = document.createElement("option");
        opt.value = f;
        opt.textContent = f;
        formatSelect.appendChild(opt);
      });

    } catch (err) {
      console.error("Error cargando catálogo para selects:", err);
      utils.statusEl.textContent = `Error al cargar datos iniciales: ${err.message}`;
      utils.statusEl.style.color = "red";
    }
  }

  // --- Wrapper de Fetch ---
  async function fetchProtected(url, options = {}) {
    if (!options.headers) {
      options.headers = {};
    }

    if (accessToken) {
      options.headers['Authorization'] = `Bearer ${accessToken}`;
    }

    let response = await fetch(url, options);

    if (response.status === 401) {
      console.log("Token de acceso expirado. Refrescando...");
      const refreshed = await getNewAccessToken();

      if (refreshed) {
        options.headers['Authorization'] = `Bearer ${accessToken}`;
        console.log("Reintentando petición con nuevo token...");
        response = await fetch(url, options);
      }
    }

    return response;
  }

  // --- Lógica de Carga de Resultados (GET) ---
  async function loadResults(url) {
    if (!url) return;

    resultsContainer.style.display = "none";
    statusInfo.style.display = "none";
    loadStatus.textContent = "Cargando...";
    loadStatus.style.color = "blue";
    bookCount.textContent = "";

    try {
      const res = await fetchProtected(url);
      const xmlText = await res.text();

      if (!res.ok) {
        const parser = new DOMParser();
        const errorDoc = parser.parseFromString(xmlText, "application/xml");
        const message = errorDoc.getElementsByTagName("message")[0]?.textContent || `Error ${res.status}`;

        statusInfo.style.display = "block";
        loadStatus.textContent = "Error al cargar datos";
        loadStatus.style.color = "red";
        bookCount.textContent = `Error: ${message}`;
        return;
      }

      const parser = new DOMParser();
      const xmlDoc = parser.parseFromString(xmlText, "application/xml");
      const count = xmlDoc.getElementsByTagName("book").length;

      statusInfo.style.display = "block";

      if (count === 0) {
        loadStatus.textContent = "No se encontró ningún dato para cargar";
        loadStatus.style.color = "orange";
        bookCount.textContent = "Total de libros: 0";
      } else {
        loadStatus.textContent = "Datos cargados y transformados correctamente";
        loadStatus.style.color = "green";
        bookCount.textContent = `Total de libros: ${count}`;

        resultsContainer.style.display = "block";
        resultsFrame.style.display = "block";
        xmlSource.style.display = "none";
        toggleResultsBtn.textContent = "Mostrar XML";

        xmlSource.textContent = formatXml(xmlText);
        resultsFrame.srcdoc = xmlText;
      }

    } catch (err) {
      console.error("Error en loadResults:", err);
      statusInfo.style.display = "block";
      loadStatus.textContent = "Error de red al cargar datos";
      loadStatus.style.color = "red";
      bookCount.textContent = err.message;
    }
  }

  // --- Lógica de Toggle y Formato XML (Sin cambios) ---
  function toggleResultView() {
    if (resultsContainer.style.display !== "block") return;
    if (resultsFrame.style.display === "block") {
      resultsFrame.style.display = "none";
      xmlSource.style.display = "block";
      toggleResultsBtn.textContent = "Ocultar XML (Ver Tabla)";
    } else {
      resultsFrame.style.display = "block";
      xmlSource.style.display = "none";
      toggleResultsBtn.textContent = "Mostrar XML";
    }
  }

  function formatXml(xml) {
      let formatted = '';
      let reg = /(>)(<)(\/*)/g;
      xml = xml.replace(reg, '$1\r\n$2$3');
      let pad = 0;
      xml.split('\r\n').forEach(node => {
          let indent = 0;
          if (node.match( /.+<\/\w[^>]*>$/ )) {
              indent = 0;
          } else if (node.match( /^<\/\w/ )) {
              if (pad != 0) pad -= 1;
          } else if (node.match( /^<\w[^>]*[^\/]>.*$/ )) {
              indent = 1;
          } else {
              indent = 0;
          }
          formatted += '  '.repeat(pad) + node + '\r\n';
          pad += indent;
      });
      return formatted.trim();
  }

  // --- Asignación de Eventos (Configuración) ---
  saveConfigBtn.addEventListener("click", utils.saveConfig.bind(utils));
  testConfigBtn.addEventListener("click", utils.testConnection.bind(utils));
  resetConfigBtn.addEventListener("click", utils.resetConfig.bind(utils));

  // --- Asignación de Eventos (Consultas) ---
  getAllBtn.addEventListener("click", () => loadResults(utils.getBaseApiUrl()));
  getByIsbnBtn.addEventListener("click", () => {
    const isbn = isbnInput.value.trim();
    if (!isbn) return alert("Introduce un ISBN");
    loadResults(`${utils.getBaseApiUrl()}/isbn/${isbn}`);
  });
  getByAuthorBtn.addEventListener("click", () => {
    const author = authorSelect.value.trim();
    if (!author) return alert("Selecciona un autor");
    loadResults(`${utils.getBaseApiUrl()}/author/${author}`);
  });
  getByFormatBtn.addEventListener("click", () => {
    const format = formatSelect.value.trim();
    if (!format) return alert("Selecciona un formato");
    loadResults(`${utils.getBaseApiUrl()}/format/${format}`);
  });

  // --- Asignación de Eventos (Resultados) ---
  toggleResultsBtn.addEventListener("click", toggleResultView);

  // --- Asignación de Eventos (Login) ---
  loginBtn.addEventListener("click", handleLogin);

  // --- Lógica de Operaciones (C.R.U.D.) ---

  async function showOperationStatus(el, response) {
    try {
      const xmlText = await response.text();
      const parser = new DOMParser();
      const xmlDoc = parser.parseFromString(xmlText, "application/xml");
      const message = xmlDoc.getElementsByTagName("message")[0]?.textContent || "Respuesta desconocida";

      if (!response.ok) {
        el.textContent = `Error: ${message} (Código: ${response.status})`;
        el.style.color = "red";
      } else {
        el.textContent = `Éxito: ${message}`;
        el.style.color = "green";
      }
    } catch (e) {
      el.textContent = `Error al procesar respuesta: ${e.message}`;
      el.style.color = "red";
    }
  }

  async function handleInsert() {
    const requiredFields = [insertIsbn, insertTitle, insertYear, insertPrice, insertStock, insertGenre, insertFormat, insertAuthors];
    if (requiredFields.some(f => !f.value.trim())) {
      insertStatus.textContent = "Error: Todos los campos son obligatorios.";
      insertStatus.style.color = "red";
      return;
    }
    const data = {
      isbn: insertIsbn.value.trim(),
      title: insertTitle.value.trim(),
      year: parseInt(insertYear.value.trim()),
      price: parseFloat(insertPrice.value.trim()),
      stock: parseInt(insertStock.value.trim()),
      genre: insertGenre.value.trim(),
      format: insertFormat.value.trim(),
      authors: insertAuthors.value.trim()
    };
    const url = `${utils.getRootApiUrl()}/books/insert`;
    try {
      const response = await fetchProtected(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      await showOperationStatus(insertStatus, response);
      if (response.ok) {
        requiredFields.forEach(f => f.value = "");
        initializeApp();
      }
    } catch (err) {
      insertStatus.textContent = `Error de red: ${err.message}`;
      insertStatus.style.color = "red";
    }
  }

  async function handleUpdate() {
    const isbn = updateIsbnTarget.value.trim();
    if (!isbn) {
      updateStatus.textContent = "Error: El ISBN a modificar es obligatorio.";
      updateStatus.style.color = "red";
      return;
    }
    const data = {};
    if (updateTitle.value.trim()) data.title = updateTitle.value.trim();
    if (updatePrice.value.trim()) data.price = parseFloat(updatePrice.value.trim());
    if (updateStock.value.trim()) data.stock = parseInt(updateStock.value.trim());
    if (Object.keys(data).length === 0) {
      updateStatus.textContent = "Introduce al menos un campo para actualizar.";
      updateStatus.style.color = "orange";
      return;
    }
    const url = `${utils.getRootApiUrl()}/books/update/${isbn}`;
    try {
      const response = await fetchProtected(url, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      await showOperationStatus(updateStatus, response);
    } catch (err) {
      updateStatus.textContent = `Error de red: ${err.message}`;
      updateStatus.style.color = "red";
    }
  }

  async function handleDelete() {
    const isbns = deleteIsbns.value.trim().split(',')
                      .map(s => s.trim()).filter(s => s);
    if (isbns.length === 0) {
      deleteStatus.textContent = "Error: Introduce al menos un ISBN.";
      deleteStatus.style.color = "red";
      return;
    }
    const data = { isbns: isbns };
    const url = `${utils.getRootApiUrl()}/books/delete`;
    try {
      const response = await fetchProtected(url, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      await showOperationStatus(deleteStatus, response);
      if (response.ok) {
        deleteIsbns.value = "";
      }
    } catch (err) {
      deleteStatus.textContent = `Error de red: ${err.message}`;
      deleteStatus.style.color = "red";
    }
  }

  // --- Asignación de Eventos (Operaciones) ---
  insertBtn.addEventListener("click", handleInsert);
  updateBtn.addEventListener("click", handleUpdate);
  deleteBtn.addEventListener("click", handleDelete);


  // =======================================================
  // ==== NUEVO: Lógica de Inicio de App
  // =======================================================

  /**
   * Verifica el estado de login al cargar la página.
   * Intenta usar el refresh token si existe.
   */
  async function checkLoginState() {
    // 1. Busca el token en localStorage
    const storedRefreshToken = localStorage.getItem("refreshToken");

    if (storedRefreshToken) {
      console.log("Refresh token encontrado. Intentando re-autenticar...");
      // 2. Muestra un estado de carga mientras validamos
      loginPanel.style.display = "none";
      authStatus.textContent = "Verificando sesión...";

      // 3. Intenta obtener un nuevo token de acceso
      const refreshed = await getNewAccessToken();

      if (refreshed) {
        // 4. ¡Éxito! El usuario sigue logueado.
        console.log("Re-autenticación exitosa.");
        mainContainer.style.display = "flex";
        // No tenemos el email, pero podemos poner un mensaje genérico
        authStatus.textContent = `Autenticado (sesión recuperada)`;
        initializeApp(); // Carga la app (dropdowns, etc.)
      } else {
        // 5. El refresh token falló (expiró o es inválido)
        console.log("El refresh token falló. Se requiere login.");
        loginPanel.style.display = "block";
        mainContainer.style.display = "none";
        authStatus.textContent = "";
        loginStatus.textContent = "Tu sesión expiró. Por favor, inicia sesión de nuevo.";
        loginStatus.style.color = "red";
      }
    } else {
      // 6. No hay refresh token, es un usuario nuevo o deslogueado.
      console.log("No se encontró refresh token. Se requiere login.");
      loginPanel.style.display = "block";
      mainContainer.style.display = "none";
    }
  }

  // --- Iniciar App ---
  checkLoginState(); // ¡Llamamos a la nueva función al cargar la página!

});
