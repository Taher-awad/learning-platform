#!/usr/bin/env python3
import pytest
pytestmark = pytest.mark.integration
"""
Test script to check all Gemini API keys with different models
"""
import requests
import json

# API Keys
KEYS = [
    'AIzaSyBt_azQNz0w-vcyNEQu-tbB__pKIri6EpU',
    'AIzaSyB25zw74hDNbUx_JUL3sN4Amd6qJNx4jeg',
    'AIzaSyAf45h6lMrmnBQYDQz4PQ40ExkZB_Dvqj4'
]

# Models to test (from smallest to largest)
MODELS = [
    'gemini-1.5-flash-8b',
    'gemini-1.5-flash',
    'gemini-2.0-flash-lite',  
    'gemini-2.0-flash-exp',
    'gemini-1.0-pro',
    'gemma-3-1b-it',
    'gemma-3-4b-it',
]

def test_model(key, model, key_num):
    """Test a single model with a key"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    
    payload = {
        "contents": [{"parts": [{"text": "Say hello in one word"}]}],
        "generationConfig": {"maxOutputTokens": 10}
    }
    
    try:
        res = requests.post(url, json=payload, timeout=30)
        if res.status_code == 200:
            data = res.json()
            text = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
            return ('✅', text.strip()[:20])
        elif res.status_code == 429:
            return ('⚠️ RATE LIMITED', '')
        elif res.status_code == 404:
            return ('❌ NOT FOUND', '')
        elif res.status_code == 400:
            error = res.json().get('error', {}).get('message', '')[:50]
            return (f'❌ {res.status_code}', error)
        else:
            return (f'❌ {res.status_code}', '')
    except Exception as e:
        return (f'❌ ERROR', str(e)[:30])

def main():
    print("\n" + "="*70)
    print("  GEMINI API KEY & MODEL TEST")
    print("="*70)
    
    results = {}
    
    for ki, key in enumerate(KEYS, 1):
        print(f"\n🔑 Testing Key {ki}: {key[:20]}...")
        results[ki] = {}
        
        for model in MODELS:
            status, response = test_model(key, model, ki)
            results[ki][model] = status
            
            if '✅' in status:
                print(f"   {model:30} {status} → {response}")
            else:
                print(f"   {model:30} {status}")
    
    # Summary
    print("\n" + "="*70)
    print("  SUMMARY - Working Models")
    print("="*70)
    
    working = []
    for ki, models in results.items():
        for model, status in models.items():
            if '✅' in status:
                working.append((ki, model))
    
    if working:
        print("\n✅ WORKING COMBINATIONS:")
        for ki, model in working:
            print(f"   Key {ki} + {model}")
    else:
        print("\n❌ No working combinations found!")
        print("   All keys might be rate limited. Wait 1-2 minutes and try again.")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()
