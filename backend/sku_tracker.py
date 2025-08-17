import json
import os
import shutil

BASE_DIR = os.path.dirname(__file__)  # project root
STATUS_FILE = os.path.join(BASE_DIR, "sku_status.json")
IMAGES_DIR = os.path.join(BASE_DIR, "images")
DONE_DIR = os.path.join(BASE_DIR, "listing_done")

os.makedirs(DONE_DIR, exist_ok=True)

def load_status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_status(status):
    with open(STATUS_FILE, "w") as f:
        json.dump(status, f, indent=4)

def mark_completed(sku, platform):
    status = load_status()
    if sku not in status:
        status[sku] = {"myntra": False, "meesho": False, "flipkart": False}
    status[sku][platform] = True
    save_status(status)
    print(f"✅ Marked {sku} as completed for {platform}")

    # Check if all platforms are done
    if all_completed(sku):
        move_sku_to_done(sku)

def is_completed(sku, platform):
    status = load_status()
    return status.get(sku, {}).get(platform, False)

def all_completed(sku):
    status = load_status()
    return all(status.get(sku, {}).values())

def move_sku_to_done(sku):
    src = os.path.join(IMAGES_DIR, sku)
    dest = os.path.join(DONE_DIR, sku)

    if os.path.exists(src):
        shutil.move(src, dest)
        print(f"📦 Moved '{sku}' to listing_done/")
    else:
        print(f"⚠️ SKU folder '{sku}' not found in images/")
