#!/usr/bin/env python3
"""
Utility script to generate an encryption key for the RAG chatbot.
"""

from cryptography.fernet import Fernet


def main():
    """Generate and display a new encryption key."""
    print("RAG Chatbot - Encryption Key Generator")
    print("=" * 40)
    
    # Generate a new Fernet key
    key = Fernet.generate_key()
    
    print(f"\nGenerated encryption key: {key.decode()}")
    print("\nTo use this key:")
    print("1. Add it to your .env file as:")
    print(f"   ENCRYPTION_KEY={key.decode()}")
    print("\n2. Or export it as an environment variable:")
    print(f"   export ENCRYPTION_KEY={key.decode()}")
    
    print("\n⚠️  SECURITY NOTES:")
    print("- Keep this key secure and never commit it to version control")
    print("- Store it securely in your production environment")
    print("- If you lose this key, encrypted API keys cannot be recovered")
    print("- Generate a new key for each environment (dev, staging, prod)")


if __name__ == "__main__":
    main()