import os, time, random
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
import pyautogui
from selenium.webdriver.support.ui import Select
from fuzzywuzzy import fuzz
import re
from sku_tracker import mark_completed, is_completed, all_completed

PROFILE_DIR = os.path.join(os.path.dirname(__file__), "flipkart_profile")

def human_delay(min_seconds=0.5, max_seconds=2.0):
    """Add a random delay to simulate human behavior"""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)

def human_typing_delay():
    """Add a small random delay between keystrokes to simulate human typing"""
    time.sleep(random.uniform(0.05, 0.15))

def get_driver():
    opts = uc.ChromeOptions()
    opts.add_argument(f"--user-data-dir={PROFILE_DIR}")
    opts.add_argument("--profile-directory=flipkart_profile")
    return uc.Chrome(options=opts)

def login_if_needed(driver):
    driver.get("https://seller.flipkart.com/index.html#dashboard")
    human_delay(3, 5)  # Random delay after page load
    
    print("DEBUG URL:", driver.current_url)
    current_url = driver.current_url.lower()
    if "referral_url" in current_url:
        print("⚠️ Login required. Please log in manually.")
        input("Log in on Flipkart, then press Enter...")
        while "referral_url" in driver.current_url.lower():
            human_delay(0.5, 1.5)

        print("✅ Login successful, continuing automation.")

def navigate_to_listing(driver):
    wait = WebDriverWait(driver, 15)
    # Direct URL to bulk-upload page (adjust if changed)
    driver.get("https://seller.flipkart.com/index.html#dashboard/addListings/single?vertical=necklace_chain&vid=175")
    human_delay(2, 4)  # Random delay after navigation
    
    try:
        modal_close_button = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.XPATH, '//div[contains(@class,"ReactModal__Content")]//button[normalize-space()="Close"]'))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", modal_close_button)
        human_delay(0.3, 0.8)
        modal_close_button.click()
        print("✅ Closed tutorial modal.")
        human_delay(1, 2)
    except TimeoutException:
        print("ℹ️ No tutorial modal found, continuing...")

    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="test-input"]'))
    )
    print("✅ Navigated to Flipkart bulk listing page.")
    
    input = driver.find_element(By.CSS_SELECTOR, '[data-testid="test-input"]')
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", input)
    human_delay(0.5, 1.0)
    input.clear()
    human_delay(0.2, 0.5)
    
    # Simulate human typing with delays between characters
    for char in "Gorkhastyle":
        input.send_keys(char)
        human_typing_delay()
    
    print("✅ Entered 'Gorkhastyle' in search input.")
    human_delay(1, 2)
    
    check_brand_btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="button"]'))
    )
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'})", check_brand_btn)
    human_delay(0.5, 1.0)
    check_brand_btn.click()
    print("✅ Clicked 'Check Brand' button.")
    human_delay(2, 4)  # Wait for brand check to complete
    
    brand_info_container = wait.until(
        EC.visibility_of_element_located((By.CLASS_NAME, "styles__BrandNameInfoContainer-sc-ut1ggx-0"))
    )
    create_listing_btn = brand_info_container.find_element(By.CSS_SELECTOR, 'button[data-testid="button"]')
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'})", create_listing_btn)
    human_delay(0.5, 1.0)
    create_listing_btn.click()
    print("✅ Clicked on 'Create new listing' button.")
    human_delay(2, 4)  # Wait for page to load

def wait_for_section_available(driver, title_text, max_retries=3):
    """Enhanced wait strategy with retry mechanism"""
    wait = WebDriverWait(driver, 20)

    for attempt in range(max_retries):
        try:
            # Wait for page to stabilize
            human_delay(1.5, 3.0)
            
            # Re-fetch all cards to avoid stale references
            cards = wait.until(EC.presence_of_all_elements_located(
                (By.XPATH, '//div[contains(@class, "styles__Card-sc-1ipgdlp-0")]')
            ))
            
            # Handle dynamic titles like "Product Photos (0/5)" by using contains()
            base_title = title_text.split('(')[0].strip()  # Extract base title without count
            
            for i, card in enumerate(cards):
                try:
                    span = card.find_element(By.XPATH, f'.//span[contains(text(), "{base_title}")]')
                    print(f"✅ Found section: '{span.text}' in card {i}")
                    return card, i
                except Exception:
                    continue
                    
            if attempt < max_retries - 1:
                print(f"⚠️ Attempt {attempt + 1} failed, retrying...")
                human_delay(2, 4)
                continue
            else:
                raise Exception(f"❌ Section with base title '{base_title}' not found after {max_retries} attempts")
                
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠️ Attempt {attempt + 1} failed: {e}")
                human_delay(2, 4)
                continue
            else:
                raise

def is_section_expanded(driver, title_text):
    """Check if a section is already expanded"""
    try:
        # Find the section card by looking for span text that contains the base title
        # Handle dynamic titles like "Product Photos (0/5)" by using contains()
        base_title = title_text.split('(')[0].strip()  # Extract base title without count
        
        # Find all section cards
        cards = driver.find_elements(By.XPATH, '//div[contains(@class, "styles__Card-sc-1ipgdlp-0")]')
        
        for card in cards:
            try:
                # Look for span with title that contains the base title
                span = card.find_element(By.XPATH, f'.//span[contains(text(), "{base_title}")]')
                if span:
                    # Found the right card, now check if it's expanded
                    
                    # Strategy 1: Look for form elements within the section card
                    form_elements = card.find_elements(By.XPATH, './/input | .//select | .//textarea')
                    
                    # Strategy 2: Look for expanded content wrapper (not the collapsed one)
                    expanded_wrapper = card.find_elements(By.XPATH, './/div[contains(@class, "styles__Wrapper-sc-oojhsj-1") and not(contains(@class, "jtQedq"))]')
                    
                    # Strategy 3: Check if EDIT button is visible (section is collapsed)
                    edit_button = card.find_elements(By.XPATH, './/button[normalize-space()="EDIT"]')
                    
                    # Section is expanded if we have form elements OR expanded wrapper, AND no EDIT button
                    is_expanded = (len(form_elements) > 0 or len(expanded_wrapper) > 0) and len(edit_button) == 0
                    
                    print(f"🔍 Section '{span.text.strip()}' - Form elements: {len(form_elements)}, Expanded wrapper: {len(expanded_wrapper)}, EDIT button: {len(edit_button)}, Expanded: {is_expanded}")
                    
                    return is_expanded
                    
            except Exception as e:
                continue
        
        # If we get here, section wasn't found
        print(f"⚠️ Section with base title '{base_title}' not found")
        return False
        
    except Exception as e:
        print(f"⚠️ Error checking if section '{title_text}' is expanded: {e}")
        return False

def wait_for_section_expanded(driver, title_text, timeout=15):
    """Wait for section to be fully expanded with better verification"""
    wait = WebDriverWait(driver, timeout)
    try:
        print(f"⏳ Waiting for section '{title_text}' to expand...")
        wait.until(lambda d: is_section_expanded(d, title_text))
        print(f"✅ Section '{title_text}' is now expanded")
        
        # Additional verification - wait for form elements to be present
        base_title = title_text.split('(')[0].strip()  # Extract base title without count
        
        if "Product Photos" in base_title:
            # For Product Photos, wait for thumbnail elements
            wait.until(EC.presence_of_element_located((By.ID, "thumbnail_0")))
            print(f"✅ Section '{title_text}' form elements are ready")
        else:
            # For other sections, wait for any input/select elements
            # Find the section card using the base title
            cards = driver.find_elements(By.XPATH, '//div[contains(@class, "styles__Card-sc-1ipgdlp-0")]')
            section_card = None
            for card in cards:
                try:
                    span = card.find_element(By.XPATH, f'.//span[contains(text(), "{base_title}")]')
                    if span:
                        section_card = card
                        break
                except:
                    continue
            
            if section_card:
                wait.until(lambda d: len(section_card.find_elements(By.XPATH, './/input | .//select | .//textarea')) > 0)
                print(f"✅ Section '{title_text}' form elements are ready")
            else:
                print(f"⚠️ Could not find section card for '{title_text}'")
        
        human_delay(1, 2)  # Small delay after expansion
        return True
    except TimeoutException:
        print(f"❌ Section '{title_text}' did not expand properly within {timeout} seconds")
        return False

def open_section_by_title(driver, title_text, max_retries=3):
    """Enhanced section opening with better state management and retry logic"""
    print(f"📂 Attempting to expand section: {title_text}...")
    
    # First check if section is already expanded
    if is_section_expanded(driver, title_text):
        print(f"✅ Section '{title_text}' is already expanded.")
        return

    for attempt in range(max_retries):
        try:
            print(f"🔄 Attempt {attempt + 1}/{max_retries} to expand section: {title_text}")
            
            card, card_index = wait_for_section_available(driver, title_text)

            # Scroll the card into view
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
            human_delay(1, 2)
            
            # Try to find and click the EDIT button
            edit_button = card.find_element(By.XPATH, './/button[normalize-space()="EDIT"]')
            
            # Wait for button to be clickable
            wait = WebDriverWait(driver, 10)
            wait.until(EC.element_to_be_clickable(edit_button))
            
            # Click using JavaScript to avoid interception
            driver.execute_script("arguments[0].click();", edit_button)
            print(f"✅ Clicked 'EDIT' on section: {title_text}")
            
            # Wait for section to expand and DOM to stabilize
            human_delay(2, 4)
            
            # Verify section expanded
            if wait_for_section_expanded(driver, title_text):
                print(f"✅ Successfully expanded section: {title_text}")
                return
            else:
                print(f"⚠️ Section expansion verification failed on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    human_delay(2, 4)
                    continue
                else:
                    raise Exception(f"Section expansion verification failed after {max_retries} attempts")
            
        except ElementClickInterceptedException:
            print(f"⚠️ Click intercepted on attempt {attempt + 1}, trying fallback method...")
            try:
                # Fallback: click the entire card
                driver.execute_script("arguments[0].click();", card)
                print(f"✅ Clicked section card to expand: {title_text}")
                human_delay(2, 4)
                if wait_for_section_expanded(driver, title_text):
                    print(f"✅ Successfully expanded section: {title_text} using fallback method")
                    return
                else:
                    print(f"⚠️ Fallback method failed on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        human_delay(2, 4)
                        continue
            except Exception as fallback_error:
                print(f"⚠️ Fallback method error on attempt {attempt + 1}: {fallback_error}")
                if attempt < max_retries - 1:
                    human_delay(2, 4)
                    continue
                
        except Exception as e:
            print(f"⚠️ Error opening section '{title_text}' on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                print(f"🔄 Retrying in 2-4 seconds...")
                human_delay(2, 4)
                continue
            else:
                # Final attempt - try alternative approach
                try:
                    print(f"🔄 Final attempt: trying alternative clickable element...")
                    clickable_element = card.find_element(By.XPATH, './/button | .//div[contains(@class, "clickable")]')
                    driver.execute_script("arguments[0].click();", clickable_element)
                    print(f"✅ Clicked alternative element in section: {title_text}")
                    human_delay(2, 4)
                    if wait_for_section_expanded(driver, title_text):
                        print(f"✅ Successfully expanded section: {title_text} using alternative method")
                        return
                    else:
                        raise Exception("Alternative method failed verification")
                except Exception as e2:
                    print(f"❌ All methods failed to open section '{title_text}': {e2}")
                    raise
    
    # If we get here, all retries failed
    raise Exception(f"Failed to open section '{title_text}' after {max_retries} attempts")

def wait_for_dom_stability(driver, timeout=10):
    """Wait for DOM to become stable"""
    wait = WebDriverWait(driver, timeout)
    
    def dom_is_stable(driver):
        try:
            # Check if the expected number of cards are present and stable
            cards = driver.find_elements(By.XPATH, '//div[contains(@class, "styles__Card-sc-1ipgdlp-0")]')
            return len(cards) >= 3  # Expecting at least 3 main sections
        except:
            return False
    
    wait.until(dom_is_stable)
    print("✅ DOM appears stable")
    human_delay(1, 2)

def verify_product_photos_section_ready(driver, timeout=10):
    """Verify that Product Photos section is fully ready for image upload"""
    wait = WebDriverWait(driver, timeout)
    
    try:
        print("🔍 Verifying Product Photos section is ready...")
        
        # Check if section is expanded (handle dynamic titles)
        if not is_section_expanded(driver, "Product Photos"):
            print("❌ Product Photos section is not expanded")
            return False
        
        # Wait for thumbnail elements to be present
        wait.until(EC.presence_of_element_located((By.ID, "thumbnail_0")))
        print("✅ Thumbnail elements found")
        
        # Wait for at least one thumbnail to be clickable
        wait.until(EC.element_to_be_clickable((By.ID, "thumbnail_0")))
        print("✅ Thumbnail elements are clickable")
        
        # Check if upload button is present (optional check)
        try:
            upload_btn = driver.find_element(By.XPATH, '//button[span[text()="Upload Photo"]]')
            print("✅ Upload button found")
        except:
            print("⚠️ Upload button not immediately visible (may appear after clicking thumbnail)")
        
        print("✅ Product Photos section is ready for image upload")
        return True
        
    except TimeoutException:
        print("❌ Product Photos section is not ready within timeout")
        return False
    except Exception as e:
        print(f"❌ Error verifying Product Photos section: {e}")
        return False

def find_and_click_product_photos_edit(driver):
    """Find and click the EDIT button specifically for Product Photos section"""
    try:
        print("🔍 Looking for Product Photos section EDIT button...")
        
        # Find all section cards
        cards = driver.find_elements(By.XPATH, '//div[contains(@class, "styles__Card-sc-1ipgdlp-0")]')
        print(f"🔍 Found {len(cards)} section cards")
        
        for i, card in enumerate(cards):
            try:
                # Look for span with title that contains "Product Photos"
                span = card.find_element(By.XPATH, './/span[contains(text(), "Product Photos")]')
                if span:
                    print(f"✅ Found Product Photos section in card {i}: '{span.text.strip()}'")
                    
                    # Look for EDIT button within this card
                    edit_button = card.find_element(By.XPATH, './/button[normalize-space()="EDIT"]')
                    
                    if edit_button:
                        print("✅ Found EDIT button, clicking it...")
                        # Scroll into view and click
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", edit_button)
                        human_delay(0.5, 1.0)
                        driver.execute_script("arguments[0].click();", edit_button)
                        print("✅ Successfully clicked EDIT button for Product Photos section")
                        return True
                    else:
                        print("❌ EDIT button not found in Product Photos section")
                        return False
                        
            except Exception as e:
                continue
        
        print("❌ Product Photos section not found")
        return False
        
    except Exception as e:
        print(f"❌ Error finding/clicking Product Photos EDIT button: {e}")
        return False

def debug_product_photos_section(driver):
    """Debug function to show the HTML structure of Product Photos section"""
    try:
        print("\n🔍 Debugging Product Photos section structure:")
        print("=" * 60)
        
        # Find all section cards
        cards = driver.find_elements(By.XPATH, '//div[contains(@class, "styles__Card-sc-1ipgdlp-0")]')
        
        for i, card in enumerate(cards):
            try:
                # Get the span text
                spans = card.find_elements(By.XPATH, './/span')
                if spans:
                    span_text = spans[0].text.strip()
                    if "Product Photos" in span_text:
                        print(f"🎯 Found Product Photos section in card {i}: '{span_text}'")
                        
                        # Show the HTML structure
                        print(f"📋 Card {i} HTML structure:")
                        card_html = driver.execute_script("return arguments[0].outerHTML;", card)
                        print(card_html[:500] + "..." if len(card_html) > 500 else card_html)
                        
                        # Check for EDIT button
                        edit_buttons = card.find_elements(By.XPATH, './/button[normalize-space()="EDIT"]')
                        print(f"🔘 EDIT buttons found: {len(edit_buttons)}")
                        
                        if edit_buttons:
                            edit_button = edit_buttons[0]
                            print(f"🔘 EDIT button text: '{edit_button.text}'")
                            print(f"🔘 EDIT button classes: '{edit_button.get_attribute('class')}'")
                        
                        break
                        
            except Exception as e:
                print(f"⚠️ Error reading card {i}: {e}")
                continue
        
        print("=" * 60)
        
    except Exception as e:
        print(f"⚠️ Error debugging Product Photos section: {e}")

def log_section_states(driver):
    """Log the current state of all sections for debugging"""
    try:
        print("\n📊 Current Section States:")
        print("=" * 50)
        
        cards = driver.find_elements(By.XPATH, '//div[contains(@class, "styles__Card-sc-1ipgdlp-0")]')
        
        for i, card in enumerate(cards):
            try:
                # Get section title
                span = card.find_element(By.XPATH, './/span[1]')
                title = span.text.strip()
                
                # Check if expanded (handle dynamic titles)
                is_expanded = is_section_expanded(driver, title)
                status = "✅ EXPANDED" if is_expanded else "❌ COLLAPSED"
                
                # Check for EDIT button
                edit_buttons = card.find_elements(By.XPATH, './/button[normalize-space()="EDIT"]')
                edit_status = "EDIT button present" if edit_buttons else "No EDIT button"
                
                print(f"[{i}] {title}: {status} | {edit_status}")
                
            except Exception as e:
                print(f"[{i}] Error reading section: {e}")
        
        print("=" * 50)
        
    except Exception as e:
        print(f"⚠️ Error logging section states: {e}")

def upload_flipkart_images(driver, sku_folder):
    wait = WebDriverWait(driver, 20)

    # Step 1: Verify section is properly expanded before proceeding
    if not is_section_expanded(driver, "Product Photos"):
        print("❌ Product Photos section is not expanded. Cannot upload images.")
        raise Exception("Product Photos section must be expanded before uploading images.")

    # Step 2: Load images
    image_paths = [os.path.abspath(os.path.join(sku_folder, f))
                   for f in sorted(os.listdir(sku_folder))
                   if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

    if not image_paths:
        raise Exception("❌ No images found in SKU folder.")

    max_slots = min(6, len(image_paths))

    print(f"🖼️ Uploading {max_slots} image(s)...")

    for i in range(max_slots):
        print(f"\n▶️ Uploading image {i + 1}/{max_slots}: {os.path.basename(image_paths[i])}")

        try:
            # Step 3: Click the thumbnail to open that image slot
            thumb = wait.until(EC.element_to_be_clickable((By.ID, f"thumbnail_{i}")))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", thumb)
            human_delay(0.3, 0.8)
            thumb.click()
            human_delay(1, 2)

            # Step 4: Wait for "Upload Photo" button
            upload_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[span[text()="Upload Photo"]]')))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", upload_btn)
            driver.execute_script("arguments[0].click();", upload_btn)
            print("📤 Clicked Upload button.")

            # Step 5: Use pyautogui to upload
            human_delay(1, 2)
            pyautogui.write(f'"{image_paths[i]}"')
            human_delay(0.3, 0.8)
            pyautogui.press('enter')
            print(f"✅ Uploaded: {os.path.basename(image_paths[i])}")
            human_delay(12, 18)  # Allow time for image to upload with variation
            
        except Exception as e:
            print(f"❌ Error uploading image {i + 1}: {e}")
            print("⚠️ Continuing with next image...")
            continue

def set_input_value(driver, selector, value, b=By.ID):
    input_element = driver.find_element(b, selector)
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_element)
    human_delay(0.3, 0.8)
    input_element.clear()
    human_delay(0.2, 0.5)
    
    # Simulate human typing with variable speed
    for char in str(value):
        input_element.send_keys(char)
        human_typing_delay()
    
    print(f"✅ Set value for {selector}: {value}")
    human_delay(0.3, 0.8)

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
        print(f"⚠️ No options available for mapping value: {value}")
        return default_value if default_value is not None else value
    
    # Strategy 1: Exact match
    if value in options:
        print(f"✅ Exact match found for '{value}'")
        return value
    
    # Strategy 2: Normalized match
    normalized_value = normalize_text(value)
    for option in options:
        if normalized_value == normalize_text(option):
            print(f"✅ Normalized match found: '{value}' → '{option}'")
            return option
    
    # Strategy 3: Contains match
    for option in options:
        if normalized_value in normalize_text(option) or normalize_text(option) in normalized_value:
            print(f"✅ Contains match found: '{value}' → '{option}'")
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
        print(f"✅ Fuzzy match found: '{value}' → '{best_match}' (score: {best_match_score})")
        return best_match
    
    # Strategy 5: Use default value if provided, otherwise first option
    if default_value is not None and default_value in options:
        print(f"⚠️ No good match found for '{value}', using specified default: '{default_value}'")
        return default_value
    elif default_value is not None and default_value not in options:
        print(f"⚠️ Default value '{default_value}' not found in options, using first available option: '{options[0]}'")
        return options[0]
    else:
        print(f"⚠️ No good match found for '{value}', using first available option: '{options[0]}'")
        return options[0]

def set_select(driver, id, value, default_value=None):
    """Select option in dropdown using smart mapping with default value option"""
    wait = WebDriverWait(driver, 10)
    
    try:
        # Find and click the dropdown
        dropdown = wait.until(EC.element_to_be_clickable((By.ID, id)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dropdown)
        human_delay(0.3, 0.8)
        dropdown.click()
        human_delay(0.5, 1.0)
        
        # Get available options
        select_element = driver.find_element(By.ID, id)
        select_obj = Select(select_element)
        option_values = [opt.get_attribute("value") for opt in select_obj.options if opt.get_attribute("value")]
        
        if not option_values:
            print(f"⚠️ No options found in dropdown {id}")
            return
        
        # Map the value using smart mapping with default
        mapped_value = smart_field_mapper(value, option_values, default_value)
        
        # Select the mapped option
        select_obj.select_by_value(mapped_value)
        
        print(f"✅ Selected '{mapped_value}' in {id} dropdown")
        human_delay(0.3, 0.8)
        
    except Exception as e:
        print(f"❌ Error in set_select for {id}: {e}")
        raise

def click_save(driver):
    wait = WebDriverWait(driver, 10)
    try:
        print("⏳ Waiting for the Save button to be clickable...")
        save_button = wait.until(EC.element_to_be_clickable((
            By.XPATH, "//button[@data-testid='button' and contains(@class, 'styles__ModalConfirmBtn') and normalize-space()='Save']"
        )))
        print("✅ Save button found. Clicking with JavaScript...")
        # Scroll and click safely
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", save_button)
        human_delay(0.5, 1.0)
        driver.execute_script("arguments[0].click();", save_button)
        print("✅ Clicked modal Save button.")
        print("⏳ Waiting for modal to close...")
        wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "ReactModal__Content")))
        human_delay(1.5, 3.0)  # Allow save to process with variation
        print("✅ Modal closed successfully.")
    except TimeoutException:
        print("❌ Error: Timed out waiting for the Save button or for the modal to close.")
        print("The button was not found, not clickable, or the save action failed.")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

def handle_confirmation_dialog(driver):
    """Handle any confirmation dialogs that appear"""
    try:
        # Look for confirmation dialog
        dialog = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "ReactModal__Content")]//button[contains(text(), "Yes") or contains(text(), "Proceed")]'))
        )
        human_delay(0.5, 1.5)  # Think before confirming
        driver.execute_script("arguments[0].click();", dialog)
        print("✅ Clicked confirmation dialog button.")
        human_delay(1.5, 3.0)
        return True
    except TimeoutException:
        # No dialog found, that's fine
        return False
    except Exception as e:
        print(f"⚠️ Error handling confirmation dialog: {e}")
        return False

def set_input_value_with_retry(driver, selector, value, max_retries=3, b=By.ID):
    """Set input value with retry logic"""
    for attempt in range(max_retries):  
        try:
            set_input_value(driver, selector, value,b)
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠️ Attempt {attempt + 1} failed for {selector}: {e}, retrying...")
                human_delay(1, 2)
            else:
                print(f"❌ Failed to set {selector} after {max_retries} attempts: {e}")
                raise

def set_select_with_retry(driver, id, value, default_value=None, max_retries=3):
    """Set select value with retry logic and default value option"""
    for attempt in range(max_retries):
        try:
            set_select(driver, id, value, default_value)
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠️ Attempt {attempt + 1} failed for {id}: {e}, retrying...")
                human_delay(1, 2)
            else:
                print(f"❌ Failed to set {id} after {max_retries} attempts: {e}")
                raise

def set_keywords(driver, keyw):
    keywords = [kw.strip() for kw in keyw.split(",") if kw.strip()]
    print(f"🔍 Setting {len(keywords)} keyword(s): {keywords}")

    if not keywords:
        print("⚠️ No keywords provided, using default keyword 'jewellery'")
        keywords = ["jewellery"]

    for idx, keyword in enumerate(keywords):
        print(f"🔤 Setting keyword {idx}: '{keyword}'")

        if idx > 0:
            # Click "Add More" (+) button for new keyword field
            add_more_btns = driver.find_elements(By.CLASS_NAME, "sqtrJ")
            if not add_more_btns:
                raise Exception("❌ Could not find 'Add More' button for keywords")
            add_more_btn = add_more_btns[-1]  # always take the last one (+)
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", add_more_btn)
            human_delay(0.5, 1.0)
            add_more_btn.click()
            human_delay(1, 2)  # wait for new input to render

        # Find keyword inputs by NAME (unique per field)
        input_name = f"keywords_{idx}_value"
        try:
            field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, input_name))
            )
        except TimeoutException:
            raise Exception(f"❌ Keyword input '{input_name}' not found")

        # Clear & type keyword in a human-like way
        field.clear()
        for ch in keyword:
            field.send_keys(ch)
            human_typing_delay()

        print(f"✅ Keyword {idx} set: {keyword}")


def automate_flipkart_listing(product_data, sku_folder):
    driver = None
    success = False
    
    try:
        # Ensure SKU status entry exists before starting automation
        if(ensure_sku_status_exists(product_data['sku'])):
            print(f"✅ SKU status entry exists for {product_data['sku']}, plese veryfy before proceeding.")
            #abort
            return False
         
        
        driver = get_driver()
        wait = WebDriverWait(driver, 15)

        login_if_needed(driver)
        navigate_to_listing(driver)

        section_blocks = driver.find_elements(By.XPATH, '//div[contains(@class, "styles__Card-sc-1ipgdlp-0")]')
        print(f"🔍 Found {len(section_blocks)} blocks")

        for i, block in enumerate(section_blocks):
            try:
                spans = block.find_elements(By.TAG_NAME, "span")
                for j, span in enumerate(spans):
                    print(f"[Block {i} | Span {j}] ➤ '{span.text.strip()}'")
            except Exception as e:
                print(f"[Block {i}] ⚠️ Error: {e}")

        try:
            # Step 1: Handle Product Photos section
            print("📸 Opening Product Photos section...")
            
            # Log current section states for debugging
            log_section_states(driver)
            
            # Debug the Product Photos section specifically
            debug_product_photos_section(driver)
            
            if not is_section_expanded(driver, "Product Photos"):
                print("🔄 Product Photos section is collapsed, attempting to expand...")
                
                # Try the specific Product Photos EDIT button approach first
                if find_and_click_product_photos_edit(driver):
                    print("✅ Successfully clicked EDIT button, waiting for expansion...")
                    human_delay(2, 4)  # Wait for section to expand
                    
                    # Verify the section expanded
                    if wait_for_section_expanded(driver, "Product Photos"):
                        print("✅ Product Photos section expanded successfully")
                    else:
                        print("⚠️ Section may not have expanded properly, trying fallback method...")
                        open_section_by_title(driver, "Product Photos")
                        wait_for_section_expanded(driver, "Product Photos")
                else:
                    print("⚠️ Could not find Product Photos EDIT button, trying fallback method...")
                    open_section_by_title(driver, "Product Photos")
                    wait_for_section_expanded(driver, "Product Photos")
            else:
                print("✅ Product Photos section is already expanded")
            
            # Log section states after expansion attempt
            log_section_states(driver)
            
            # Wait for DOM to stabilize after section expansion
            wait_for_dom_stability(driver)
            
            # Verify Product Photos section is fully ready before proceeding
            if not verify_product_photos_section_ready(driver):
                print("❌ Product Photos section is not ready. Cannot proceed with image upload.")
                raise Exception("Product Photos section failed to initialize properly")
            
            print("✅ Product Photos section is ready. Proceeding with image upload...")
            human_delay(1, 2)  # Small delay before starting upload
            
            # Upload images
            upload_flipkart_images(driver, sku_folder)
            click_save(driver)
            print("✅ Clicked Save after uploading images.")
            human_delay(2, 4)  # Pause between sections

            # Step 2: Handle Price, Stock and Shipping Information section
            if not is_section_expanded(driver, "Price, Stock and Shipping Information"):
                open_section_by_title(driver, "Price, Stock and Shipping Information")
                wait_for_section_expanded(driver, "Price, Stock and Shipping Information")
            
            # Fill pricing details
            set_input_value_with_retry(driver, "sku_id", product_data['sku'])
            set_select_with_retry(driver, "listing_status", "ACTIVE")
            set_input_value_with_retry(driver, "mrp", product_data['product_mrp'])
            set_input_value_with_retry(driver, "flipkart_selling_price", product_data['meesho_price'])
            set_select_with_retry(driver,"minimum_order_quantity", "1")
            set_select_with_retry(driver, "service_profile", "NON_FBF")
            set_select_with_retry(driver,"procurement_type","REGULAR")
            set_input_value_with_retry(driver,"shipping_days","2")
            set_input_value_with_retry(driver, "stock_size", product_data['inventory'])
            set_select_with_retry(driver,"shipping_provider","FLIPKART")
            set_input_value_with_retry(driver,"length","5")
            set_input_value_with_retry(driver,"breadth","5")
            set_input_value_with_retry(driver,"height","5")
            set_input_value_with_retry(driver,"weight","0.1")
            set_input_value_with_retry(driver, "hsn", product_data['hsnCode'])
            set_select_with_retry(driver, "tax_code", f"GST_{product_data['gst']}")
            set_select_with_retry(driver, "country_of_origin", "IN")
            set_input_value_with_retry(driver, "manufacturer_details","Kangan siliguri")
            set_input_value_with_retry(driver, "packer_details","Kangan siliguri")
            click_save(driver)
            human_delay(2, 4)  # Pause between sections

            # Step 3: Handle Product Description section
            if not is_section_expanded(driver, "Product Description"):
                open_section_by_title(driver, "Product Description")
                wait_for_section_expanded(driver, "Product Description")
            
            # Fill product description details
            set_input_value_with_retry(driver, "model_number", product_data['sku'])
            set_select_with_retry(driver, "base_material", product_data['material'])
            set_select_with_retry(driver, "type", product_data['type'])
            set_select_with_retry(driver, "color", product_data['color'])
            set_select_with_retry(driver, "gemstone",product_data['stoneType'], "NA")
            set_select_with_retry(driver,"ideal_for","Women")
            set_select_with_retry(driver, "certification", "NA")
            set_input_value_with_retry(driver, "pack_of", product_data['netQuantity'])
            set_select_with_retry(driver, "plating", product_data['plating'], "Gold-plated")
            set_input_value_with_retry(driver, "silver_weight", "0")
            click_save(driver)
            human_delay(2, 4)  # Pause between sections

            # Step 4: Handle Additional Description section (only if needed)
            if not is_section_expanded(driver, "Additional Description"):
                open_section_by_title(driver, "Additional Description (Optional)")
                wait_for_section_expanded(driver, "Additional Description")
            
            # Fill additional description details
            set_input_value_with_retry(driver, "necklace_type", product_data['type'])
            set_select_with_retry(driver, "necklace_length", product_data['size'])
            textarea = wait.until(EC.presence_of_element_located((By.ID, "description")))
            textarea.clear()
            textarea.send_keys(f"{product_data['description']}")
            # product_data['keywords'] is a string sprated with commas and every keyword should be trimmed, seperated and set to name "keywords_0_value" here 0 is index which should be incremented based on number of keywords
            print(product_data['keywords'])
            set_keywords(driver, product_data['keywords'])
            click_save(driver)
            human_delay(2, 4)  # Pause before final step

            # Step 5: Handle Send to QC
            try:
                # Wait for the Send to QC button to be enabled
                wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "uQOWs")))
                send_to_qc_button = driver.find_element(By.CLASS_NAME, "uQOWs")
                driver.execute_script("arguments[0].scrollIntoView();", send_to_qc_button)
                human_delay(1, 2)  # Think before final action
                send_to_qc_button.click()
                print("✅ Clicked Send to QC button.")
                
                # Handle any confirmation dialog
                handle_confirmation_dialog(driver)
                
            except Exception as e:
                print(f"⚠️ Could not click Send to QC button: {e}")
                # Try alternative approach
                try:
                    send_to_qc_button = wait.until(EC.element_to_be_clickable(
                        (By.XPATH, "//button[contains(text(), 'Send to QC')]")
                    ))
                    driver.execute_script("arguments[0].scrollIntoView();", send_to_qc_button)
                    human_delay(1, 2)
                    send_to_qc_button.click()
                    print("✅ Clicked Send to QC button (alternative method).")
                    
                    # Handle any confirmation dialog
                    handle_confirmation_dialog(driver)
                    
                except Exception as e2:
                    print(f"❌ Failed to click Send to QC button: {e2}")

            # If we get here, the automation was successful
            mark_completed(product_data['sku'], "flipkart")
            print("🎉 Flipkart listing automation completed successfully!")

        except TimeoutException as e:
            print("❌ Error: Timed out waiting for the section to expand or elements to be clickable.")
            print("This usually means:")
            print("  - The section failed to expand properly")
            print("  - The page didn't load completely")
            print("  - Network issues or slow loading")
            print(f"Specific error: {e}")
            
            # Mark as failed but don't raise - let the finally block handle cleanup
            print("⚠️ Marking Flipkart listing as failed due to timeout")
            
        except Exception as e:
            print(f"❌ An unexpected error occurred: {e}")
            print("Please check the browser to see what went wrong.")
            
            # Mark as failed but don't raise - let the finally block handle cleanup
            print("⚠️ Marking Flipkart listing as failed due to unexpected error")
            
    except Exception as e:
        print(f"❌ Critical error in automation setup: {e}")
        print("⚠️ Marking Flipkart listing as failed due to critical error")
        
    finally:
        # Always try to mark completion status, even if there were errors
        try:
            if not success:
                print("⚠️ Automation did not complete successfully. Checking if we can mark partial progress...")
                
                # Check if we at least got to the Product Photos section
                if driver and is_section_expanded(driver, "Product Photos"):
                    print("✅ At least Product Photos section was expanded. Marking as partially completed.")
                    # You could create a custom status here if needed
                else:
                    print("❌ No significant progress made. Marking as failed.")
                    
        except Exception as e:
            print(f"⚠️ Error while trying to mark completion status: {e}")
        
        # Cleanup
        human_delay(2, 4)  # Final pause before cleanup
        
        # Return success status
        return success

def ensure_sku_status_exists(sku):
    """Ensure that a SKU status entry exists in the JSON file, even if automation fails"""
    try:
        from sku_tracker import load_status, save_status
        
        status = load_status()
        if sku not in status:
            status[sku] = {"myntra": False, "meesho": False, "flipkart": False}
            save_status(status)
            print(f"✅ Created SKU status entry for {sku}")
        else:
            print(f"ℹ️ SKU status entry already exists for {sku}")
            
        return status[sku]["flipkart"]
        
    except Exception as e:
        print(f"⚠️ Error ensuring SKU status exists: {e}")
        return None
