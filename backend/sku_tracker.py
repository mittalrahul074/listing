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
    print("checking all sku done")
    if all_completed(sku):
        print("all done, moving to done folder")
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

def check_and_move_all_completed_skus():
    """Check all SKUs in sku_status.json, move fully completed ones, and remove them from JSON."""
    status = load_status()
    moved_count = 0
    to_delete = []

    for sku, platforms in status.items():
        if all(platforms.values()):  # all platforms done
            src = os.path.join(IMAGES_DIR, sku)
            dest = os.path.join(DONE_DIR, sku)

            if os.path.exists(src):
                shutil.move(src, dest)
                print(f"📦 Auto-moved completed SKU '{sku}' to listing_done/")
            else:
                print(f"⚠️ Completed SKU '{sku}' not found in images/ (maybe already moved)")
            to_delete.append(sku)
            moved_count += 1

    # Remove moved SKUs from JSON
    for sku in to_delete:
        del status[sku]

    if to_delete:
        save_status(status)
        print(f"🧹 Removed {len(to_delete)} completed SKUs from sku_status.json")

    if moved_count == 0:
        print("✅ No pending completed SKUs to move.")
    else:
        print(f"✅ {moved_count} SKUs moved and cleaned from JSON.")
