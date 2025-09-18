"""
Modelos de datos para transacciones bancarias.
Define las estructuras de datos y validaciones.
"""
from typing import Dict, Any, Optional, List
from decimal import Decimal
from enum import Enum
import time
import uuid

class TransactionType(Enum):
    """Tipos de transacciones soportadas."""
    TRANSFER = "transfer"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    PAYMENT = "payment"

class TransactionStatus(Enum):
    """Estados posibles de una transacción."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Currency(Enum):
    """Monedas soportadas."""
    USD = "USD"
    EUR = "EUR"
    MXN = "MXN"
    COP = "COP"
    ARS = "ARS"

class Transaction:
    """Modelo de datos para una transacción bancaria."""
    
    def __init__(self, transaction_data: Dict[str, Any]):
        self.transaction_id = transaction_data.get('transaction_id') or str(uuid.uuid4())
        self.user_id = transaction_data.get('user_id')
        self.transaction_type = TransactionType(transaction_data.get('transaction_type', 'transfer'))
        self.amount = Decimal(str(transaction_data.get('amount', 0)))
        self.currency = Currency(transaction_data.get('currency', 'USD'))
        self.from_account = transaction_data.get('from_account')
        self.to_account = transaction_data.get('to_account')
        self.description = transaction_data.get('description', '')[:200]  # Limitar descripción
        self.status = TransactionStatus(transaction_data.get('status', 'pending'))
        self.timestamp = transaction_data.get('timestamp') or str(int(time.time()))
        self.core_reference = transaction_data.get('core_reference')
        self.metadata = transaction_data.get('metadata', {})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la transacción a diccionario."""
        return {
            'transaction_id': self.transaction_id,
            'user_id': self.user_id,
            'transaction_type': self.transaction_type.value,
            'amount': float(self.amount),
            'currency': self.currency.value,
            'from_account': self.from_account,
            'to_account': self.to_account,
            'description': self.description,
            'status': self.status.value,
            'timestamp': self.timestamp,
            'core_reference': self.core_reference,
            'metadata': self.metadata
        }
    
    def to_dynamodb_item(self) -> Dict[str, Any]:
        """Convierte la transacción a formato DynamoDB."""
        item = self.to_dict()
        item['amount'] = self.amount  # Mantener como Decimal para DynamoDB
        return item
    
    def validate(self) -> List[str]:
        """
        Valida la transacción y retorna lista de errores.
        
        Returns:
            Lista de errores de validación (vacía si es válida)
        """
        errors = []
        
        # Validar campos requeridos
        if not self.user_id:
            errors.append("user_id es requerido")
        
        if self.amount <= 0:
            errors.append("amount debe ser mayor a cero")
        
        if self.amount > 1000000:  # Límite máximo
            errors.append("amount excede el límite máximo")
        
        # Validar cuentas según tipo de transacción
        if self.transaction_type in [TransactionType.TRANSFER, TransactionType.WITHDRAWAL]:
            if not self.from_account:
                errors.append("from_account es requerido para este tipo de transacción")
        
        if self.transaction_type in [TransactionType.TRANSFER, TransactionType.DEPOSIT]:
            if not self.to_account:
                errors.append("to_account es requerido para este tipo de transacción")
        
        # Validar que las cuentas sean diferentes en transferencias
        if (self.transaction_type == TransactionType.TRANSFER and 
            self.from_account == self.to_account):
            errors.append("from_account y to_account no pueden ser iguales")
        
        # Validar formato de cuentas
        for account_field, account_value in [('from_account', self.from_account), 
                                           ('to_account', self.to_account)]:
            if account_value and (not account_value.isdigit() or len(account_value) != 10):
                errors.append(f"{account_field} debe tener formato válido (10 dígitos)")
        
        return errors
    
    def is_valid(self) -> bool:
        """Retorna True si la transacción es válida."""
        return len(self.validate()) == 0
    
    def set_status(self, new_status: TransactionStatus, core_reference: Optional[str] = None):
        """
        Actualiza el estado de la transacción.
        
        Args:
            new_status: Nuevo estado
            core_reference: Referencia del core bancario (opcional)
        """
        self.status = new_status
        if core_reference:
            self.core_reference = core_reference
        
        # Actualizar metadata con información del cambio de estado
        if 'status_history' not in self.metadata:
            self.metadata['status_history'] = []
        
        self.metadata['status_history'].append({
            'status': new_status.value,
            'timestamp': str(int(time.time())),
            'core_reference': core_reference
        })

class Account:
    """Modelo de datos para una cuenta bancaria."""
    
    def __init__(self, account_data: Dict[str, Any]):
        self.account_id = account_data.get('account_id')
        self.user_id = account_data.get('user_id')
        self.account_type = account_data.get('account_type', 'checking')
        self.balance = Decimal(str(account_data.get('balance', 0)))
        self.available_balance = Decimal(str(account_data.get('available_balance', 0)))
        self.currency = Currency(account_data.get('currency', 'USD'))
        self.status = account_data.get('status', 'active')
        self.created_at = account_data.get('created_at') or str(int(time.time()))
        self.updated_at = account_data.get('updated_at') or str(int(time.time()))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la cuenta a diccionario."""
        return {
            'account_id': self.account_id,
            'user_id': self.user_id,
            'account_type': self.account_type,
            'balance': float(self.balance),
            'available_balance': float(self.available_balance),
            'currency': self.currency.value,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    def has_sufficient_funds(self, amount: Decimal) -> bool:
        """
        Verifica si la cuenta tiene fondos suficientes.
        
        Args:
            amount: Monto a verificar
            
        Returns:
            True si hay fondos suficientes
        """
        return self.available_balance >= amount
    
    def update_balance(self, amount: Decimal, transaction_type: TransactionType):
        """
        Actualiza el saldo de la cuenta.
        
        Args:
            amount: Monto de la transacción
            transaction_type: Tipo de transacción
        """
        if transaction_type in [TransactionType.DEPOSIT]:
            self.balance += amount
            self.available_balance += amount
        elif transaction_type in [TransactionType.WITHDRAWAL, TransactionType.TRANSFER]:
            self.balance -= amount
            self.available_balance -= amount
        
        self.updated_at = str(int(time.time()))

class UserProfile:
    """Modelo de datos para el perfil de usuario."""
    
    def __init__(self, profile_data: Dict[str, Any]):
        self.user_id = profile_data.get('user_id')
        self.first_name = profile_data.get('first_name', '')
        self.last_name = profile_data.get('last_name', '')
        self.email = profile_data.get('email', '')
        self.phone_number = profile_data.get('phone_number', '')
        self.accounts = profile_data.get('accounts', [])
        self.user_tier = profile_data.get('user_tier', 'standard')
        self.preferences = profile_data.get('preferences', {})
        self.notification_settings = profile_data.get('notification_settings', {})
        self.created_at = profile_data.get('created_at') or str(int(time.time()))
        self.updated_at = profile_data.get('updated_at') or str(int(time.time()))
        self.last_login = profile_data.get('last_login')
        self.is_active = profile_data.get('is_active', True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el perfil a diccionario."""
        return {
            'user_id': self.user_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'phone_number': self.phone_number,
            'accounts': self.accounts,
            'user_tier': self.user_tier,
            'preferences': self.preferences,
            'notification_settings': self.notification_settings,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'last_login': self.last_login,
            'is_active': self.is_active
        }
    
    def get_display_name(self) -> str:
        """Retorna el nombre completo para mostrar."""
        return f"{self.first_name} {self.last_name}".strip()
    
    def has_account(self, account_id: str) -> bool:
        """
        Verifica si el usuario tiene acceso a una cuenta específica.
        
        Args:
            account_id: ID de la cuenta a verificar
            
        Returns:
            True si el usuario tiene acceso a la cuenta
        """
        return account_id in self.accounts
    
    def add_account(self, account_id: str):
        """
        Agrega una cuenta al perfil del usuario.
        
        Args:
            account_id: ID de la cuenta a agregar
        """
        if account_id not in self.accounts:
            self.accounts.append(account_id)
            self.updated_at = str(int(time.time()))
    
    def remove_account(self, account_id: str):
        """
        Remueve una cuenta del perfil del usuario.
        
        Args:
            account_id: ID de la cuenta a remover
        """
        if account_id in self.accounts:
            self.accounts.remove(account_id)
            self.updated_at = str(int(time.time()))

class TransactionFilter:
    """Filtros para consultas de transacciones."""
    
    def __init__(self, filter_data: Dict[str, Any]):
        self.start_date = filter_data.get('start_date')
        self.end_date = filter_data.get('end_date')
        self.transaction_type = filter_data.get('transaction_type')
        self.min_amount = filter_data.get('min_amount')
        self.max_amount = filter_data.get('max_amount')
        self.status = filter_data.get('status')
        self.limit = min(filter_data.get('limit', 50), 100)  # Máximo 100
        self.offset = max(filter_data.get('offset', 0), 0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte los filtros a diccionario."""
        return {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'transaction_type': self.transaction_type,
            'min_amount': self.min_amount,
            'max_amount': self.max_amount,
            'status': self.status,
            'limit': self.limit,
            'offset': self.offset
        }
