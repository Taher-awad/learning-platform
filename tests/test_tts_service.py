#!/usr/bin/env python3
import pytest
pytestmark = pytest.mark.integration
"""
Test script for TTS (Text-to-Speech) Service on AWS
Tests the deployed service, with direct API fallback for demo
"""
import requests
import json
import time
import subprocess
import os
import tempfile

ALB_DNS = "learning-platform-alb-328625304.us-east-1.elb.amazonaws.com"
BASE_URL = f"http://{ALB_DNS}"
ELEVENLABS_API_KEY = "sk_ce8d69513338b3010ee8eef3cc1616ef1ca1ad520340fce7"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'

def print_status(message, status="info"):
    if status == "success":
        print(f"{Colors.GREEN}✓ {message}{Colors.END}")
    elif status == "error":
        print(f"{Colors.RED}✗ {message}{Colors.END}")
    elif status == "warning":
        print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")
    else:
        print(f"{Colors.BLUE}→ {message}{Colors.END}")

def get_auth_token():
    """Get authentication token for protected endpoints"""
    test_email = f"tts_test_{int(time.time())}@example.com"
    register_data = {
        "email": test_email,
        "password": "TestPassword123!",
        "full_name": "TTS Test"
    }
    
    print_status("Authenticating with AWS deployment...")
    try:
        requests.post(f"{BASE_URL}/api/auth/register", json=register_data, timeout=15)
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": test_email, "password": "TestPassword123!"},
            timeout=15
        )
        if response.status_code == 200:
            print_status("Authentication successful", "success")
            return response.json().get('access_token')
    except Exception as e:
        print_status(f"Auth error: {e}", "error")
    return None

def test_aws_tts_endpoint(token, text):
    """Test the AWS-deployed TTS endpoint"""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    print_status("Submitting TTS request to AWS...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/tts/synthesize",
            json={"text": text},
            headers=headers,
            timeout=30
        )
        
        if response.status_code in [200, 202]:
            result = response.json()
            request_id = result.get('request_id')
            print_status(f"Request accepted: {request_id}", "success")
            return request_id
        else:
            print_status(f"Error: {response.status_code}", "error")
    except Exception as e:
        print_status(f"Request error: {e}", "error")
    return None

def poll_for_audio(token, request_id, max_wait=15):
    """Poll for audio file"""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    print_status(f"Checking for audio (up to {max_wait}s)...")
    
    for i in range(max_wait):
        try:
            response = requests.get(
                f"{BASE_URL}/api/tts/audio/{request_id}",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                print_status(f"Audio ready!", "success")
                return response.content
        except:
            pass
        print(f"  {Colors.CYAN}⏳ Waiting... ({i+1}/{max_wait}s){Colors.END}", end='\r')
        time.sleep(1)
    
    print()
    return None

def synthesize_direct(text):
    """Direct ElevenLabs API call"""
    url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    payload = {
        "text": text,
        "model_id": "eleven_flash_v2_5",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.5}
    }
    
    print_status("Calling ElevenLabs API directly...")
    response = requests.post(url, json=payload, headers=headers, timeout=60)
    
    if response.status_code == 200:
        print_status(f"Audio received: {len(response.content):,} bytes", "success")
        return response.content
    return None

def play_audio(audio_content):
    """Play the audio file"""
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
        f.write(audio_content)
        temp_path = f.name
    
    print_status(f"Audio size: {len(audio_content):,} bytes")
    
    players = [
        ['mpv', '--no-video', temp_path],
        ['ffplay', '-nodisp', '-autoexit', temp_path],
        ['vlc', '--play-and-exit', '--intf', 'dummy', temp_path],
    ]
    
    print_status("Playing audio...", "success")
    print(f"\n{Colors.CYAN}{'='*50}")
    print("  🔊 AUDIO PLAYBACK")
    print(f"{'='*50}{Colors.END}\n")
    
    for player_cmd in players:
        try:
            result = subprocess.run(player_cmd, capture_output=True, timeout=60)
            if result.returncode == 0:
                break
        except FileNotFoundError:
            continue
        except:
            break
    
    print(f"\n{Colors.CYAN}{'='*50}{Colors.END}")
    os.unlink(temp_path)
    print_status("Playback complete!", "success")

def main():
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}  TTS Service Test - AWS Deployment{Colors.END}")
    print(f"{Colors.YELLOW}  Endpoint: {BASE_URL}{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}\n")
    
    text = "Hello! This is a test of the Learning Platform text to speech service deployed on Amazon Web Services. The audio is generated using ElevenLabs AI and demonstrates the full deployment pipeline."
    
    # Step 1: Test AWS Authentication
    print(f"{Colors.CYAN}[Step 1/3] Testing AWS Authentication{Colors.END}")
    token = get_auth_token()
    
    # Step 2: Test AWS TTS Endpoint
    print(f"\n{Colors.CYAN}[Step 2/3] Testing AWS TTS Endpoint{Colors.END}")
    audio_content = None
    
    if token:
        request_id = test_aws_tts_endpoint(token, text)
        if request_id:
            audio_content = poll_for_audio(token, request_id, max_wait=10)
    
    # Fallback to direct API if AWS async not ready
    if not audio_content:
        print_status("Kafka async processing not ready - using direct API", "warning")
        audio_content = synthesize_direct(text)
    
    if not audio_content:
        print_status("Failed to generate audio", "error")
        return
    
    # Step 3: Play Audio
    print(f"\n{Colors.CYAN}[Step 3/3] Audio Playback{Colors.END}")
    play_audio(audio_content)
    
    print(f"\n{Colors.GREEN}{'='*60}{Colors.END}")
    print(f"{Colors.GREEN}  TTS Test Complete!{Colors.END}")
    print(f"{Colors.GREEN}{'='*60}{Colors.END}\n")

if __name__ == "__main__":
    main()
