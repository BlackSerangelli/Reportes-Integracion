class OllamaClient {
    constructor({ baseUrl = 'http://localhost:11434', timeout = 15000, model = 'deepseek-coder' } = {}) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.timeout = timeout;
        this.model = model;
    }

    async chat(message, options = {}) {
        if (!message || typeof message !== 'string') {
            throw new Error('message debe ser una cadena no vacía');
        }

        const payload = {
            model: this.model,
            messages: [{ role: 'user', content: message }],
            stream: false,
            options: Object.assign({ temperature: 0.1, top_p: 0.1, top_k: 10, num_predict: 100, repeat_penalty: 1.0 }, options)
        };

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);

        try {
            const res = await fetch(`${this.baseUrl}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!res.ok) {
                const err = await res.text();
                throw new Error(`Ollama HTTP ${res.status}: ${err}`);
            }

            const data = await res.json();
            // Soportar varias estructuras de respuesta
            if (data && data.message && data.message.content) return data.message.content;
            if (data && data.response) return data.response;
            // fallback: stringify whole response
            return JSON.stringify(data);
        } catch (err) {
            if (err.name === 'AbortError') throw new Error('Timeout al conectar con Ollama');
            throw err;
        }
    }
}

// UI wiring
document.addEventListener('DOMContentLoaded', () => {
    const messagesDiv = document.getElementById('messages');
    const chatForm = document.getElementById('chatForm');
    const userInput = document.getElementById('userInput');
    const statusSpan = document.getElementById('status');

    const client = new OllamaClient({ baseUrl: 'http://localhost:11434', timeout: 15000, model: 'deepseek-coder' });

    // Mostrar estado básico: comprobamos tags (si la API lo soporta)
    (async function checkConnection() {
        try {
            const r = await fetch(`${client.baseUrl}/api/tags`);
            if (r.ok) {
                statusSpan.textContent = 'Estado: Conectado a Ollama';
                statusSpan.style.color = '#4caf50';
                return;
            }
        } catch (e) {
            // ignore
        }
        statusSpan.textContent = 'Estado: No se pudo conectar a Ollama';
        statusSpan.style.color = '#f44336';
    })();

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = userInput.value.trim();
        if (!message) return;

        addMessage(message, 'user');
        userInput.value = '';

        const loading = addMessage('⏳ Pensando...', 'assistant');

        try {
            const resp = await client.chat(message);
            loading.textContent = resp;
            loading.className = 'message assistant';
        } catch (err) {
            loading.textContent = `Error: ${err.message}`;
            loading.className = 'message assistant error';
            console.error(err);
        }
    });

    function addMessage(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.textContent = content;
        messagesDiv.appendChild(messageDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        return messageDiv;
    }

    window.clearChat = () => {
        messagesDiv.innerHTML = '';
        addMessage('Chat limpiado', 'assistant');
    };
});