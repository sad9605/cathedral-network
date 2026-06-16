#!/usr/bin/env python3
"""
Steganographic Communications Layer
Covert Warden communications with plausible deniability
"""

import os
import json
import base64
from PIL import Image
from datetime import datetime
from typing import Optional, Dict

class SteganographicCommLayer:
    """
    Covert Warden communications layer.
    Embeds warnings in innocuous social media images.
    """
    
    def __init__(self, image_dir: str = "assets/images/"):
        self.image_dir = image_dir
        self.pattern = "CATHEDRAL_"
        
        # Create directory if it doesn't exist
        os.makedirs(image_dir, exist_ok=True)
    
    def _encode_message(self, message: Dict) -> str:
        """Encode message for embedding."""
        json_str = json.dumps(message)
        encoded = base64.b64encode(json_str.encode()).decode()
        return self.pattern + encoded
    
    def _decode_message(self, encoded: str) -> Optional[Dict]:
        """Decode extracted message."""
        if encoded and encoded.startswith(self.pattern):
            try:
                b64_data = encoded.replace(self.pattern, "")
                decoded = base64.b64decode(b64_data).decode()
                return json.loads(decoded)
            except Exception:
                return None
        return None
    
    def embed_warning(self, message: Dict, cover_image_path: str) -> str:
        """
        Embed JSON warning into image using LSB steganography.
        Returns path to output image.
        """
        # For demo - create a fake image if none exists
        if not os.path.exists(cover_image_path):
            print(f"⚠️ Cover image not found: {cover_image_path}")
            print("   Creating a placeholder image...")
            from PIL import Image, ImageDraw
            
            img = Image.new('RGB', (800, 600), color=(73, 109, 137))
            d = ImageDraw.Draw(img)
            d.text((10, 10), "Cathedral Cover Image", fill=(255, 255, 255))
            img.save(cover_image_path)
        
        # Encode message
        encoded = self._encode_message(message)
        
        # Embed using LSB (simplified - would use actual steganography in production)
        output_path = cover_image_path.replace(".", "_embedded.")
        
        # For demo, just copy the image and store metadata
        from shutil import copyfile
        copyfile(cover_image_path, output_path)
        
        # Store the encoded message in a sidecar file for demo
        sidecar = output_path + ".meta"
        with open(sidecar, 'w') as f:
            json.dump({'encoded': encoded, 'timestamp': datetime.now().isoformat()}, f)
        
        return output_path
    
    def extract_warning(self, image_path: str) -> Optional[Dict]:
        """
        Extract and decode hidden warning.
        Returns None if no Cathedral payload found.
        """
        # Check for sidecar file
        sidecar = image_path + ".meta"
        if os.path.exists(sidecar):
            with open(sidecar, 'r') as f:
                data = json.load(f)
                return self._decode_message(data.get('encoded', ''))
        
        return None
    
    def upload_to_social(self, image_path: str) -> bool:
        """
        Simulate upload to social media.
        """
        print(f"📤 Uploading {image_path} to social media...")
        print("   ✅ Upload successful (simulated)")
        return True

# Standalone execution
if __name__ == "__main__":
    print("🛰️ Steganographic Communications Layer")
    print("=" * 50)
    
    layer = SteganographicCommLayer()
    
    # Create a test message
    test_message = {
        'priority': 'HIGH',
        'type': 'Warden_Escalation',
        'threat': 'Data_Center_Stress',
        'location': 'Virginia_USA',
        'timestamp': datetime.now().isoformat()
    }
    
    print(f"\n📝 Embedding message:")
    print(json.dumps(test_message, indent=2))
    
    # Embed in image
    output = layer.embed_warning(test_message, 'assets/cover.jpg')
    print(f"\n✅ Message embedded: {output}")
    
    # Extract message
    extracted = layer.extract_warning(output)
    if extracted:
        print(f"\n📥 Extracted message:")
        print(json.dumps(extracted, indent=2))
    
    # Simulate upload
    layer.upload_to_social(output)
    
    print("\n✅ Steganographic layer ready")
