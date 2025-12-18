"""
Test script to verify API key loading and test Ground X API connection
"""
import os
import sys
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

def test_env_loading():
    """Test if environment variables are loaded correctly"""
    print("=" * 60)
    print("ENVIRONMENT VARIABLE CHECK")
    print("=" * 60)
    
    gx_key = os.getenv("GROUNDX_API_KEY")
    or_key = os.getenv("OPENROUTER_API_KEY")
    
    print(f"\n1. GROUNDX_API_KEY:")
    if not gx_key:
        print("   ❌ NOT FOUND - Key is None or empty")
    elif gx_key == "your-groundx-api-key-here":
        print("   ⚠️  PLACEHOLDER VALUE - Still using placeholder")
        print(f"   Value: {gx_key[:20]}...")
    else:
        print("   ✅ FOUND")
        print(f"   Length: {len(gx_key)} characters")
        print(f"   Starts with: {gx_key[:10]}...")
        print(f"   Ends with: ...{gx_key[-5:]}")
    
    print(f"\n2. OPENROUTER_API_KEY:")
    if not or_key:
        print("   ❌ NOT FOUND - Key is None or empty")
    elif or_key == "your-openrouter-api-key-here":
        print("   ⚠️  PLACEHOLDER VALUE - Still using placeholder")
        print(f"   Value: {or_key[:20]}...")
    else:
        print("   ✅ FOUND")
        print(f"   Length: {len(or_key)} characters")
        print(f"   Starts with: {or_key[:10]}...")
    
    print("\n3. .env file location check:")
    env_path = os.path.join(os.getcwd(), ".env")
    print(f"   Looking for: {env_path}")
    if os.path.exists(env_path):
        print("   ✅ .env file exists")
        with open(env_path, 'r') as f:
            content = f.read()
            print(f"   File size: {len(content)} bytes")
            if "GROUNDX_API_KEY" in content:
                print("   ✅ Contains GROUNDX_API_KEY")
            else:
                print("   ❌ Does NOT contain GROUNDX_API_KEY")
    else:
        print("   ❌ .env file NOT FOUND")
    
    return gx_key, or_key

def test_groundx_api(gx_key):
    """Test Ground X API connection"""
    print("\n" + "=" * 60)
    print("GROUND X API CONNECTION TEST")
    print("=" * 60)
    
    if not gx_key or gx_key == "your-groundx-api-key-here":
        print("\n❌ Cannot test - API key is missing or placeholder")
        return False
    
    try:
        from groundx import GroundX
        
        print("\n1. Testing GroundX client initialization...")
        client = GroundX(api_key=gx_key)
        print("   ✅ Client created successfully")
        
        print("\n2. Testing buckets.list() endpoint...")
        try:
            buckets_response = client.buckets.list()
            print("   ✅ API connection successful!")
            print(f"   Response type: {type(buckets_response)}")
            if hasattr(buckets_response, 'buckets'):
                print(f"   Number of buckets: {len(buckets_response.buckets) if buckets_response.buckets else 0}")
            return True
        except Exception as e:
            print(f"   ❌ API call failed: {type(e).__name__}")
            print(f"   Error message: {str(e)}")
            return False
            
    except ImportError as e:
        print(f"\n❌ Cannot import GroundX: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {type(e).__name__}: {e}")
        return False

def test_openrouter_api(or_key):
    """Test OpenRouter API connection"""
    print("\n" + "=" * 60)
    print("OPENROUTER API CONNECTION TEST")
    print("=" * 60)
    
    if not or_key or or_key == "your-openrouter-api-key-here":
        print("\n❌ Cannot test - API key is missing or placeholder")
        return False
    
    print("\n1. Testing OpenRouter API endpoint...")
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {or_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "openai/gpt-4o-mini",
                "messages": [{"role": "user", "content": "Say 'test' if you can read this."}],
                "max_tokens": 10
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print("   ✅ API connection successful!")
            result = response.json()
            if "choices" in result:
                print(f"   Response received: {result['choices'][0]['message']['content']}")
            return True
        else:
            print(f"   ❌ API call failed with status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {type(e).__name__}: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("API CONNECTION TEST SUITE")
    print("=" * 60)
    print(f"\nWorking directory: {os.getcwd()}")
    
    gx_key, or_key = test_env_loading()
    
    gx_success = test_groundx_api(gx_key)
    or_success = test_openrouter_api(or_key)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"\nGround X API: {'✅ Working' if gx_success else '❌ Failed'}")
    print(f"OpenRouter API: {'✅ Working' if or_success else '❌ Failed'}")
    
    if not gx_success:
        print("\n⚠️  To fix Ground X API:")
        print("   1. Get your API key from Ground X")
        print("   2. Update .env file: GROUNDX_API_KEY=your-actual-key")
        print("   3. Restart the Streamlit app")
    
    if not or_success:
        print("\n⚠️  To fix OpenRouter API:")
        print("   1. Get your API key from https://openrouter.ai/")
        print("   2. Update .env file: OPENROUTER_API_KEY=your-actual-key")
        print("   3. Restart the Streamlit app")


