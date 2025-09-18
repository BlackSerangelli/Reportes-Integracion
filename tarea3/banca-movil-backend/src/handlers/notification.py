"""
Función Lambda para procesar y enviar notificaciones.
Se ejecuta de forma asíncrona cuando se publican mensajes en SNS.
"""
import json
import boto3
import os
import logging
from typing import Dict, Any
import time

# Configuración de logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Clientes AWS
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

# Variables de entorno
USER_PROFILES_TABLE = os.environ.get('USER_PROFILES_TABLE')

def send_notification_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Handler principal para procesar notificaciones desde SNS.
    
    Args:
        event: Evento de SNS
        context: Contexto de Lambda
        
    Returns:
        Resultado del procesamiento
    """
    try:
        # Procesar cada mensaje del evento SNS
        for record in event['Records']:
            if record['EventSource'] == 'aws:sns':
                process_sns_message(record['Sns'])
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'processed_records': len(event['Records'])
            })
        }
        
    except Exception as e:
        logger.error(f"Error procesando notificaciones: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def process_sns_message(sns_message: Dict[str, Any]) -> None:
    """
    Procesa un mensaje individual de SNS.
    
    Args:
        sns_message: Mensaje de SNS a procesar
    """
    try:
        # Parsear el mensaje
        message_body = json.loads(sns_message['Message'])
        notification_type = message_body.get('notification_type')
        
        logger.info(f"Procesando notificación tipo: {notification_type}")
        
        # Enrutar según el tipo de notificación
        if notification_type == 'transfer_completed':
            handle_transfer_notification(message_body)
        elif notification_type == 'security_alert':
            handle_security_notification(message_body)
        elif notification_type == 'account_update':
            handle_account_update_notification(message_body)
        elif notification_type == 'promotional':
            handle_promotional_notification(message_body)
        else:
            logger.warning(f"Tipo de notificación no reconocido: {notification_type}")
        
    except Exception as e:
        logger.error(f"Error procesando mensaje SNS: {str(e)}")

def handle_transfer_notification(message: Dict[str, Any]) -> None:
    """
    Maneja notificaciones de transferencias completadas.
    
    Args:
        message: Datos del mensaje de transferencia
    """
    try:
        user_id = message.get('user_id')
        transaction_id = message.get('transaction_id')
        amount = message.get('amount')
        from_account = message.get('from_account')
        to_account = message.get('to_account')
        
        # Obtener preferencias de notificación del usuario
        user_preferences = get_user_notification_preferences(user_id)
        
        if not user_preferences:
            logger.warning(f"No se encontraron preferencias para usuario {user_id}")
            return
        
        # Preparar mensaje de notificación
        notification_message = f"Transferencia completada: ${amount} desde {from_account} hacia {to_account}. ID: {transaction_id}"
        
        # Enviar notificaciones según las preferencias del usuario
        if user_preferences.get('push_notifications', True):
            send_push_notification(user_id, "Transferencia Completada", notification_message)
        
        if user_preferences.get('email_notifications', False):
            send_email_notification(user_id, "Transferencia Completada", notification_message)
        
        if user_preferences.get('sms_notifications', False):
            send_sms_notification(user_id, notification_message)
        
        logger.info(f"Notificación de transferencia enviada para usuario {user_id}")
        
    except Exception as e:
        logger.error(f"Error enviando notificación de transferencia: {str(e)}")

def handle_security_notification(message: Dict[str, Any]) -> None:
    """
    Maneja notificaciones de seguridad críticas.
    
    Args:
        message: Datos del mensaje de seguridad
    """
    try:
        user_id = message.get('user_id')
        alert_type = message.get('alert_type')
        description = message.get('description')
        
        # Las alertas de seguridad se envían siempre, independientemente de las preferencias
        notification_message = f"Alerta de Seguridad: {description}"
        
        # Enviar por todos los canales disponibles para alertas de seguridad
        send_push_notification(user_id, f"Alerta de Seguridad - {alert_type}", notification_message)
        send_email_notification(user_id, f"Alerta de Seguridad - {alert_type}", notification_message)
        send_sms_notification(user_id, notification_message)
        
        logger.info(f"Alerta de seguridad enviada para usuario {user_id}: {alert_type}")
        
    except Exception as e:
        logger.error(f"Error enviando alerta de seguridad: {str(e)}")

def handle_account_update_notification(message: Dict[str, Any]) -> None:
    """
    Maneja notificaciones de actualizaciones de cuenta.
    
    Args:
        message: Datos del mensaje de actualización
    """
    try:
        user_id = message.get('user_id')
        update_type = message.get('update_type')
        description = message.get('description')
        
        user_preferences = get_user_notification_preferences(user_id)
        
        if not user_preferences or not user_preferences.get('account_updates', True):
            return
        
        notification_message = f"Actualización de cuenta: {description}"
        
        if user_preferences.get('push_notifications', True):
            send_push_notification(user_id, f"Actualización - {update_type}", notification_message)
        
        if user_preferences.get('email_notifications', False):
            send_email_notification(user_id, f"Actualización - {update_type}", notification_message)
        
        logger.info(f"Notificación de actualización enviada para usuario {user_id}")
        
    except Exception as e:
        logger.error(f"Error enviando notificación de actualización: {str(e)}")

def handle_promotional_notification(message: Dict[str, Any]) -> None:
    """
    Maneja notificaciones promocionales.
    
    Args:
        message: Datos del mensaje promocional
    """
    try:
        user_id = message.get('user_id')
        campaign_id = message.get('campaign_id')
        title = message.get('title')
        content = message.get('content')
        
        user_preferences = get_user_notification_preferences(user_id)
        
        # Solo enviar si el usuario ha optado por recibir notificaciones promocionales
        if not user_preferences or not user_preferences.get('marketing_notifications', False):
            logger.info(f"Usuario {user_id} ha optado por no recibir notificaciones promocionales")
            return
        
        if user_preferences.get('push_notifications', True):
            send_push_notification(user_id, title, content)
        
        if user_preferences.get('email_notifications', False):
            send_email_notification(user_id, title, content)
        
        logger.info(f"Notificación promocional enviada para usuario {user_id}, campaña {campaign_id}")
        
    except Exception as e:
        logger.error(f"Error enviando notificación promocional: {str(e)}")

def get_user_notification_preferences(user_id: str) -> Dict[str, Any] or None:
    """
    Obtiene las preferencias de notificación del usuario.
    
    Args:
        user_id: ID del usuario
        
    Returns:
        Preferencias de notificación del usuario
    """
    try:
        table = dynamodb.Table(USER_PROFILES_TABLE)
        response = table.get_item(Key={'user_id': user_id})
        
        if 'Item' not in response:
            return None
        
        user_profile = response['Item']
        return user_profile.get('notification_settings', {})
        
    except Exception as e:
        logger.error(f"Error obteniendo preferencias de usuario: {str(e)}")
        return None

def send_push_notification(user_id: str, title: str, message: str) -> None:
    """
    Envía una notificación push al dispositivo del usuario.
    
    Args:
        user_id: ID del usuario
        title: Título de la notificación
        message: Contenido de la notificación
    """
    try:
        # SIMULACIÓN: En producción, aquí integraríamos con un servicio como
        # Amazon Pinpoint, Firebase Cloud Messaging, o Apple Push Notifications
        
        logger.info(f"PUSH NOTIFICATION enviada a {user_id}: {title} - {message}")
        
        # En un entorno real, aquí haríamos:
        # 1. Obtener el token del dispositivo del usuario desde DynamoDB
        # 2. Usar Amazon Pinpoint o SNS Mobile Push para enviar la notificación
        # 3. Manejar errores de dispositivos inactivos o tokens inválidos
        
    except Exception as e:
        logger.error(f"Error enviando push notification: {str(e)}")

def send_email_notification(user_id: str, subject: str, message: str) -> None:
    """
    Envía una notificación por email al usuario.
    
    Args:
        user_id: ID del usuario
        subject: Asunto del email
        message: Contenido del email
    """
    try:
        # SIMULACIÓN: En producción integraríamos con Amazon SES
        
        logger.info(f"EMAIL enviado a usuario {user_id}: {subject} - {message}")
        
        # En un entorno real:
        # 1. Obtener email del usuario desde DynamoDB
        # 2. Usar Amazon SES para enviar el email
        # 3. Usar plantillas HTML para emails más atractivos
        # 4. Manejar bounces y quejas
        
    except Exception as e:
        logger.error(f"Error enviando email: {str(e)}")

def send_sms_notification(user_id: str, message: str) -> None:
    """
    Envía una notificación SMS al usuario.
    
    Args:
        user_id: ID del usuario
        message: Contenido del SMS
    """
    try:
        # SIMULACIÓN: En producción usaríamos Amazon SNS SMS
        
        logger.info(f"SMS enviado a usuario {user_id}: {message}")
        
        # En un entorno real:
        # 1. Obtener número de teléfono del usuario desde DynamoDB
        # 2. Usar Amazon SNS SMS para enviar el mensaje
        # 3. Manejar números inválidos y límites de envío
        # 4. Considerar costos por SMS
        
    except Exception as e:
        logger.error(f"Error enviando SMS: {str(e)}")

def create_success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Crea una respuesta HTTP exitosa."""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
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
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'success': False,
            'error': message,
            'timestamp': str(int(time.time()))
        })
    }
