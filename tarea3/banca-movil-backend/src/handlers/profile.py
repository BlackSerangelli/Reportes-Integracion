"""
Función Lambda para actualizar el perfil de usuario.
Maneja información personal y preferencias de la cuenta.
"""
import json
import boto3
import os
import logging
from typing import Dict, Any
import time
import re

# Configuración de logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Clientes AWS
dynamodb = boto3.resource('dynamodb')

# Variables de entorno
USER_PROFILES_TABLE = os.environ.get('USER_PROFILES_TABLE')

def update_profile_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Handler principal para actualizar el perfil de usuario.
    
    Args:
        event: Evento de API Gateway
        context: Contexto de Lambda
        
    Returns:
        Respuesta HTTP con el perfil actualizado
    """
    try:
        # Parsear datos de entrada
        body = json.loads(event['body'])
        user_id = event['requestContext']['authorizer']['claims']['sub']
        
        logger.info(f"Actualizando perfil para usuario {user_id}")
        
        # Validar datos de entrada
        validated_data = validate_profile_data(body)
        
        # Actualizar perfil en DynamoDB
        updated_profile = update_user_profile(user_id, validated_data)
        
        return create_success_response({
            'user_id': user_id,
            'profile': updated_profile,
            'updated_fields': list(validated_data.keys())
        })
        
    except ValueError as e:
        logger.error(f"Error de validación: {str(e)}")
        return create_error_response(400, f"Datos inválidos: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        return create_error_response(500, "Error interno del servidor")

def validate_profile_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida y sanitiza los datos del perfil.
    
    Args:
        data: Datos del perfil a validar
        
    Returns:
        Datos validados y sanitizados
        
    Raises:
        ValueError: Si los datos son inválidos
    """
    validated_data = {}
    
    # Campos permitidos para actualización
    allowed_fields = {
        'first_name': str,
        'last_name': str,
        'email': str,
        'phone_number': str,
        'address': dict,
        'preferences': dict,
        'notification_settings': dict
    }
    
    for field, field_type in allowed_fields.items():
        if field in data:
            value = data[field]
            
            # Validar tipo de dato
            if not isinstance(value, field_type):
                raise ValueError(f"Tipo de dato inválido para {field}")
            
            # Validaciones específicas por campo
            if field == 'first_name' or field == 'last_name':
                validated_data[field] = validate_name(value)
            elif field == 'email':
                validated_data[field] = validate_email(value)
            elif field == 'phone_number':
                validated_data[field] = validate_phone_number(value)
            elif field == 'address':
                validated_data[field] = validate_address(value)
            elif field == 'preferences':
                validated_data[field] = validate_preferences(value)
            elif field == 'notification_settings':
                validated_data[field] = validate_notification_settings(value)
    
    if not validated_data:
        raise ValueError("No se proporcionaron campos válidos para actualizar")
    
    return validated_data

def validate_name(name: str) -> str:
    """
    Valida un nombre (primer nombre o apellido).
    
    Args:
        name: Nombre a validar
        
    Returns:
        Nombre validado y sanitizado
        
    Raises:
        ValueError: Si el nombre es inválido
    """
    name = name.strip()
    
    if not name:
        raise ValueError("El nombre no puede estar vacío")
    
    if len(name) < 2 or len(name) > 50:
        raise ValueError("El nombre debe tener entre 2 y 50 caracteres")
    
    # Permitir solo letras, espacios y algunos caracteres especiales
    if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s'-]+$", name):
        raise ValueError("El nombre contiene caracteres no válidos")
    
    return name.title()  # Capitalizar primera letra de cada palabra

def validate_email(email: str) -> str:
    """
    Valida una dirección de correo electrónico.
    
    Args:
        email: Email a validar
        
    Returns:
        Email validado
        
    Raises:
        ValueError: Si el email es inválido
    """
    email = email.strip().lower()
    
    # Regex básica para validación de email
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        raise ValueError("Formato de email inválido")
    
    if len(email) > 100:
        raise ValueError("Email demasiado largo")
    
    return email

def validate_phone_number(phone: str) -> str:
    """
    Valida un número de teléfono.
    
    Args:
        phone: Número de teléfono a validar
        
    Returns:
        Número de teléfono validado y formateado
        
    Raises:
        ValueError: Si el número es inválido
    """
    # Remover espacios y caracteres especiales
    phone = re.sub(r'[^\d+]', '', phone.strip())
    
    # Validar formato básico (permitir + al inicio)
    if not re.match(r'^\+?[1-9]\d{9,14}$', phone):
        raise ValueError("Formato de número de teléfono inválido")
    
    return phone

def validate_address(address: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida los datos de dirección.
    
    Args:
        address: Diccionario con datos de dirección
        
    Returns:
        Dirección validada
        
    Raises:
        ValueError: Si la dirección es inválida
    """
    validated_address = {}
    
    required_fields = ['street', 'city', 'state', 'zip_code', 'country']
    optional_fields = ['apartment', 'additional_info']
    
    for field in required_fields:
        if field not in address or not address[field]:
            raise ValueError(f"Campo de dirección requerido: {field}")
        
        value = str(address[field]).strip()
        if len(value) < 2 or len(value) > 100:
            raise ValueError(f"Longitud inválida para {field}")
        
        validated_address[field] = value
    
    for field in optional_fields:
        if field in address and address[field]:
            value = str(address[field]).strip()
            if len(value) <= 100:
                validated_address[field] = value
    
    return validated_address

def validate_preferences(preferences: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida las preferencias del usuario.
    
    Args:
        preferences: Diccionario con preferencias
        
    Returns:
        Preferencias validadas
    """
    validated_preferences = {}
    
    # Preferencias permitidas
    allowed_preferences = {
        'language': ['es', 'en', 'fr', 'pt'],
        'currency': ['USD', 'EUR', 'MXN', 'COP', 'ARS'],
        'theme': ['light', 'dark', 'auto'],
        'timezone': str
    }
    
    for pref, allowed_values in allowed_preferences.items():
        if pref in preferences:
            value = preferences[pref]
            
            if isinstance(allowed_values, list):
                if value in allowed_values:
                    validated_preferences[pref] = value
            elif isinstance(allowed_values, type):
                if isinstance(value, allowed_values):
                    validated_preferences[pref] = value
    
    return validated_preferences

def validate_notification_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida la configuración de notificaciones.
    
    Args:
        settings: Configuración de notificaciones
        
    Returns:
        Configuración validada
    """
    validated_settings = {}
    
    # Tipos de notificaciones permitidas
    notification_types = [
        'push_notifications',
        'email_notifications',
        'sms_notifications',
        'transaction_alerts',
        'security_alerts',
        'marketing_notifications'
    ]
    
    for notification_type in notification_types:
        if notification_type in settings:
            # Debe ser un booleano
            if isinstance(settings[notification_type], bool):
                validated_settings[notification_type] = settings[notification_type]
    
    return validated_settings

def update_user_profile(user_id: str, validated_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Actualiza el perfil del usuario en DynamoDB.
    
    Args:
        user_id: ID del usuario
        validated_data: Datos validados a actualizar
        
    Returns:
        Perfil actualizado
    """
    try:
        table = dynamodb.Table(USER_PROFILES_TABLE)
        
        # Construir expresión de actualización
        update_expression = "SET "
        expression_attribute_names = {}
        expression_attribute_values = {}
        
        for i, (field, value) in enumerate(validated_data.items()):
            if i > 0:
                update_expression += ", "
            
            attr_name = f"#{field}"
            attr_value = f":{field}"
            
            update_expression += f"{attr_name} = {attr_value}"
            expression_attribute_names[attr_name] = field
            expression_attribute_values[attr_value] = value
        
        # Agregar timestamp de última actualización
        update_expression += ", #updated_at = :updated_at"
        expression_attribute_names["#updated_at"] = "updated_at"
        expression_attribute_values[":updated_at"] = str(int(time.time()))
        
        # Ejecutar actualización
        response = table.update_item(
            Key={'user_id': user_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues='ALL_NEW'
        )
        
        updated_profile = response.get('Attributes', {})
        
        # Remover campos sensibles de la respuesta
        sensitive_fields = ['accounts', 'internal_id']
        for field in sensitive_fields:
            updated_profile.pop(field, None)
        
        logger.info(f"Perfil actualizado exitosamente para usuario {user_id}")
        return updated_profile
        
    except Exception as e:
        logger.error(f"Error actualizando perfil: {str(e)}")
        raise

def create_success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Crea una respuesta HTTP exitosa."""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'PUT, OPTIONS',
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
