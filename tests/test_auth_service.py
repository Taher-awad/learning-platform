#!/usr/bin/env python3
"""
Test script for Auth Service
Demonstrates user registration and login functionality
"""
import requests
import json
import time
import sys

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

def main():
    print(f"\n{Colors.YELLOW}=== Auth Service Test ==={Colors.END}")
    print(f"Endpoint: {BASE_URL}/api/auth/")
    print("-" * 50)
    
    # Test 1: Register new user
    test_email = f"test_{int(time.time())}@example.com"
    register_data = {
        "email": test_email,
        "password": "TestPassword123!",
        "full_name": "Test User"
    }
    
    print(f"\n{Colors.BLUE}1. Testing User Registration{Colors.END}")
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json=register_data,
            timeout=15
        )
        print_result("User Registration", response.status_code == 200, f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {json.dumps(response.json(), indent=2)[:200]}...")
            user_data = response.json()
        else:
            print(f"  Error: {response.text[:200]}")
    except Exception as e:
        print_result("User Registration", False, str(e))
        return
    
    # Test 2: Login with credentials
    print(f"\n{Colors.BLUE}2. Testing User Login{Colors.END}")
    login_data = {
        "email": test_email,
        "password": "TestPassword123!"
    }
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=login_data,
            timeout=15
        )
        print_result("User Login", response.status_code == 200, f"Status: {response.status_code}")
        if response.status_code == 200:
            token_data = response.json()
            print(f"  Token received: {bool(token_data.get('access_token'))}")
            print(f"  Token (truncated): {token_data.get('access_token', '')[:50]}...")
        else:
            print(f"  Error: {response.text[:200]}")
    except Exception as e:
        print_result("User Login", False, str(e))
    
    # Test 3: Verify token
    print(f"\n{Colors.BLUE}3. Testing Token Verification{Colors.END}")
    if 'token_data' in dir() and token_data.get('access_token'):
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        try:
            response = requests.get(
                f"{BASE_URL}/api/auth/me",
                headers=headers,
                timeout=10
            )
            print_result("Token Verification", response.status_code == 200, f"Status: {response.status_code}")
            if response.status_code == 200:
                print(f"  User: {response.json()}")
        except Exception as e:
            print_result("Token Verification", False, str(e))
    else:
        print_result("Token Verification", False, "No token available")
    
    print(f"\n{Colors.YELLOW}=== Auth Service Test Complete ==={Colors.END}\n")

if __name__ == "__main__":
    main()
