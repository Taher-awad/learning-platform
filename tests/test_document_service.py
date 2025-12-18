#!/usr/bin/env python3
import pytest
pytestmark = pytest.mark.integration
"""
Test script for Document Service
Demonstrates document upload, S3 storage, and notes generation
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
    test_email = f"doctest_{int(time.time())}@example.com"
    register_data = {
        "email": test_email,
        "password": "TestPassword123!",
        "full_name": "Doc Test User"
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
    print(f"\n{Colors.YELLOW}=== Document Service Test ==={Colors.END}")
    print(f"Endpoint: {BASE_URL}/api/documents/")
    print("-" * 50)
    
    # Get auth token first
    print(f"\n{Colors.BLUE}0. Getting Authentication Token{Colors.END}")
    token = get_auth_token()
    if token:
        print_result("Auth Token", True, f"Token obtained")
        headers = {"Authorization": f"Bearer {token}"}
    else:
        print_result("Auth Token", False, "Could not obtain token")
        headers = {}
    
    # Test 1: Upload document
    print(f"\n{Colors.BLUE}1. Testing Document Upload (S3){Colors.END}")
    test_content = b"This is a test document for demonstrating S3 storage. It contains sample text that will be processed and notes will be generated automatically using Google Gemini AI."
    files = {"file": ("test_document.txt", test_content, "text/plain")}
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/documents/upload",
            files=files,
            headers=headers,
            timeout=60
        )
        print_result("Document Upload", response.status_code == 200, f"Status: {response.status_code}")
        if response.status_code == 200:
            doc_data = response.json()
            doc_id = doc_data.get('id')
            print(f"  Document ID: {doc_id}")
            print(f"  Message: {doc_data.get('message')}")
        elif response.status_code == 401:
            print(f"  Auth Required: Set up proper authentication")
        else:
            print(f"  Error: {response.text[:200]}")
            doc_id = None
    except Exception as e:
        print_result("Document Upload", False, str(e))
        doc_id = None
    
    # Test 2: List documents
    print(f"\n{Colors.BLUE}2. Testing List Documents{Colors.END}")
    try:
        response = requests.get(
            f"{BASE_URL}/api/documents",
            headers=headers,
            timeout=15
        )
        print_result("List Documents", response.status_code in [200, 401], f"Status: {response.status_code}")
        if response.status_code == 200:
            docs = response.json()
            print(f"  Document count: {len(docs)}")
    except Exception as e:
        print_result("List Documents", False, str(e))
    
    # Test 3: Get specific document
    if doc_id:
        print(f"\n{Colors.BLUE}3. Testing Get Document Details{Colors.END}")
        try:
            response = requests.get(
                f"{BASE_URL}/api/documents/{doc_id}",
                headers=headers,
                timeout=15
            )
            print_result("Get Document", response.status_code == 200, f"Status: {response.status_code}")
            if response.status_code == 200:
                doc = response.json()
                print(f"  Filename: {doc.get('filename')}")
                print(f"  Status: {doc.get('status')}")
                print(f"  S3 Bucket: {doc.get('s3_bucket')}")
        except Exception as e:
            print_result("Get Document", False, str(e))
    
    print(f"\n{Colors.YELLOW}=== Document Service Test Complete ==={Colors.END}\n")

if __name__ == "__main__":
    main()
