"""
1Password SDK Configuration Module
Handles authentication and secret retrieval using the 1Password SDK with local authentication.
"""
import os
import asyncio
from typing import Optional, Dict

# Cache for the 1Password client
_op_client = None

# Cache for parsed configuration
_config_cache: Optional[Dict[str, str]] = None

# Lock for async client initialization
_client_lock = asyncio.Lock()

async def _get_op_client_async():
    """
    Get or create the 1Password SDK client with local authentication (async).
    
    Returns:
        1Password SDK client instance
        
    Raises:
        Exception: If client creation or authentication fails
    """
    global _op_client
    
    if _op_client is not None:
        return _op_client
    
    async with _client_lock:
        # Double-check after acquiring lock
        if _op_client is not None:
            return _op_client
        
        try:
            # Import here to handle ImportError gracefully
            try:
                from onepassword import Client, DesktopAuth
            except ImportError:
                raise Exception("1Password SDK not installed. Run: pip install onepassword-sdk")
            
            # Get the account name from environment variable
            # The account name should match what appears in the 1Password desktop app sidebar
            # If not set, try with empty string - the desktop app may prompt or auto-select
            account_name = os.getenv("ONEPASSWORD_ACCOUNT_NAME", "")
            
            # Create DesktopAuth - empty string will let the desktop app handle account selection
            auth = DesktopAuth(account_name)
            
            # Authenticate using the Client.authenticate class method
            _op_client = await Client.authenticate(
                auth=auth,
                integration_name="Khoros TUI Reader",
                integration_version="1.0.0"
            )
            
            print("1Password SDK client initialized successfully")
            return _op_client
            
        except Exception as e:
            error_msg = str(e)
            raise Exception(f"Failed to initialize 1Password SDK client: {e}")


def get_op_client():
    """
    Get or create the 1Password SDK client with local authentication (sync wrapper).
    
    Returns:
        1Password SDK client instance
        
    Raises:
        Exception: If client creation or authentication fails
    """
    # Use asyncio.run() to execute async code from sync context
    # This will work as long as we're not already in an async context
    try:
        loop = asyncio.get_running_loop()
        # If we're in an async context, we can't use asyncio.run()
        # This shouldn't happen in our use case, but handle it gracefully
        raise RuntimeError(
            "Cannot initialize 1Password client from async context. "
            "Use _get_op_client_async() instead."
        )
    except RuntimeError:
        # No running loop, safe to use asyncio.run()
        return asyncio.run(_get_op_client_async())


async def _get_secret_from_1password_async(ref: str) -> Optional[str]:
    """
    Retrieve a secret from 1Password using the SDK (async).
    
    Args:
        ref: 1Password reference (e.g., "op://Private/Khoros/username")
        
    Returns:
        Secret value or None if not found
    """
    try:
        client = await _get_op_client_async()
        
        if not ref.startswith("op://"):
            print(f"Warning: Invalid 1Password reference format: {ref}")
            return None
        
        # Use the secrets.resolve() method which takes the full op:// reference
        try:
            secret_value = await client.secrets.resolve(ref)
            return secret_value
        except Exception as resolve_error:
            error_msg = str(resolve_error)
            error_lower = error_msg.lower()
            
            # Check if it's a field not found error
            if "field cannot be found" in error_lower or "field not found" in error_lower:
                print(f"Warning: Field not found in 1Password item for reference: {ref}")
                print(f"  Error details: {error_msg}")
                print(f"  Tip: Common field names are 'username', 'password', 'email', or 'credential'")
                print(f"  Try using one of these field names instead in your .env.template file")
            elif "not found" in error_lower or "does not exist" in error_lower:
                print(f"Warning: Item or vault not found in 1Password for reference: {ref}")
            else:
                print(f"Error resolving secret from 1Password for '{ref}': {resolve_error}")
            return None
        
    except Exception as e:
        print(f"Error retrieving secret from 1Password for '{ref}': {e}")
        return None


def get_secret_from_1password(ref: str) -> Optional[str]:
    """
    Retrieve a secret from 1Password using the SDK (sync wrapper).
    
    Args:
        ref: 1Password reference (e.g., "op://Private/Khoros/username")
        
    Returns:
        Secret value or None if not found
    """
    # Use asyncio.run() to execute async code from sync context
    try:
        asyncio.get_running_loop()
        # If we're in an async context, we can't use asyncio.run()
        raise RuntimeError(
            "Cannot retrieve secret from async context. "
            "Use _get_secret_from_1password_async() instead."
        )
    except RuntimeError:
        # No running loop, safe to use asyncio.run()
        return asyncio.run(_get_secret_from_1password_async(ref))


def load_config_from_env_template(template_path: str = ".env.template") -> Dict[str, str]:
    """
    Load configuration from .env.template file, resolving 1Password references.
    
    This function also sets ONEPASSWORD_ACCOUNT_NAME in the environment if it's
    found in the template, so the SDK can use it during initialization.
    
    Args:
        template_path: Path to the .env.template file
        
    Returns:
        Dictionary mapping environment variable names to their values
    """
    global _config_cache
    
    if _config_cache is not None:
        return _config_cache
    
    config = {}
    
    if not os.path.exists(template_path):
        print(f"Warning: .env.template file not found at {template_path}")
        return config
    
    try:
        # First pass: Load ONEPASSWORD_ACCOUNT_NAME from template and set it in environment
        # This must be done BEFORE resolving any 1Password references
        with open(template_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse KEY=VALUE format
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Special handling for ONEPASSWORD_ACCOUNT_NAME - set it immediately
                    # so it's available when resolving 1Password references
                    if key == "ONEPASSWORD_ACCOUNT_NAME" and value and not value.startswith("op://"):
                        os.environ[key] = value
                        config[key] = value
        
        # Second pass: Resolve 1Password references now that account name is set
        with open(template_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse KEY=VALUE format
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Skip ONEPASSWORD_ACCOUNT_NAME as we already processed it in first pass
                    if key == "ONEPASSWORD_ACCOUNT_NAME":
                        continue
                    
                    # Check if value is a 1Password reference
                    if value.startswith("op://"):
                        # Resolve from 1Password
                        secret_value = get_secret_from_1password(value)
                        if secret_value:
                            config[key] = secret_value
                        else:
                            print(f"Warning: Could not resolve 1Password reference for {key}: {value}")
                    else:
                        # Use value as-is (could be empty or a literal value)
                        if value:  # Only set non-empty values
                            config[key] = value
        
        _config_cache = config
        print(f"Loaded {len(config)} configuration values from {template_path}")
        return config
        
    except Exception as e:
        print(f"Error loading configuration from {template_path}: {e}")
        return config


def get_config_value(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get a configuration value, resolving 1Password references as needed.
    
    This function provides a drop-in replacement for os.getenv() that
    automatically resolves 1Password references.
    
    Args:
        key: Configuration key name
        default: Default value if key is not found
        
    Returns:
        Configuration value or default
    """
    # First check environment variables (in case they're set explicitly)
    value = os.getenv(key)
    if value:
        return value
    
    # Load config from template if not already loaded
    config = load_config_from_env_template()
    
    # Return from config cache
    return config.get(key, default)


def clear_config_cache():
    """Clear the configuration cache (useful for testing or reloading config)."""
    global _config_cache
    _config_cache = None


def clear_op_client():
    """Clear the 1Password client (useful for testing or re-authentication)."""
    global _op_client
    _op_client = None
