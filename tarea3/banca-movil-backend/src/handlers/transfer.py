"""
Función Lambda para procesar transferencias de fondos.
Implementa validaciones de seguridad y comunicación con el core bancario.
"""
import json
import boto3
import os
from decimal import Decimal
import logging
from typing import Dict, Any
import uuid
import time

# Configuración de logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Clientes AWS
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
sqs = boto3.client('sqs')

# Variables de entorno
USER_PROFILES_TABLE = os.environ.get('USER_PROFILES_TABLE')
NOTIFICATION_TOPIC = os.environ.get('NOTIFICATION_TOPIC')
TRANSACTION_QUEUE = os.environ.get('TRANSACTION_QUEUE')
CORE_BANKING_ENDPOINT = os.environ.get('CORE_BANKING_ENDPOINT')

def transfer_funds_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Handler principal para procesar transferencias de fondos.
    
    Args:
        event: Evento de API Gateway
        context: Contexto de Lambda
        
    Returns:
        Respuesta HTTP con el resultado de la transferencia
    """
    try:
        # Parsear el cuerpo de la petición
        body = json.loads(event['body'])
        user_id = event['requestContext']['authorizer']['claims']['sub']
        
        # Validar datos de entrada
        transfer_data = validate_transfer_request(body, user_id)
        
        logger.info(f"Procesando transferencia: {transfer_data['transaction_id']}")
        
        # Verificar saldo disponible
        if not check_available_balance(transfer_data):
            return create_error_response(400, "Saldo insuficiente")
        
        # Validar cuenta destino
        if not validate_destination_account(transfer_data['to_account']):
            return create_error_response(400, "Cuenta destino inválida")
        
        # Procesar transferencia en el core bancario
        transaction_result = process_transfer_in_core_banking(transfer_data)
        
        if transaction_result['success']:
            # Enviar a cola para procesamiento asíncrono
            send_to_transaction_queue(transfer_data, transaction_result)
            
            # Enviar notificación
            send_transfer_notification(transfer_data, transaction_result)
            
            return create_success_response({
                'transaction_id': transfer_data['transaction_id'],
                'status': 'completed',
                'amount': transfer_data['amount'],
                'from_account': transfer_data['from_account'],
                'to_account': transfer_data['to_account'],
                'timestamp': transaction_result['timestamp']
            })
        else:
            return create_error_response(400, f"Error en transferencia: {transaction_result['error']}")
            
    except ValueError as e:
        logger.error(f"Error de validación: {str(e)}")
        return create_error_response(400, f"Datos inválidos: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        return create_error_response(500, "Error interno del servidor")

def validate_transfer_request(body: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """
    Valida los datos de la petición de transferencia.
    
    Args:
        body: Cuerpo de la petición
        user_id: ID del usuario autenticado
        
    Returns:
        Datos validados de la transferencia
        
    Raises:
        ValueError: Si los datos son inválidos
    """
    required_fields = ['from_account', 'to_account', 'amount', 'description']
    for field in required_fields:
        if field not in body:
            raise ValueError(f"Campo requerido faltante: {field}")
    
    # Validar formato de cuentas
    if not body['from_account'].isdigit() or len(body['from_account']) != 10:
        raise ValueError("Formato de cuenta origen inválido")
    
    if not body['to_account'].isdigit() or len(body['to_account']) != 10:
        raise ValueError("Formato de cuenta destino inválido")
    
    # Validar monto
    try:
        amount = float(body['amount'])
        if amount <= 0 or amount > 50000:  # Límite diario
            raise ValueError("Monto inválido (debe ser > 0 y <= 50,000)")
    except (ValueError, TypeError):
        raise ValueError("Monto debe ser un número válido")
    
    # Validar que el usuario posee la cuenta origen
    if not validate_account_ownership(user_id, body['from_account']):
        raise ValueError("No tienes permisos para esta cuenta origen")
    
    return {
        'transaction_id': str(uuid.uuid4()),
        'user_id': user_id,
        'from_account': body['from_account'],
        'to_account': body['to_account'],
        'amount': amount,
        'description': body['description'][:100],  # Limitar descripción
        'currency': body.get('currency', 'USD'),
        'timestamp': str(int(time.time()))
    }

def validate_account_ownership(user_id: str, account_id: str) -> bool:
    """
    Valida que el usuario es propietario de la cuenta.
    
    Args:
        user_id: ID del usuario
        account_id: ID de la cuenta
        
    Returns:
        True si el usuario es propietario, False en caso contrario
    """
    try:
        table = dynamodb.Table(USER_PROFILES_TABLE)
        response = table.get_item(Key={'user_id': user_id})
        
        if 'Item' not in response:
            return False
            
        user_accounts = response['Item'].get('accounts', [])
        return account_id in user_accounts
        
    except Exception as e:
        logger.error(f"Error validando propiedad de cuenta: {str(e)}")
        return False

def check_available_balance(transfer_data: Dict[str, Any]) -> bool:
    """
    Verifica que la cuenta origen tenga saldo suficiente.
    
    Args:
        transfer_data: Datos de la transferencia
        
    Returns:
        True si hay saldo suficiente, False en caso contrario
    """
    try:
        # SIMULACIÓN: En producción consultaríamos el core bancario
        # Para esta demo, simulamos diferentes saldos
        account_id = transfer_data['from_account']
        amount = transfer_data['amount']
        
        import random
        seed = hash(account_id) % 1000000
        random.seed(seed)
        available_balance = round(random.uniform(1000, 50000), 2)
        
        logger.info(f"Saldo disponible simulado: {available_balance}, monto a transferir: {amount}")
        
        return available_balance >= amount
        
    except Exception as e:
        logger.error(f"Error verificando saldo: {str(e)}")
        return False

def validate_destination_account(account_id: str) -> bool:
    """
    Valida que la cuenta destino existe y está activa.
    
    Args:
        account_id: ID de la cuenta destino
        
    Returns:
        True si la cuenta es válida, False en caso contrario
    """
    try:
        # SIMULACIÓN: En producción consultaríamos el core bancario
        # Para esta demo, consideramos válidas todas las cuentas de 10 dígitos
        return len(account_id) == 10 and account_id.isdigit()
        
    except Exception as e:
        logger.error(f"Error validando cuenta destino: {str(e)}")
        return False

def process_transfer_in_core_banking(transfer_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Procesa la transferencia en el core bancario on-premises.
    
    Args:
        transfer_data: Datos de la transferencia
        
    Returns:
        Resultado del procesamiento
    """
    try:
        # SIMULACIÓN: En producción haríamos una llamada segura al core bancario
        # a través de VPN/Direct Connect
        
        logger.info(f"Simulando transferencia en core bancario: {transfer_data['transaction_id']}")
        
        # Simular tiempo de procesamiento
        import random
        time.sleep(random.uniform(0.1, 0.5))
        
        # Simular 95% de éxito
        success_rate = 0.95
        is_successful = random.random() < success_rate
        
        if is_successful:
            return {
                'success': True,
                'transaction_id': transfer_data['transaction_id'],
                'core_reference': f"CB{int(time.time())}{random.randint(1000, 9999)}",
                'timestamp': str(int(time.time())),
                'status': 'completed'
            }
        else:
            return {
                'success': False,
                'error': 'Error temporal en el sistema bancario',
                'timestamp': str(int(time.time()))
            }
            
    except Exception as e:
        logger.error(f"Error procesando en core bancario: {str(e)}")
        return {
            'success': False,
            'error': 'Error de comunicación con sistema bancario',
            'timestamp': str(int(time.time()))
        }

def send_to_transaction_queue(transfer_data: Dict[str, Any], result: Dict[str, Any]) -> None:
    """
    Envía la transacción a la cola SQS para procesamiento asíncrono.
    
    Args:
        transfer_data: Datos de la transferencia
        result: Resultado del procesamiento
    """
    try:
        message_body = {
            'transaction_type': 'transfer',
            'transaction_data': transfer_data,
            'processing_result': result,
            'timestamp': str(int(time.time()))
        }
        
        sqs.send_message(
            QueueUrl=TRANSACTION_QUEUE,
            MessageBody=json.dumps(message_body, default=str)
        )
        
        logger.info(f"Transacción enviada a cola: {transfer_data['transaction_id']}")
        
    except Exception as e:
        logger.error(f"Error enviando a cola: {str(e)}")

def send_transfer_notification(transfer_data: Dict[str, Any], result: Dict[str, Any]) -> None:
    """
    Envía notificación de transferencia completada.
    
    Args:
        transfer_data: Datos de la transferencia
        result: Resultado del procesamiento
    """
    try:
        message = {
            'notification_type': 'transfer_completed',
            'user_id': transfer_data['user_id'],
            'transaction_id': transfer_data['transaction_id'],
            'amount': transfer_data['amount'],
            'from_account': transfer_data['from_account'],
            'to_account': transfer_data['to_account'],
            'timestamp': result['timestamp']
        }
        
        sns.publish(
            TopicArn=NOTIFICATION_TOPIC,
            Message=json.dumps(message, default=str),
            Subject='Transferencia Completada'
        )
        
        logger.info(f"Notificación enviada para transacción: {transfer_data['transaction_id']}")
        
    except Exception as e:
        logger.error(f"Error enviando notificación: {str(e)}")

def create_success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Crea una respuesta HTTP exitosa."""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
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
