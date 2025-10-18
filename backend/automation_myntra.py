import pyautogui
import os, re, gc, time, shutil, pythoncom
import win32com.client as win32
import win32gui
import undetected_chromedriver as uc

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from sku_tracker import mark_completed, is_completed, all_completed
from fuzzywuzzy import fuzz


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
    # print(f" -> Writing cell[{row}, {column}] = {repr(cleaned)}")
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
    # print(f" -> Selecting option index {option_index} in cell ({row}, {col})")
    
    cell = sheet.Cells(row, col)
    cell.Activate()
    time.sleep(0.5)
    # print("   Cell activated.")
    shell = win32.Dispatch("WScript.Shell")
    try:
        shell.AppActivate("Excel")
        time.sleep(0.3)
    except Exception:
        print("   Could not activate Excel window.")
        
    # Open the dropdown need to press Alt + Down Arrow
    time.sleep(0.5)
    # Prefer bringing Excel to foreground via its HWND then send Alt+Down using explicit key sequence,
    # which tends to be more reliable than hotkey() on Windows for some environments.
    try:
        # Attempt to obtain the Excel window handle from the sheet object
        hwnd = None
        try:
            hwnd = int(sheet.Application.Hwnd)
        except Exception:
            try:
                hwnd = int(sheet.Parent.Application.Hwnd)
            except Exception:
                hwnd = None

        if hwnd:
            try:
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.25)
            except Exception:
                # If SetForegroundWindow fails, continue and try sending keys anyway
                pass

        # Use an explicit keyDown/press/keyUp sequence rather than hotkey()
        pyautogui.keyDown('alt')
        pyautogui.press('down')
        pyautogui.keyUp('alt')
        # print("   Dropdown opened via pyautogui key sequence.")
    except Exception:
        # Fallback to SendKeys if pyautogui approach fails
        try:
            shell.SendKeys("%{DOWN}")
            # print("   Dropdown opened via SendKeys fallback.")
        except Exception:
            print("   Failed to open dropdown via pyautogui and SendKeys.")
    time.sleep(0.5)
    # print("   Dropdown opened.")
    # print("   Dropdown opened.")
    # Move down option_index - 1 times
    for _ in range(option_index):
        shell.SendKeys("{DOWN}")
        time.sleep(0.2)

    # Confirm selection
    shell.SendKeys("{ENTER}")
    time.sleep(0.3)

def normalize_text(text):
    """Normalize text for better matching"""
    if not text:
        return ""
    
    # Convert to lowercase and strip whitespace
    text = str(text).lower().strip()
    
    # Remove special characters and numbers
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove common plural forms
    if text.endswith('s') and len(text) > 3:
        text = text[:-1]
    
    return text

def smart_field_mapper(value, options, default_value=None):
    """Smart mapping with fallback logic and default value option"""
    if not options:
        # print(f"⚠️ No options available for mapping value: {value}")
        return default_value if default_value is not None else value
    
    # Strategy 1: Exact match
    if value in options:
        # print(f"✅ Exact match found for '{value}'")
        return value
    
    # Strategy 2: Normalized match
    normalized_value = normalize_text(value)
    for option in options:
        if normalized_value == normalize_text(option):
            # print(f"✅ Normalized match found: '{value}' → '{option}'")
            return option
    
    # Strategy 3: Contains match
    for option in options:
        if normalized_value in normalize_text(option) or normalize_text(option) in normalized_value:
            # print(f"✅ Contains match found: '{value}' → '{option}'")
            return option
    
    # Strategy 4: Fuzzy matching
    best_match = None
    best_match_score = 0
    for option in options:
        score = fuzz.ratio(normalized_value, normalize_text(option))
        if score > best_match_score and score > 70:  # Only accept good matches
            best_match_score = score
            best_match = option
    
    if best_match:
        # print(f"✅ Fuzzy match found: '{value}' → '{best_match}' (score: {best_match_score})")
        return best_match
    
    # Strategy 5: Use default value if provided, otherwise first option
    if default_value is not None and default_value in options:
        # print(f"⚠️ No good match found for '{value}', using specified default: '{default_value}'")
        return default_value
    elif default_value is not None and default_value not in options:
        # print(f"⚠️ Default value '{default_value}' not found in options, using first available option: '{options[0]}'")
        return options[0]
    else:
        # print(f"⚠️ No good match found for '{value}', using first available option: '{options[0]}'")
        return options[0]

def select_from_dropdown_by_text(sheet, row, col, desired_value):
    """
    Select a value from an Excel dropdown (data validation) by matching text.
    Works even if the dropdown list is long.
    """
    # inseart # print between lines to debug the issue
    cell = sheet.Cells(row, col)
    cell.Activate()
    time.sleep(0.3)

    # print(f"Selecting '{desired_value}' in cell ({row}, {col})")

    # Get data validation formula
    try:
        formula = cell.Validation.Formula1  # e.g. "Sheet2!$A$1:$A$50" or "Option1,Option2,Option3"
    except Exception:
        raise ValueError(f"No dropdown found at cell ({row}, {col})")
    
    # print(f"Dropdown formula: {formula}")

    # Case 1: Inline list like "Option1,Option2,Option3"
    if "," in formula:
        options = [opt.strip() for opt in formula.split(",")]
    else:
        # Case 2: Reference to a range, resolve it
        # ref_range = sheet.Range(formula.replace("=", ""))
        # options = [str(c.Value).strip() for c in ref_range if c.Value]
        ref_text = formula.replace("=", "")
        # print(f"Resolving reference: {ref_text}")

        # Check if reference points to another sheet
        if "!" in ref_text:
            sheet_name, cell_range = ref_text.split("!", 1)
            wb = sheet.Parent  # get workbook object
            ref_sheet = wb.Sheets(sheet_name.replace("'", ""))  # remove quotes if any
            ref_range = ref_sheet.Range(cell_range)
        else:
            ref_range = sheet.Range(ref_text)

        options = [str(c.Value).strip() for c in ref_range if c.Value]
        # print(f"Dropdown options loaded: {len(options)} items")

    # print(f"Dropdown options: {options}")
    # Find desired option index
    if desired_value not in options:
        # print(f"Value '{desired_value}' not found in dropdown options {options}")
        desired_value = smart_field_mapper(desired_value, options)

    option_index = options.index(desired_value) + 1
    # print(f"Found '{desired_value}' at index {option_index}")

    if option_index > 20:
        # print(f"⚠️ Option index {option_index} is large; using typing to jump faster.")
        # Type initial characters to jump closer to desired option
        shell = win32.Dispatch("WScript.Shell")
        value_to_type = options[option_index -1][:min(5, len(options[option_index -1])//2)]
        # print(f"   Typing '{value_to_type}' to jump to option faster.")
        shell.SendKeys(value_to_type)
        time.sleep(10.0)
        #update option list after typing only including options that start with typed text
        filtered_options = [opt for opt in options if opt.lower().startswith(value_to_type.lower())]
        if desired_value in filtered_options:
            option_index = filtered_options.index(desired_value) + 1   
    # Now simulate keystrokes
    select_from_dropdown(sheet, row, col, option_index)

    # print(f"✅ Selected '{desired_value}' in cell ({row}, {col})")


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
        template_path = os.path.join(base_dir, 'myntra_excel', 't.xlsx')
        output_filename = f"{product_data['sku']}.xlsx"
        output_path = os.path.join(base_dir, 'myntra_sku', output_filename)

        shutil.copyfile(template_path, output_path)

        wb = excel.Workbooks.Open(output_path)
        sheet = wb.Sheets('Necklace and Chains')
        row = 4

        # print("Dropping down selections...")
        # select_from_dropdown_by_text(sheet,row,6,"Gorkhastyle")
        select_from_dropdown_by_text(sheet,row,48,"Gold Plated")
        # print("Dropped 1")
        # select_from_dropdown_by_text(sheet,row,10,"India")
        select_from_dropdown(sheet,row,15,1)
        select_from_dropdown_by_text(sheet,row,17,"Onesize")
        select_from_dropdown(sheet,row,18,1)
        select_from_dropdown(sheet,row,24,2)
        select_from_dropdown_by_text(sheet,row,25,"Gold")
        select_from_dropdown(sheet,row,28,1)
        select_from_dropdown_by_text(sheet,row,30,"2025")
        select_from_dropdown(sheet,row,31,1)
        select_from_dropdown_by_text(sheet,row,40,"Ethnic")
        try:
            select_from_dropdown_by_text(sheet,row,41,product_data['material'])
        except Exception:
            select_from_dropdown_by_text(sheet,row,41,"Alloy")
        select_from_dropdown_by_text(sheet,row,42,"NA")
        select_from_dropdown_by_text(sheet,row,43,"Necklace")
        select_from_dropdown_by_text(sheet,row,45,"NA")
        select_from_dropdown(sheet,row,47,4)
        select_from_dropdown(sheet,row,51,6)

        # Map column numbers to product fields
        value_map = {
            2:1,
            3:  product_data['sku'],
            4:  product_data['productName'],
            5:  product_data['sku'],
            7:  "Mittal Distributors, 1st floor niladri galaxy, bidhan market, darjeeling, 734001",
            8:  "Mittal Distributors, 1st floor niladri galaxy, bidhan market, darjeeling, 734001",
            16: "Onesize",
            19: product_data['color'],
            21: "71171990",
            23: product_data['product_mrp'],
            # 25: product_data['color'],
            # 29: product_data['occasion'],
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
            # human delay
            time.sleep(0.3)

        

        wb.Save()

        return output_path
        # print(f"✅ Product '{product_data['sku']}' saved at: {output_path}")

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

        # print(f"✅ Ready to upload SKU {sku} file: {excel_path}")

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
        # print(f"✅ Excel ready for SKU {product_data['sku']}: {excel_path}")
        # Uncomment to auto-upload:
        # open_myntra_website_and_upload(excel_path, sku_folder, product_data['sku'])
        mark_completed(product_data['sku'], "myntra")
    except Exception as e:
        print(f"❌ Failed to automate SKU {product_data['sku']}: {e}")
