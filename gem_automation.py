import time
import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURATION ---
SEARCH_KEYWORD = "Split Air Conditioner"
DOWNLOAD_PATH = os.path.join(os.getcwd(), "gem_bids", SEARCH_KEYWORD.replace(" ", "_"))

if not os.path.exists(DOWNLOAD_PATH):
    os.makedirs(DOWNLOAD_PATH)

GEM_BID_LIST_URL = "https://bidplus.gem.gov.in/all-bids"

def initialize_gem_driver():
    """Initializes Chrome with settings optimized for GeM downloads."""
    options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": DOWNLOAD_PATH,
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True 
    }
    options.add_experimental_option("prefs", prefs)
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()
    return driver

def wait_for_new_file(initial_files, timeout=30):
    """Waits for a new PDF file to appear in the download directory."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        current_files = set(os.listdir(DOWNLOAD_PATH))
        new_files = current_files - initial_files
        pdf_files = [f for f in new_files if f.lower().endswith('.pdf')]
        if pdf_files:
            return pdf_files[0]
        time.sleep(1)
    return None

def run_gem_automation():
    driver = None
    try:
        driver = initialize_gem_driver()
        wait = WebDriverWait(driver, 20) 

        # 1. Direct Navigation
        print(f"Step 1: Navigating directly to {GEM_BID_LIST_URL}...")
        driver.get(GEM_BID_LIST_URL)

        # 2. Search for Keyword
        print(f"Step 2: Searching for '{SEARCH_KEYWORD}'...")
        search_box = wait.until(EC.presence_of_element_located((By.ID, "searchBid"))) 
        search_box.clear()
        search_box.send_keys(SEARCH_KEYWORD)
        
        search_icon = wait.until(EC.element_to_be_clickable((By.ID, "searchBidRA"))) 
        search_icon.click()
        print("   -> Search icon clicked.")
        
        # 3. Sort By: Bid Start Date: Latest First
        print("Step 3: Applying Sort (Latest First)...")
        try:
            time.sleep(3) 
            sort_button = wait.until(EC.element_to_be_clickable((By.ID, "currentSort")))
            sort_button.click()
            latest_first_option = wait.until(EC.element_to_be_clickable((By.ID, "Bid-Start-Date-Latest")))
            latest_first_option.click()
            print("   -> 'Latest First' selected.")
            time.sleep(5) 
        except Exception as e:
            print(f"   Note: Could not apply sort. Error: {e}")

        # 4. Pagination Loop
        current_page = 1
        while True:
            print(f"\n--- Processing Page {current_page} ---")
            
            wait.until(EC.presence_of_all_elements_located((By.XPATH, "//a[contains(text(), 'GEM/')]")))
            bid_links = driver.find_elements(By.XPATH, "//a[contains(text(), 'GEM/')]")
            
            if not bid_links:
                print("No bids found on this page. Stopping.")
                break

            print(f"Found {len(bid_links)} bids on Page {current_page}.")
            
            for link in bid_links:
                bid_id = link.text.strip()
                target_filename = f"{bid_id.replace('/', '_')}.pdf"
                target_path = os.path.join(DOWNLOAD_PATH, target_filename)
                
                if os.path.exists(target_path):
                    print(f"   [-] Skipping {bid_id}: Already exists.")
                    continue
                
                try:
                    print(f"   [+] Downloading {bid_id}...")
                    initial_files = set(os.listdir(DOWNLOAD_PATH))
                    driver.execute_script("arguments[0].click();", link)
                    
                    new_file_name = wait_for_new_file(initial_files)
                    if new_file_name:
                        old_path = os.path.join(DOWNLOAD_PATH, new_file_name)
                        os.rename(old_path, target_path)
                        print(f"       -> Saved as {target_filename}")
                    time.sleep(1)
                except Exception as e:
                    print(f"   [!] Error downloading {bid_id}: {e}")
                    continue
            
            # 5. Move to Next Page
            print(f"Completed Page {current_page}. Proceeding...")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            try:
                next_page_num = current_page + 1
                next_selectors = [
                    f"//ul[contains(@class, 'pagination')]//a[text()='{next_page_num}']",
                    "//a[@rel='next']",
                    "//li[contains(@class,'next')]/a",
                    "//a[contains(text(), 'Next')]"
                ]
                
                next_page_btn = None
                for selector in next_selectors:
                    try:
                        btns = driver.find_elements(By.XPATH, selector)
                        for b in btns:
                            if b.is_displayed() and b.is_enabled():
                                next_page_btn = b
                                break
                        if next_page_btn: break
                    except:
                        continue
                
                if next_page_btn:
                    driver.execute_script("arguments[0].click();", next_page_btn)
                    current_page += 1
                    time.sleep(5) 
                else:
                    break
            except:
                break

    except KeyboardInterrupt:
        print("\n[!] User interrupted the script (Ctrl+C). Closing safely...")
    except Exception as e:
        print(f"\n[!] An error occurred: {e}")
    finally:
        if driver:
            print("Cleaning up and closing browser...")
            driver.quit()
        print(f"Process ended. Files in: {DOWNLOAD_PATH}")

if __name__ == "__main__":
    run_gem_automation()