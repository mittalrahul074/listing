from selenium.webdriver.common.by import By
import time, os
import random
import pyautogui
import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from sku_tracker import mark_completed, is_completed, all_completed

PROFILE_DIR = os.path.join(os.path.dirname(__file__), "meesho_profile")

def human_delay(min_seconds=0.5, max_seconds=2.0):
    """Add a random delay to simulate human behavior"""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)

def human_typing_delay():
    """Add a small random delay between keystrokes to simulate human typing"""
    time.sleep(random.uniform(0.05, 0.15))

def get_driver():
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument(f"--user-data-dir={PROFILE_DIR}")
    driver = uc.Chrome(options=chrome_options)
    return driver

def handle_unauthorized_brands_popup(driver):
    """
    Handles the popup that appears when 'unauthorized brands/illegal keywords' are found.
    It clicks the 'I understand' acknowledgement and then the 'Update Changes' button.

    Args:
        driver: The Selenium WebDriver instance.

    Returns:
        True if the popup was successfully handled, False otherwise.
    """
    wait = WebDriverWait(driver, 15) # Increased wait time for elements in this popup

    try:
        print("Attempting to handle 'unauthorized brands/illegal keywords' popup...")

        # 1. Locate and click the 'I understand' checkbox/container
        # We target the <p> tag that contains the specific text, as it's often clickable.
        understand_checkbox_xpath = '//p[contains(text(), "I understand that") and contains(text(), "all products from this catalog are not branded or illegal to sell")]'
        
        understand_checkbox_elem = wait.until(
            EC.element_to_be_clickable((By.XPATH, understand_checkbox_xpath))
        )
        
        # Ensure it's in view before clicking
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", understand_checkbox_elem)
        human_delay(0.3, 0.8) # Small pause for rendering/stability
        understand_checkbox_elem.click()
        print("✅ Clicked 'I understand' checkbox/container.")

        # 2. Locate and click the 'Update Changes' button
        # This button is initially disabled and becomes enabled after the checkbox is clicked.
        update_changes_button_xpath = '//button[.//span[normalize-space(text())="Update Changes"]]'
        
        # Wait until the button is no longer disabled and is clickable
        update_changes_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, update_changes_button_xpath))
        )
        
        # Ensure it's in view before clicking
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", update_changes_button)
        human_delay(0.3, 0.8) # Small pause
        update_changes_button.click()
        print("✅ Clicked 'Update Changes' button.")
        
        return True

    except TimeoutException:
        print("⚠️ Timeout: Elements for 'unauthorized brands/illegal keywords' popup not found or not clickable within the given time.")
        return False
    except ElementClickInterceptedException:
        print("⚠️ ElementClickInterceptedException: Another element is covering the target. Attempting JavaScript click.")
        # Sometimes a direct click fails, try JavaScript click as a fallback
        try:
            driver.execute_script("arguments[0].click();", understand_checkbox_elem)
            human_delay(0.3, 0.8)
            update_changes_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, update_changes_button_xpath))
            )
            driver.execute_script("arguments[0].click();", update_changes_button)
            print("✅ Handled popup with JavaScript click fallback.")
            return True
        except Exception as js_err:
            print(f"❌ Failed to handle popup even with JavaScript click fallback: {js_err}")
            return False
    except Exception as e:
        print(f"❌ An unexpected error occurred while handling 'unauthorized brands' popup: {e}")
        return False
    
def select_gst_value(driver, gst_value, id):
    wait = WebDriverWait(driver, 20)
    gst_input = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, f'input[name="{id}"]'))
    )
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", gst_input)
    human_delay(0.3, 0.8)
    gst_input.click()
    human_delay(0.5, 1.0)

    if(id=="brand"):
        brand_input = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "css-mnn31")))
        human_delay(0.3, 0.8)
        
        # Simulate human typing for brand input
        for char in str(gst_value):
            brand_input.send_keys(char)
            human_typing_delay()
        
        human_delay(0.3, 0.8)

    menu_container = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, '//div[contains(@class,"MuiMenu-paper") and contains(@style, "opacity: 1")]')
        )
    )
    option_xpath = f'.//li[contains(@class,"MuiMenuItem-root")]//p[normalize-space(text())="{gst_value}"]'
    gst_option = menu_container.find_element(By.XPATH, option_xpath)
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", gst_option)
    human_delay(0.3, 0.8)
    gst_option.click()

    gst_input = driver.find_element(By.ID, f"{id}")
    actual_value = gst_input.get_attribute("value").strip()
    if actual_value == str(gst_value):
        return True
    else:
        raise ValueError(f"❌ GST value mismatch: expected {gst_value}, got {actual_value}")
    
def set_value(driver, value, id):
    wait = WebDriverWait(driver, 15)
    # Wait for the input to be present and interactable
    xpath = f"//input[@id='{id}']"
    wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
    def get_input():
        return driver.find_element(By.ID, id)
    for attempt in range(2):  # retry once if stale
        try:
            input = get_input()
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", input)
            input.clear()  # Only needed if field might not start empty
            human_delay(0.2, 0.5)  # Random delay
            
            # Simulate human typing with variable speed
            for char in str(value):
                input.send_keys(char)
                human_typing_delay()
            
            print(f"✅ Set {id} to {value}")
            break
        except Exception as e:
            print(f"⚠️ Element stale, retrying... (attempt {attempt + 1})")
            human_delay(1, 2)
            if attempt == 1:
                raise e

def select_free_size(driver):
    wait = WebDriverWait(driver, 20)
    size_container = wait.until(EC.presence_of_element_located((
        By.XPATH,
        '//p[text()="Size"]/ancestor::div[contains(@class, "css-gvoll6")]'
    )))
    dropdown_section = size_container.find_element(
        By.CLASS_NAME, "css-1ozu3yc"
    )
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dropdown_section)
    human_delay(0.2, 0.5)
    dropdown_section.click()
    menu_container = wait.until(EC.visibility_of_element_located((
        By.XPATH, '//div[contains(@class,"MuiMenu-paper") and contains(@style,"opacity: 1")]'
    )))
    free_size_p = menu_container.find_element(By.XPATH, './/p[normalize-space()="Free Size"]')
    wrapper_div = free_size_p.find_element(By.XPATH, './parent::div')
    checkbox_svg = wrapper_div.find_element(By.TAG_NAME, 'svg')
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox_svg)
    human_delay(0.3, 0.8)
    checkbox_svg.click()
    apply_button = menu_container.find_element(By.XPATH, './/button[.//span[normalize-space()="Apply"]]')
    human_delay(0.2, 0.5)
    apply_button.click()

def keywords_conv(keywords):
    # sperate the keywords by "|" insted of ","
    if "," in keywords:
        keywords = keywords.replace(",", "|")
    
    return keywords


def automate_meesho_listing(product_data, sku_folder):
    driver = None
    try:
        driver = get_driver()
        driver.get('https://supplier.meesho.com/panel/v3/new/root/login?utm_source=meesho&utm_medium=website&utm_campaign=header')
        human_delay(2, 4)  # Random delay after page load

        if "login" in driver.current_url:
            input("Log in to Meesho in the opened browser, then press Enter here to continue...")
            human_delay(2, 4)
            while "login" in driver.current_url:
                print("⏳ Waiting for login to complete...")
                human_delay(1, 2)

        driver.get('https://supplier.meesho.com/panel/v3/new/cataloging/yoxpf/catalogs/single/select-category')
        human_delay(2, 4)  # Random delay after navigation

        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-testid="your-categories-list"]')))
        human_delay(1, 2)

        categories = driver.find_elements(By.CSS_SELECTOR, '[data-testid="your-categories-list"]')
        clicked = False
        for cat in categories:
            try:
                h5 = cat.find_element(By.TAG_NAME, 'h5')
                if 'Necklaces & Chains' in h5.text:
                    driver.execute_script("arguments[0].scrollIntoView(true);", cat)
                    human_delay(0.5, 1.0)
                    cat.click()
                    print("✅ Clicked on 'Necklaces & Chains'")
                    clicked = True
                    break
            except Exception as e:
                print(f"⚠️ Error with one category block: {e}")

        if not clicked:
            print("❌ 'Necklaces & Chains' not found.")
            return

        all_image_files = [os.path.abspath(os.path.join(sku_folder, f)) for f in sorted(os.listdir(sku_folder))]
        if not all_image_files:
            raise FileNotFoundError("No images found in SKU folder.")
        primary_image = all_image_files[0]
        secondary_images = all_image_files[1:]

        wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "css-1hs0f8l")))
        add_image_btn = driver.find_element(By.CLASS_NAME, "css-1hs0f8l") 
        driver.execute_script("arguments[0].scrollIntoView(true);", add_image_btn)
        human_delay(0.5, 1.0)
        add_image_btn.click()
        print("✅ Clicked on 'Add Image' button")
        human_delay(1.5, 2.5)
        pyautogui.write(f'"{primary_image}"')
        human_delay(0.5, 1.0)
        pyautogui.press('enter')
        print("✅ Primary image submitted.")
        human_delay(1.5, 2.5)

        wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "css-u0efm2")))
        continue_btn = driver.find_element(By.CLASS_NAME, "css-u0efm2")
        driver.execute_script("arguments[0].scrollIntoView(true);", continue_btn)
        human_delay(0.5, 1.0)
        continue_btn.click()
        print("✅ Clicked on 'Continue' button to proceed with product details.")

        human_delay(2, 4)  # Wait for form to load

        wait.until(EC.presence_of_element_located((By.ID, "supplier_gst_percent")))
        print("✅ GST field is now visible.")

        # Fill form fields with human-like timing
        select_gst_value(driver, product_data['gst'], "supplier_gst_percent")
        human_delay(1, 2)
        select_gst_value(driver, product_data['hsnCode'], "hsn_code")
        human_delay(1, 2)
        set_value(driver, product_data['netWeight'], "product_weight_in_gms")
        human_delay(1, 2)
        set_value(driver, product_data['sku'], "supplier_product_id")
        human_delay(1, 2)
        set_value(driver, product_data['productName']+" "+keywords_conv(product_data['keywords']) , "product_name") 
        human_delay(1, 2)
        select_free_size(driver)
        human_delay(1, 2)
        price = (int(product_data['meesho_price'])-80)
        set_value(driver, price, "meesho_price")
        human_delay(1, 2)
        set_value(driver, product_data['product_mrp'], "product_mrp")
        human_delay(1, 2)
        set_value(driver, product_data['inventory'],"inventory")
        human_delay(1, 2)
        select_gst_value(driver, product_data['material'], "base_metal")
        human_delay(1, 2)
        select_gst_value(driver, product_data['color'], "color")
        human_delay(1, 2)
        select_gst_value(driver, "Necklaces", "generic_name")
        human_delay(1, 2)
        select_gst_value(driver, product_data['netQuantity'], "multipack")
        human_delay(1, 2)
        select_gst_value(driver, product_data['occasion'], "occasion")
        human_delay(1, 2)
        select_gst_value(driver, product_data['plating'], "plating")
        human_delay(1, 2)
        select_gst_value(driver, "cm", "product_dimension_unit")
        human_delay(1, 2)
        select_gst_value(driver, product_data['size'], "sizing")
        human_delay(1, 2)
        select_gst_value(driver, product_data['stoneType'], "stone_type")
        human_delay(1, 2)
        select_gst_value(driver, "Hand-crafted","trend")
        human_delay(1, 2)
        select_gst_value(driver, "India", "country_of_origin")
        human_delay(1, 2)
        set_value(driver,"Kangan Siliguri", "manufacturer_name")
        human_delay(1, 2)
        set_value(driver,"1st fllor rg complex ss market, siliguri darjeeling, gorkhaland", "manufacturer_address")
        human_delay(1, 2)
        set_value(driver , "734001", "manufacturer_pincode")
        human_delay(1, 2)
        set_value(driver,"Kangan Siliguri", "packer_name")
        human_delay(1, 2)
        set_value(driver,"1st fllor rg complex ss market, siliguri darjeeling, gorkhaland", "packer_address")
        human_delay(1, 2)
        set_value(driver , "734001", "packer_pincode")
        human_delay(1, 2)
        select_gst_value(driver, "Gorkhastyle", "brand")
        human_delay(1, 2)
        select_gst_value(driver, product_data['type'],"type")
        human_delay(1, 2)

        textarea = wait.until(EC.presence_of_element_located((
            By.XPATH, '//textarea[@id="comment"]'
        )))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", textarea)
        textarea.clear()
        
        # Simulate human typing for description
        for char in f"{product_data['description']}\n\n":
            textarea.send_keys(char)
            human_typing_delay()
        
        print("✅ Description text set.")
        human_delay(1, 2)

        if len(all_image_files) <= 1:
            print("🟡 Only primary image found. Skipping 'Add Images'.")
        else:
            try:
                try:
                    wait.until(EC.element_to_be_clickable((By.CLASS_NAME,"css-azct56")))
                except TimeoutException:
                    print("Timeout waiting for blocking element to disappear, proceeding anyway.")
                add_more_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-testid="add-more"]')))
                driver.execute_script("arguments[0].scrollIntoView(true);", add_more_btn)
                human_delay(0.5, 1.0)
                driver.execute_script("arguments[0].click();", add_more_btn)
                print("✅ Clicked on 'Add More Images' button.")
                human_delay(1.5, 2.5)
                
                pyautogui.write('"{}"'.format('" "'.join(secondary_images)))
                human_delay(0.5, 1.0)
                pyautogui.press('enter')
                print(f"✅ Uploaded {len(secondary_images)} secondary image(s).")
                human_delay(1.5, 2.5)
            except Exception as e:
                print(f"⚠️ Error clicking 'Add More Images': {e}")
                print("🟡 Skipping secondary images upload due to error.")
                return

        try:
            submit_btn_xpath = '//button[.//span[normalize-space(text())="Submit Catalog"]]'
            submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, submit_btn_xpath)))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)
            human_delay(0.5, 1.0)
            submit_btn.click()
            print("✅ Clicked on 'Submit Catalog' button.")
            human_delay(1.5, 2.5)
        
        except TimeoutException:
            print("❌ Submit button not found or not clickable. Check if all required fields are filled.")
            return
        
        wait = WebDriverWait(driver, 15)
        try:
            dialog_xpath = '//div[@role="dialog" and contains(@class, "MuiDialog-paper")]'
            wait.until(EC.visibility_of_element_located((By.XPATH, dialog_xpath)))
            print("✅ Submission dialog appeared.")
            proceed_btn_xpath = f'{dialog_xpath}//button[.//span[normalize-space(text())="Proceed"]]'
            proceed_btn = wait.until(EC.element_to_be_clickable((By.XPATH, proceed_btn_xpath)))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", proceed_btn)
            human_delay(0.5, 1.0)
            proceed_btn.click()
            print("✅ Clicked 'Proceed' in submission dialog.")
            mark_completed(product_data['sku'], "meesho")
            return True
        except TimeoutException as e:
            print(f"❌ Error clicking 'Proceed' button: {e}")
            return False

        # Optionally close browser at end
        # driver.quit()

    except Exception as e:
        import traceback
        print("=== Exception Trace ===")
        traceback.print_exc()
        print(f"Error type: {type(e)}")
        if driver is not None:
            try:
                driver.save_screenshot('debug_crash.png')
                driver.quit()
            except Exception:
                pass

# Usage:
# automate_meesho_listing(product_data, sku_folder)