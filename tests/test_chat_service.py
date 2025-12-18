#!/usr/bin/env python3
import pytest
pytestmark = pytest.mark.integration
"""
Test script for Chat Service
Demonstrates AI chat functionality with PostgreSQL history storage
"""
import requests
import json
import time

ALB_DNS = "learning-platform-alb-328625304.us-east-1.elb.amazonaws.com"
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
    test_email = f"chattest_{int(time.time())}@example.com"
    register_data = {
        "email": test_email,
        "password": "TestPassword123!",
        "full_name": "Chat Test User"
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
    print(f"\n{Colors.YELLOW}=== Chat Service Test ==={Colors.END}")
    print(f"Endpoint: {BASE_URL}/api/chat/")
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
    
    # Test 1: Send a chat message
    print(f"\n{Colors.BLUE}1. Testing Chat Message{Colors.END}")
    message_data = {"message": "What is machine learning? Give a brief explanation."}
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat/message",
            json=message_data,
            headers=headers,
            timeout=60
        )
        print_result("Send Message", response.status_code == 200, f"Status: {response.status_code}")
        if response.status_code == 200:
            chat_response = response.json()
            print(f"  Response length: {len(str(chat_response.get('response', '')))}")
            print(f"  Response (truncated): {str(chat_response.get('response', ''))[:200]}...")
        elif response.status_code == 401:
            print(f"  Auth Required: Protected endpoint")
        else:
            print(f"  Error: {response.text[:200]}")
    except Exception as e:
        print_result("Send Message", False, str(e))
    
    # Test 2: Get conversation history
    print(f"\n{Colors.BLUE}2. Testing Get Conversations{Colors.END}")
    try:
        response = requests.get(
            f"{BASE_URL}/api/chat/conversations",
            headers=headers,
            timeout=15
        )
        print_result("Get Conversations", response.status_code in [200, 401], f"Status: {response.status_code}")
        if response.status_code == 200:
            conversations = response.json()
            print(f"  Conversation count: {len(conversations)}")
    except Exception as e:
        print_result("Get Conversations", False, str(e))
    
    # Test 3: Multi-turn conversation
    print(f"\n{Colors.BLUE}3. Testing Follow-up Question{Colors.END}")
    followup_data = {"message": "Can you give me an example of machine learning?"}
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat/message",
            json=followup_data,
            headers=headers,
            timeout=60
        )
        print_result("Follow-up Message", response.status_code in [200, 401], f"Status: {response.status_code}")
        if response.status_code == 200:
            chat_response = response.json()
            print(f"  Response (truncated): {str(chat_response.get('response', ''))[:200]}...")
    except Exception as e:
        print_result("Follow-up Message", False, str(e))
    
    print(f"\n{Colors.YELLOW}=== Chat Service Test Complete ==={Colors.END}\n")

if __name__ == "__main__":
    main()
