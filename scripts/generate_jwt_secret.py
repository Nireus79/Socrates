#!/usr/bin/env python3
"""
Generate a strong JWT secret key for production use.

Generates cryptographically secure random secret keys suitable for JWT signing.
Provides multiple formats: hex, base64, and raw.

Usage:
    python scripts/generate_jwt_secret.py
    python scripts/generate_jwt_secret.py --format base64
    python scripts/generate_jwt_secret.py --length 64

The secret can be used in:
    JWT_SECRET_KEY={generated_secret}
"""

import os
import sys
import argparse
import secrets
import base64
from pathlib import Path


def generate_jwt_secret(length: int = 32, format_type: str = "hex") -> str:
    """
    Generate a cryptographically secure JWT secret.

    Args:
        length: Secret length in bytes (default: 32)
        format_type: Output format - 'hex', 'base64', or 'raw'

    Returns:
        Generated secret in requested format
    """
    # Generate random bytes
    random_bytes = secrets.token_bytes(length)

    # Format based on request
    if format_type == "hex":
        return random_bytes.hex()
    elif format_type == "base64":
        return base64.b64encode(random_bytes).decode("utf-8")
    elif format_type == "raw":
        return random_bytes.decode("utf-8", errors="ignore")
    else:
        raise ValueError(f"Invalid format: {format_type}. Use 'hex', 'base64', or 'raw'")


def validate_secret(secret: str) -> bool:
    """
    Validate JWT secret meets minimum requirements.

    Args:
        secret: Secret to validate

    Returns:
        True if secret is valid
    """
    # Minimum 32 bytes (256 bits) for HS256/HS384/HS512
    # Hex format: 64 characters (32 bytes)
    # Base64 format: ~44 characters (32 bytes)
    if len(secret) < 32:
        return False
    return True


def save_to_env(secret: str, env_file: str = ".env.production") -> bool:
    """
    Save secret to environment file.

    Args:
        secret: Secret to save
        env_file: Environment file path

    Returns:
        True if successful
    """
    env_path = Path(env_file)

    # Read existing content
    content = ""
    if env_path.exists():
        with open(env_path, "r") as f:
            content = f.read()

    # Remove existing JWT_SECRET_KEY if present
    lines = content.split("\n")
    lines = [line for line in lines if not line.startswith("JWT_SECRET_KEY=")]

    # Add new secret
    lines.append(f"JWT_SECRET_KEY={secret}")

    # Write back
    with open(env_path, "w") as f:
        f.write("\n".join(lines))

    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate a strong JWT secret key for production use"
    )
    parser.add_argument(
        "--length",
        type=int,
        default=32,
        help="Secret length in bytes (default: 32)",
    )
    parser.add_argument(
        "--format",
        choices=["hex", "base64", "raw"],
        default="hex",
        help="Output format (default: hex)",
    )
    parser.add_argument(
        "--save",
        metavar="FILE",
        help="Save secret to environment file",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate an existing secret",
    )

    args = parser.parse_args()

    if args.validate:
        # Validate mode
        secret = input("Enter JWT secret to validate: ")
        if validate_secret(secret):
            print("✓ Secret is valid")
            print(f"  Length: {len(secret)} characters")
            return 0
        else:
            print("✗ Secret is invalid (too short)")
            print(f"  Length: {len(secret)} characters (minimum: 32)")
            return 1

    # Generate mode
    print("Generating JWT secret key...")
    secret = generate_jwt_secret(length=args.length, format_type=args.format)

    # Validate generated secret
    if not validate_secret(secret):
        print(f"✗ Generated secret validation failed")
        return 1

    print(f"✓ Secret generated successfully")
    print(f"  Format: {args.format}")
    print(f"  Length: {len(secret)} characters")
    print()
    print("Generated secret:")
    print("-" * 80)
    print(secret)
    print("-" * 80)
    print()

    # Save to file if requested
    if args.save:
        try:
            save_to_env(secret, args.save)
            print(f"✓ Secret saved to {args.save}")
        except Exception as e:
            print(f"✗ Failed to save secret: {e}")
            return 1

    print()
    print("⚠️  Keep this secret secure and never commit it to version control!")
    print("Add to your .env.production file:")
    print(f"  JWT_SECRET_KEY={secret}")
    print()
    print("To use in your application:")
    print("  export JWT_SECRET_KEY=<generated_secret>")
    print("  python socrates.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
