# Multi-Platform Product Listing Automation

## Setup Instructions

1. **Install Flask** (if not already installed):
   ```bash
   pip install flask
   ```

2. **Run the application**:
   ```bash
   python app.py
   ```

3. **Open your browser** and go to:
   ```
   http://localhost:5000
   ```

## Directory Structure

```
project/
├── app.py                 # Flask application
├── templates/
│   └── index.html        # Main form template
├── static/
│   ├── css/
│   │   └── main.css      # Styling
│   └── js/
│       └── main.js       # JavaScript functionality
├── images/               # Product image folders (organized by SKU)
│   └── {SKU}/           # Each product SKU gets its own folder
│       ├── front.jpg
│       ├── side.jpg
│       └── ...
├── listing_done/         # Archived images after successful listing
├── exports/              # Generated export files
└── temp/                 # Temporary files
```

## How to Use

1. **Create image folders**: For each product SKU (e.g., "ABC123"), create a folder in the `images/` directory
2. **Add product images**: Place all product photos in the SKU folder
3. **Fill the form**: Open the web interface and fill in product details
4. **Generate variants**: For bangles, use the variant generator to create multiple sizes
5. **Export data**: Use the export buttons to generate platform-specific data

## Image Folder Naming

- Create folder: `images/ABC123/` (where ABC123 is your SKU)
- Add images: `front.jpg`, `side.jpg`, `back.jpg`, etc.
- After successful listing, the folder moves to `listing_done/ABC123/`

## Features

- ✅ Unified form for all platforms
- ✅ SKU-based image management
- ✅ Automatic bangle variant generation
- ✅ Real-time form validation
- ✅ Platform-specific export formats
- ✅ Responsive design
- ✅ Toast notifications

## Troubleshooting

- **CSS not loading**: Make sure files are in the correct `static/` directories
- **Images not showing**: Ensure image folders are named exactly as the SKU
- **Form not responsive**: Check that JavaScript file is properly linked
