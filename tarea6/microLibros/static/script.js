// ====== CONFIG BÁSICA ======
const DEFAULT_AUTH_HOST = "35.225.153.19";
const DEFAULT_AUTH_PORT = "5002";
const AUTH_SERVICE_URL = `http://${DEFAULT_AUTH_HOST}:${DEFAULT_AUTH_PORT}`;

// ====== ESTADO ======
let accessToken = null;
let refreshToken = null;
let accessExpTs = null; // epoch seconds
let sessionInterval = null;

// ====== ELEMENTOS ======
const authSummary = document.getElementById("authSummary");
const logoutBtn = document.getElementById("logoutBtn");

// Login / Registro
const loginUsername = document.getElementById("loginUsername");
const loginPassword = document.getElementById("loginPassword");
const loginBtn = document.getElementById("loginBtn");
const showRegister = document.getElementById("showRegister");
const hideRegister = document.getElementById("hideRegister");
const registerBox = document.getElementById("registerBox");
const registerUsername = document.getElementById("registerUsername");
const registerEmail = document.getElementById("registerEmail");
const registerPassword = document.getElementById("registerPassword");
const registerBtn = document.getElementById("registerBtn");
const loginStatus = document.getElementById("loginStatus");
const registerStatus = document.getElementById("registerStatus");
const authBaseLabel = document.getElementById("authBaseLabel");

// Config Libros
const hostInput = document.getElementById("hostInput");
const portInput = document.getElementById("portInput");
const basePathInput = document.getElementById("basePathInput");
const saveConfigBtn = document.getElementById("saveConfigBtn");
const resetConfigBtn = document.getElementById("resetConfigBtn");
const connectionStatus = document.getElementById("connectionStatus");
const booksBaseLabel = document.getElementById("booksBaseLabel");

// Libros: GET
const getAllBtn = document.getElementById("getAllBtn");
const isbnInput = document.getElementById("isbnInput");
const getByIsbnBtn = document.getElementById("getByIsbnBtn");
const authorInput = document.getElementById("authorInput");
const getByAuthorBtn = document.getElementById("getByAuthorBtn");
const formatInput = document.getElementById("formatInput");
const getByFormatBtn = document.getElementById("getByFormatBtn");

// Resultados
const statusInfo = document.getElementById("statusInfo");
const loadStatus = document.getElementById("loadStatus");
const bookCount = document.getElementById("bookCount");
const resultsContainer = document.getElementById("resultsContainer");
const resultsFrame = document.getElementById("resultsFrame");
const xmlSource = document.getElementById("xmlSource");
const toggleResultsBtn = document.getElementById("toggleResultsBtn");

// CRUD
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

// Comparación JWT
const compareBtn = document.getElementById("compareBtn");
const compareSummary = document.getElementById("compareSummary");
const localJwtResult = document.getElementById("local-jwt-result");
const redisJwtResult = document.getElementById("redis-jwt-result");

// Log de Cliente
const clientLog = document.getElementById("clientLog");

// ====== LOG DE CLIENTE ======
function logToClient(message, data) {
    const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 23);
    let logMessage = `[${timestamp}] ${message}`;
    if (data) {
        logMessage += `\n${typeof data === 'string' ? data : JSON.stringify(data, null, 2)}`;
    }
    clientLog.value = logMessage + '\n\n' + clientLog.value;
}

// ====== UTILS (libros) ======
function buildBooksBase() {
  const host = (localStorage.getItem("bookHost") || hostInput.value || "35.225.153.19").trim();
  const port = (localStorage.getItem("bookPort") || portInput.value || "5000").trim();
  const base = (localStorage.getItem("bookBasePath") || basePathInput.value || "/api").trim();
  return `http://${host}:${port}${base}`;
}

function booksUrl(path) {
  const base = buildBooksBase();
  return `${base}${path}`;
}

function syncBooksConfigToUi() {
  hostInput.value = localStorage.getItem("bookHost") || "35.225.153.19";
  portInput.value = localStorage.getItem("bookPort") || "5000";
  basePathInput.value = localStorage.getItem("bookBasePath") || "/api";
  booksBaseLabel.textContent = buildBooksBase();
}

function saveBooksConfig() {
  localStorage.setItem("bookHost", hostInput.value.trim());
  localStorage.setItem("bookPort", portInput.value.trim());
  localStorage.setItem("bookBasePath", basePathInput.value.trim());
  booksBaseLabel.textContent = buildBooksBase();
  connectionStatus.textContent = "Configuración guardada.";
  connectionStatus.className = "status ok";
}

function resetBooksConfig() {
  localStorage.removeItem("bookHost");
  localStorage.removeItem("bookPort");
  localStorage.removeItem("bookBasePath");
  syncBooksConfigToUi();
  connectionStatus.textContent = "Configuración reseteada.";
  connectionStatus.className = "status warn";
}

// ====== AUTH ======
function updateAuthSummary() {
    if (sessionInterval) clearInterval(sessionInterval);
    if (accessToken && accessExpTs) {
        sessionInterval = setInterval(() => {
            const now = Math.floor(Date.now() / 1000);
            const left = Math.max(0, accessExpTs - now);
            const payload = decodeJwt(accessToken);
            authSummary.textContent = `Autenticado como ${payload?.identity || "?"} · Access expira en ${left}s`;
        }, 1000);
        logoutBtn.style.display = "inline-flex";
    } else {
        authSummary.textContent = "No autenticado";
        logoutBtn.style.display = "none";
    }
    authBaseLabel.textContent = AUTH_SERVICE_URL;
}

function decodeJwt(token) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(atob(base64).split('').map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)).join(''));
    return JSON.parse(jsonPayload);
  } catch {
    return null;
  }
}

async function login() {
  loginStatus.textContent = "Iniciando sesión...";
  loginStatus.className = "status info";
  try {
    const res = await fetch(`${AUTH_SERVICE_URL}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: loginUsername.value.trim(), password: loginPassword.value.trim() })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.msg || data.error || "Login falló");

    accessToken = data.access_token;
    refreshToken = data.refresh_token;
    localStorage.setItem("refreshToken", refreshToken);

    const payload = decodeJwt(accessToken);
    accessExpTs = payload?.exp || null;

    loginStatus.textContent = "Sesión iniciada";
    loginStatus.className = "status ok";

    logToClient('Login ok', { user: { username: payload.identity, sub: payload.sub }, access_exp: new Date(payload.exp * 1000).toLocaleString() });
    updateAuthSummary();
  } catch (e) {
    loginStatus.textContent = e.message;
    loginStatus.className = "status err";
    logToClient(`Login FAIL: ${e.message}`);
  }
}

async function register() {
  registerStatus.textContent = "Registrando...";
  registerStatus.className = "status info";
  try {
    const res = await fetch(`${AUTH_SERVICE_URL}/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: registerUsername.value.trim(),
        email: registerEmail.value.trim(),
        password: registerPassword.value.trim()
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.msg || data.error || "Registro falló");
    registerStatus.textContent = "¡Registro exitoso! Ahora inicia sesión.";
    registerStatus.className = "status ok";
    logToClient('Register ok', { username: registerUsername.value.trim() });
  } catch (e) {
    registerStatus.textContent = e.message;
    registerStatus.className = "status err";
    logToClient(`Register FAIL: ${e.message}`);
  }
}

async function refreshAccess() {
  const tokenToUse = refreshToken || localStorage.getItem("refreshToken");
  if (!tokenToUse) return false;
  try {
    const res = await fetch(`${AUTH_SERVICE_URL}/refresh`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${tokenToUse}` }
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.msg || data.error || "Refresh falló");
    accessToken = data.access_token;
    const payload = decodeJwt(accessToken);
    accessExpTs = payload?.exp || null;
    updateAuthSummary();
    logToClient('Token refrescado exitosamente');
    return true;
  } catch (e) {
    accessToken = null;
    accessExpTs = null;
    localStorage.removeItem("refreshToken");
    updateAuthSummary();
    logToClient(`Refresh FAIL: ${e.message}`);
    return false;
  }
}

async function logout() {
  logToClient('Cerrando sesión...');
  try {
    await fetchProtected(`${AUTH_SERVICE_URL}/logout`, { method: "POST" });
  } catch {}
  accessToken = null;
  accessExpTs = null;
  refreshToken = null;
  localStorage.removeItem("refreshToken");
  updateAuthSummary();
  logToClient('Sesión cerrada localmente.');
}

async function fetchProtected(url, options = {}) {
  options.headers = options.headers || {};
  if (accessToken) options.headers["Authorization"] = `Bearer ${accessToken}`;

  let res = await fetch(url, options);
  if (res.status === 401) {
    logToClient('Token de acceso inválido/expirado (401). Intentando refrescar...');
    const ok = await refreshAccess();
    if (ok) {
      logToClient('Refresh exitoso. Reintentando petición original...');
      options.headers["Authorization"] = `Bearer ${accessToken}`;
      res = await fetch(url, options);
    }
  }
  return res;
}

// ====== LIBROS ======
function setLoading(msg = "Cargando...") {
  statusInfo.classList.remove("hide");
  loadStatus.textContent = msg;
  loadStatus.className = "status info";
  bookCount.textContent = "";
}

function setError(msg) {
  statusInfo.classList.remove("hide");
  loadStatus.textContent = "Error";
  loadStatus.className = "status err";
  bookCount.textContent = msg;
}

function setOk(msg) {
  statusInfo.classList.remove("hide");
  loadStatus.textContent = msg;
  loadStatus.className = "status ok";
}

function formatXml(xml) {
  let formatted = '', pad = 0;
  xml.replace(/(>)(<)(\/*)/g, '$1\r\n$2$3').split('\r\n').forEach(node => {
    let indent = 0;
    if (/.+<\/\w[^>]*>$/.test(node)) indent = 0;
    else if (/^<\/\w/.test(node)) { if (pad) pad -= 1; }
    else if (/^<\w[^>]*[^\/]>.*$/.test(node)) indent = 1;
    formatted += '  '.repeat(pad) + node + '\n';
    pad += indent;
  });
  return formatted.trim();
}

async function loadResults(url) {
  setLoading();
  resultsContainer.classList.add("hide");
  xmlSource.classList.add("hide");
  resultsFrame.classList.remove("hide");
  toggleResultsBtn.textContent = "Mostrar XML";
  logToClient(`Requesting GET ${url}`);

  try {
    const res = await fetchProtected(url);
    const text = await res.text();
    logToClient(`Response GET ${url} status ${res.status}`);

    if (!res.ok) {
      try {
        const errDoc = new DOMParser().parseFromString(text, "application/xml");
        const message = errDoc.querySelector("message")?.textContent || `Error ${res.status}`;
        setError(message);
      } catch {
        setError(`Error ${res.status}`);
      }
      return;
    }

    const doc = new DOMParser().parseFromString(text, "application/xml");
    const count = doc.getElementsByTagName("book").length;
    setOk("Datos cargados y transformados.");
    bookCount.textContent = `Total de libros: ${count}`;

    resultsContainer.classList.remove("hide");
    resultsFrame.srcdoc = text;
    xmlSource.textContent = formatXml(text);
  } catch (e) {
    setError(e.message);
    logToClient(`Request FAIL: ${e.message}`);
  }
}

// ====== CRUD ======
async function showOperationStatus(el, response, text) {
  try {
    let message = `HTTP ${response.status}`;
    try {
      const xml = new DOMParser().parseFromString(text, "application/xml");
      message = xml.querySelector("message")?.textContent || message;
    } catch {}
    el.textContent = message;
    el.className = "status " + (response.ok ? "ok" : "err");
  } catch (e) {
    el.textContent = e.message;
    el.className = "status err";
  }
}

async function handleInsert() {
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
  if (!data.isbn || !data.title || !data.year || isNaN(data.price) || isNaN(data.stock) || !data.genre || !data.format || !data.authors) {
    insertStatus.textContent = "Todos los campos son obligatorios.";
    insertStatus.className = "status err";
    return;
  }
  const url = booksUrl("/books/insert");
  logToClient(`Requesting POST ${url}`, data);
  const res = await fetchProtected(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });
  const text = await res.text();
  logToClient(`Response POST ${url} status ${res.status}`, text);
  await showOperationStatus(insertStatus, res, text);
  if (res.ok) {
    [insertIsbn, insertTitle, insertYear, insertPrice, insertStock, insertGenre, insertFormat, insertAuthors].forEach(i => i.value = "");
  }
}

async function handleUpdate() {
  const isbn = updateIsbnTarget.value.trim();
  if (!isbn) {
    updateStatus.textContent = "El ISBN objetivo es obligatorio.";
    updateStatus.className = "status err";
    return;
  }
  const data = {};
  if (updateTitle.value.trim()) data.title = updateTitle.value.trim();
  if (updatePrice.value.trim()) data.price = parseFloat(updatePrice.value.trim());
  if (updateStock.value.trim()) data.stock = parseInt(updateStock.value.trim());
  if (Object.keys(data).length === 0) {
    updateStatus.textContent = "Introduce al menos un campo.";
    updateStatus.className = "status warn";
    return;
  }
  const url = booksUrl(`/books/update/${encodeURIComponent(isbn)}`);
  logToClient(`Requesting PUT ${url}`, data);
  const res = await fetchProtected(url, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });
  const text = await res.text();
  logToClient(`Response PUT ${url} status ${res.status}`, text);
  await showOperationStatus(updateStatus, res, text);
}

async function handleDelete() {
  const list = deleteIsbns.value.split(",").map(s => s.trim()).filter(Boolean);
  if (list.length === 0) {
    deleteStatus.textContent = "Introduce al menos un ISBN.";
    deleteStatus.className = "status err";
    return;
  }
  const url = booksUrl(`/books/delete`);
  logToClient(`Requesting DELETE ${url}`, { isbns: list });
  const res = await fetchProtected(url, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ isbns: list })
  });
  const text = await res.text();
  logToClient(`Response DELETE ${url} status ${res.status}`, text);
  await showOperationStatus(deleteStatus, res, text);
  if (res.ok) deleteIsbns.value = "";
}

// ====== COMPARACIÓN JWT ======
function prettyJson(obj) {
  try { return JSON.stringify(obj, null, 2); } catch { return String(obj); }
}

async function compareNow() {
  if (!accessToken) {
    compareSummary.textContent = "No hay access token.";
    compareSummary.className = "status warn";
    localJwtResult.textContent = "";
    redisJwtResult.textContent = "";
    return;
  }
  const local = decodeJwt(accessToken) || {};
  localJwtResult.textContent = prettyJson(local);

  redisJwtResult.textContent = "Consultando...";
  let redisData = null, protectedOk = false;
  try {
    const st = await fetchProtected(`${AUTH_SERVICE_URL}/token/status`);
    redisData = await st.json();
    redisJwtResult.textContent = prettyJson(redisData);

    const pr = await fetchProtected(`${AUTH_SERVICE_URL}/protected`);
    protectedOk = pr.ok;

    const badge = (redisData?.is_revoked === false && protectedOk) ? "✅" : "⚠️";
    compareSummary.textContent = `${badge} Token Válido y Activo`;
    compareSummary.className = "status " + ((redisData?.is_revoked === false && protectedOk) ? "ok" : "warn");

  } catch (e) {
    redisJwtResult.textContent = e.message;
    compareSummary.textContent = "Error en la comparación";
    compareSummary.className = "status err";
    logToClient(`Compare FAIL: ${e.message}`);
  }
}

// ====== EVENTOS ======
loginBtn.addEventListener("click", login);
logoutBtn.addEventListener("click", logout);

showRegister.addEventListener("click", () => { registerBox.classList.remove("hide"); });
hideRegister.addEventListener("click", () => { registerBox.classList.add("hide"); });
registerBtn.addEventListener("click", register);

saveConfigBtn.addEventListener("click", saveBooksConfig);
resetConfigBtn.addEventListener("click", resetBooksConfig);

getAllBtn.addEventListener("click", () => loadResults(booksUrl("/books")));
getByIsbnBtn.addEventListener("click", () => {
  const v = isbnInput.value.trim();
  if (v) loadResults(booksUrl(`/books/isbn/${encodeURIComponent(v)}`));
});
getByAuthorBtn.addEventListener("click", () => {
  const v = authorInput.value.trim();
  if (v) loadResults(booksUrl(`/books/author/${encodeURIComponent(v)}`));
});
getByFormatBtn.addEventListener("click", () => {
  const v = formatInput.value.trim();
  if (v) loadResults(booksUrl(`/books/format/${encodeURIComponent(v)}`));
});

toggleResultsBtn.addEventListener("click", () => {
  if (resultsContainer.classList.contains("hide")) return;
  const showingXml = !xmlSource.classList.contains("hide");
  xmlSource.classList.toggle("hide");
  resultsFrame.classList.toggle("hide");
  toggleResultsBtn.textContent = showingXml ? "Mostrar XML" : "Ocultar XML (Ver Tabla)";
});

compareBtn.addEventListener("click", compareNow);

// CORRECCIÓN: Faltaban estos listeners para el CRUD
insertBtn.addEventListener("click", handleInsert);
updateBtn.addEventListener("click", handleUpdate);
deleteBtn.addEventListener("click", handleDelete);


// ====== ARRANQUE ======
(async function start() {
  logToClient('Cliente iniciado. Esperando acción...');
  syncBooksConfigToUi();

  const stored = localStorage.getItem("refreshToken");
  if (stored) {
    refreshToken = stored;
    logToClient('Refresh token encontrado. Intentando recuperar sesión...');
    await refreshAccess();
  } else {
    logToClient('No se encontró sesión previa.');
  }
  updateAuthSummary();
})();
