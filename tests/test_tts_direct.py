#!/usr/bin/env python3
import pytest
pytestmark = pytest.mark.integration
"""
Direct TTS Test - Bypasses Kafka, tests ElevenLabs API directly
This test synthesizes speech and plays it locally
"""
import requests
import tempfile
import subprocess
import os
import time

# Colors for output
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

# ElevenLabs API Key from GEMINI.md
ELEVENLABS_API_KEY = "sk_ce8d69513338b3010ee8eef3cc1616ef1ca1ad520340fce7"

def synthesize_speech(text):
    """Call ElevenLabs API directly"""
    url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"  # Rachel voice
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    payload = {
        "text": text,
        "model_id": "eleven_flash_v2_5",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    
    print_status(f"Text: \"{text[:60]}...\"" if len(text) > 60 else f"Text: \"{text}\"")
    print_status("Calling ElevenLabs API...")
    
    response = requests.post(url, json=payload, headers=headers, timeout=60)
    
    if response.status_code == 200:
        print_status(f"Audio received: {len(response.content):,} bytes", "success")
        return response.content
    else:
        print_status(f"API Error: {response.status_code} - {response.text[:200]}", "error")
        return None

def play_audio(audio_content):
    """Save and play the audio file"""
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
        f.write(audio_content)
        temp_path = f.name
    
    print_status(f"Audio saved: {temp_path}")
    
    # Try different audio players
    players = [
        ['mpv', '--no-video', temp_path],
        ['ffplay', '-nodisp', '-autoexit', temp_path],
        ['aplay', temp_path],
        ['paplay', temp_path],
        ['mplayer', temp_path],
        ['vlc', '--play-and-exit', '--intf', 'dummy', temp_path],
    ]
    
    print_status("Playing audio...", "success")
    print(f"\n{Colors.CYAN}{'='*50}")
    print("  🔊 AUDIO PLAYBACK")
    print(f"{'='*50}{Colors.END}\n")
    
    played = False
    for player_cmd in players:
        try:
            result = subprocess.run(player_cmd, capture_output=True, timeout=60)
            if result.returncode == 0:
                played = True
                break
        except FileNotFoundError:
            continue
        except subprocess.TimeoutExpired:
            print_status("Playback timed out", "warning")
            played = True
            break
        except Exception:
            continue
    
    print(f"\n{Colors.CYAN}{'='*50}{Colors.END}")
    
    if not played:
        print_status("No audio player found (mpv, ffplay, vlc, mplayer)", "warning")
        print_status(f"Audio file saved at: {temp_path}")
        print_status("Play it manually with: mpv " + temp_path)
        return temp_path
    
    # Cleanup
    os.unlink(temp_path)
    print_status("Playback complete!", "success")
    return None

def main():
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}  Direct TTS Test - ElevenLabs API{Colors.END}")
    print(f"{Colors.YELLOW}  This test bypasses the deployed service{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}\n")
    
    # Text to synthesize
    text = "Hello! This is a direct test of the ElevenLabs text to speech API. This audio is being generated using the Rachel voice with the eleven flash version 2.5 model. The audio quality should be excellent!"
    
    # Step 1: Synthesize
    print(f"{Colors.CYAN}[Step 1/2] Text-to-Speech Synthesis{Colors.END}")
    audio_content = synthesize_speech(text)
    
    if not audio_content:
        print_status("Failed to generate audio", "error")
        return
    
    # Step 2: Play
    print(f"\n{Colors.CYAN}[Step 2/2] Audio Playback{Colors.END}")
    play_audio(audio_content)
    
    print(f"\n{Colors.GREEN}{'='*60}{Colors.END}")
    print(f"{Colors.GREEN}  TTS Test Complete!{Colors.END}")
    print(f"{Colors.GREEN}{'='*60}{Colors.END}\n")

if __name__ == "__main__":
    main()
