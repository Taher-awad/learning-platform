#!/bin/bash
# Run all service tests

echo "========================================="
echo "Learning Platform - Complete Test Suite"
echo "========================================="

cd "$(dirname "$0")"

echo ""
echo "Running Auth Service Tests..."
python3 test_auth_service.py

echo ""
echo "Running Document Service Tests..."
python3 test_document_service.py

echo ""
echo "Running Chat Service Tests..."
python3 test_chat_service.py

echo ""
echo "Running Quiz Service Tests..."
python3 test_quiz_service.py

echo ""
echo "Running TTS Service Tests..."
python3 test_tts_service.py

echo ""
echo "Running STT Service Tests..."
python3 test_stt_service.py

echo ""
echo "========================================="
echo "All Tests Complete!"
echo "========================================="
