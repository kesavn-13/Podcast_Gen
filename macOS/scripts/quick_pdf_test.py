#!/usr/bin/env python3
"""
Quick test for PDF paper processing
Simple verification that PDF can be read and processed
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

def test_pdf_reading():
    """Test if we can read the PDF file"""
    pdf_path = "samples/papers/LightEndoStereo- A Real-time Lightweight Stereo Matching Method for Endoscopy Images.pdf"
    
    print("🔍 Quick PDF Test")
    print("=" * 40)
    print(f"📄 Testing: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return False
    
    file_size = os.path.getsize(pdf_path) / (1024 * 1024)  # MB
    print(f"📊 File size: {file_size:.2f} MB")
    
    # Test PyMuPDF
    try:
        import fitz
        doc = fitz.open(pdf_path)
        page_count = len(doc)
        
        # Extract first page text
        first_page = doc[0]
        text = first_page.get_text()
        doc.close()
        
        print(f"✅ PyMuPDF: {page_count} pages")
        print(f"📝 First page text preview:")
        print(text[:300] + "..." if len(text) > 300 else text)
        
        return True
        
    except ImportError:
        print("❌ PyMuPDF not installed")
        return False
    except Exception as e:
        print(f"❌ PyMuPDF error: {e}")
        return False

def test_google_api():
    """Test if Google API is configured"""
    print("\n🤖 Google API Test")
    print("=" * 40)
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            print("❌ GOOGLE_API_KEY not found in .env")
            return False
        
        print(f"✅ API Key configured: {api_key[:10]}...")
        
        # Test connection
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        # Use the model from .env file
        model_name = os.getenv('GOOGLE_MODEL', 'gemini-2.0-flash')
        model = genai.GenerativeModel(model_name)
        response = model.generate_content('Hello, respond with just "API working"')
        
        print(f"✅ Google API response: {response.text}")
        return True
        
    except Exception as e:
        print(f"❌ Google API error: {e}")
        return False

def test_audio_system():
    """Test if audio system is working (Coqui-only)"""
    print("\n🎵 Audio System Test")  
    print("=" * 40)
    
    try:
        from app.audio_generator import CoquiLocalTTSEngine
        _ = CoquiLocalTTSEngine()
        print("✅ Coqui Local TTS available")
        return True
    except Exception as e:
        print(f"❌ Coqui TTS not available: {e}")
        return False

def main():
    """Run quick tests"""
    print("🚀 Quick PDF Paper Test")
    print("=" * 50)
    
    tests = [
        ("PDF Reading", test_pdf_reading),
        ("Google API", test_google_api), 
        ("Audio System", test_audio_system)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            results.append((test_name, False))
    
    print("\n🎯 QUICK TEST RESULTS")
    print("=" * 50)
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 All quick tests passed! Ready to run full test.")
        print("Run: python scripts/test_new_pdf_paper.py")
    else:
        print("\n⚠️  Some issues found. Fix these before running full test.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)