"""
Secrets Manager - Abstraction layer for secure secret storage
Supports Azure Key Vault, AWS Secrets Manager, and fallback to environment variables
"""
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Auto-load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        logger.info("Loaded .env file")
except ImportError:
    pass

# Secret storage backend configuration
SECRET_BACKEND = os.environ.get("SECRET_BACKEND", "env").lower()  # "azure", "aws", or "env"

def get_secret(secret_name: str, default: str = "") -> str:
    """
    Retrieve secret from configured backend
    Priority: Azure Key Vault > AWS Secrets Manager > Environment Variable
    """
    try:
        if SECRET_BACKEND == "azure":   # nosec B105 
            return _get_azure_secret(secret_name, default)
        elif SECRET_BACKEND == "aws":   # nosec B105 
            return _get_aws_secret(secret_name, default)
        else:
            return os.environ.get(secret_name, default)
    except Exception:
        logger.warning("Secret retrieval failed — falling back to env var")
        return os.environ.get(secret_name, default)

def _get_azure_secret(secret_name: str, default: str) -> str:
    """Retrieve secret from Azure Key Vault"""
    try:
        from azure.keyvault.secrets import SecretClient
        from azure.identity import DefaultAzureCredential
        
        vault_url = os.environ.get("AZURE_KEY_VAULT_URL")
        if not vault_url:
            raise ValueError("AZURE_KEY_VAULT_URL not configured")
        
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=vault_url, credential=credential)
        secret = client.get_secret(secret_name)
        logger.info("Retrieved secret from Azure Key Vault")
        return secret.value
    except Exception as e:
        logger.error("Azure Key Vault error — check credentials")
        raise

def _get_aws_secret(secret_name: str, default: str) -> str:
    """Retrieve secret from AWS Secrets Manager"""
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        region = os.environ.get("AWS_REGION", "us-east-1")
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region
        )
        
        response = client.get_secret_value(SecretId=secret_name)
        logger.info("Retrieved secret from AWS Secrets Manager")
        
        if 'SecretString' in response:
            return response['SecretString']
        else:
            import base64
            return base64.b64decode(response['SecretBinary']).decode('utf-8')
    except ClientError as e:
        logger.error("AWS Secrets Manager error — check credentials")
        raise

def rotate_secret(secret_name: str, new_value: str) -> bool:
    """
    Rotate a secret (update to new value)
    Returns True on success, False on failure
    """
    try:
        if SECRET_BACKEND == "azure": # nosec B105 
            return _rotate_azure_secret(secret_name, new_value)
        elif SECRET_BACKEND == "aws": # nosec B105 
            return _rotate_aws_secret(secret_name, new_value)
        else:
            logger.warning("Secret rotation not supported for env backend")
            return False
    except Exception:
        logger.error("Secret rotation failed")
        return False

def _rotate_azure_secret(secret_name: str, new_value: str) -> bool:
    """Rotate secret in Azure Key Vault"""
    try:
        from azure.keyvault.secrets import SecretClient
        from azure.identity import DefaultAzureCredential
        
        vault_url = os.environ.get("AZURE_KEY_VAULT_URL")
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=vault_url, credential=credential)
        client.set_secret(secret_name, new_value)
        logger.info("Rotated secret in Azure Key Vault")
        return True
    except Exception:
        logger.error("Azure Key Vault rotation error")
        return False

def _rotate_aws_secret(secret_name: str, new_value: str) -> bool:
    """Rotate secret in AWS Secrets Manager"""
    try:
        import boto3
        
        region = os.environ.get("AWS_REGION", "us-east-1")
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region
        )
        
        client.update_secret(SecretId=secret_name, SecretString=new_value)
        logger.info("Rotated secret in AWS Secrets Manager")
        return True
    except Exception:
        logger.error("AWS Secrets Manager rotation error")
        return False
