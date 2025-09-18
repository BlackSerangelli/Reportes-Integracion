# Ejemplos de Uso de la API de Banca Móvil

Esta documentación proporciona ejemplos prácticos de cómo usar la API de banca móvil serverless.

## Configuración Inicial

### Variables de Entorno
```bash
export API_BASE_URL="https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/dev"
export USER_POOL_ID="us-east-1_xxxxxxxxx"
export USER_POOL_CLIENT_ID="xxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### Autenticación con Cognito

Antes de usar cualquier endpoint, necesitas obtener un token JWT:

```bash
# Registrar un nuevo usuario
aws cognito-idp sign-up \
  --client-id $USER_POOL_CLIENT_ID \
  --username "usuario@ejemplo.com" \
  --password "TuPassword123!" \
  --user-attributes Name=email,Value=usuario@ejemplo.com Name=phone_number,Value=+1234567890

# Confirmar el registro (si tienes el código de verificación)
aws cognito-idp confirm-sign-up \
  --client-id $USER_POOL_CLIENT_ID \
  --username "usuario@ejemplo.com" \
  --confirmation-code "123456"

# Iniciar sesión y obtener tokens
aws cognito-idp initiate-auth \
  --client-id $USER_POOL_CLIENT_ID \
  --auth-flow USER_PASSWORD_AUTH \
  --auth-parameters USERNAME=usuario@ejemplo.com,PASSWORD=TuPassword123!
```

## Ejemplos de API

### 1. Consultar Saldo

```bash
curl -X GET "$API_BASE_URL/balance/1234567890" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json"
```

**Respuesta esperada:**
```json
{
  "success": true,
  "data": {
    "account_id": "1234567890",
    "balance": 15750.50,
    "currency": "USD",
    "available_balance": 15250.50,
    "last_updated": "1703123456",
    "account_type": "checking",
    "source": "core_banking"
  },
  "timestamp": "1703123456"
}
```

### 2. Realizar Transferencia

```bash
curl -X POST "$API_BASE_URL/transfer" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "from_account": "1234567890",
    "to_account": "0987654321",
    "amount": 500.00,
    "description": "Pago de renta",
    "currency": "USD"
  }'
```

**Respuesta esperada:**
```json
{
  "success": true,
  "data": {
    "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "amount": 500.00,
    "from_account": "1234567890",
    "to_account": "0987654321",
    "timestamp": "1703123456"
  },
  "timestamp": "1703123456"
}
```

### 3. Consultar Historial de Transacciones

```bash
# Obtener últimas 20 transacciones
curl -X GET "$API_BASE_URL/transactions/1234567890?limit=20" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json"

# Filtrar por tipo y fecha
curl -X GET "$API_BASE_URL/transactions/1234567890?type=transfer&start_date=2023-12-01&limit=10" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json"

# Filtrar por rango de montos
curl -X GET "$API_BASE_URL/transactions/1234567890?min_amount=100&max_amount=1000" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json"
```

**Respuesta esperada:**
```json
{
  "success": true,
  "data": {
    "account_id": "1234567890",
    "transactions": [
      {
        "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
        "timestamp": "1703123456",
        "transaction_type": "transfer",
        "amount": 500.00,
        "description": "Pago de renta",
        "from_account": "1234567890",
        "to_account": "0987654321",
        "status": "completed",
        "reference": "REF123456"
      },
      {
        "transaction_id": "550e8400-e29b-41d4-a716-446655440001",
        "timestamp": "1703120000",
        "transaction_type": "deposit",
        "amount": 2000.00,
        "description": "Depósito nómina",
        "to_account": "1234567890",
        "status": "completed",
        "reference": "REF123457"
      }
    ],
    "total_count": 2,
    "filters_applied": {
      "limit": 20,
      "offset": 0
    }
  },
  "timestamp": "1703123456"
}
```

### 4. Actualizar Perfil de Usuario

```bash
curl -X PUT "$API_BASE_URL/profile" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Juan",
    "last_name": "Pérez",
    "email": "juan.perez@ejemplo.com",
    "phone_number": "+1234567890",
    "address": {
      "street": "Calle Principal 123",
      "city": "Ciudad",
      "state": "Estado",
      "zip_code": "12345",
      "country": "México"
    },
    "preferences": {
      "language": "es",
      "currency": "MXN",
      "theme": "dark"
    },
    "notification_settings": {
      "push_notifications": true,
      "email_notifications": true,
      "sms_notifications": false,
      "transaction_alerts": true
    }
  }'
```

**Respuesta esperada:**
```json
{
  "success": true,
  "data": {
    "user_id": "us-east-1:12345678-1234-1234-1234-123456789012",
    "profile": {
      "first_name": "Juan",
      "last_name": "Pérez",
      "email": "juan.perez@ejemplo.com",
      "phone_number": "+1234567890",
      "address": {
        "street": "Calle Principal 123",
        "city": "Ciudad",
        "state": "Estado",
        "zip_code": "12345",
        "country": "México"
      },
      "preferences": {
        "language": "es",
        "currency": "MXN",
        "theme": "dark"
      },
      "notification_settings": {
        "push_notifications": true,
        "email_notifications": true,
        "sms_notifications": false,
        "transaction_alerts": true
      },
      "updated_at": "1703123456"
    },
    "updated_fields": ["first_name", "last_name", "email", "phone_number", "address", "preferences", "notification_settings"]
  },
  "timestamp": "1703123456"
}
```

## Manejo de Errores

### Error de Autenticación (401)
```json
{
  "success": false,
  "error": "Token de acceso inválido o expirado",
  "timestamp": "1703123456"
}
```

### Error de Autorización (403)
```json
{
  "success": false,
  "error": "Acceso denegado a la cuenta",
  "timestamp": "1703123456"
}
```

### Error de Validación (400)
```json
{
  "success": false,
  "error": "Datos inválidos: Monto debe ser mayor a cero",
  "timestamp": "1703123456"
}
```

### Error de Saldo Insuficiente (400)
```json
{
  "success": false,
  "error": "Saldo insuficiente",
  "timestamp": "1703123456"
}
```

### Error Interno del Servidor (500)
```json
{
  "success": false,
  "error": "Error interno del servidor",
  "timestamp": "1703123456"
}
```

## Scripts de Prueba

### Script de Bash para Pruebas Automatizadas

```bash
#!/bin/bash

# Configurar variables
API_BASE_URL="https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/dev"
JWT_TOKEN="your-jwt-token-here"

echo "🔍 Probando API de Banca Móvil..."

# Test 1: Consultar saldo
echo "📊 Test 1: Consultando saldo..."
curl -s -X GET "$API_BASE_URL/balance/1234567890" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" | jq '.'

# Test 2: Realizar transferencia pequeña
echo "💸 Test 2: Realizando transferencia..."
curl -s -X POST "$API_BASE_URL/transfer" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "from_account": "1234567890",
    "to_account": "0987654321",
    "amount": 10.00,
    "description": "Prueba de transferencia"
  }' | jq '.'

# Test 3: Consultar historial
echo "📋 Test 3: Consultando historial..."
curl -s -X GET "$API_BASE_URL/transactions/1234567890?limit=5" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" | jq '.'

echo "✅ Pruebas completadas"
```

### Script de Python para Pruebas

```python
import requests
import json
import os

class BankingAPIClient:
    def __init__(self, base_url, jwt_token):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }
    
    def get_balance(self, account_id):
        """Obtener saldo de cuenta"""
        response = requests.get(
            f"{self.base_url}/balance/{account_id}",
            headers=self.headers
        )
        return response.json()
    
    def transfer_funds(self, from_account, to_account, amount, description=""):
        """Realizar transferencia"""
        data = {
            'from_account': from_account,
            'to_account': to_account,
            'amount': amount,
            'description': description
        }
        response = requests.post(
            f"{self.base_url}/transfer",
            headers=self.headers,
            json=data
        )
        return response.json()
    
    def get_transactions(self, account_id, **filters):
        """Obtener historial de transacciones"""
        params = {k: v for k, v in filters.items() if v is not None}
        response = requests.get(
            f"{self.base_url}/transactions/{account_id}",
            headers=self.headers,
            params=params
        )
        return response.json()

# Ejemplo de uso
if __name__ == "__main__":
    api = BankingAPIClient(
        base_url=os.getenv('API_BASE_URL'),
        jwt_token=os.getenv('JWT_TOKEN')
    )
    
    # Consultar saldo
    balance = api.get_balance('1234567890')
    print("Saldo:", json.dumps(balance, indent=2))
    
    # Realizar transferencia
    transfer = api.transfer_funds(
        from_account='1234567890',
        to_account='0987654321',
        amount=25.00,
        description='Prueba desde Python'
    )
    print("Transferencia:", json.dumps(transfer, indent=2))
    
    # Consultar historial
    transactions = api.get_transactions(
        account_id='1234567890',
        limit=10,
        type='transfer'
    )
    print("Transacciones:", json.dumps(transactions, indent=2))
```

## Mejores Prácticas

### Seguridad
1. **Nunca hardcodees tokens JWT** en el código
2. **Usa HTTPS** para todas las comunicaciones
3. **Implementa rate limiting** en el cliente
4. **Maneja los tokens de refresh** apropiadamente

### Rendimiento
1. **Implementa cache** en el cliente para consultas frecuentes
2. **Usa paginación** para listas grandes
3. **Implementa retry logic** con backoff exponencial
4. **Monitorea latencia** y timeouts

### Monitoreo
1. **Logea todas las transacciones** importantes
2. **Implementa health checks** periódicos
3. **Monitorea métricas** de negocio (volumen, errores)
4. **Configura alertas** para eventos críticos
