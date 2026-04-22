#!/bin/bash

# Badminton Video Editor - Quick Start Script
# This script sets up and runs the application

echo "🏸 Badminton Video Editor - Setup"
echo "=================================="
echo ""

# Check Python version
python_version=$(python3 --version 2>&1)
if [[ $? -ne 0 ]]; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

echo "✓ Found $python_version"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt
if [[ $? -ne 0 ]]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi
echo "✓ Dependencies installed"
echo ""

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads edited_videos
echo "✓ Directories created"
echo ""

# Start backend
echo "🚀 Starting Backend Server..."
echo "   URL: http://localhost:5000"
echo ""
echo "📋 API Endpoints:"
echo "   GET  /api/health"
echo "   POST /api/upload"
echo "   GET  /api/videos"
echo "   GET  /api/video/{id}/segments"
echo ""
echo "=================================="
echo "✓ Backend is running!"
echo ""
echo "📖 Next steps:"
echo "   1. Open 'frontend.html' in your web browser"
echo "   2. Upload a badminton video"
echo "   3. Wait for ML processing"
echo "   4. Edit and export!"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=================================="
echo ""

# Start the Flask app
python backend.py
