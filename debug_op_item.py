#!/usr/bin/env python3
"""
Debug script to inspect a 1Password item and see what fields are available.
Usage: python debug_op_item.py "op://TUI_Reader/v5altvci6cnslgjwz4xuxcfvfa"
"""
import sys
import asyncio
from onepassword import Client, DesktopAuth
import os

async def inspect_item(ref: str):
    """Inspect a 1Password item and show its structure."""
    try:
        account_name = os.getenv("ONEPASSWORD_ACCOUNT_NAME", "")
        auth = DesktopAuth(account_name)
        client = await Client.authenticate(
            auth=auth,
            integration_name="Khoros TUI Reader Debug",
            integration_version="1.0.0"
        )
        
        # Parse the reference
        if not ref.startswith("op://"):
            ref = f"op://{ref}"
        
        # Extract vault and item
        parts = ref[5:].split("/")
        if len(parts) < 2:
            print("Invalid reference format. Expected: op://vault/item")
            return
        
        vault_name = parts[0]
        item_identifier = parts[1]
        
        print(f"Inspecting item in vault '{vault_name}': {item_identifier}\n")
        
        # Get the item
        try:
            item = await client.items.get(vault_name, item_identifier)
            
            print(f"Item Title: {item.overview.title}")
            print(f"Item Category: {item.overview.category}")
            print(f"\nFields found in this item:\n")
            
            if hasattr(item, 'fields') and item.fields:
                for i, field in enumerate(item.fields, 1):
                    field_id = getattr(field, 'id', 'N/A')
                    field_label = getattr(field, 'label', 'N/A')
                    field_type = getattr(field, 'type', 'N/A')
                    field_value = getattr(field, 'value', None)
                    
                    # Don't show password values, just indicate they exist
                    if field_type == 'P' or field_label and 'password' in field_label.lower():
                        value_preview = "[PASSWORD - hidden]"
                    else:
                        if isinstance(field_value, list):
                            value_preview = str(field_value[:1]) if field_value else "[]"
                        else:
                            value_preview = str(field_value)[:50] if field_value else "None"
                    
                    print(f"  {i}. Label: {field_label}")
                    print(f"     ID: {field_id}")
                    print(f"     Type: {field_type}")
                    print(f"     Value: {value_preview}")
                    print()
            else:
                print("  No fields found in this item")
            
            # Try to resolve the original reference to see what error we get
            print("\n" + "="*60)
            print("Testing field access:")
            print("="*60)
            
            # Try common field names
            for field_name in ["login", "username", "email", "password"]:
                test_ref = f"op://{vault_name}/{item_identifier}/{field_name}"
                try:
                    value = await client.secrets.resolve(test_ref)
                    print(f"✓ '{field_name}' exists: {value[:20] if len(str(value)) > 20 else value}...")
                except Exception as e:
                    error_msg = str(e)
                    if "cannot be found" in error_msg.lower():
                        print(f"✗ '{field_name}' not found")
                    else:
                        print(f"✗ '{field_name}': {error_msg}")
                        
        except Exception as e:
            print(f"Error accessing item: {e}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        ref = "op://TUI_Reader/v5altvci6cnslgjwz4xuxcfvfa"
        print(f"No reference provided, using default: {ref}\n")
    else:
        ref = sys.argv[1]
    
    asyncio.run(inspect_item(ref))

