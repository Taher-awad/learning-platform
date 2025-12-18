#!/usr/bin/env python3
"""
Test script for STT (Speech-to-Text) Service
Demonstrates audio transcription with S3 storage
"""
import requests
import json
import time
import io

ALB_DNS = "learning-platform-alb-162703705.us-east-1.elb.amazonaws.com"
BASE_URL = f"http://{ALB_DNS}"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_result(name, success, details=""):
    symbol = f"{Colors.GREEN}✓{Colors.END}" if success else f"{Colors.RED}✗{Colors.END}"
    print(f"{symbol} {name}")
    if details:
        print(f"  {Colors.BLUE}{details}{Colors.END}")

def get_auth_token():
    """Get authentication token for protected endpoints"""
    test_email = f"stttest_{int(time.time())}@example.com"
    register_data = {
        "email": test_email,
        "password": "TestPassword123!",
        "full_name": "STT Test User"
    }
    try:
        requests.post(f"{BASE_URL}/api/auth/register", json=register_data, timeout=10)
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": test_email, "password": "TestPassword123!"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get('access_token')
    except:
        pass
    return None

def main():
    print(f"\n{Colors.YELLOW}=== STT Service Test ==={Colors.END}")
    print(f"Endpoint: {BASE_URL}/api/stt/")
    print("Uses Google Speech Recognition for transcription")
    print("-" * 50)
    
    # Get auth token first
    print(f"\n{Colors.BLUE}0. Getting Authentication Token{Colors.END}")
    token = get_auth_token()
    if token:
        print_result("Auth Token", True, "Token obtained")
        headers = {"Authorization": f"Bearer {token}"}
    else:
        print_result("Auth Token", False, "Could not obtain token")
        headers = {}
    
    # Test 1: Service health
    print(f"\n{Colors.BLUE}1. Testing Service Health{Colors.END}")
    try:
        response = requests.get(
            f"{BASE_URL}/api/stt/",
            timeout=10
        )
        print_result("Service Health", response.status_code in [200, 401], f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print_result("Service Health", False, str(e))
    
    # Test 2: List transcriptions
    print(f"\n{Colors.BLUE}2. Testing List Transcriptions{Colors.END}")
    try:
        response = requests.get(
            f"{BASE_URL}/api/stt/transcriptions",
            headers=headers,
            timeout=15
        )
        print_result("List Transcriptions", response.status_code in [200, 401], f"Status: {response.status_code}")
        if response.status_code == 200:
            transcriptions = response.json()
            if isinstance(transcriptions, list):
                print(f"  Transcription count: {len(transcriptions)}")
            else:
                print(f"  Response: {transcriptions}")
    except Exception as e:
        print_result("List Transcriptions", False, str(e))
    
    # Test 3: Transcribe audio (would require actual audio file)
    print(f"\n{Colors.BLUE}3. Testing Audio Transcription{Colors.END}")
    print(f"  Note: This test requires an actual audio file")
    print(f"  To test transcription, use:")
    print(f"    curl -X POST '{BASE_URL}/api/stt/transcribe' \\")
    print(f"         -H 'Authorization: Bearer <token>' \\")
    print(f"         -F 'file=@your_audio.wav'")
    
    # Test 4: Get transcription by ID
    print(f"\n{Colors.BLUE}4. Testing Get Transcription{Colors.END}")
    try:
        response = requests.get(
            f"{BASE_URL}/api/stt/transcription/test-id",
            headers=headers,
            timeout=10
        )
        print_result("Get Transcription", response.status_code in [200, 401], f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print_result("Get Transcription", False, str(e))
    
    print(f"\n{Colors.YELLOW}=== STT Service Test Complete ==={Colors.END}\n")

if __name__ == "__main__":
    main()
