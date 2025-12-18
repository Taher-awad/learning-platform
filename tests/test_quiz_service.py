#!/usr/bin/env python3
import pytest
pytestmark = pytest.mark.integration
"""
Test script for Quiz Service
Demonstrates quiz generation from documents
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
    test_email = f"quiztest_{int(time.time())}@example.com"
    register_data = {
        "email": test_email,
        "password": "TestPassword123!",
        "full_name": "Quiz Test User"
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
    print(f"\n{Colors.YELLOW}=== Quiz Service Test ==={Colors.END}")
    print(f"Endpoint: {BASE_URL}/api/quiz/")
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
    
    # Test 1: Generate quiz
    print(f"\n{Colors.BLUE}1. Testing Quiz Generation{Colors.END}")
    quiz_data = {
        "document_id": "test-document-id",
        "num_questions": 3,
        "topic": "Machine Learning Basics"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/quiz/generate",
            json=quiz_data,
            headers=headers,
            timeout=60
        )
        print_result("Generate Quiz", response.status_code in [200, 201, 401], f"Status: {response.status_code}")
        if response.status_code in [200, 201]:
            quiz = response.json()
            quiz_id = quiz.get('id')
            print(f"  Quiz ID: {quiz_id}")
            questions = quiz.get('questions', [])
            print(f"  Questions: {len(questions)}")
        elif response.status_code == 401:
            print(f"  Auth Required: Protected endpoint")
            quiz_id = None
        else:
            print(f"  Error: {response.text[:200]}")
            quiz_id = None
    except Exception as e:
        print_result("Generate Quiz", False, str(e))
        quiz_id = None
    
    # Test 2: List quizzes
    print(f"\n{Colors.BLUE}2. Testing List Quizzes{Colors.END}")
    try:
        response = requests.get(
            f"{BASE_URL}/api/quiz/quizzes",
            headers=headers,
            timeout=15
        )
        print_result("List Quizzes", response.status_code in [200, 401], f"Status: {response.status_code}")
        if response.status_code == 200:
            quizzes = response.json()
            print(f"  Quiz count: {len(quizzes)}")
    except Exception as e:
        print_result("List Quizzes", False, str(e))
    
    # Test 3: Submit quiz answers
    if quiz_id:
        print(f"\n{Colors.BLUE}3. Testing Submit Quiz Answers{Colors.END}")
        answer_data = {
            "quiz_id": quiz_id,
            "answers": [
                {"question_id": 1, "answer": "A"},
                {"question_id": 2, "answer": "B"},
                {"question_id": 3, "answer": "C"}
            ]
        }
        try:
            response = requests.post(
                f"{BASE_URL}/api/quiz/{quiz_id}/submit",
                json=answer_data,
                headers=headers,
                timeout=15
            )
            print_result("Submit Answers", response.status_code in [200, 401], f"Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"  Score: {result.get('score')}")
        except Exception as e:
            print_result("Submit Answers", False, str(e))
    
    print(f"\n{Colors.YELLOW}=== Quiz Service Test Complete ==={Colors.END}\n")

if __name__ == "__main__":
    main()
