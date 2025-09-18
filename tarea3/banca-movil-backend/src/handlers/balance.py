"""
Función Lambda para obtener el saldo de una cuenta bancaria.
Implementa conexión segura con el core bancario on-premises.
"""
import json
import boto3
import os
from decimal import Decimal
import logging
from typing import Dict, Any

# Configuración de logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Clientes AWS
dynamodb = boto3.resource('dynamodb')
ssm = boto3.client('ssm')

# Variables de entorno
USER_PROFILES_TABLE = os.environ.get('USER_PROFILES_TABLE')
TRANSACTION_CACHE_TABLE = os.environ.get('TRANSACTION_CACHE_TABLE')
CORE_BANKING_ENDPOINT = os.environ.get('CORE_BANKING_ENDPOINT')

def get_balance_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Handler principal para obtener el saldo de una cuenta.
    
    Args:
        event: Evento de API Gateway
        context: Contexto de Lambda
        
    Returns:
        Respuesta HTTP con el saldo de la cuenta
    """
    try:
        # Extraer parámetros de la petición
        account_id = event['pathParameters']['account_id']
        user_id = event['requestContext']['authorizer']['claims']['sub']
        
        logger.info(f"Consultando saldo para cuenta {account_id}, usuario {user_id}")
        
        # Validar que el usuario tiene acceso a la cuenta
        if not validate_account_access(user_id, account_id):
            return create_error_response(403, "Acceso denegado a la cuenta")
        
        # Intentar obtener saldo del cache primero
        cached_balance = get_cached_balance(account_id)
        if cached_balance:
            logger.info("Saldo obtenido del cache")
            return create_success_response(cached_balance)
        
        # Si no está en cache, consultar al core bancario
        balance_data = get_balance_from_core_banking(account_id)
        
        # Actualizar cache para futuras consultas
        update_balance_cache(account_id, balance_data)
        
        return create_success_response(balance_data)
        
    except ValueError as e:
        logger.error(f"Error de validación: {str(e)}")
        return create_error_response(400, f"Datos inválidos: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        return create_error_response(500, "Error interno del servidor")

def validate_account_access(user_id: str, account_id: str) -> bool:
    """
    Valida que el usuario tiene acceso a la cuenta solicitada.
    
    Args:
        user_id: ID del usuario autenticado
        account_id: ID de la cuenta a consultar
        
    Returns:
        True si el usuario tiene acceso, False en caso contrario
    """
    try:
        table = dynamodb.Table(USER_PROFILES_TABLE)
        response = table.get_item(Key={'user_id': user_id})
        
        if 'Item' not in response:
            return False
            
        user_accounts = response['Item'].get('accounts', [])
        return account_id in user_accounts
        
    except Exception as e:
        logger.error(f"Error validando acceso: {str(e)}")
        return False

def get_cached_balance(account_id: str) -> Dict[str, Any] or None:
    """
    Obtiene el saldo de la cuenta desde el cache de DynamoDB.
    
    Args:
        account_id: ID de la cuenta
        
    Returns:
        Datos del saldo si están en cache, None si no
    """
    try:
        table = dynamodb.Table(TRANSACTION_CACHE_TABLE)
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('account_id').eq(account_id),
            ScanIndexForward=False,  # Ordenar por timestamp descendente
            Limit=1,
            FilterExpression=boto3.dynamodb.conditions.Attr('record_type').eq('balance')
        )
        
        if response['Items']:
            item = response['Items'][0]
            # Verificar si el cache no ha expirado (5 minutos)
            import time
            current_time = int(time.time())
            if current_time - int(item['timestamp']) < 300:  # 5 minutos
                return {
                    'account_id': item['account_id'],
                    'balance': float(item['balance']),
                    'currency': item['currency'],
                    'last_updated': item['timestamp'],
                    'source': 'cache'
                }
        
        return None
        
    except Exception as e:
        logger.error(f"Error obteniendo saldo del cache: {str(e)}")
        return None

def get_balance_from_core_banking(account_id: str) -> Dict[str, Any]:
    """
    Obtiene el saldo directamente del core bancario on-premises.
    
    En un entorno real, esto haría una llamada segura (VPN/Direct Connect)
    al sistema bancario principal. Para esta simulación, generamos datos ficticios.
    
    Args:
        account_id: ID de la cuenta
        
    Returns:
        Datos del saldo desde el core bancario
    """
    try:
        # SIMULACIÓN: En producción, aquí haríamos una llamada HTTP segura
        # al endpoint del core bancario a través de VPN/Direct Connect
        
        # Simular diferentes tipos de cuentas y saldos
        import random
        import time
        
        # Simular diferentes saldos basados en el ID de cuenta
        seed = hash(account_id) % 1000000
        random.seed(seed)
        
        balance_amount = round(random.uniform(1000, 50000), 2)
        
        balance_data = {
            'account_id': account_id,
            'balance': balance_amount,
            'currency': 'USD',
            'available_balance': balance_amount - round(random.uniform(0, 500), 2),
            'last_updated': str(int(time.time())),
            'account_type': random.choice(['checking', 'savings', 'credit']),
            'source': 'core_banking'
        }
        
        logger.info(f"Saldo obtenido del core bancario: {balance_data}")
        return balance_data
        
    except Exception as e:
        logger.error(f"Error consultando core bancario: {str(e)}")
        raise

def update_balance_cache(account_id: str, balance_data: Dict[str, Any]) -> None:
    """
    Actualiza el cache de saldos en DynamoDB.
    
    Args:
        account_id: ID de la cuenta
        balance_data: Datos del saldo a cachear
    """
    try:
        table = dynamodb.Table(TRANSACTION_CACHE_TABLE)
        
        import time
        current_timestamp = str(int(time.time()))
        
        table.put_item(
            Item={
                'account_id': account_id,
                'timestamp': current_timestamp,
                'record_type': 'balance',
                'balance': Decimal(str(balance_data['balance'])),
                'currency': balance_data['currency'],
                'available_balance': Decimal(str(balance_data.get('available_balance', balance_data['balance']))),
                'account_type': balance_data.get('account_type', 'checking'),
                'ttl': int(time.time()) + 300  # Cache por 5 minutos
            }
        )
        
        logger.info(f"Cache actualizado para cuenta {account_id}")
        
    except Exception as e:
        logger.error(f"Error actualizando cache: {str(e)}")

def create_success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Crea una respuesta HTTP exitosa."""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        },
        'body': json.dumps({
            'success': True,
            'data': data,
            'timestamp': str(int(time.time()))
        }, default=str)
    }

def create_error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Crea una respuesta HTTP de error."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'success': False,
            'error': message,
            'timestamp': str(int(time.time()))
        })
    }
