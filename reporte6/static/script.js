// Espera a que el DOM esté cargado
document.addEventListener("DOMContentLoaded", () => {

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

  // ==== NUEVO: Referencias a Elementos (Operaciones) ====
  // Insertar
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
  // Actualizar
  const updateBtn = document.getElementById("updateBtn");
  const updateIsbnTarget = document.getElementById("updateIsbnTarget");
  const updateTitle = document.getElementById("updateTitle");
  const updatePrice = document.getElementById("updatePrice");
  const updateStock = document.getElementById("updateStock");
  const updateStatus = document.getElementById("updateStatus");
  // Borrar
  const deleteBtn = document.getElementById("deleteBtn");
  const deleteIsbns = document.getElementById("deleteIsbns");
  const deleteStatus = document.getElementById("deleteStatus");
  // =======================================================


  // --- Lógica de Inicialización (Existente) ---

  async function initializeApp() {
    // (Tu función initializeApp existente va aquí...)
    // ...
    utils.loadConfig();
    try {
      // Limpiar selects antes de poblar
      authorSelect.innerHTML = '<option value="">-- Selecciona Autor --</option>';
      formatSelect.innerHTML = '<option value="">-- Selecciona Formato --</option>';

      const url = utils.getBaseApiUrl();
      const res = await fetch(url);
      if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`);
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
      utils.statusEl.textContent = "Error al cargar datos iniciales.";
      utils.statusEl.style.color = "red";
    }
  }

  // --- Lógica de Carga de Resultados (Existente) ---

  async function loadResults(url) {
    // (Tu función loadResults existente va aquí...)
    // ...
    if (!url) return;
    resultsContainer.style.display = "none";
    statusInfo.style.display = "none";
    loadStatus.textContent = "";
    bookCount.textContent = "";
    try {
      const res = await fetch(url);
      const xmlText = await res.text();
      if (!res.ok) {
        statusInfo.style.display = "block";
        loadStatus.textContent = "No se encontró ningún dato para cargar";
        loadStatus.style.color = "red";
        bookCount.textContent = `Error: ${res.status} ${res.statusText}`;
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
        resultsFrame.src = url;
        xmlSource.textContent = formatXml(xmlText);
      }
    } catch (err) {
      console.error("Error fetching XML for source view:", err);
      statusInfo.style.display = "block";
      loadStatus.textContent = "Error al cargar los datos";
      loadStatus.style.color = "red";
      bookCount.textContent = err.message;
    }
  }

  // --- Lógica de Toggle (Existente) ---

  function toggleResultView() {
    // (Tu función toggleResultView existente va aquí...)
    // ...
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

  // --- Lógica de Formato XML (Existente) ---

  function formatXml(xml) {
    // (Tu función formatXml existente va aquí...)
    // ...
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

  // --- Asignación de Eventos (Existente) ---
  saveConfigBtn.addEventListener("click", utils.saveConfig.bind(utils));
  testConfigBtn.addEventListener("click", utils.testConnection.bind(utils));
  resetConfigBtn.addEventListener("click", utils.resetConfig.bind(utils));
  getAllBtn.addEventListener("click", () => {
    loadResults(utils.getBaseApiUrl());
  });
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
  toggleResultsBtn.addEventListener("click", toggleResultView);


  // ==== NUEVO: Lógica de Operaciones (Insertar, Actualizar, Borrar) ====

  /**
   * Muestra un mensaje de estado en un formulario de operación
   * @param {HTMLElement} el - El elemento <p> del estado
   * @param {string} message - El mensaje a mostrar
   * @param {boolean} isError - True si es un error (rojo), false si es éxito (verde)
   */
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

  /**
   * Maneja la inserción de un nuevo libro
   */
  async function handleInsert() {
    // Validar campos requeridos
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
      authors: insertAuthors.value.trim() // El backend espera un string separado por comas
    };

    const url = `${utils.getRootApiUrl()}/books/insert`;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });

      await showOperationStatus(insertStatus, response);

      if (response.ok) {
        // Limpiar campos y refrescar dropdowns
        requiredFields.forEach(f => f.value = "");
        initializeApp(); // Recarga los autores y formatos
      }
    } catch (err) {
      insertStatus.textContent = `Error de red: ${err.message}`;
      insertStatus.style.color = "red";
    }
  }

  /**
   * Maneja la actualización de un libro
   */
  async function handleUpdate() {
    const isbn = updateIsbnTarget.value.trim();
    if (!isbn) {
      updateStatus.textContent = "Error: El ISBN a modificar es obligatorio.";
      updateStatus.style.color = "red";
      return;
    }

    // Construir objeto solo con los campos que se van a actualizar
    const data = {};
    if (updateTitle.value.trim()) data.title = updateTitle.value.trim();
    if (updatePrice.value.trim()) data.price = parseFloat(updatePrice.value.trim());
    if (updateStock.value.trim()) data.stock = parseInt(updateStock.value.trim());

    if (Object.keys(data).length === 0) {
      updateStatus.textContent = "Introduce al menos un campo (título, precio o stock) para actualizar.";
      updateStatus.style.color = "orange";
      return;
    }

    const url = `${utils.getRootApiUrl()}/books/update/${isbn}`;

    try {
      const response = await fetch(url, {
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

  /**
   * Maneja el borrado de libros
   */
  async function handleDelete() {
    const isbns = deleteIsbns.value.trim().split(',')
                      .map(s => s.trim()).filter(s => s); // Limpia y filtra vacíos

    if (isbns.length === 0) {
      deleteStatus.textContent = "Error: Introduce al menos un ISBN.";
      deleteStatus.style.color = "red";
      return;
    }

    const data = { isbns: isbns };
    const url = `${utils.getRootApiUrl()}/books/delete`;

    try {
      const response = await fetch(url, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });

      await showOperationStatus(deleteStatus, response);

      if (response.ok) {
        deleteIsbns.value = ""; // Limpiar textarea
      }

    } catch (err) {
      deleteStatus.textContent = `Error de red: ${err.message}`;
      deleteStatus.style.color = "red";
    }
  }

  // ==== NUEVO: Asignación de Eventos (Operaciones) ====
  insertBtn.addEventListener("click", handleInsert);
  updateBtn.addEventListener("click", handleUpdate);
  deleteBtn.addEventListener("click", handleDelete);

  // --- Iniciar App ---
  initializeApp(); // Carga inicial
});
