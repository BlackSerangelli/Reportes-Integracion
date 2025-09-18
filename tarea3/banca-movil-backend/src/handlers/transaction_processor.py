"""
Función Lambda para procesar transacciones de forma asíncrona.
Se ejecuta cuando llegan mensajes a la cola SQS de transacciones.
"""
import json
import boto3
import os
import logging
from typing import Dict, Any, List
import time
from decimal import Decimal

# Configuración de logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Clientes AWS
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

# Variables de entorno
TRANSACTION_CACHE_TABLE = os.environ.get('TRANSACTION_CACHE_TABLE')
NOTIFICATION_TOPIC = os.environ.get('NOTIFICATION_TOPIC')

def process_transaction_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Handler principal para procesar transacciones desde SQS.
    
    Args:
        event: Evento de SQS con mensajes de transacciones
        context: Contexto de Lambda
        
    Returns:
        Resultado del procesamiento
    """
    try:
        processed_count = 0
        failed_count = 0
        
        # Procesar cada mensaje del lote
        for record in event['Records']:
            try:
                process_transaction_record(record)
                processed_count += 1
            except Exception as e:
                logger.error(f"Error procesando registro: {str(e)}")
                failed_count += 1
        
        logger.info(f"Procesamiento completado: {processed_count} exitosos, {failed_count} fallidos")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'processed': processed_count,
                'failed': failed_count
            })
        }
        
    except Exception as e:
        logger.error(f"Error general en procesamiento: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def process_transaction_record(record: Dict[str, Any]) -> None:
    """
    Procesa un registro individual de transacción.
    
    Args:
        record: Registro de SQS con datos de transacción
    """
    try:
        # Parsear el mensaje
        message_body = json.loads(record['body'])
        transaction_type = message_body.get('transaction_type')
        transaction_data = message_body.get('transaction_data')
        processing_result = message_body.get('processing_result')
        
        logger.info(f"Procesando transacción {transaction_data.get('transaction_id')} tipo {transaction_type}")
        
        # Procesar según el tipo de transacción
        if transaction_type == 'transfer':
            process_transfer_transaction(transaction_data, processing_result)
        elif transaction_type == 'deposit':
            process_deposit_transaction(transaction_data, processing_result)
        elif transaction_type == 'withdrawal':
            process_withdrawal_transaction(transaction_data, processing_result)
        else:
            logger.warning(f"Tipo de transacción no reconocido: {transaction_type}")
        
    except Exception as e:
        logger.error(f"Error procesando registro de transacción: {str(e)}")
        raise

def process_transfer_transaction(transaction_data: Dict[str, Any], result: Dict[str, Any]) -> None:
    """
    Procesa una transacción de transferencia.
    
    Args:
        transaction_data: Datos de la transacción
        result: Resultado del procesamiento inicial
    """
    try:
        transaction_id = transaction_data['transaction_id']
        
        # Actualizar cache de transacciones para ambas cuentas
        update_transaction_cache_for_account(
            transaction_data['from_account'], 
            transaction_data, 
            result, 
            'outgoing_transfer'
        )
        
        update_transaction_cache_for_account(
            transaction_data['to_account'], 
            transaction_data, 
            result, 
            'incoming_transfer'
        )
        
        # Actualizar saldos en cache (invalidar cache existente)
        invalidate_balance_cache(transaction_data['from_account'])
        invalidate_balance_cache(transaction_data['to_account'])
        
        # Generar eventos de auditoría
        create_audit_record(transaction_data, result, 'transfer_processed')
        
        # Enviar notificaciones adicionales si es necesario
        if float(transaction_data['amount']) > 10000:  # Transacciones grandes
            send_large_transaction_alert(transaction_data)
        
        logger.info(f"Transferencia procesada completamente: {transaction_id}")
        
    except Exception as e:
        logger.error(f"Error procesando transferencia: {str(e)}")
        raise

def process_deposit_transaction(transaction_data: Dict[str, Any], result: Dict[str, Any]) -> None:
    """
    Procesa una transacción de depósito.
    
    Args:
        transaction_data: Datos de la transacción
        result: Resultado del procesamiento inicial
    """
    try:
        transaction_id = transaction_data['transaction_id']
        
        # Actualizar cache de transacciones
        update_transaction_cache_for_account(
            transaction_data['to_account'], 
            transaction_data, 
            result, 
            'deposit'
        )
        
        # Invalidar cache de saldo
        invalidate_balance_cache(transaction_data['to_account'])
        
        # Auditoría
        create_audit_record(transaction_data, result, 'deposit_processed')
        
        logger.info(f"Depósito procesado: {transaction_id}")
        
    except Exception as e:
        logger.error(f"Error procesando depósito: {str(e)}")
        raise

def process_withdrawal_transaction(transaction_data: Dict[str, Any], result: Dict[str, Any]) -> None:
    """
    Procesa una transacción de retiro.
    
    Args:
        transaction_data: Datos de la transacción
        result: Resultado del procesamiento inicial
    """
    try:
        transaction_id = transaction_data['transaction_id']
        
        # Actualizar cache de transacciones
        update_transaction_cache_for_account(
            transaction_data['from_account'], 
            transaction_data, 
            result, 
            'withdrawal'
        )
        
        # Invalidar cache de saldo
        invalidate_balance_cache(transaction_data['from_account'])
        
        # Auditoría
        create_audit_record(transaction_data, result, 'withdrawal_processed')
        
        logger.info(f"Retiro procesado: {transaction_id}")
        
    except Exception as e:
        logger.error(f"Error procesando retiro: {str(e)}")
        raise

def update_transaction_cache_for_account(account_id: str, transaction_data: Dict[str, Any], 
                                       result: Dict[str, Any], transaction_type: str) -> None:
    """
    Actualiza el cache de transacciones para una cuenta específica.
    
    Args:
        account_id: ID de la cuenta
        transaction_data: Datos de la transacción
        result: Resultado del procesamiento
        transaction_type: Tipo específico de transacción para esta cuenta
    """
    try:
        table = dynamodb.Table(TRANSACTION_CACHE_TABLE)
        
        # Preparar item para el cache
        cache_item = {
            'account_id': account_id,
            'timestamp': result['timestamp'],
            'record_type': 'transaction',
            'transaction_id': transaction_data['transaction_id'],
            'transaction_type': transaction_type,
            'amount': Decimal(str(transaction_data['amount'])),
            'currency': transaction_data.get('currency', 'USD'),
            'description': transaction_data.get('description', ''),
            'status': result.get('status', 'completed'),
            'core_reference': result.get('core_reference', ''),
            'from_account': transaction_data.get('from_account'),
            'to_account': transaction_data.get('to_account'),
            'ttl': int(time.time()) + 2592000  # Cache por 30 días
        }
        
        # Insertar en DynamoDB
        table.put_item(Item=cache_item)
        
        logger.info(f"Cache de transacciones actualizado para cuenta {account_id}")
        
    except Exception as e:
        logger.error(f"Error actualizando cache de transacciones: {str(e)}")
        raise

def invalidate_balance_cache(account_id: str) -> None:
    """
    Invalida el cache de saldo para una cuenta específica.
    
    Args:
        account_id: ID de la cuenta
    """
    try:
        table = dynamodb.Table(TRANSACTION_CACHE_TABLE)
        
        # Buscar registros de saldo en cache
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('account_id').eq(account_id),
            FilterExpression=boto3.dynamodb.conditions.Attr('record_type').eq('balance')
        )
        
        # Eliminar registros de saldo existentes
        with table.batch_writer() as batch:
            for item in response.get('Items', []):
                batch.delete_item(
                    Key={
                        'account_id': item['account_id'],
                        'timestamp': item['timestamp']
                    }
                )
        
        logger.info(f"Cache de saldo invalidado para cuenta {account_id}")
        
    except Exception as e:
        logger.error(f"Error invalidando cache de saldo: {str(e)}")

def create_audit_record(transaction_data: Dict[str, Any], result: Dict[str, Any], event_type: str) -> None:
    """
    Crea un registro de auditoría para la transacción.
    
    Args:
        transaction_data: Datos de la transacción
        result: Resultado del procesamiento
        event_type: Tipo de evento de auditoría
    """
    try:
        audit_record = {
            'event_type': event_type,
            'transaction_id': transaction_data['transaction_id'],
            'user_id': transaction_data.get('user_id'),
            'amount': transaction_data['amount'],
            'from_account': transaction_data.get('from_account'),
            'to_account': transaction_data.get('to_account'),
            'core_reference': result.get('core_reference'),
            'timestamp': result['timestamp'],
            'processing_time': str(int(time.time()))
        }
        
        # En un entorno real, esto se enviaría a un sistema de auditoría
        # como Amazon CloudTrail, Elasticsearch, o un data lake
        logger.info(f"AUDIT: {json.dumps(audit_record, default=str)}")
        
    except Exception as e:
        logger.error(f"Error creando registro de auditoría: {str(e)}")

def send_large_transaction_alert(transaction_data: Dict[str, Any]) -> None:
    """
    Envía una alerta para transacciones grandes.
    
    Args:
        transaction_data: Datos de la transacción
    """
    try:
        alert_message = {
            'notification_type': 'security_alert',
            'alert_type': 'large_transaction',
            'user_id': transaction_data['user_id'],
            'transaction_id': transaction_data['transaction_id'],
            'amount': transaction_data['amount'],
            'description': f"Transacción grande detectada: ${transaction_data['amount']}",
            'timestamp': str(int(time.time()))
        }
        
        # Enviar alerta a SNS
        sns.publish(
            TopicArn=NOTIFICATION_TOPIC,
            Message=json.dumps(alert_message, default=str),
            Subject='Alerta de Transacción Grande'
        )
        
        logger.info(f"Alerta de transacción grande enviada: {transaction_data['transaction_id']}")
        
    except Exception as e:
        logger.error(f"Error enviando alerta de transacción grande: {str(e)}")

def calculate_transaction_metrics(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calcula métricas de las transacciones procesadas.
    
    Args:
        transactions: Lista de transacciones
        
    Returns:
        Métricas calculadas
    """
    try:
        if not transactions:
            return {}
        
        total_amount = sum(float(t.get('amount', 0)) for t in transactions)
        avg_amount = total_amount / len(transactions)
        
        transaction_types = {}
        for transaction in transactions:
            tx_type = transaction.get('transaction_type', 'unknown')
            transaction_types[tx_type] = transaction_types.get(tx_type, 0) + 1
        
        return {
            'total_transactions': len(transactions),
            'total_amount': round(total_amount, 2),
            'average_amount': round(avg_amount, 2),
            'transaction_types': transaction_types,
            'timestamp': str(int(time.time()))
        }
        
    except Exception as e:
        logger.error(f"Error calculando métricas: {str(e)}")
        return {}
