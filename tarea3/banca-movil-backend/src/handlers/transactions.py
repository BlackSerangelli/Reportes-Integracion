"""
Función Lambda para obtener el historial de transacciones.
Implementa paginación y filtros para optimizar el rendimiento.
"""
import json
import boto3
import os
from decimal import Decimal
import logging
from typing import Dict, Any, List
import time
from boto3.dynamodb.conditions import Key, Attr

# Configuración de logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Clientes AWS
dynamodb = boto3.resource('dynamodb')

# Variables de entorno
TRANSACTION_CACHE_TABLE = os.environ.get('TRANSACTION_CACHE_TABLE')
USER_PROFILES_TABLE = os.environ.get('USER_PROFILES_TABLE')

def get_transactions_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Handler principal para obtener el historial de transacciones.
    
    Args:
        event: Evento de API Gateway
        context: Contexto de Lambda
        
    Returns:
        Respuesta HTTP con el historial de transacciones
    """
    try:
        # Extraer parámetros
        account_id = event['pathParameters']['account_id']
        user_id = event['requestContext']['authorizer']['claims']['sub']
        query_params = event.get('queryStringParameters') or {}
        
        logger.info(f"Consultando transacciones para cuenta {account_id}, usuario {user_id}")
        
        # Validar acceso a la cuenta
        if not validate_account_access(user_id, account_id):
            return create_error_response(403, "Acceso denegado a la cuenta")
        
        # Parsear parámetros de consulta
        filters = parse_query_parameters(query_params)
        
        # Obtener transacciones
        transactions = get_transactions_from_cache(account_id, filters)
        
        # Si no hay transacciones en cache, consultar core bancario
        if not transactions:
            transactions = get_transactions_from_core_banking(account_id, filters)
            # Actualizar cache con las transacciones obtenidas
            update_transactions_cache(account_id, transactions)
        
        # Formatear respuesta
        response_data = {
            'account_id': account_id,
            'transactions': transactions,
            'total_count': len(transactions),
            'filters_applied': filters,
            'timestamp': str(int(time.time()))
        }
        
        return create_success_response(response_data)
        
    except ValueError as e:
        logger.error(f"Error de validación: {str(e)}")
        return create_error_response(400, f"Parámetros inválidos: {str(e)}")
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

def parse_query_parameters(query_params: Dict[str, str]) -> Dict[str, Any]:
    """
    Parsea y valida los parámetros de consulta.
    
    Args:
        query_params: Parámetros de consulta de la URL
        
    Returns:
        Filtros parseados y validados
    """
    filters = {
        'limit': 50,  # Límite por defecto
        'offset': 0,
        'start_date': None,
        'end_date': None,
        'transaction_type': None,
        'min_amount': None,
        'max_amount': None
    }
    
    try:
        # Límite de resultados
        if 'limit' in query_params:
            limit = int(query_params['limit'])
            filters['limit'] = min(max(1, limit), 100)  # Entre 1 y 100
        
        # Offset para paginación
        if 'offset' in query_params:
            filters['offset'] = max(0, int(query_params['offset']))
        
        # Filtro por fechas
        if 'start_date' in query_params:
            filters['start_date'] = query_params['start_date']
        
        if 'end_date' in query_params:
            filters['end_date'] = query_params['end_date']
        
        # Filtro por tipo de transacción
        if 'type' in query_params:
            valid_types = ['transfer', 'deposit', 'withdrawal', 'payment']
            if query_params['type'] in valid_types:
                filters['transaction_type'] = query_params['type']
        
        # Filtros por monto
        if 'min_amount' in query_params:
            filters['min_amount'] = float(query_params['min_amount'])
        
        if 'max_amount' in query_params:
            filters['max_amount'] = float(query_params['max_amount'])
        
        return filters
        
    except (ValueError, TypeError) as e:
        raise ValueError(f"Parámetros de consulta inválidos: {str(e)}")

def get_transactions_from_cache(account_id: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Obtiene transacciones desde el cache de DynamoDB.
    
    Args:
        account_id: ID de la cuenta
        filters: Filtros a aplicar
        
    Returns:
        Lista de transacciones desde el cache
    """
    try:
        table = dynamodb.Table(TRANSACTION_CACHE_TABLE)
        
        # Construir condición de consulta
        key_condition = Key('account_id').eq(account_id)
        
        # Filtrar por fechas si se especifican
        filter_expression = Attr('record_type').eq('transaction')
        
        if filters['start_date']:
            filter_expression = filter_expression & Attr('timestamp').gte(filters['start_date'])
        
        if filters['end_date']:
            filter_expression = filter_expression & Attr('timestamp').lte(filters['end_date'])
        
        if filters['transaction_type']:
            filter_expression = filter_expression & Attr('transaction_type').eq(filters['transaction_type'])
        
        if filters['min_amount']:
            filter_expression = filter_expression & Attr('amount').gte(Decimal(str(filters['min_amount'])))
        
        if filters['max_amount']:
            filter_expression = filter_expression & Attr('amount').lte(Decimal(str(filters['max_amount'])))
        
        # Ejecutar consulta
        response = table.query(
            KeyConditionExpression=key_condition,
            FilterExpression=filter_expression,
            ScanIndexForward=False,  # Ordenar por timestamp descendente
            Limit=filters['limit'] + filters['offset']
        )
        
        # Aplicar offset y formatear resultados
        items = response.get('Items', [])
        transactions = []
        
        for item in items[filters['offset']:]:
            transactions.append({
                'transaction_id': item.get('transaction_id'),
                'timestamp': item.get('timestamp'),
                'transaction_type': item.get('transaction_type'),
                'amount': float(item.get('amount', 0)),
                'description': item.get('description'),
                'from_account': item.get('from_account'),
                'to_account': item.get('to_account'),
                'status': item.get('status'),
                'reference': item.get('reference')
            })
        
        logger.info(f"Obtenidas {len(transactions)} transacciones del cache")
        return transactions
        
    except Exception as e:
        logger.error(f"Error obteniendo transacciones del cache: {str(e)}")
        return []

def get_transactions_from_core_banking(account_id: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Obtiene transacciones directamente del core bancario on-premises.
    
    Args:
        account_id: ID de la cuenta
        filters: Filtros a aplicar
        
    Returns:
        Lista de transacciones desde el core bancario
    """
    try:
        # SIMULACIÓN: En producción haríamos una llamada segura al core bancario
        logger.info(f"Simulando consulta de transacciones al core bancario para cuenta {account_id}")
        
        import random
        import uuid
        from datetime import datetime, timedelta
        
        # Generar transacciones ficticias basadas en el ID de cuenta
        seed = hash(account_id) % 1000000
        random.seed(seed)
        
        transactions = []
        num_transactions = min(random.randint(5, 30), filters['limit'])
        
        transaction_types = ['transfer', 'deposit', 'withdrawal', 'payment']
        
        for i in range(num_transactions):
            # Generar timestamp aleatorio en los últimos 30 días
            days_ago = random.randint(0, 30)
            transaction_time = datetime.now() - timedelta(days=days_ago)
            timestamp = str(int(transaction_time.timestamp()))
            
            transaction_type = random.choice(transaction_types)
            amount = round(random.uniform(10, 5000), 2)
            
            # Aplicar filtros
            if filters['min_amount'] and amount < filters['min_amount']:
                continue
            if filters['max_amount'] and amount > filters['max_amount']:
                continue
            if filters['transaction_type'] and transaction_type != filters['transaction_type']:
                continue
            
            transaction = {
                'transaction_id': str(uuid.uuid4()),
                'timestamp': timestamp,
                'transaction_type': transaction_type,
                'amount': amount,
                'description': f"Transacción {transaction_type} #{i+1}",
                'from_account': account_id if transaction_type in ['transfer', 'withdrawal'] else None,
                'to_account': account_id if transaction_type in ['transfer', 'deposit'] else None,
                'status': 'completed',
                'reference': f"REF{random.randint(100000, 999999)}"
            }
            
            transactions.append(transaction)
        
        # Ordenar por timestamp descendente
        transactions.sort(key=lambda x: x['timestamp'], reverse=True)
        
        logger.info(f"Generadas {len(transactions)} transacciones ficticias")
        return transactions
        
    except Exception as e:
        logger.error(f"Error consultando core bancario: {str(e)}")
        return []

def update_transactions_cache(account_id: str, transactions: List[Dict[str, Any]]) -> None:
    """
    Actualiza el cache de transacciones en DynamoDB.
    
    Args:
        account_id: ID de la cuenta
        transactions: Lista de transacciones a cachear
    """
    try:
        table = dynamodb.Table(TRANSACTION_CACHE_TABLE)
        
        # Actualizar cache en lotes para mejor rendimiento
        with table.batch_writer() as batch:
            for transaction in transactions:
                cache_item = {
                    'account_id': account_id,
                    'timestamp': transaction['timestamp'],
                    'record_type': 'transaction',
                    'transaction_id': transaction['transaction_id'],
                    'transaction_type': transaction['transaction_type'],
                    'amount': Decimal(str(transaction['amount'])),
                    'description': transaction['description'],
                    'from_account': transaction.get('from_account'),
                    'to_account': transaction.get('to_account'),
                    'status': transaction['status'],
                    'reference': transaction['reference'],
                    'ttl': int(time.time()) + 3600  # Cache por 1 hora
                }
                
                batch.put_item(Item=cache_item)
        
        logger.info(f"Cache actualizado con {len(transactions)} transacciones")
        
    except Exception as e:
        logger.error(f"Error actualizando cache de transacciones: {str(e)}")

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
