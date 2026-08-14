import os
import csv
import time
import random
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import concurrent.futures
import threading
import glob
import shutil

is_github_actions = os.getenv('GITHUB_ACTIONS') is not None

if is_github_actions:
    try:
        from pyvirtualdisplay import Display
        display = Display(visible=0, size=(1920, 1080))
        display.start()
        print("Virtual display started on GitHub Actions")
    except Exception as e:
        print(f"Failed to start virtual display: {e}")
else:
    print("Local execution")

download_dir = os.path.join(os.getcwd(), "downloads")
os.makedirs(download_dir, exist_ok=True)

print(f"Current working directory: {os.getcwd()}")
print(f"Download folder: {download_dir}")
print(f"Exists? {os.path.exists(download_dir)}")
print(f"Files in download directory: {os.listdir(download_dir)}")

COPART_USER = os.environ["COPART_USER"]
COPART_PASS = os.environ["COPART_PASS"]
FLASK_CLEAR_URL = os.environ["FLASK_CLEAR_URL"]
FLASK_UPLOAD_URL = os.environ["FLASK_UPLOAD_URL"]

chrome_path = "/usr/bin/chromium-browser"
driver_path = "/usr/bin/chromedriver"

options = webdriver.ChromeOptions()
options.binary_location = chrome_path

options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-features=VizDisplayCompositor")
options.add_argument("--disable-software-rasterizer")

prefs = {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": False,
    "profile.default_content_settings.popups": 0,
    "profile.content_settings.exceptions.automatic_downloads.*.setting": 1
}
options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(service=Service(driver_path), options=options)

driver.execute_cdp_cmd(
    "Page.setDownloadBehavior",
    {"behavior": "allow", "downloadPath": download_dir}
)

wait = WebDriverWait(driver, 30)

def move_and_rename_file(original_filename, new_filename):
    original_path = os.path.join(download_dir, original_filename)
    new_path = os.path.join(download_dir, new_filename)
    
    if os.path.exists(original_path):
        time.sleep(2)
        shutil.move(original_path, new_path)
        print(f"File renamed: {original_filename} -> {new_filename}")
        return True
    return False

def parse_sale_date(date_str):
    if not date_str or not isinstance(date_str, str) or "Будущий" in date_str:
        return None
    try:
        parts = date_str.strip().split()
        if len(parts) < 3:
            return None
            
        dt_str = f"{parts[0]} {parts[1]} {parts[2]}"
        return datetime.strptime(dt_str, '%m/%d/%Y %I:%M %p')
    except Exception as e:
        print(f"Date parsing error '{date_str}': {e}")
        return None

def wait_for_download_complete(timeout=60):
    import time
    
    start_time = time.time()
    last_temp_files = []
    
    while time.time() - start_time < timeout:
        temp_files = glob.glob(os.path.join(download_dir, "*.crdownload"))
        temp_files.extend(glob.glob(os.path.join(download_dir, "*.tmp")))
        
        if temp_files:
            if temp_files != last_temp_files:
                print(f"Downloading files: {[os.path.basename(f) for f in temp_files]}")
                last_temp_files = temp_files
        else:
            csv_files = glob.glob(os.path.join(download_dir, "*.csv"))
            if csv_files:
                print(f"Download completed. Files: {[os.path.basename(f) for f in csv_files]}")
                return True
                
        time.sleep(2)
    
    print("Download timeout")
    return False

def dwn(file_number):
    files_before = set(os.listdir(download_dir))
    print(f"Files count before download: {len(files_before)}")
    
    time.sleep(3)
    
    down_but = wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "button.export-csv-button, a.search-export-btn")
        )
    )
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", down_but)
    driver.execute_script("arguments[0].click();", down_but)
    print("Export button clicked")
    
    time.sleep(5)
    
    try:
        confirm_export_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "exportButton"))
        )
        driver.execute_script("arguments[0].click();", confirm_export_btn)
        print("Export confirmation (exportButton) clicked")
    except Exception:
        print("Export confirmation button (exportButton) did not appear - continuing")

    try:
        modal_ok = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'OK') or contains(text(), 'Ok') or contains(@class, 'confirm') or contains(@class, 'cprt-btn-yellow')]"))
        )
        driver.execute_script("arguments[0].click();", modal_ok)
        print("OK button clicked")
    except Exception:
        print("OK button did not appear - continuing")
    
    download_success = wait_for_download_complete(timeout=45)
    
    files_after = set(os.listdir(download_dir))
    new_files = files_after - files_before
    
    if new_files:
        new_csv_files = [f for f in new_files if f.endswith('.csv')]
        if new_csv_files:
            original_filename = new_csv_files[0]
            new_filename = f"copart_{file_number}.csv"
            
            original_path = os.path.join(download_dir, original_filename)
            new_path = os.path.join(download_dir, new_filename)
            
            if os.path.exists(original_path):
                os.rename(original_path, new_path)
                print(f"File renamed to: {new_filename}")
                return True
    else:
        print("No new files detected")
    
    return False

def login_to_copart():
    try:
        print("Logging in to Copart...")
        
        email_input = wait.until(
            EC.any_of(
                EC.presence_of_element_located((By.ID, "email-member-number")),
                EC.presence_of_element_located((By.ID, "username")),
            )
        )
        email_input.clear()
        email_input.send_keys(COPART_USER)
        print("Username entered")
        time.sleep(2)

        password_input = wait.until(
            EC.any_of(
                EC.presence_of_element_located((By.ID, "member-password")),
                EC.presence_of_element_located((By.ID, "password")),
            )
        )
        password_input.clear()
        password_input.send_keys(COPART_PASS)
        print("Password entered")
        time.sleep(2)

        login_button = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button.cprt-btn-yellow, button.cprt-btn-blue")
            )
        )
        login_button.click()
        print("Login button clicked")
        time.sleep(5)
        
        return True
    except Exception as e:
        print(f"Login error: {e}")
        driver.save_screenshot("login_error.png")
        return False

start_time = time.perf_counter()
try:
    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22BMW%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755087829153")
    time.sleep(5)

    try:
        cookie_accept = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        )
        cookie_accept.click()
        print("Cookie banner closed")
    except:
        print("Cookie banner not found")

    export_button = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.export-csv-button"))
    )
    export_button.click()

    time.sleep(5)

    if login_to_copart():
        print("Successful login")
    else:
        print("Failed to log in")

    down_but = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".cprt-btn-white.export-csv-button")))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", down_but)
    driver.execute_script("arguments[0].click();", down_but)
    time.sleep(5)

    if wait_for_download_complete(timeout=45):
        csv_files = glob.glob(os.path.join(download_dir, "*.csv"))
        if csv_files:
            original_filename = os.path.basename(csv_files[0])
            new_filename = f"copart_0.csv"
            original_path = os.path.join(download_dir, original_filename)
            new_path = os.path.join(download_dir, new_filename)
            if os.path.exists(original_path):
                os.rename(original_path, new_path)
                print(f"First file renamed to: {new_filename}")
                
    time.sleep(5)

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23MakeCode:AUDI%20OR%20%23MakeDesc:Audi%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755087161008")
    dwn(1)

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22CHEVROLET%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755087856342")
    dwn(2)

    print("Files in downloads directory:", os.listdir(download_dir))

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22DODGE%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755087889113")
    dwn(3)

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22FORD%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755087931691")
    dwn(4)

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22HONDA%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755087971944")
    dwn(5)

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22HYUNDAI%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755088054340")
    dwn(6)

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22INFINITI%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755088090041")
    dwn(7)

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22JEEP%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755088110603")
    dwn(8)

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22KIA%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755088140164")
    dwn(9)

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22LAND%20ROVER%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755088170217")
    dwn(10)

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22LEXUS%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755088181066")
    dwn(11)

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22MAZDA%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755088206898")
    dwn(12)

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22MERCEDES-BENZ%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755088223365")
    dwn(13)

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22MITSUBISHI%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755088264648")
    dwn(14)

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22NISSAN%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755088378890")
    dwn(15)

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22PORSCHE%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755088413462")
    dwn(16)

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22RAM%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755088427207")
    dwn(17)

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22SUBARU%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755088457590")
    dwn(18)

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22TESLA%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755088471371")
    dwn(19)

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22TOYOTA%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755088558906")
    dwn(20)

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22VOLKSWAGEN%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_1%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755088505967")
    dwn(21)

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22VOLVO%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755088600335")
    dwn(22)

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22ACURA%5C%22%22,%22lot_make_desc:%5C%22ALFA%20ROMEO%5C%22%22,%22lot_make_desc:%5C%22BENTLEY%5C%22%22,%22lot_make_desc:%5C%22DUCATI%5C%22%22,%22lot_make_desc:%5C%22FIAT%5C%22%22,%22lot_make_desc:%5C%22GENESIS%5C%22%22,%22lot_make_desc:%5C%22ISUZU%5C%22%22,%22lot_make_desc:%5C%22JAGUAR%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2011%20TO%202026%5D&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1757615256143")
    dwn(23)

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22BUICK%5C%22%22,%22lot_make_desc:%5C%22CADILLAC%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2011%20TO%202026%5D&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1757615434783")
    dwn(24)

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22CHRYSLER%5C%22%22,%22lot_make_desc:%5C%22LINCOLN%5C%22%22,%22lot_make_desc:%5C%22LUCID%20MOTORS%5C%22%22,%22lot_make_desc:%5C%22MASERATI%5C%22%22,%22lot_make_desc:%5C%22MINI%5C%22%22,%22lot_make_desc:%5C%22POLESTAR%5C%22%22,%22lot_make_desc:%5C%22SUZUKI%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2011%20TO%202026%5D&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1757615509431")
    dwn(25)

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22NISSAN%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2011%20TO%202026%5D&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1757615549643")
    dwn(26)

except Exception as e:
    print(f"Error occurred: {e}")
finally:
    driver.quit()
    if is_github_actions and 'display' in locals():
        display.stop()
        print("Virtual display stopped")
print(f"CSVs downloaded in {time.perf_counter() - start_time:.2f} seconds")


MAKE_MAP = {
    "AUDI": "AUDI",
    "BMW": "BMW",
    "CHEV": "CHEVROLET",
    "DODG": "DODGE",
    "FORD": "FORD",
    "HOND": "HONDA",
    "HYUN": "HYUNDAI",
    "INFI": "INFINITI",
    "JEP": "JEEP",
    "KIA": "KIA",
    "LAND": "LAND ROVER",
    "LEXS": "LEXUS",
    "MAZD": "MAZDA",
    "MERZ": "MERCEDES-BENZ",
    "MCRE": "MERCEDES-BENZ",
    "MITS": "MITSUBISHI",
    "NISS": "NISSAN",
    "PORS": "PORSHE",
    "RAM": "RAM",
    "SUBA": "SUBARU",
    "TESL": "TESLA",
    "TOYT": "TOYOTA",
    "VOLK": "VOLKSWAGEN",
    "VOLV": "VOLVO",
    "ACUR": "ACURA",
    "ALFA": "ALFA ROMEO",
    "CHRY": "CHRYSLER",
    "BUIC": "BUICK",
    "BENT": "BENTLEY",
    "CADI": "CADILLAC",
    "GENS": "GENESIS",
    "FIAT": "FIAT",
    "DUCA": "DUCATI",
    "GMC": "GMC",
    "LINC": "LINCOLN",
    "LUCI": "LUCID",
    "MIN": "MINI",
    "MASE": "MASERATI",
    "JAGU": "JAGUAR",
    "PLSR": "POLESTAR",
    "SUZI": "SUZUKI",
    "ISU": "ISUZU"
}

def normalize_make(make):
    make = make.strip().upper()
    return MAKE_MAP.get(make, make)


flask_clear_url = 'http://www.bwauto.com.ua/clear_table'
flask_upload_url = 'http://www.bwauto.com.ua/upload_data'

start_clear = time.perf_counter()
response = requests.post(flask_clear_url)
if response.ok:
    print(f"Table cars cleared in {time.perf_counter() - start_clear:.2f} seconds")
else:
    print(f"Clear error: {response.text}")


all_data = []
start_csv = time.perf_counter()

for file_name in os.listdir(download_dir):
    if not file_name.endswith(".csv"):
        continue

    file_path = os.path.join(download_dir, file_name)
    print(f"Processing file: {file_name}")

    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        for row in reader:
            if not row or len(row) != 21:
                continue
            row[5] = normalize_make(row[5])
            sort_order_value = random.randint(1, 1_000_000)
            parsed_dt = parse_sale_date(row[3])
            sale_date_json = parsed_dt.isoformat() if parsed_dt else None
            all_data.append({
                "lot_url": row[0],
                "lot_number": row[1],
                "retail_value": row[2],
                "sale_date": row[3],
                "sale_date_parsed": sale_date_json,
                "year": int(row[4]) if row[4].isdigit() else None,
                "make": row[5],
                "model": row[6],
                "engine": row[7],
                "cylinders": row[8],
                "vin": row[9],
                "title": row[10],
                "odometer": row[11],
                "odometer_desc": row[12],
                "damage": row[13],
                "current_bid": row[14],
                "my_bid": row[15],
                "item_number": row[16],
                "sale_name": row[17],
                "auto_grade": row[18],
                "sale_light": row[19],
                "announcements": row[20],
                "sort_order": sort_order_value
            })
    os.remove(file_path)
    print(f"File {file_name} deleted")

print(f"CSVs processed in {time.perf_counter() - start_csv:.2f} seconds")
print(f"Total records: {len(all_data)}")

import concurrent.futures
import threading

batch_size = 200
batches = [all_data[i:i+batch_size] for i in range(0, len(all_data), batch_size)]
total_batches = len(batches)

batch_list = list(enumerate(batches, start=1))

inserted_total, failed_total = 0, 0
lock = threading.Lock()

def send_batch(batch_num, batch):
    global inserted_total, failed_total
    try:
        print(f"Sending batch {batch_num}/{total_batches}...")
        response = requests.post(flask_upload_url, json=batch)
        if response.ok:
            inserted = len(batch)
            failed = 0
            print(f"Batch {batch_num}/{total_batches} successfully inserted ({inserted} records)")
        else:
            inserted = 0
            failed = len(batch)
            print(f"Insertion error in batch {batch_num}: {response.text}")
    except Exception as e:
        inserted = 0
        failed = len(batch)
        print(f"Exception in batch {batch_num}: {e}")

    with lock:
        inserted_total += inserted
        failed_total += failed
        print(f"Progress: {inserted_total} inserted, {failed_total} failed")

    return inserted, failed


start_upload = time.perf_counter()

with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
    results = executor.map(lambda args: send_batch(*args), batch_list)

for inserted, failed in results:
    pass

print(f"Data sent in {time.perf_counter() - start_upload:.2f} seconds")
print(f"Total inserted: {inserted_total}, failed batches: {failed_total}")
