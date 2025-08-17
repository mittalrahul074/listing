from flask import Flask, render_template, request, jsonify, send_file
import os
from pathlib import Path
from automation_meesho import automate_meesho_listing
from automation_flipkart import automate_flipkart_listing
from automation_myntra import automate_myntra_listing

app = Flask(__name__)

# Configure static files
app.static_folder = 'static'
app.template_folder = 'templates'

@app.route("/", methods=["GET", "POST"])
def main_form():
    # Dynamically collect SKUs present in /images/ folder, or pull from database
    import os
    sku_list = sorted(os.listdir(os.path.join(os.path.dirname(__file__), '..', 'images')))  # path to root/images

    gst_list = [3, 5, 12, 18]

    return render_template("index.html", sku_list=sku_list, gst_list=gst_list)

@app.route('/')
def index():
    """Main page with the product listing form."""
    return render_template('index.html')

@app.route('/api/validate-sku', methods=['POST'])
def validate_sku():
    """Validate if SKU has corresponding image folder."""
    data = request.get_json()
    sku = data.get('sku', '')

    images_path = Path('images') / sku

    if images_path.exists() and images_path.is_dir():
        # Get list of images in the folder  
        image_files = []
        for ext in ['.jpg', '.jpeg', '.png', '.webp']:
            image_files.extend(list(images_path.glob(f'*{ext}')))
            image_files.extend(list(images_path.glob(f'*{ext.upper()}')))

        return jsonify({
            'valid': True,
            'image_count': len(image_files),
            'images': [str(img.name) for img in image_files]
        })
    else:
        return jsonify({
            'valid': False,
            'message': f'No image folder found for SKU: {sku}'
        })

@app.route('/api/generate-variants', methods=['POST'])
def generate_variants():
    """Generate bangle variants for different sizes."""
    data = request.get_json()
    base_sku = data.get('sku', '')
    product_type = data.get('product_type', '')

    if product_type.lower() == 'bangle':
        sizes = ['2.4', '2.6', '2.8']
        variants = []

        for size in sizes:
            variant_sku = f"{base_sku}-{size.replace('.', '')}"
            variants.append({
                'sku': variant_sku,
                'size': size + '"',
                'original_sku': base_sku
            })

        return jsonify({
            'success': True,
            'variants': variants
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Variant generation only available for bangles'
        })


@app.route('/export_meesho', methods=['POST'])
def export_meesho():
    data = request.get_json()
    sku = data['sku']
    if not sku:
        return jsonify({'status': 'error', 'message': 'SKU not provided.'}), 400
    product_data = data  # Or transform fields as needed

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sku_folder = os.path.join(base_dir, 'images', sku)
    
    if not os.path.isdir(sku_folder):
        return jsonify({'status': 'error', 'message': f'Image folder not found for SKU: {sku}'}), 404
    
    try:
    # Fire browser automation (blocking; for async/queue, use threading/celery)
        automate_meesho_listing(product_data, sku_folder)
        return jsonify({'status': 'success', 'message': f'Product {sku} submitted to Meesho!'})
    
    # On success, archive images (optional)
    # image_manager.archive_images(sku)
    
    except Exception as e:
        print(f"Error in Meesho automation for SKU {sku}: {e}")
        return jsonify({'status': 'error', 'message': f'Automation failed: {e}'}), 500
    
@app.route('/export_myntra', methods=['POST'])
def export_myntra():
    data = request.get_json()
    sku = data['sku']
    if not sku:
        return jsonify({'status': 'error', 'message': 'SKU not provided.'}), 400
    product_data = data  # Or transform fields as needed

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sku_folder = os.path.join(base_dir, 'images', sku)
    
    if not os.path.isdir(sku_folder):
        return jsonify({'status': 'error', 'message': f'Image folder not found for SKU: {sku}'}), 404
    
    try:
    # Fire browser automation (blocking; for async/queue, use threading/celery)
        automate_myntra_listing(product_data, sku_folder)
        return jsonify({'status': 'success', 'message': f'Product {sku} submitted to Meesho!'})
    
    # On success, archive images (optional)
    # image_manager.archive_images(sku)
    
    except Exception as e:
        print(f"Error in Meesho automation for SKU {sku}: {e}")
        return jsonify({'status': 'error', 'message': f'Automation failed: {e}'}), 500

@app.route('/export_flipkart', methods=['POST'])
def export_flipkart():
    data = request.get_json()
    sku = data['sku']
    if not sku:
        return jsonify({'status': 'error', 'message': 'SKU not provided.'}), 400
    product_data = data  # Or transform fields as needed

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sku_folder = os.path.join(base_dir, 'images', sku)
    
    if not os.path.isdir(sku_folder):
        return jsonify({'status': 'error', 'message': f'Image folder not found for SKU: {sku}'}), 404
    
    try:
    # Fire browser automation (blocking; for async/queue, use threading/celery)
        automate_flipkart_listing(product_data, sku_folder)
        return jsonify({'status': 'success', 'message': f'Product {sku} submitted to Flipkart!'})
    
    # On success, archive images (optional)
    # image_manager.archive_images(sku)
    
    except Exception as e:
        print(f"Error in Flipkart automation for SKU {sku}: {e}")
        return jsonify({'status': 'error', 'message': f'Automation failed: {e}'}), 500
    
if __name__ == '__main__':
    # Ensure required directories exist
    for directory in ['images', 'listing_done', 'exports', 'temp']:
        Path(directory).mkdir(exist_ok=True)

    print("🚀 Starting Multi-Platform Product Listing Automation")
    print("📝 Open http://localhost:5000 in your browser")
    print("📁 Make sure to create image folders with SKU names in the 'images' directory")

    app.run(debug=True, host='0.0.0.0', port=5000)