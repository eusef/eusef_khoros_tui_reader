"""
1Password SDK Configuration Module
Handles authentication and secret retrieval using the 1Password SDK with local authentication.
"""
import os
import asyncio
from typing import Optional, Dict
try:
    import tomllib  # Python 3.11+
except Exception:
    tomllib = None

# Import nest_asyncio to allow asyncio.run() from within async contexts
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass  # Will handle async contexts differently if not available

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
                # Try common alternative field names automatically
                # Parse the reference to extract vault/item/field
                parts = ref[5:].split("/")
                if len(parts) >= 3:
                    vault = parts[0]
                    item = parts[1]
                    original_field = parts[2]
                    
                    # Map common field name alternatives
                    field_alternatives = {
                        "login": ["username", "email", "credential"],
                        "user": ["username", "email", "login", "credential"],
                        "pass": ["password", "credential"],
                        "pwd": ["password", "credential"],
                        "password": ["credential", "pass", "pwd"],
                        "app-password": ["password", "credential", "app password", "app_password"],
                        "app_password": ["password", "credential", "app-password", "app password"],
                        "app password": ["password", "credential", "app-password", "app_password"],
                        "token": ["credential", "access token", "access_token", "password"],
                        "access-token": ["token", "credential", "access_token", "access token"],
                        "access_token": ["token", "credential", "access-token", "access token"],
                        "access token": ["token", "credential", "access_token", "access-token"],
                        "credential": ["username", "password", "email"],
                    }
                    
                    # Get alternatives for the original field name (case-insensitive)
                    alternatives = field_alternatives.get(original_field.lower(), [])
                    
                    # Also try common field names if no specific mapping exists
                    if not alternatives:
                        common_fields = ["username", "password", "email", "credential"]
                        if original_field.lower() not in [f.lower() for f in common_fields]:
                            alternatives = common_fields
                    
                    # Try each alternative
                    for alt_field in alternatives:
                        alt_ref = f"op://{vault}/{item}/{alt_field}"
                        try:
                            alt_value = await client.secrets.resolve(alt_ref)
                            print(f"Warning: Field '{original_field}' not found, but found alternative field '{alt_field}'")
                            print(f"  Consider updating your .env.template to use: {alt_ref}")
                            return alt_value
                        except Exception:
                            continue  # Try next alternative
                    
                    # No alternatives worked, show helpful error
                    print(f"Warning: Field not found in 1Password item for reference: {ref}")
                    print(f"  Error details: {error_msg}")
                    if alternatives:
                        print(f"  Tried alternatives: {', '.join(alternatives)}")
                    print(f"  Tip: Common field names are 'username', 'password', 'email', or 'credential'")
                    print(f"  Try using one of these field names instead in your .env.template file")
                else:
                    print(f"Warning: Field not found in 1Password item for reference: {ref}")
                    print(f"  Error details: {error_msg}")
                    print(f"  Tip: Common field names are 'username', 'password', 'email', or 'credential'")
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
    # Use asyncio.run() to execute async code
    # nest_asyncio allows this to work even from within async contexts
    return asyncio.run(_get_secret_from_1password_async(ref))


def _flatten_toml_config(config_toml: Dict) -> Dict[str, str]:
    """Flatten structured TOML config into legacy flat keys used by get_config_value."""
    flattened: Dict[str, str] = {}
    # 1Password
    op_cfg = config_toml.get("onepassword", {}) if isinstance(config_toml, dict) else {}
    account_name = op_cfg.get("account_name")
    if account_name:
        # Also set env to help SDK initialization
        os.environ["ONEPASSWORD_ACCOUNT_NAME"] = str(account_name)
        flattened["ONEPASSWORD_ACCOUNT_NAME"] = str(account_name)

    # Khoros
    kh = config_toml.get("khoros", {})
    if isinstance(kh, dict):
        if kh.get("hostname"): flattened["hostname"] = str(kh["hostname"])
        if kh.get("tapestry"): flattened["tapestry"] = str(kh["tapestry"])
        if kh.get("username"): flattened["username"] = str(kh["username"])
        if kh.get("password"): flattened["password"] = str(kh["password"])

    # BlueSky
    bs = config_toml.get("bluesky", {})
    if isinstance(bs, dict):
        if bs.get("handle"): flattened["BLUESKY_HANDLE"] = str(bs["handle"])
        if bs.get("app_password"): flattened["BLUESKY_APP_PASSWORD"] = str(bs["app_password"]) 

    # Mastodon
    md = config_toml.get("mastodon", {})
    if isinstance(md, dict):
        if md.get("server"): flattened["MASTODON_SERVER"] = str(md["server"]) 
        if md.get("access_token"): flattened["MASTODON_ACCESS_TOKEN"] = str(md["access_token"]) 

    # Gemini
    gm = config_toml.get("gemini", {})
    if isinstance(gm, dict):
        if gm.get("api_key"): flattened["GEMINI_API_KEY"] = str(gm["api_key"]) 

    return flattened


def load_config_from_toml(config_path: str = "config.toml") -> Dict[str, str]:
    """
    Load configuration from config.toml, resolving 1Password references.
    Returns a flat dict of keys for compatibility with existing code.
    """
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    config: Dict[str, str] = {}
    if not os.path.exists(config_path):
        return config
    if tomllib is None:
        print("Warning: tomllib not available; cannot read config.toml. Using .env.template fallback if present.")
        return config

    try:
        with open(config_path, "rb") as f:
            parsed = tomllib.load(f)

        # Flatten into legacy keys used across the app
        flat = _flatten_toml_config(parsed)

        # Resolve 1Password account name first if provided and not an op:// ref
        if flat.get("ONEPASSWORD_ACCOUNT_NAME") and not str(flat["ONEPASSWORD_ACCOUNT_NAME"]).startswith("op://"):
            os.environ["ONEPASSWORD_ACCOUNT_NAME"] = flat["ONEPASSWORD_ACCOUNT_NAME"]

        # Resolve op:// references
        for k, v in list(flat.items()):
            if isinstance(v, str) and v.startswith("op://"):
                resolved = get_secret_from_1password(v)
                if resolved:
                    config[k] = resolved
                else:
                    print(f"Warning: Could not resolve 1Password reference for {k}: {v}")
            else:
                if v:
                    config[k] = v

        _config_cache = config
        print(f"Loaded {len(config)} configuration values from {config_path}")
        return config
    except Exception as e:
        print(f"Error loading configuration from {config_path}: {e}")
        return config


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
    
    This function prioritizes config.toml over environment variables,
    providing a single source of truth for configuration.
    
    Args:
        key: Configuration key name
        default: Default value if key is not found
        
    Returns:
        Configuration value or default
    """
    # Load config from file first: prefer config.toml, fallback to .env.template
    # This ensures config.toml is the source of truth
    config = load_config_from_toml()
    if not config:
        config = load_config_from_env_template()
    
    # Return from config cache if found
    if key in config:
        return config[key]
    
    # Only check environment variables as a fallback if not in config file
    # (This handles cases where someone sets env vars manually)
    value = os.getenv(key)
    if value:
        # If the env var contains an op:// reference, resolve it
        # (nest_asyncio allows this to work even in async contexts)
        if isinstance(value, str) and value.startswith("op://"):
            resolved = get_secret_from_1password(value)
            if resolved:
                return resolved
            # If resolution fails, fall through to default
        else:
            return value
    
    # Return default if not found anywhere
    return default


def clear_config_cache():
    """Clear the configuration cache (useful for testing or reloading config)."""
    global _config_cache
    _config_cache = None


async def _close_op_client_async():
    """Close the 1Password client properly (async)."""
    global _op_client
    if _op_client is not None:
        try:
            # The 1Password SDK client should be closed to clean up resources
            # Check if the client has a close method
            if hasattr(_op_client, 'close'):
                await _op_client.close()
            elif hasattr(_op_client, '__aexit__'):
                await _op_client.__aexit__(None, None, None)
        except Exception as e:
            print(f"Warning: Error closing 1Password client: {e}")
        finally:
            _op_client = None


def clear_op_client():
    """Clear the 1Password client (useful for testing or re-authentication)."""
    global _op_client
    if _op_client is not None:
        try:
            asyncio.run(_close_op_client_async())
        except Exception as e:
            print(f"Warning: Could not properly close 1Password client: {e}")
            _op_client = None
    else:
        _op_client = None
