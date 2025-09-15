# 🚀 Deploy DeepSeek-Coder en Google Cloud con CentOS + Docker

Este documento describe cómo desplegar **DeepSeek-Coder** en una VM de **Google Cloud** usando **CentOS Stream**, **Docker** y la interfaz **Open WebUI**.

---

## 📦 Instalación y despliegue

```bash
# 1. Actualizar el sistema
sudo dnf update -y
sudo dnf install -y dnf-utils device-mapper-persistent-data lvm2

# 2. Instalar Docker
sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo systemctl enable docker
sudo systemctl start docker
docker --version

# 3. Ejecutar Ollama en contenedor
sudo docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama

# 4. Descargar y ejecutar DeepSeek-Coder
sudo docker exec -it ollama bash -c "
  ollama pull deepseek-coder:1.3b &&   ollama run deepseek-coder:1.3b
"

# 5. Instalar Open WebUI
sudo docker run -d   -p 3000:8080   --add-host=host.docker.internal:host-gateway   -v open-webui:/app/backend/data   --name open-webui   --restart always   ghcr.io/open-webui/open-webui:main

# 6. Como apagarlo y volverlo a inicializar

sudo docker stop ollama
sudo docker stop open-webui

sudo docker start ollama
sudo docker start open-webui
```

---

## 🔒 Reglas de firewall en Google Cloud

```bash
# Asigno la etiqueta a la VM
gcloud compute instances add-tags maquina01 \
  --tags=ollama \
  --zone=us-central1-f

# Abrir puerto 11434 (Ollama API)
gcloud compute firewall-rules create allow-ollama   --allow=tcp:11434   --target-tags=ollama   --description="Allow Ollama API"

# Abrir puerto 3000 (Open WebUI)
gcloud compute firewall-rules create allow-webui   --allow=tcp:3000   --target-tags=ollama   --description="Allow Open WebUI"
```

> Para mayor seguridad, restringe acceso con:
> `--source-ranges=<TU_IP_PUBLICA>/32`

---

## 🌐 Conexión

- **API de Ollama**
  [http://EXTERNAL_IP_VM:11434](http://EXTERNAL_IP_VM:11434)

- **Open WebUI**
  [http://EXTERNAL_IP_VM:3000](http://EXTERNAL_IP_VM:3000)

---

✅ Con esto tendrás **DeepSeek-Coder** corriendo en Docker sobre tu VM en Google Cloud, con acceso vía API y web.
