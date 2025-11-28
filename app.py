from flask import Flask, request, jsonify
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import requests

app = Flask(__name__)

# Download and cache a beautiful font on first run
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Bold.ttf"
FONT_PATH = "/tmp/Montserrat-Bold.ttf"

def download_font():
    """Download Montserrat Bold font (similar to Gemini's style)"""
    try:
        response = requests.get(FONT_URL)
        with open(FONT_PATH, 'wb') as f:
            f.write(response.content)
        print("Font downloaded successfully")
    except Exception as e:
        print(f"Font download failed: {e}")

# Download font on startup
try:
    download_font()
except:
    print("Warning: Font download failed, will use fallback")

@app.route('/add-text', methods=['POST'])
def add_text():
    """
    Add text overlay to image
    
    Expected JSON:
    {
        "image": "base64_encoded_image",
        "text": "CONNECT LINKEDIN",
        "config": {  // Optional, these are defaults
            "pill_x": 600,
            "pill_y": 280,
            "pill_width": 1120,
            "pill_height": 420,
            "pill_color": "#F5F2E6",
            "text_color": "#192A56",
            "font_size": 280,
            "corner_radius": 45
        }
    }
    """
    try:
        data = request.json
        
        # Get image and text
        image_b64 = data['image']
        text = data['text']
        
        # Get configuration (with defaults)
        config = data.get('config', {})
        pill_x = config.get('pill_x', 600)
        pill_y = config.get('pill_y', 280)
        pill_width = config.get('pill_width', 1120)
        pill_height = config.get('pill_height', 420)
        pill_color = config.get('pill_color', '#F5F2E6')
        text_color = config.get('text_color', '#192A56')
        font_size = config.get('font_size', 280)
        corner_radius = config.get('corner_radius', 45)
        
        # Convert hex colors to RGB tuples
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        pill_rgb = hex_to_rgb(pill_color) + (255,)  # Add alpha
        text_rgb = hex_to_rgb(text_color) + (255,)
        
        # Decode image
        image_data = base64.b64decode(image_b64)
        img = Image.open(io.BytesIO(image_data))
        
        # Convert to RGBA for transparency support
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Create drawing context
        draw = ImageDraw.Draw(img, 'RGBA')
        
        # Draw shadow (offset)
        shadow_offset = 10
        shadow = Image.new('RGBA', img.size, (255, 255, 255, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rounded_rectangle(
            [(pill_x + shadow_offset, pill_y + shadow_offset), 
             (pill_x + pill_width + shadow_offset, pill_y + pill_height + shadow_offset)],
            radius=corner_radius,
            fill=(0, 0, 0, 60)
        )
        img = Image.alpha_composite(img, shadow)
        
        # Draw pill background
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle(
            [(pill_x, pill_y), (pill_x + pill_width, pill_y + pill_height)],
            radius=corner_radius,
            fill=pill_rgb
        )
        
        # Load font
        try:
            font = ImageFont.truetype(FONT_PATH, font_size)
        except:
            # Fallback to DejaVu if Montserrat not available
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            except:
                font = ImageFont.load_default()
        
        # Calculate text position (centered in pill)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        text_x = pill_x + (pill_width - text_width) // 2
        text_y = pill_y + (pill_height - text_height) // 2 - 20  # Slight adjustment
        
        # Draw text
        draw.text((text_x, text_y), text, fill=text_rgb, font=font)
        
        # Convert back to base64
        buffer = io.BytesIO()
        img.convert('RGB').save(buffer, format='PNG')
        result_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return jsonify({
            'success': True,
            'image': result_base64
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
