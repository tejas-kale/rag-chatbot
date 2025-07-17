# API Key Encryption Documentation

This document describes the encryption implementation for securely storing API keys in the RAG chatbot application.

## Overview

The application uses **Fernet symmetric encryption** from the `cryptography` library to securely store sensitive information like LLM API keys in the SQLite database. This ensures that even if the database is compromised, the API keys remain protected.

## Features

- **Automatic encryption/decryption**: API keys are automatically encrypted before storage and decrypted when retrieved
- **Environment-based key management**: The encryption key is stored in environment variables, never hardcoded
- **Error handling**: Graceful handling of missing keys or invalid encrypted data
- **Backward compatibility**: Existing code can use the persistence manager without changes

## Setup

### 1. Generate an Encryption Key

Use the provided utility script to generate a secure encryption key:

```bash
python generate_encryption_key.py
```

This will output a base64-encoded key that you should store securely.

### 2. Configure Environment

Add the encryption key to your environment:

**Option A: Using .env file**
```env
ENCRYPTION_KEY=your-generated-key-here
```

**Option B: Environment variable**
```bash
export ENCRYPTION_KEY=your-generated-key-here
```

## Usage

### Using the PersistenceManager

```python
from persistence_service import PersistenceManager

# Create persistence manager
pm = PersistenceManager()

# Store encrypted API keys for a user
api_keys = {
    "openai": "sk-your-openai-key",
    "anthropic": "sk-ant-your-key",
    "google": "your-google-key"
}

# Set API keys (automatically encrypted)
success = pm.set_api_keys("user_id", api_keys)

# Get API keys (automatically decrypted)
retrieved_keys = pm.get_api_keys("user_id")
```

### Direct Encryption/Decryption

```python
# Encrypt data
encrypted_data = pm.encrypt_key({"openai": "sk-key"})

# Decrypt data
decrypted_data = pm.decrypt_key(encrypted_data)
```

## Database Schema

The `user_settings` table stores encrypted API keys in the `api_keys` column as `LargeBinary` data:

```sql
CREATE TABLE user_settings (
    id INTEGER PRIMARY KEY,
    user_id VARCHAR(100),
    api_keys BLOB,  -- Encrypted JSON data
    custom_prompts TEXT,
    created_at DATETIME,
    updated_at DATETIME
);
```

## Security Considerations

### Key Management
- **Generate unique keys** for each environment (development, staging, production)
- **Store keys securely** using your deployment platform's secrets management
- **Never commit keys** to version control
- **Rotate keys periodically** and update encrypted data accordingly

### Data Protection
- Encrypted data cannot be decrypted without the correct key
- If the encryption key is lost, encrypted API keys cannot be recovered
- The application gracefully handles missing or invalid encryption keys

## Error Handling

The encryption system includes comprehensive error handling:

- **Missing encryption key**: Operations return `None` and log warnings
- **Invalid encrypted data**: Decryption returns `None` and logs errors
- **Encryption failures**: Operations return `None` and log errors

## Testing

Run the encryption tests to verify functionality:

```bash
# Run unit tests
python -m pytest test_encryption.py -v

# Generate a test key
python generate_encryption_key.py
```

## Implementation Details

### Encryption Flow
1. API keys dictionary → JSON string → UTF-8 bytes → Fernet encryption → Binary storage
2. Binary storage → Fernet decryption → UTF-8 bytes → JSON string → Dictionary

### Key Features
- Uses **Fernet symmetric encryption** (AES 128 in CBC mode with HMAC SHA256)
- **Authenticated encryption** prevents tampering
- **Random IV/nonce** for each encryption operation
- **Base64-encoded keys** for easy storage in environment variables

### Performance
- Encryption/decryption is fast for typical API key data sizes
- Keys are cached in the PersistenceManager instance for efficiency
- No significant impact on database operations

## Migration

Existing installations can migrate to encrypted storage:

1. Generate and configure an encryption key
2. Retrieve existing API keys (if any)
3. Re-save them using the new encrypted methods
4. Old unencrypted data will be replaced automatically

The application handles both encrypted and unencrypted data gracefully during the transition period.