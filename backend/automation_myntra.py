import pyautogui
import os, re, gc, time, shutil, pythoncom
import win32com.client as win32
import undetected_chromedriver as uc

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from sku_tracker import mark_completed, is_completed, all_completed


gen_py = os.path.join(os.environ['LOCALAPPDATA'], "Temp", "gen_py")
if os.path.exists(gen_py):
    shutil.rmtree(gen_py)
# -----------------------------
#  Global Config
# -----------------------------
PROFILE_DIR = os.path.join(os.path.dirname(__file__), "myntra_profile")


# -----------------------------
#  Utility Functions
# -----------------------------
def clean_value(value: str) -> str:
    """
    Clean a given string by removing hidden characters, BOMs, and excess whitespace.
    Ensures Myntra validation does not fail on invisible characters.
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)

    # Normalize whitespace and remove hidden characters
    value = (
        value.replace("\xa0", " ")   # non-breaking space
             .replace("\u200b", "")  # zero-width space
             .replace("\ufeff", "")  # BOM
    )

    # Remove all control characters except \t, \n
    value = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", value)

    return value.strip()


def set_value(sheet, row: int, column: int, value):
    """
    Safely set a cell value in Excel while cleaning the input.
    """
    cleaned = clean_value(value)
    print(f" -> Writing cell[{row}, {column}] = {repr(cleaned)}")
    sheet.Cells(row, column).Value = cleaned

def type_into_cell(sheet, row, col, text):
    cell = sheet.Cells(row, col)
    cell.Activate()           # bring cursor to cell
    time.sleep(0.3)
    shell = win32.Dispatch("WScript.Shell")
    shell.SendKeys(str(text))
    time.sleep(0.2)
    shell.SendKeys("{ENTER}")
    time.sleep(0.2)

def get_driver():
    """
    Initialize undetected Chrome driver with persistent profile.
    """
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument(f"--user-data-dir={PROFILE_DIR}")
    return uc.Chrome(options=chrome_options)

def select_from_dropdown(sheet, row, col, option_index=1):
    """
    Select a value from a dropdown list in Excel by index (1 = first option).
    Uses keystrokes to ensure Excel logs it as a real selection.
    """
    cell = sheet.Cells(row, col)
    cell.Activate()
    time.sleep(0.3)

    shell = win32.Dispatch("WScript.Shell")

    # Open the dropdown
    shell.SendKeys("%{DOWN}")
    time.sleep(0.5)

    # Move down option_index - 1 times
    for _ in range(option_index - 1):
        shell.SendKeys("{DOWN}")
        time.sleep(0.2)

    # Confirm selection
    shell.SendKeys("{ENTER}")
    time.sleep(0.3)

def select_from_dropdown_by_text(sheet, row, col, desired_value):
    """
    Select a value from an Excel dropdown (data validation) by matching text.
    Works even if the dropdown list is long.
    """
    cell = sheet.Cells(row, col)
    cell.Activate()
    time.sleep(0.3)

    # Get data validation formula
    try:
        formula = cell.Validation.Formula1  # e.g. "Sheet2!$A$1:$A$50" or "Option1,Option2,Option3"
    except Exception:
        raise ValueError(f"No dropdown found at cell ({row}, {col})")

    # Case 1: Inline list like "Option1,Option2,Option3"
    if "," in formula:
        options = [opt.strip() for opt in formula.split(",")]
    else:
        # Case 2: Reference to a range, resolve it
        ref_range = sheet.Range(formula.replace("=", ""))
        options = [str(c.Value).strip() for c in ref_range if c.Value]

    # Find desired option index
    if desired_value not in options:
        raise ValueError(f"Value '{desired_value}' not found in dropdown options {options}")

    option_index = options.index(desired_value) + 1

    # Now simulate keystrokes
    shell = win32.Dispatch("WScript.Shell")
    shell.SendKeys("%{DOWN}")  # open dropdown
    time.sleep(0.5)

    for _ in range(option_index - 1):
        shell.SendKeys("{DOWN}")
        time.sleep(0.05)

    shell.SendKeys("{ENTER}")
    time.sleep(0.3)

    print(f"✅ Selected '{desired_value}' in cell ({row}, {col})")


# -----------------------------
#  Excel Handling
# -----------------------------
def set_up_excel(product_data: dict) -> str:
    """
    Open Myntra template Excel, write cleaned product data, and save a SKU-specific copy.
    Returns path to the created file.
    """
    pythoncom.CoInitialize()
    excel = None
    wb = None
    sheet = None

    try:
        excel = win32.gencache.EnsureDispatch("Excel.Application")
        excel.Visible = True
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # template_path = os.path.join(base_dir, 'myntra_excel', f'{product_data["productType"]}.xlsx')
        template_path = os.path.join(base_dir, 'myntra_excel', 'Myntra-Sku-Template-2025-09-17.xlsx')
        output_filename = f"{product_data['sku']}.xlsx"
        output_path = os.path.join(base_dir, 'myntra_sku', output_filename)

        shutil.copyfile(template_path, output_path)

        wb = excel.Workbooks.Open(output_path)
        sheet = wb.Sheets('Necklace and Chains')
        row = 4

        # Map column numbers to product fields
        value_map = {
            1:1,
            2:1,
            3:  product_data['sku'],
            4:  product_data['productName'],
            5:  product_data['productName'],
            7:  "Mittal Distributors, 1st floor niladri galaxy, bidhan market, darjeeling, 734001",
            8:  "Mittal Distributors, 1st floor niladri galaxy, bidhan market, darjeeling, 734001",
            16: "Onesize",
            19: product_data['color'],
            21: "71171990",
            23: product_data['product_mrp'],
            # 25: product_data['color'],
            29: product_data['occasion'],
            32: product_data['description'],
            34: "Material: Alloy Care Instructions: Wipe your jewellery with a soft cloth after every use Always store your jewellery in a flat box to avoid accidental scratches Keep sprays and perfumes away from your jewellery Do not soak your jewellery in soap water Clean your jewellery using a soft brush Dipped in jewellery cleaning solution only",
            35: "Length: 28 inches",  # ✅ fixed spelling + format
            36: product_data['productName'],
            # 48: product_data['plating'],
            57: product_data['inventory'],
        }

        # Write values to sheet
        for col, val in value_map.items():
            type_into_cell(sheet, row, col, val)

        select_from_dropdown_by_text(sheet,row,6, "Gorkhastyle")
        select_from_dropdown_by_text(sheet,row,10,"India")
        select_from_dropdown(sheet,row,15,1)
        select_from_dropdown_by_text(sheet,row,17,"Onesize")
        select_from_dropdown(sheet,row,18,1)
        select_from_dropdown(sheet,row,24,2)
        select_from_dropdown_by_text(sheet,row,25,"Gold")
        select_from_dropdown(sheet,row,28,1)
        select_from_dropdown(sheet,row,29,4)
        select_from_dropdown_by_text(sheet,row,30,"2025")
        select_from_dropdown(sheet,row,31,1)
        select_from_dropdown_by_text(sheet,row,41,product_data['material'])
        select_from_dropdown_by_text(sheet,row,42,"NA")
        select_from_dropdown_by_text(sheet,row,45,"NA")
        select_from_dropdown(sheet,row,47,4)
        select_from_dropdown_by_text(sheet,row,48,"Gold Plated")
        select_from_dropdown(sheet,row,51,6)
        

        wb.Save()
        print(f"✅ Product '{product_data['sku']}' saved at: {output_path}")

        return output_path

    finally:
        if wb:
            wb.Close(SaveChanges=True)
        if excel:
            excel.Quit()
        del excel, wb, sheet
        gc.collect()
        pythoncom.CoUninitialize()


# -----------------------------
#  Selenium Automation
# -----------------------------
def open_myntra_website_and_upload(excel_path: str, sku_folder: str, sku: str):
    """
    Automates login & navigation to Myntra DIY catalog upload page.
    """
    driver = None
    try:
        driver = get_driver()
        wait = WebDriverWait(driver, 15)

        driver.get("https://partners.myntrainfo.com/DiyCataloguingV2")
        time.sleep(15)  # allow initial load

        if "login" in driver.current_url.lower():
            input("⚠️ Please log in to Myntra manually, then press Enter...")
            while "login" in driver.current_url.lower():
                time.sleep(5)

        driver.get("https://partners.myntrainfo.com/DiyCataloguingV2")
        time.sleep(5)

        upload_btn = driver.find_element(By.XPATH, '//button[normalize-space()="Add New DIY Products"]')
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", upload_btn)
        upload_btn.click()
        time.sleep(3)

        print(f"✅ Ready to upload SKU {sku} file: {excel_path}")

    except TimeoutException:
        print("❌ Login page did not load in time.")
    except Exception as e:
        print(f"❌ Unexpected Selenium error: {e}")
    finally:
        if driver:
            driver.quit()


# -----------------------------
#  Orchestration
# -----------------------------
def automate_myntra_listing(product_data: dict, sku_folder: str):
    """
    Main entrypoint: prepares Excel, fills product data, and marks SKU as completed.
    """
    try:
        excel_path = set_up_excel(product_data)
        print(f"✅ Excel ready for SKU {product_data['sku']}: {excel_path}")
        # Uncomment to auto-upload:
        # open_myntra_website_and_upload(excel_path, sku_folder, product_data['sku'])
        mark_completed(product_data['sku'], "myntra")
    except Exception as e:
        print(f"❌ Failed to automate SKU {product_data['sku']}: {e}")
