#!/bin/bash
# macOS Fix Script for Podcast Generator
# Run this on macOS to install missing dependencies

echo "🍎 Installing macOS dependencies for Podcast Generator..."

# Install required packages
pip3 install pyobjc-framework-Cocoa pyobjc-framework-AVFoundation pyobjc-framework-Speech

echo "✅ Dependencies installed!"
echo "Now run: python3 scripts/test_new_pdf_paper_simplified.py"