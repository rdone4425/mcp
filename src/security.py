"""
Security and privacy utilities for AI Context Memory.
"""

import os
import base64
import hashlib
import secrets
from typing import Optional, Dict, Any, List
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)

class EncryptionManager:
    """Manages encryption and decryption of sensitive data."""
    
    def __init__(self, password: Optional[str] = None, salt: Optional[bytes] = None):
        """Initialize encryption manager.
        
        Args:
            password: Password for encryption (if None, encryption is disabled)
            salt: Salt for key derivation (if None, a new salt is generated)
        """
        self.enabled = password is not None
        self._fernet = None
        self._salt = salt
        
        if self.enabled:
            self._initialize_encryption(password, salt)
    
    def _initialize_encryption(self, password: str, salt: Optional[bytes] = None):
        """Initialize encryption with password and salt."""
        try:
            # Generate salt if not provided
            if salt is None:
                self._salt = os.urandom(16)
            else:
                self._salt = salt
            
            # Derive key from password
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=self._salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            
            # Initialize Fernet cipher
            self._fernet = Fernet(key)
            
            logger.info("Encryption initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise
    
    def get_salt(self) -> Optional[bytes]:
        """Get the salt used for key derivation."""
        return self._salt
    
    def encrypt(self, data: str) -> str:
        """Encrypt a string.
        
        Args:
            data: String to encrypt
            
        Returns:
            Encrypted string (base64 encoded) or original string if encryption disabled
        """
        if not self.enabled or not data:
            return data
        
        try:
            encrypted_bytes = self._fernet.encrypt(data.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt a string.
        
        Args:
            encrypted_data: Encrypted string (base64 encoded)
            
        Returns:
            Decrypted string or original string if encryption disabled
        """
        if not self.enabled or not encrypted_data:
            return encrypted_data
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def encrypt_dict(self, data: Dict[str, Any], fields_to_encrypt: List[str]) -> Dict[str, Any]:
        """Encrypt specific fields in a dictionary.
        
        Args:
            data: Dictionary containing data
            fields_to_encrypt: List of field names to encrypt
            
        Returns:
            Dictionary with specified fields encrypted
        """
        if not self.enabled:
            return data
        
        encrypted_data = data.copy()
        
        for field in fields_to_encrypt:
            if field in encrypted_data and encrypted_data[field] is not None:
                if isinstance(encrypted_data[field], str):
                    encrypted_data[field] = self.encrypt(encrypted_data[field])
                elif isinstance(encrypted_data[field], list):
                    # Encrypt list items (e.g., tags)
                    encrypted_data[field] = [
                        self.encrypt(item) if isinstance(item, str) else item
                        for item in encrypted_data[field]
                    ]
        
        return encrypted_data
    
    def decrypt_dict(self, data: Dict[str, Any], fields_to_decrypt: List[str]) -> Dict[str, Any]:
        """Decrypt specific fields in a dictionary.
        
        Args:
            data: Dictionary containing encrypted data
            fields_to_decrypt: List of field names to decrypt
            
        Returns:
            Dictionary with specified fields decrypted
        """
        if not self.enabled:
            return data
        
        decrypted_data = data.copy()
        
        for field in fields_to_decrypt:
            if field in decrypted_data and decrypted_data[field] is not None:
                try:
                    if isinstance(decrypted_data[field], str):
                        decrypted_data[field] = self.decrypt(decrypted_data[field])
                    elif isinstance(decrypted_data[field], list):
                        # Decrypt list items (e.g., tags)
                        decrypted_data[field] = [
                            self.decrypt(item) if isinstance(item, str) else item
                            for item in decrypted_data[field]
                        ]
                except Exception as e:
                    logger.warning(f"Failed to decrypt field '{field}': {e}")
                    # Keep original value if decryption fails
        
        return decrypted_data

class PrivacyManager:
    """Manages privacy settings and data access control."""
    
    def __init__(self):
        """Initialize privacy manager."""
        self.sensitive_fields = {'content', 'context'}  # Fields that contain sensitive data
        self.allowed_memory_types = {'fact', 'preference', 'conversation', 'note'}
        self.blocked_keywords = set()  # Keywords that should not be stored
        self.max_content_length = 10000  # Maximum content length
        self.max_context_length = 1000   # Maximum context length
        self.retention_days = None       # Data retention period (None = no limit)
        
    def set_blocked_keywords(self, keywords: List[str]):
        """Set keywords that should not be stored.
        
        Args:
            keywords: List of keywords to block
        """
        self.blocked_keywords = {kw.lower().strip() for kw in keywords if kw.strip()}
        logger.info(f"Set {len(self.blocked_keywords)} blocked keywords")
    
    def add_blocked_keyword(self, keyword: str):
        """Add a keyword to the blocked list.
        
        Args:
            keyword: Keyword to block
        """
        if keyword.strip():
            self.blocked_keywords.add(keyword.lower().strip())
            logger.info(f"Added blocked keyword: {keyword}")
    
    def remove_blocked_keyword(self, keyword: str):
        """Remove a keyword from the blocked list.
        
        Args:
            keyword: Keyword to unblock
        """
        keyword_lower = keyword.lower().strip()
        if keyword_lower in self.blocked_keywords:
            self.blocked_keywords.remove(keyword_lower)
            logger.info(f"Removed blocked keyword: {keyword}")
    
    def set_retention_period(self, days: Optional[int]):
        """Set data retention period.
        
        Args:
            days: Number of days to retain data (None = no limit)
        """
        self.retention_days = days
        if days:
            logger.info(f"Set data retention period to {days} days")
        else:
            logger.info("Disabled data retention limit")
    
    def validate_content(self, content: str) -> tuple[bool, Optional[str]]:
        """Validate content against privacy rules.
        
        Args:
            content: Content to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not content or not content.strip():
            return False, "Content cannot be empty"
        
        # Check length limits
        if len(content) > self.max_content_length:
            return False, f"Content too long (max {self.max_content_length} characters)"
        
        # Check for blocked keywords
        content_lower = content.lower()
        for keyword in self.blocked_keywords:
            if keyword in content_lower:
                return False, f"Content contains blocked keyword: {keyword}"
        
        return True, None
    
    def validate_context(self, context: Optional[str]) -> tuple[bool, Optional[str]]:
        """Validate context against privacy rules.
        
        Args:
            context: Context to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not context:
            return True, None
        
        # Check length limits
        if len(context) > self.max_context_length:
            return False, f"Context too long (max {self.max_context_length} characters)"
        
        # Check for blocked keywords
        context_lower = context.lower()
        for keyword in self.blocked_keywords:
            if keyword in context_lower:
                return False, f"Context contains blocked keyword: {keyword}"
        
        return True, None
    
    def validate_memory_type(self, memory_type: str) -> tuple[bool, Optional[str]]:
        """Validate memory type.
        
        Args:
            memory_type: Memory type to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if memory_type not in self.allowed_memory_types:
            return False, f"Memory type '{memory_type}' not allowed"
        
        return True, None
    
    def sanitize_content(self, content: str) -> str:
        """Sanitize content by removing or masking sensitive information.
        
        Args:
            content: Content to sanitize
            
        Returns:
            Sanitized content
        """
        if not content:
            return content
        
        # Basic sanitization - remove common PII patterns
        import re
        
        # Mask email addresses
        content = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
                        '[EMAIL]', content)
        
        # Mask phone numbers (basic patterns)
        content = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', content)
        content = re.sub(r'\b\(\d{3}\)\s*\d{3}[-.]?\d{4}\b', '[PHONE]', content)
        
        # Mask credit card numbers (basic pattern)
        content = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD]', content)
        
        # Mask SSN (US format)
        content = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', content)
        
        return content
    
    def should_encrypt_field(self, field_name: str) -> bool:
        """Check if a field should be encrypted.
        
        Args:
            field_name: Name of the field
            
        Returns:
            True if field should be encrypted
        """
        return field_name in self.sensitive_fields
    
    def get_privacy_settings(self) -> Dict[str, Any]:
        """Get current privacy settings.
        
        Returns:
            Dictionary of privacy settings
        """
        return {
            'sensitive_fields': list(self.sensitive_fields),
            'allowed_memory_types': list(self.allowed_memory_types),
            'blocked_keywords_count': len(self.blocked_keywords),
            'max_content_length': self.max_content_length,
            'max_context_length': self.max_context_length,
            'retention_days': self.retention_days
        }

class SecureMemoryManager:
    """Memory manager with encryption and privacy features."""
    
    def __init__(self, base_manager, encryption_manager: EncryptionManager, 
                 privacy_manager: PrivacyManager):
        """Initialize secure memory manager.
        
        Args:
            base_manager: Base memory manager instance
            encryption_manager: Encryption manager instance
            privacy_manager: Privacy manager instance
        """
        self.base_manager = base_manager
        self.encryption = encryption_manager
        self.privacy = privacy_manager
        
        # Fields that should be encrypted
        self.encrypted_fields = ['content', 'context']
    
    async def store_memory(self, content: str, memory_type, tags=None, context=None):
        """Store a memory with encryption and privacy validation.
        
        Args:
            content: Memory content
            memory_type: Type of memory
            tags: Optional tags
            context: Optional context
            
        Returns:
            Memory ID if successful
        """
        # Validate privacy rules
        is_valid, error = self.privacy.validate_content(content)
        if not is_valid:
            raise ValueError(f"Privacy validation failed: {error}")
        
        is_valid, error = self.privacy.validate_context(context)
        if not is_valid:
            raise ValueError(f"Privacy validation failed: {error}")
        
        is_valid, error = self.privacy.validate_memory_type(memory_type.value if hasattr(memory_type, 'value') else str(memory_type))
        if not is_valid:
            raise ValueError(f"Privacy validation failed: {error}")
        
        # Sanitize content
        sanitized_content = self.privacy.sanitize_content(content)
        sanitized_context = self.privacy.sanitize_content(context) if context else None
        
        # Encrypt sensitive data
        encrypted_content = self.encryption.encrypt(sanitized_content)
        encrypted_context = self.encryption.encrypt(sanitized_context) if sanitized_context else None
        
        # Store using base manager
        return await self.base_manager.store_memory(
            content=encrypted_content,
            memory_type=memory_type,
            tags=tags,
            context=encrypted_context
        )
    
    async def get_memory_by_id(self, memory_id: int):
        """Get a memory by ID with decryption.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            Decrypted memory object
        """
        # Get encrypted memory
        memory = await self.base_manager.get_memory_by_id(memory_id)
        if not memory:
            return None
        
        # Decrypt sensitive fields
        if memory.content:
            memory.content = self.encryption.decrypt(memory.content)
        if memory.context:
            memory.context = self.encryption.decrypt(memory.context)
        
        return memory
    
    async def clear_expired_memories(self):
        """Clear memories that have exceeded the retention period."""
        if not self.privacy.retention_days:
            return 0  # No retention limit set
        
        from datetime import datetime, timedelta
        
        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=self.privacy.retention_days)
        
        # Get all memories
        all_memories = await self.base_manager.list_memories()
        
        expired_count = 0
        for memory in all_memories:
            if memory.created_at and memory.created_at < cutoff_date:
                await self.base_manager.delete_memory(memory.id)
                expired_count += 1
        
        if expired_count > 0:
            logger.info(f"Cleared {expired_count} expired memories")
        
        return expired_count
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get security and privacy status.
        
        Returns:
            Dictionary of security status
        """
        return {
            'encryption_enabled': self.encryption.enabled,
            'privacy_settings': self.privacy.get_privacy_settings(),
            'encrypted_fields': self.encrypted_fields
        }