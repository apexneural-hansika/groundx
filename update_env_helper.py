"""
Helper script to update .env file with API keys
"""
import os
import sys

def update_env_file():
    """Interactive helper to update .env file"""
    env_path = os.path.join(os.getcwd(), ".env")
    
    print("=" * 60)
    print("ENV FILE UPDATE HELPER")
    print("=" * 60)
    print(f"\n.env file location: {env_path}")
    
    if not os.path.exists(env_path):
        print("❌ .env file not found!")
        return
    
    # Read current content
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print("\nCurrent .env content:")
    for i, line in enumerate(lines, 1):
        if '=' in line and not line.strip().startswith('#'):
            key, value = line.split('=', 1)
            if 'API_KEY' in key:
                # Mask the value
                if value.strip() in ['your-groundx-api-key-here', 'your-openrouter-api-key-here']:
                    print(f"  Line {i}: {key.strip()}={value.strip()} (PLACEHOLDER)")
                else:
                    masked = value.strip()[:10] + "..." + value.strip()[-5:] if len(value.strip()) > 15 else "***"
                    print(f"  Line {i}: {key.strip()}={masked} (REAL VALUE)")
            else:
                print(f"  Line {i}: {line.strip()}")
        else:
            print(f"  Line {i}: {line.strip()}")
    
    print("\n" + "=" * 60)
    print("To update your API keys:")
    print("=" * 60)
    print("\n1. Open the .env file in a text editor:")
    print(f"   {env_path}")
    print("\n2. Replace the placeholder values:")
    print("   GROUNDX_API_KEY=your-groundx-api-key-here")
    print("   → GROUNDX_API_KEY=sk_live_...your-actual-key...")
    print("\n   OPENROUTER_API_KEY=your-openrouter-api-key-here")
    print("   → OPENROUTER_API_KEY=sk-or-...your-actual-key...")
    print("\n3. Save the file")
    print("4. In the Streamlit app, click '🔄 Reload API Keys' button")
    print("\n" + "=" * 60)
    
    # Check if still using placeholders
    has_placeholders = False
    for line in lines:
        if 'your-groundx-api-key-here' in line or 'your-openrouter-api-key-here' in line:
            has_placeholders = True
            break
    
    if has_placeholders:
        print("\n⚠️  WARNING: Your .env file still contains placeholder values!")
        print("   Please update them with your actual API keys.")
    else:
        print("\n✅ Your .env file appears to have real API keys!")
        print("   If you're still seeing errors, try:")
        print("   1. Click '🔄 Reload API Keys' in the app")
        print("   2. Refresh the browser page")
        print("   3. Restart the Streamlit app")

if __name__ == "__main__":
    update_env_file()


