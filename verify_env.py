"""
Verify .env file format and content
"""
import os
from dotenv import dotenv_values, load_dotenv

print("=" * 60)
print(".ENV FILE VERIFICATION")
print("=" * 60)

# Check file exists
env_path = os.path.join(os.getcwd(), ".env")
print(f"\n1. File Location: {env_path}")
print(f"   Exists: {os.path.exists(env_path)}")

if os.path.exists(env_path):
    # Read raw file
    with open(env_path, 'rb') as f:
        raw_content = f.read()
    
    print(f"\n2. File Properties:")
    print(f"   Size: {len(raw_content)} bytes")
    print(f"   Has BOM: {raw_content.startswith(b'\xef\xbb\xbf')}")
    
    # Read as text
    content = raw_content.decode('utf-8-sig')  # utf-8-sig handles BOM automatically
    lines = content.strip().split('\n')
    print(f"   Number of lines: {len(lines)}")
    
    print(f"\n3. File Content:")
    for i, line in enumerate(lines, 1):
        if '=' in line:
            key, value = line.split('=', 1)
            # Mask the value for security
            if value and value != "your-groundx-api-key-here" and value != "your-openrouter-api-key-here":
                masked_value = value[:10] + "..." + value[-5:] if len(value) > 15 else "***"
                print(f"   Line {i}: {key}={masked_value}")
            else:
                print(f"   Line {i}: {key}={value}")
        else:
            print(f"   Line {i}: {line}")
    
    # Use dotenv_values
    print(f"\n4. Parsed by python-dotenv:")
    env_vars = dotenv_values('.env')
    for key, value in env_vars.items():
        if value and value != "your-groundx-api-key-here" and value != "your-openrouter-api-key-here":
            masked_value = value[:10] + "..." + value[-5:] if len(value) > 15 else "***"
            print(f"   {key}: {masked_value} (length: {len(value)})")
        else:
            print(f"   {key}: {value} (PLACEHOLDER)")
    
    # Test loading
    print(f"\n5. Environment Loading Test:")
    load_dotenv(override=True)
    gx_key = os.getenv("GROUNDX_API_KEY")
    or_key = os.getenv("OPENROUTER_API_KEY")
    
    print(f"   GROUNDX_API_KEY loaded: {'YES' if gx_key else 'NO'}")
    if gx_key:
        if gx_key == "your-groundx-api-key-here":
            print(f"   Status: PLACEHOLDER VALUE")
        else:
            print(f"   Status: REAL VALUE (length: {len(gx_key)})")
    
    print(f"   OPENROUTER_API_KEY loaded: {'YES' if or_key else 'NO'}")
    if or_key:
        if or_key == "your-openrouter-api-key-here":
            print(f"   Status: PLACEHOLDER VALUE")
        else:
            print(f"   Status: REAL VALUE (length: {len(or_key)})")
    
    print(f"\n6. Format Check:")
    issues = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            issues.append(f"Line missing '=': {line}")
        elif line.startswith('='):
            issues.append(f"Line starts with '=': {line}")
        elif line.count('=') > 1 and not line.startswith('#'):
            # Check if it's a valid key=value (first = is the separator)
            key, value = line.split('=', 1)
            if not key.strip():
                issues.append(f"Empty key: {line}")
    
    if issues:
        print("   ⚠️  Issues found:")
        for issue in issues:
            print(f"      - {issue}")
    else:
        print("   ✅ Format is correct")

print("\n" + "=" * 60)


