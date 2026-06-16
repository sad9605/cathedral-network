#!/bin/bash
echo "🚀 Deploying All Unconventional Intelligence Tracks"
echo "===================================================="

# Create all files from the code above
# (Run the code blocks from above first)

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install pillow opencv-python numpy scipy 2>/dev/null || pip install pillow opencv-python numpy scipy

# Create directory structure
mkdir -p assets/images

# Run tests
echo ""
echo "🧠 Testing Track 1: Stochastic Pattern Analysis"
python3 stochastic_pattern_analysis.py

echo ""
echo "🛰️ Testing Track 2: Steganographic Layer"
python3 steganographic_layer.py

echo ""
echo "🎨 Testing Track 3: Provenance Engine"
python3 provenance_engine.py

echo ""
echo "✅ All unconventional intelligence tracks deployed!"
