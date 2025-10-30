"""
Check available Google Gemini models for your API key
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def check_available_models():
    """Check what models are available with your API key"""
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ No API key found")
        return
    
    genai.configure(api_key=api_key)
    
    print("🔍 CHECKING AVAILABLE GOOGLE GEMINI MODELS")
    print("=" * 50)
    
    try:
        models = genai.list_models()
        
        print("✅ Available models:")
        for model in models:
            print(f"   📋 {model.name}")
            print(f"      Display Name: {model.display_name}")
            print(f"      Supported Methods: {model.supported_generation_methods}")
            print()
        
        # Test generateContent capability
        print("\n🧪 Testing generateContent capability:")
        
        # Convert to list first
        models_list = list(models)
        
        # Debug: Check a few models directly
        for i, model in enumerate(models_list[:3]):
            methods = getattr(model, 'supported_generation_methods', [])
            has_generate = 'generateContent' in methods
            print(f"   Debug - {model.name}: methods={methods}, has_generateContent={has_generate}")
        
        generation_models = [m for m in models_list if 'generateContent' in getattr(m, 'supported_generation_methods', [])]
        
        print(f"   Found {len(generation_models)} models with generateContent")
        
        if generation_models:
            # Try gemini-2.0-flash first (most reliable)
            preferred_models = [
                "models/gemini-2.0-flash",
                "models/gemini-2.5-flash", 
                "models/gemini-flash-latest"
            ]
            
            test_model = None
            for pref in preferred_models:
                if any(m.name == pref for m in generation_models):
                    test_model = next(m for m in generation_models if m.name == pref)
                    break
            
            if not test_model:
                test_model = generation_models[0]
            
            print(f"   Testing with: {test_model.name}")
            
            try:
                model = genai.GenerativeModel(test_model.name)
                response = model.generate_content("Say hello!")
                print(f"   ✅ Test successful: {response.text[:50]}...")
                print(f"   🎯 Use this model: {test_model.name}")
            except Exception as e:
                print(f"   ❌ Test failed: {e}")
        else:
            print("   ❌ No models support generateContent")
    
    except Exception as e:
        print(f"❌ Error checking models: {e}")

if __name__ == "__main__":
    check_available_models()