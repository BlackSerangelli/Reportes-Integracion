#!/bin/bash

# Script de despliegue para la aplicación de banca móvil serverless
# Uso: ./deploy.sh [dev|staging|prod]

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Verificar parámetros
ENVIRONMENT=${1:-dev}
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    error "Ambiente inválido. Uso: $0 [dev|staging|prod]"
    exit 1
fi

log "Iniciando despliegue para ambiente: $ENVIRONMENT"

# Verificar dependencias
command -v sam >/dev/null 2>&1 || { error "SAM CLI no está instalado. Abortar."; exit 1; }
command -v aws >/dev/null 2>&1 || { error "AWS CLI no está instalado. Abortar."; exit 1; }

# Verificar credenciales de AWS
aws sts get-caller-identity >/dev/null 2>&1 || { error "No se encontraron credenciales válidas de AWS."; exit 1; }

# Validar template
log "Validando template SAM..."
sam validate --template template.yaml

# Build
log "Construyendo aplicación..."
sam build --cached --parallel

# Deploy
log "Desplegando a $ENVIRONMENT..."

case $ENVIRONMENT in
    "dev")
        STACK_NAME="banca-movil-backend-dev"
        REGION="us-east-1"
        ;;
    "staging")
        STACK_NAME="banca-movil-backend-staging"
        REGION="us-east-1"
        ;;
    "prod")
        STACK_NAME="banca-movil-backend-prod"
        REGION="us-east-1"
        # Solicitar confirmación para producción
        read -p "¿Estás seguro de que quieres desplegar a PRODUCCIÓN? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "Despliegue cancelado."
            exit 0
        fi
        ;;
esac

# Ejecutar despliegue
sam deploy \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides Environment="$ENVIRONMENT" \
    --s3-prefix "banca-movil-backend-$ENVIRONMENT" \
    --resolve-s3 \
    --no-confirm-changeset

# Obtener outputs del stack
log "Obteniendo información del despliegue..."
API_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`BankingApiUrl`].OutputValue' \
    --output text)

USER_POOL_ID=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
    --output text)

USER_POOL_CLIENT_ID=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' \
    --output text)

# Mostrar información del despliegue
echo
echo -e "${BLUE}===============================================${NC}"
echo -e "${GREEN}✅ Despliegue completado exitosamente!${NC}"
echo -e "${BLUE}===============================================${NC}"
echo
echo -e "${YELLOW}Información del despliegue:${NC}"
echo -e "Ambiente: ${GREEN}$ENVIRONMENT${NC}"
echo -e "Stack: ${GREEN}$STACK_NAME${NC}"
echo -e "Región: ${GREEN}$REGION${NC}"
echo
echo -e "${YELLOW}Endpoints y recursos:${NC}"
echo -e "API URL: ${GREEN}$API_URL${NC}"
echo -e "User Pool ID: ${GREEN}$USER_POOL_ID${NC}"
echo -e "User Pool Client ID: ${GREEN}$USER_POOL_CLIENT_ID${NC}"
echo
echo -e "${YELLOW}Próximos pasos:${NC}"
echo "1. Configurar la aplicación móvil con los endpoints anteriores"
echo "2. Configurar usuarios de prueba en Cognito"
echo "3. Probar las APIs usando Postman o curl"
echo
echo -e "${BLUE}===============================================${NC}"

log "Despliegue completado para $ENVIRONMENT"
