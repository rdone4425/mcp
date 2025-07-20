"""
Unit tests for security and privacy features.
"""

import pytest
import pytest_asyncio
import os
from unittest.mock import AsyncMock, MagicMock

from src.security import EncryptionManager, PrivacyManager, SecureMemoryManager

class TestEncryptionManager:
    """Test encryption functionality."""
    
    def test_encryption_disabled(self):
        """Test encryption manager with no password (disabled)."""
        manager = EncryptionManager()
        
        assert not manager.enabled
        assert manager.get_salt() is None
        
        # Should return original data when disabled
        test_data = "sensitive information"
        assert manager.encrypt(test_data) == test_data
        assert manager.decrypt(test_data) == test_data
    
    def test_encryption_enabled(self):
        """Test encryption manager with password (enabled)."""
        password = "test_password_123"
        manager = EncryptionManager(password)
        
        assert manager.enabled
        assert manager.get_salt() is not None
        assert len(manager.get_salt()) == 16  # Salt should be 16 bytes
    
    def test_encrypt_decrypt_string(self):
        """Test string encryption and decryption."""
        password = "test_password_123"
        manager = EncryptionManager(password)
        
        original_data = "This is sensitive information"
        
        # Encrypt
        encrypted_data = manager.encrypt(original_data)
        assert encrypted_data != original_data
        assert len(encrypted_data) > len(original_data)  # Encrypted data should be longer
        
        # Decrypt
        decrypted_data = manager.decrypt(encrypted_data)
        assert decrypted_data == original_data
    
    def test_encrypt_decrypt_empty_string(self):
        """Test encryption of empty strings."""
        password = "test_password_123"
        manager = EncryptionManager(password)
        
        # Empty string should remain empty
        assert manager.encrypt("") == ""
        assert manager.decrypt("") == ""
        
        # None should remain None
        assert manager.encrypt(None) == None
        assert manager.decrypt(None) == None
    
    def test_encrypt_decrypt_dict(self):
        """Test dictionary field encryption and decryption."""
        password = "test_password_123"
        manager = EncryptionManager(password)
        
        original_dict = {
            'id': 1,
            'content': 'Sensitive content',
            'context': 'Sensitive context',
            'tags': ['secret', 'private'],
            'public_field': 'Not encrypted'
        }
        
        fields_to_encrypt = ['content', 'context', 'tags']
        
        # Encrypt
        encrypted_dict = manager.encrypt_dict(original_dict, fields_to_encrypt)
        
        assert encrypted_dict['id'] == original_dict['id']  # Not encrypted
        assert encrypted_dict['public_field'] == original_dict['public_field']  # Not encrypted
        assert encrypted_dict['content'] != original_dict['content']  # Encrypted
        assert encrypted_dict['context'] != original_dict['context']  # Encrypted
        assert encrypted_dict['tags'] != original_dict['tags']  # Encrypted
        
        # Decrypt
        decrypted_dict = manager.decrypt_dict(encrypted_dict, fields_to_encrypt)
        
        assert decrypted_dict['content'] == original_dict['content']
        assert decrypted_dict['context'] == original_dict['context']
        assert decrypted_dict['tags'] == original_dict['tags']
    
    def test_encryption_with_salt(self):
        """Test encryption with provided salt."""
        password = "test_password_123"
        salt = os.urandom(16)
        
        manager1 = EncryptionManager(password, salt)
        manager2 = EncryptionManager(password, salt)
        
        # Same password and salt should produce same encryption key
        test_data = "test data"
        encrypted1 = manager1.encrypt(test_data)
        encrypted2 = manager2.encrypt(test_data)
        
        # Both managers should be able to decrypt each other's data
        assert manager1.decrypt(encrypted2) == test_data
        assert manager2.decrypt(encrypted1) == test_data
    
    def test_encryption_different_passwords(self):
        """Test that different passwords produce different results."""
        manager1 = EncryptionManager("password1")
        manager2 = EncryptionManager("password2")
        
        test_data = "test data"
        encrypted1 = manager1.encrypt(test_data)
        encrypted2 = manager2.encrypt(test_data)
        
        # Different passwords should produce different encrypted data
        assert encrypted1 != encrypted2
        
        # Each manager should only decrypt its own data
        assert manager1.decrypt(encrypted1) == test_data
        assert manager2.decrypt(encrypted2) == test_data
        
        # Cross-decryption should fail
        with pytest.raises(Exception):
            manager1.decrypt(encrypted2)
        with pytest.raises(Exception):
            manager2.decrypt(encrypted1)

class TestPrivacyManager:
    """Test privacy management functionality."""
    
    def test_privacy_manager_initialization(self):
        """Test privacy manager initialization."""
        manager = PrivacyManager()
        
        assert 'content' in manager.sensitive_fields
        assert 'context' in manager.sensitive_fields
        assert len(manager.blocked_keywords) == 0
        assert manager.max_content_length == 10000
        assert manager.max_context_length == 1000
        assert manager.retention_days is None
    
    def test_blocked_keywords(self):
        """Test blocked keywords functionality."""
        manager = PrivacyManager()
        
        # Add blocked keywords
        manager.set_blocked_keywords(['password', 'secret', 'confidential'])
        assert len(manager.blocked_keywords) == 3
        assert 'password' in manager.blocked_keywords
        
        # Add individual keyword
        manager.add_blocked_keyword('private')
        assert 'private' in manager.blocked_keywords
        
        # Remove keyword
        manager.remove_blocked_keyword('password')
        assert 'password' not in manager.blocked_keywords
        assert len(manager.blocked_keywords) == 3
    
    def test_content_validation(self):
        """Test content validation."""
        manager = PrivacyManager()
        manager.set_blocked_keywords(['password', 'secret'])
        
        # Valid content
        is_valid, error = manager.validate_content("This is normal content")
        assert is_valid
        assert error is None
        
        # Empty content
        is_valid, error = manager.validate_content("")
        assert not is_valid
        assert "cannot be empty" in error
        
        # Content with blocked keyword
        is_valid, error = manager.validate_content("My password is 123456")
        assert not is_valid
        assert "blocked keyword" in error
        
        # Content too long
        long_content = "x" * 10001
        is_valid, error = manager.validate_content(long_content)
        assert not is_valid
        assert "too long" in error
    
    def test_context_validation(self):
        """Test context validation."""
        manager = PrivacyManager()
        manager.set_blocked_keywords(['secret'])
        
        # Valid context
        is_valid, error = manager.validate_context("Normal context")
        assert is_valid
        assert error is None
        
        # None context (should be valid)
        is_valid, error = manager.validate_context(None)
        assert is_valid
        assert error is None
        
        # Context with blocked keyword
        is_valid, error = manager.validate_context("This is secret information")
        assert not is_valid
        assert "blocked keyword" in error
        
        # Context too long
        long_context = "x" * 1001
        is_valid, error = manager.validate_context(long_context)
        assert not is_valid
        assert "too long" in error
    
    def test_memory_type_validation(self):
        """Test memory type validation."""
        manager = PrivacyManager()
        
        # Valid memory types
        for memory_type in ['fact', 'preference', 'conversation', 'note']:
            is_valid, error = manager.validate_memory_type(memory_type)
            assert is_valid
            assert error is None
        
        # Invalid memory type
        is_valid, error = manager.validate_memory_type('invalid_type')
        assert not is_valid
        assert "not allowed" in error
    
    def test_content_sanitization(self):
        """Test content sanitization."""
        manager = PrivacyManager()
        
        # Test email masking
        content = "Contact me at john.doe@example.com for more info"
        sanitized = manager.sanitize_content(content)
        assert "[EMAIL]" in sanitized
        assert "john.doe@example.com" not in sanitized
        
        # Test phone number masking
        content = "Call me at 555-123-4567 or (555) 123-4567"
        sanitized = manager.sanitize_content(content)
        assert "[PHONE]" in sanitized
        assert "555-123-4567" not in sanitized
        
        # Test credit card masking
        content = "My card number is 1234 5678 9012 3456"
        sanitized = manager.sanitize_content(content)
        assert "[CARD]" in sanitized
        assert "1234 5678 9012 3456" not in sanitized
        
        # Test SSN masking
        content = "SSN: 123-45-6789"
        sanitized = manager.sanitize_content(content)
        assert "[SSN]" in sanitized
        assert "123-45-6789" not in sanitized
    
    def test_retention_period(self):
        """Test retention period settings."""
        manager = PrivacyManager()
        
        # Initially no retention limit
        assert manager.retention_days is None
        
        # Set retention period
        manager.set_retention_period(30)
        assert manager.retention_days == 30
        
        # Disable retention limit
        manager.set_retention_period(None)
        assert manager.retention_days is None
    
    def test_sensitive_fields(self):
        """Test sensitive field identification."""
        manager = PrivacyManager()
        
        assert manager.should_encrypt_field('content')
        assert manager.should_encrypt_field('context')
        assert not manager.should_encrypt_field('id')
        assert not manager.should_encrypt_field('created_at')
    
    def test_privacy_settings(self):
        """Test privacy settings retrieval."""
        manager = PrivacyManager()
        manager.set_blocked_keywords(['test', 'secret'])
        manager.set_retention_period(30)
        
        settings = manager.get_privacy_settings()
        
        assert 'sensitive_fields' in settings
        assert 'allowed_memory_types' in settings
        assert settings['blocked_keywords_count'] == 2
        assert settings['max_content_length'] == 10000
        assert settings['max_context_length'] == 1000
        assert settings['retention_days'] == 30

class TestSecureMemoryManager:
    """Test secure memory manager integration."""
    
    @pytest_asyncio.fixture
    async def secure_manager(self):
        """Create a secure memory manager for testing."""
        # Create encryption and privacy managers
        encryption = EncryptionManager("test_password")
        privacy = PrivacyManager()
        
        # Create properly encrypted test data
        encrypted_content = encryption.encrypt("test content")
        encrypted_context = encryption.encrypt("test context")
        
        # Mock base manager
        base_manager = AsyncMock()
        base_manager.store_memory.return_value = 123
        base_manager.get_memory_by_id.return_value = MagicMock(
            id=123,
            content=encrypted_content,
            context=encrypted_context
        )
        
        # Create secure manager
        secure_manager = SecureMemoryManager(base_manager, encryption, privacy)
        
        return secure_manager, base_manager
    
    @pytest.mark.asyncio
    async def test_secure_store_memory(self, secure_manager):
        """Test secure memory storage."""
        manager, base_manager = secure_manager
        
        # Mock memory type
        memory_type = MagicMock()
        memory_type.value = "fact"
        
        # Store memory
        memory_id = await manager.store_memory(
            content="Sensitive information",
            memory_type=memory_type,
            tags=["test"],
            context="Test context"
        )
        
        assert memory_id == 123
        
        # Verify base manager was called with encrypted data
        base_manager.store_memory.assert_called_once()
        call_args = base_manager.store_memory.call_args
        
        # Content should be encrypted (different from original)
        assert call_args.kwargs['content'] != "Sensitive information"
        assert call_args.kwargs['context'] != "Test context"
    
    @pytest.mark.asyncio
    async def test_secure_get_memory(self, secure_manager):
        """Test secure memory retrieval."""
        manager, base_manager = secure_manager
        
        # Get memory
        memory = await manager.get_memory_by_id(123)
        
        assert memory is not None
        assert memory.content == "test content"  # Should be decrypted
        assert memory.context == "test context"  # Should be decrypted
        
        # Verify base manager was called
        base_manager.get_memory_by_id.assert_called_once_with(123)
    
    @pytest.mark.asyncio
    async def test_privacy_validation_failure(self, secure_manager):
        """Test privacy validation failure."""
        manager, base_manager = secure_manager
        
        # Set up privacy manager with blocked keywords
        manager.privacy.set_blocked_keywords(['secret'])
        
        memory_type = MagicMock()
        memory_type.value = "fact"
        
        # Try to store memory with blocked keyword
        with pytest.raises(ValueError, match="Privacy validation failed"):
            await manager.store_memory(
                content="This is secret information",
                memory_type=memory_type
            )
        
        # Base manager should not be called
        base_manager.store_memory.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_security_status(self, secure_manager):
        """Test security status retrieval."""
        manager, _ = secure_manager
        
        status = manager.get_security_status()
        
        assert 'encryption_enabled' in status
        assert 'privacy_settings' in status
        assert 'encrypted_fields' in status
        assert status['encryption_enabled'] is True
        assert 'content' in status['encrypted_fields']