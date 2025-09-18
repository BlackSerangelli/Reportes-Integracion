"""
Utilidades de seguridad para la aplicación de banca móvil.
Incluye funciones para encriptación, validación y auditoría.
"""
import hashlib
import hmac
import secrets
import time
from typing import Dict, Any, Optional
import json
import logging

logger = logging.getLogger(__name__)

class SecurityUtils:
    """Clase con utilidades de seguridad para transacciones bancarias."""
    
    @staticmethod
    def generate_transaction_hash(transaction_data: Dict[str, Any]) -> str:
        """
        Genera un hash único para una transacción.
        
        Args:
            transaction_data: Datos de la transacción
            
        Returns:
            Hash SHA-256 de la transacción
        """
        # Crear string determinística de los datos de transacción
        hash_data = {
            'transaction_id': transaction_data.get('transaction_id'),
            'amount': str(transaction_data.get('amount')),
            'from_account': transaction_data.get('from_account'),
            'to_account': transaction_data.get('to_account'),
            'timestamp': transaction_data.get('timestamp'),
            'user_id': transaction_data.get('user_id')
        }
        
        # Ordenar keys para consistencia
        sorted_data = json.dumps(hash_data, sort_keys=True, separators=(',', ':'))
        
        # Generar hash
        return hashlib.sha256(sorted_data.encode('utf-8')).hexdigest()
    
    @staticmethod
    def verify_transaction_integrity(transaction_data: Dict[str, Any], 
                                   expected_hash: str) -> bool:
        """
        Verifica la integridad de una transacción comparando hashes.
        
        Args:
            transaction_data: Datos de la transacción
            expected_hash: Hash esperado
            
        Returns:
            True si la transacción es íntegra, False en caso contrario
        """
        calculated_hash = SecurityUtils.generate_transaction_hash(transaction_data)
        return hmac.compare_digest(calculated_hash, expected_hash)
    
    @staticmethod
    def mask_account_number(account_number: str) -> str:
        """
        Enmascara un número de cuenta para logs y respuestas.
        
        Args:
            account_number: Número de cuenta completo
            
        Returns:
            Número de cuenta enmascarado
        """
        if not account_number or len(account_number) < 4:
            return "****"
        
        return f"****{account_number[-4:]}"
    
    @staticmethod
    def generate_audit_token() -> str:
        """
        Genera un token único para auditoría.
        
        Returns:
            Token de auditoría único
        """
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_amount_limits(amount: float, transaction_type: str, 
                             user_tier: str = 'standard') -> Dict[str, Any]:
        """
        Valida si un monto está dentro de los límites permitidos.
        
        Args:
            amount: Monto de la transacción
            transaction_type: Tipo de transacción
            user_tier: Nivel del usuario (standard, premium, corporate)
            
        Returns:
            Diccionario con resultado de validación
        """
        # Límites por tipo de transacción y nivel de usuario
        limits = {
            'standard': {
                'transfer': {'daily': 10000, 'single': 5000},
                'withdrawal': {'daily': 5000, 'single': 1000},
                'payment': {'daily': 15000, 'single': 3000}
            },
            'premium': {
                'transfer': {'daily': 50000, 'single': 25000},
                'withdrawal': {'daily': 10000, 'single': 5000},
                'payment': {'daily': 75000, 'single': 15000}
            },
            'corporate': {
                'transfer': {'daily': 500000, 'single': 100000},
                'withdrawal': {'daily': 50000, 'single': 25000},
                'payment': {'daily': 1000000, 'single': 200000}
            }
        }
        
        user_limits = limits.get(user_tier, limits['standard'])
        transaction_limits = user_limits.get(transaction_type, {'daily': 1000, 'single': 500})
        
        result = {
            'valid': True,
            'reason': None,
            'single_limit': transaction_limits['single'],
            'daily_limit': transaction_limits['daily']
        }
        
        if amount > transaction_limits['single']:
            result['valid'] = False
            result['reason'] = f"Monto excede límite por transacción (${transaction_limits['single']})"
        
        return result
    
    @staticmethod
    def detect_suspicious_pattern(user_id: str, transaction_data: Dict[str, Any], 
                                 recent_transactions: list) -> Dict[str, Any]:
        """
        Detecta patrones sospechosos en las transacciones.
        
        Args:
            user_id: ID del usuario
            transaction_data: Datos de la transacción actual
            recent_transactions: Transacciones recientes del usuario
            
        Returns:
            Análisis de patrones sospechosos
        """
        suspicion_score = 0
        flags = []
        
        current_amount = float(transaction_data.get('amount', 0))
        current_time = int(transaction_data.get('timestamp', time.time()))
        
        # Verificar transacciones múltiples en poco tiempo
        recent_count = 0
        recent_total = 0
        
        for tx in recent_transactions[-10:]:  # Últimas 10 transacciones
            tx_time = int(tx.get('timestamp', 0))
            if current_time - tx_time < 300:  # Últimos 5 minutos
                recent_count += 1
                recent_total += float(tx.get('amount', 0))
        
        if recent_count >= 5:
            suspicion_score += 30
            flags.append("multiple_transactions_short_time")
        
        # Verificar montos inusuales
        if recent_transactions:
            avg_amount = sum(float(tx.get('amount', 0)) for tx in recent_transactions[-20:]) / min(20, len(recent_transactions))
            if current_amount > avg_amount * 10:
                suspicion_score += 25
                flags.append("unusually_large_amount")
        
        # Verificar horarios inusuales (transacciones nocturnas)
        from datetime import datetime
        tx_hour = datetime.fromtimestamp(current_time).hour
        if tx_hour < 6 or tx_hour > 23:
            suspicion_score += 10
            flags.append("unusual_hour")
        
        # Verificar transacciones a cuentas nuevas
        known_accounts = set()
        for tx in recent_transactions[-50:]:
            if tx.get('to_account'):
                known_accounts.add(tx['to_account'])
        
        if transaction_data.get('to_account') and transaction_data['to_account'] not in known_accounts:
            suspicion_score += 15
            flags.append("new_recipient_account")
        
        risk_level = "low"
        if suspicion_score >= 50:
            risk_level = "high"
        elif suspicion_score >= 25:
            risk_level = "medium"
        
        return {
            'suspicion_score': suspicion_score,
            'risk_level': risk_level,
            'flags': flags,
            'requires_additional_auth': suspicion_score >= 40
        }

class EncryptionUtils:
    """Utilidades para encriptación de datos sensibles."""
    
    @staticmethod
    def encrypt_sensitive_data(data: str, key: Optional[str] = None) -> str:
        """
        Encripta datos sensibles.
        
        En un entorno real, usaríamos AWS KMS o similar.
        Esta es una implementación simplificada para demostración.
        
        Args:
            data: Datos a encriptar
            key: Clave de encriptación (opcional)
            
        Returns:
            Datos encriptados en base64
        """
        import base64
        
        # SIMULACIÓN: En producción usaríamos AWS KMS
        # Por ahora, solo codificamos en base64 para demostración
        encoded_data = base64.b64encode(data.encode('utf-8')).decode('utf-8')
        
        logger.info("Datos encriptados (simulación)")
        return encoded_data
    
    @staticmethod
    def decrypt_sensitive_data(encrypted_data: str, key: Optional[str] = None) -> str:
        """
        Desencripta datos sensibles.
        
        Args:
            encrypted_data: Datos encriptados
            key: Clave de desencriptación (opcional)
            
        Returns:
            Datos desencriptados
        """
        import base64
        
        # SIMULACIÓN: En producción usaríamos AWS KMS
        try:
            decoded_data = base64.b64decode(encrypted_data.encode('utf-8')).decode('utf-8')
            logger.info("Datos desencriptados (simulación)")
            return decoded_data
        except Exception as e:
            logger.error(f"Error desencriptando datos: {str(e)}")
            raise

class AuditLogger:
    """Logger especializado para auditoría de transacciones bancarias."""
    
    def __init__(self):
        self.logger = logging.getLogger('audit')
        self.logger.setLevel(logging.INFO)
    
    def log_transaction_attempt(self, user_id: str, transaction_data: Dict[str, Any]) -> None:
        """
        Registra un intento de transacción.
        
        Args:
            user_id: ID del usuario
            transaction_data: Datos de la transacción
        """
        audit_entry = {
            'event_type': 'transaction_attempt',
            'user_id': user_id,
            'transaction_id': transaction_data.get('transaction_id'),
            'amount': transaction_data.get('amount'),
            'from_account': SecurityUtils.mask_account_number(transaction_data.get('from_account', '')),
            'to_account': SecurityUtils.mask_account_number(transaction_data.get('to_account', '')),
            'timestamp': str(int(time.time())),
            'audit_token': SecurityUtils.generate_audit_token()
        }
        
        self.logger.info(f"AUDIT: {json.dumps(audit_entry)}")
    
    def log_security_event(self, user_id: str, event_type: str, details: Dict[str, Any]) -> None:
        """
        Registra un evento de seguridad.
        
        Args:
            user_id: ID del usuario
            event_type: Tipo de evento de seguridad
            details: Detalles del evento
        """
        audit_entry = {
            'event_type': f'security_{event_type}',
            'user_id': user_id,
            'details': details,
            'timestamp': str(int(time.time())),
            'audit_token': SecurityUtils.generate_audit_token()
        }
        
        self.logger.warning(f"SECURITY_AUDIT: {json.dumps(audit_entry)}")
    
    def log_access_attempt(self, user_id: str, resource: str, success: bool, 
                          ip_address: Optional[str] = None) -> None:
        """
        Registra un intento de acceso a recursos.
        
        Args:
            user_id: ID del usuario
            resource: Recurso al que se intentó acceder
            success: Si el acceso fue exitoso
            ip_address: Dirección IP del cliente
        """
        audit_entry = {
            'event_type': 'access_attempt',
            'user_id': user_id,
            'resource': resource,
            'success': success,
            'ip_address': ip_address,
            'timestamp': str(int(time.time())),
            'audit_token': SecurityUtils.generate_audit_token()
        }
        
        level = 'info' if success else 'warning'
        getattr(self.logger, level)(f"ACCESS_AUDIT: {json.dumps(audit_entry)}")
