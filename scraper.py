import os
import csv
import time
import random
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import concurrent.futures
import threading

# =======================
# Настройки Selenium
# =======================
download_dir = os.path.abspath("downloads")
os.makedirs(download_dir, exist_ok=True)
print("Download folder:", download_dir)
print("Exists?", os.path.exists(download_dir))

# Данные из GitHub Secrets
COPART_USER = os.environ["COPART_USER"]
COPART_PASS = os.environ["COPART_PASS"]
FLASK_CLEAR_URL = os.environ["FLASK_CLEAR_URL"]
FLASK_UPLOAD_URL = os.environ["FLASK_UPLOAD_URL"]

# =======================
# Selenium настройки
# =======================
chrome_path = "/usr/bin/chromium-browser"
driver_path = "/usr/bin/chromedriver"

options = webdriver.ChromeOptions()
options.binary_location = chrome_path
options.add_argument("--headless=new")           # headless-режим
options.add_argument("--no-sandbox")             # важно для GitHub Actions
options.add_argument("--disable-dev-shm-usage")  # решает проблему с памятью
options.add_argument("--window-size=1920,1080")

prefs = {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(service=Service(driver_path), options=options)
wait = WebDriverWait(driver, 30)

# =======================
# Функция скачивания CSV
# =======================
def dwn():
    time.sleep(5)
    down_but = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".cprt-btn-white.export-csv-button")))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", down_but)
    driver.execute_script("arguments[0].click();", down_but)
    time.sleep(5)
    ok_buttons = driver.find_elements(By.CSS_SELECTOR, ".cprt-btn-yellow")
    if ok_buttons:
        try:
            WebDriverWait(driver, 3).until(EC.element_to_be_clickable(ok_buttons[0]))
            ok_buttons[0].click()
            print("✅ Кнопка OK нажата")
            time.sleep(10)
        except:
            print("⚠ Кнопка OK нашлась, но не кликнулась")
    else:
        print("ℹ Кнопка OK не появилась — продолжаем")

# =======================
# Скачиваем CSV с сайта Copart
# =======================
start_time = time.perf_counter()
try:
    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22BMW%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755087829153")
    time.sleep(5)

    # Закрываем куки, если есть
    try:
        cookie_accept = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        )
        cookie_accept.click()
        print("✅ Cookie баннер закрыт")
    except:
        print("ℹ Cookie баннер не найден")

    
    export_button = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.export-csv-button"))
    )
    export_button.click()

    time.sleep(5)

    email_input = wait.until(EC.presence_of_element_located((By.ID, "username")))
    email_input.clear()
    email_input.send_keys("COPART_USER")
    time.sleep(5)

    password_input = wait.until(EC.presence_of_element_located((By.ID, "password")))
    password_input.clear()
    password_input.send_keys("COPART_PASS")
    time.sleep(5)

    login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.cprt-btn-yellow")))
    login_button.click()
    time.sleep(5)



    down_but = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".cprt-btn-white.export-csv-button")))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", down_but)
    driver.execute_script("arguments[0].click();", down_but)

    time.sleep(5)


    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23MakeCode:AUDI%20OR%20%23MakeDesc:Audi%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755087161008")
    dwn()

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22CHEVROLET%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755087856342")
    dwn()

    print("Файлы в папке downloads:", os.listdir(download_dir))

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22DODGE%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755087889113")
    dwn()

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22FORD%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755087931691")
    dwn()

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22HONDA%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755087971944")
    dwn()

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22HYUNDAI%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755088054340")
    dwn()

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22INFINITI%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755088090041")
    dwn()

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22JEEP%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755088110603")
    dwn()

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22KIA%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755088140164")
    dwn()

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22LAND%20ROVER%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755088170217")
    dwn()

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22LEXUS%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755088181066")
    dwn()

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22MAZDA%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755088206898")
    dwn()

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22MERCEDES-BENZ%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755088223365")
    dwn()

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22MITSUBISHI%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755088264648")
    dwn()

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22NISSAN%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755088378890")
    dwn()

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22PORSCHE%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755088413462")
    dwn()

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22RAM%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755088427207")
    dwn()

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22SUBARU%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755088457590")
    dwn()

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22TESLA%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755088471371")
    dwn()

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22TOYOTA%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755088558906")
    dwn()

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22VOLKSWAGEN%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_1%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755088505967")
    dwn()

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22VOLVO%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D,Audi&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1755088600335")
    dwn()

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22ACURA%5C%22%22,%22lot_make_desc:%5C%22ALFA%20ROMEO%5C%22%22,%22lot_make_desc:%5C%22BENTLEY%5C%22%22,%22lot_make_desc:%5C%22DUCATI%5C%22%22,%22lot_make_desc:%5C%22FIAT%5C%22%22,%22lot_make_desc:%5C%22GENESIS%5C%22%22,%22lot_make_desc:%5C%22ISUZU%5C%22%22,%22lot_make_desc:%5C%22JAGUAR%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2011%20TO%202026%5D&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1757615256143")
    dwn()

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22BUICK%5C%22%22,%22lot_make_desc:%5C%22CADILLAC%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2011%20TO%202026%5D&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1757615434783")
    dwn()

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22CHRYSLER%5C%22%22,%22lot_make_desc:%5C%22LINCOLN%5C%22%22,%22lot_make_desc:%5C%22LUCID%20MOTORS%5C%22%22,%22lot_make_desc:%5C%22MASERATI%5C%22%22,%22lot_make_desc:%5C%22MINI%5C%22%22,%22lot_make_desc:%5C%22POLESTAR%5C%22%22,%22lot_make_desc:%5C%22SUZUKI%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2011%20TO%202026%5D&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1757615509431")
    dwn()

    driver.get("https://www.copart.com/ru/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22MAKE%22:%5B%22lot_make_desc:%5C%22NISSAN%5C%22%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23EXUPLTS:auction_date_utc:*%22%5D,%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2011%20TO%202026%5D%22%5D%7D,%22watchListOnly%22:false,%22searchName%22:%22%22,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2011%20TO%202026%5D&from=%2FvehicleFinder&fromSource=widget&qId=655dade8-be5d-47c3-9e34-130c4cb31ff7-1757615549643")
    dwn()

finally:
    driver.quit()
print(f"⏱ CSV скачаны за {time.perf_counter() - start_time:.2f} секунд")

# =======================
# Нормализация марок
# =======================
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

# =======================
# Чистим таблицу через Flask API
# =======================
flask_clear_url = 'http://www.bwauto.com.ua/clear_table'
flask_upload_url = 'http://www.bwauto.com.ua/upload_data'

start_clear = time.perf_counter()
response = requests.post(flask_clear_url)
if response.ok:
    print(f"✅ Таблица cars очищена за {time.perf_counter() - start_clear:.2f} секунд")
else:
    print(f"❌ Ошибка очистки: {response.text}")

# =======================
# Читаем CSV и собираем данные
# =======================
all_data = []
start_csv = time.perf_counter()

for file_name in os.listdir(download_dir):
    if not file_name.endswith(".csv"):
        continue

    file_path = os.path.join(download_dir, file_name)
    print(f"Обработка файла: {file_name}")

    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        for row in reader:
            if not row or len(row) != 21:
                continue
            row[5] = normalize_make(row[5])
            sort_order_value = random.randint(1, 1_000_000)
            all_data.append({
                "lot_url": row[0],
                "lot_number": row[1],
                "retail_value": row[2],
                "sale_date": row[3],
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
    print(f"Файл {file_name} удален")

print(f"⏱ CSV обработаны за {time.perf_counter() - start_csv:.2f} секунд")
print(f"Всего записей: {len(all_data)}")

import concurrent.futures
import threading

batch_size = 200
batches = [all_data[i:i+batch_size] for i in range(0, len(all_data), batch_size)]
total_batches = len(batches)

batch_list = list(enumerate(batches, start=1))  # [(1, batch1), (2, batch2), ...]

inserted_total, failed_total = 0, 0
lock = threading.Lock()

def send_batch(batch_num, batch):
    global inserted_total, failed_total
    try:
        print(f"⏳ Отправка пакета {batch_num}/{total_batches}...")
        response = requests.post(flask_upload_url, json=batch)
        if response.ok:
            inserted = len(batch)
            failed = 0
            print(f"✅ Пакет {batch_num}/{total_batches} успешно вставлен ({inserted} записей)")
        else:
            inserted = 0
            failed = len(batch)
            print(f"❌ Ошибка вставки пакета {batch_num}: {response.text}")
    except Exception as e:
        inserted = 0
        failed = len(batch)
        print(f"❌ Exception в пакете {batch_num}: {e}")

    with lock:
        inserted_total += inserted
        failed_total += failed
        print(f"ℹ Прогресс: {inserted_total} вставлено, {failed_total} неудачных")

    return inserted, failed

# ============================
# Параллельная отправка
# ============================
start_upload = time.perf_counter()

with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
    results = executor.map(lambda args: send_batch(*args), batch_list)

for inserted, failed in results:
    pass  # счётчики уже обновляются внутри send_batch

print(f"✅ Данные отправлены за {time.perf_counter() - start_upload:.2f} секунд")
print(f"Всего вставлено: {inserted_total}, неудачных пакетов: {failed_total}")
