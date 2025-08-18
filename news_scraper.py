"""
news_scraper.py

Automated news scraper that:
- Detects OS and Browser driver settings via driver_config.py
- Uses Selenium with ChromeDriver or Chrome Headless Shell
- Parses news entries from a given site URL based on selectors in config.py
- Filters news items by inclusion/exclusion keywords
- Follows valid links to extract details (images, file info, download links)
- Outputs results to a timestamped CSV file

Requires:
    config.py         - Constants for HTML selectors, strings, and providers
    driver_config.py  - Logic to detect OS/arch, chromedriver paths, and headless options
"""

import time
import csv
import os
import threading
import sqlite3
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import config
import driver_config

existing_records = 0
successful_records = 0
update_site = False

log_dir = os.path.join(config.LOG_DIR, datetime.now().strftime("%Y.%m"))
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y.%m.%d_%H.%M.%S')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ],
)

def log(level: str, message: str) -> None:
    """
    Log a message with the given level.

    Parameters:
        level (str): Logging level as a string. 
                     Examples: 'debug', 'info', 'warning', 'error', 'critical'.
                     Case-insensitive.
        message (str): The message to log.

    Returns:
        None
    """
    level = level.upper()
    numeric_level = getattr(logging, level, logging.INFO)
    logging.log(numeric_level, message)


log(
    "info",
    "".join(
        f"\n{' ' * 28} {key}: {value}" 
        for key, value in config.__dict__.items() 
        if not key.startswith("__")
    )
)

log(
    "info",
    "".join(
        f"\n{' ' * 28} {key}: {value}" 
        for key, value in driver_config.__dict__.items() 
        if not key.startswith("__")
    )
)


def database_op(data: dict = None, db_name: str = None, table_name: str = None, table_header: list = None) -> bool:
    """
    Perform insert operation on a dictionary data onto a table of a particular database.

    Parameters:
        data (dict, required): 
                    Dictionary of data in `attr: value` pairs to be inserted.
        db_name (str, default: `YYYY.MM.DD_HH.MM.SS.db`): 
                    Database name or path. If database not found, then it is created.
        table_name (str, default: `table_YYYYMMDD_HHMMSS`): 
                    Table name where data will be inserted. If table not found, 
                    then it is created inside the given database.
        table_header (str, default: keys from data as TEXT):
                    Table header row to which data will be inserted correspondingly.
                    FORMAT: 
                        ```
                        field1 DATATYPE [NOT NULL] [DEFAULT val],
                        field2 DATATYPE [NOT NULL] [DEFAULT val],
                        field3 DATATYPE [NOT NULL] [DEFAULT val],
                        . . .,
                        [PRIMARY KEY (FIELD_N, FIELD_N)]
                        ```

    Returns:
        bool: True for successful operation. Otherwise False.
    """

    global existing_records
    
    dt_now = datetime.now().strftime("%Y%m%d_%H%M%S")

    if not data:
        log("warning", "Missing data dictionary")
        return False

    if not db_name:
        db_name = dt_now + ".db"
        log("info", f"DB_NAME: {db_name}")

    if not table_name:
        table_name = "table_" + dt_now
        log("info", f"TABLE NAME: {table_name}")

    if not table_header:
        table_header = ", ".join(
            f"{field} TEXT"
            for field in data
        )
        log("info", f"TABLE HEADER: {table_header}")

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {table_header}
            )
            """
        )
    except Exception:
        log("error", "DB connect / TABLE creation")
        conn.commit()
        conn.close()
        return False
    
    pk_attr = [
        data[1]
        for data in cursor.execute(f"PRAGMA TABLE_INFO({table_name})").fetchall()
        if data[-1] != 0
    ]

    op_success = True

    if pk_attr:
        pk_values = [data[key] for key in pk_attr]
        
        if not pk_values:
            log("warning", "Missing primary keys value.")
            op_success = False
        else:
            try:
                pk_placeholder = " AND ".join(f"{key} = ?" for key in pk_attr)
                
                cursor.execute(
                    f"SELECT 1 FROM {table_name} WHERE {pk_placeholder}",
                    pk_values
                ) 
            
                if cursor.fetchone():
                    log("info", "Key values exists. Skipping DB insert.")
                    existing_records += 1
                    op_success = False

            except Exception:
                log("error", "Checking Primary Key")
                op_success = False

        if not op_success:
            conn.commit()
            conn.close()
            return op_success

    header_fields = ', '.join(str(field) for field in data.keys())
    field_placeholder = ', '.join('?' * len(data))
    values = [value for value in data.values()]

    try:
        cursor.execute(
            f"""
            INSERT OR IGNORE INTO {table_name} 
            ({header_fields}) VALUES ({field_placeholder})
            """,
            values
        )
    except Exception:
        log("error", "DB Insert Operation")
        op_success = False
    else:
        success_msg = f"Completed: "
        if pk_attr:
            success_msg += f"{pk_values}"
        else:
            success_msg += f"{[val[:10] for val in data.values()]}"

        log("info", success_msg)

    conn.commit()
    conn.close()
    return op_success


def create_driver(chromedriver_path: str, driver_config) -> webdriver.Chrome:
    """
    Create and configure a Chrome WebDriver instance.

    This function sets up a Selenium Chrome WebDriver with options and preferences
    defined by the given driver_config object. It allows enabling or disabling 
    site permissions, JavaScript, and headless mode based on the provided ChromeDriver path.
    
    Parameters:
        chromedriver_path (str): The file system path to the ChromeDriver executable.
        driver_config: An object containing configuration flags and helper methods
                       such as disable_site_permissions, disable_js, detect_os_arch,
                       and build_chromedriver_path.

    Returns:
        webdriver.Chrome: A configured Chrome WebDriver instance ready for automation.
    """
    options = Options()
    prefs = {}

    if driver_config.disable_site_permissions:
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        prefs.update({
            "profile.default_content_setting_values.geolocation": 2,
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_setting_values.media_stream_mic": 2,
            "profile.default_content_setting_values.media_stream_camera": 2,
        })

    if driver_config.disable_js:
        prefs["profile.managed_default_content_settings.javascript"] = 2

    if prefs:
        options.add_experimental_option("prefs", prefs)

    if "chrome-headless-shell" in chromedriver_path:
        os_arch = driver_config.detect_os_arch()
        standard_driver_path = driver_config.build_chromedriver_path(os_arch, headless=False)
        options.binary_location = os.path.abspath(chromedriver_path)
        service = Service(standard_driver_path)
    else:
        if "headless" in chromedriver_path.lower():
            options.add_argument("--headless=new")
        service = Service(chromedriver_path)

    return webdriver.Chrome(service=service, options=options)


def browser(site=None):
    """
    Scrape news articles from a website and save results to CSV and SQLite database.

    If no site URL is provided, prompts the user to input one. Uses Selenium to
    load pages and BeautifulSoup to parse HTML content. Extracted news data is
    filtered, saved, and managed to avoid duplicate entries.

    Parameters:
        site (str, optional): The URL of the site to scrape. If None, prompts the user to input a URL.

    Returns:
        None

    Side effects:
        - Creates output directories and files under "Outputs".
        - Writes news data to a CSV file.
        - Inserts records into a SQLite database.
        - Prints status and error messages to logger.
    """

    global existing_records
    global successful_records
    global update_site

    now = datetime.now()
    formatted_ym = now.strftime("%Y.%m")
    
    formatted_dt = config.OUTPUT_DATETIME
    if not formatted_dt:
        formatted_dt = now.strftime("%Y.%m.%d_%H.%M.%S")

    os.makedirs(os.path.join("Outputs", formatted_ym), exist_ok=True)
    output_file = config.CSV_FILE
    
    if not site:
        site = input("Enter site URL to scrape: ").strip()

    chromedriver_path = f"./{driver_config.chromedriver_path}"

    # Main browser
    driver = create_driver(chromedriver_path, driver_config)
    driver.get(site)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    parent_div = soup.find("div", class_=config.PARENT_DIV_CLASS)
    if not parent_div:
        log("warning", "Can't find main content div.")
        return

    news_section_div = parent_div.find("div", class_=config.NEWS_LIST_DIV_CLASS)
    if not news_section_div:
        log("warning", "Can't find news list div.")
        return

    news_section = news_section_div.find(config.NEWS_LIST_UL_TAG)
    if not news_section:
        log("warning", "Can't find news list section.")
        return

    if not os.path.isfile(output_file):
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=config.FIELDNAMES)
            writer.writeheader()

    detail_driver = create_driver(chromedriver_path, driver_config)
    
    for li in news_section.find_all(config.NEWS_ITEM_LI_TAG):
        title_tag = li.find(config.TITLE_A_TAG, title=True)
        title = title_tag[config.TITLE_A_TITLE_ATTR].strip() if title_tag else ""
        href = title_tag[config.TITLE_A_HREF_ATTR].strip() if title_tag else ""
        date_span = li.find("span", class_=config.NEWS_DATE_CLASS)
        date = date_span.get_text(strip=True).replace("/", ".") if date_span else ""
        
        if date:
            try:
                date = datetime.strptime(date, "%d.%m.%Y").strftime("%Y.%m.%d")
            except ValueError:
                pass

        if config.END_DATE in date:
            log("warning", "Encounted terminate date.")
            update_site = True
            break

        if config.TITLE_FILTER_INCLUDE not in title:
            continue
        if config.TITLE_FILTER_EXCLUDE in title:
            continue

        detail_driver.get(href)
        
        detail_soup = BeautifulSoup(detail_driver.page_source, "html.parser")
        news_div = detail_soup.find("div", class_=config.DETAIL_NEWS_DIV_CLASS)
        if not news_div:
            continue

        img1_tag = news_div.find("div", class_=config.DETAIL_IMAGE1_DIV_CLASS)
        image1 = img1_tag.find(config.DETAIL_IMAGE1_IMG_TAG)["src"] if img1_tag and img1_tag.find(config.DETAIL_IMAGE1_IMG_TAG) else ""

        img2_div = news_div.find("div", class_=config.DETAIL_IMAGE2_DIV_CLASS)
        image2 = ""
        if img2_div and img2_div.find("img"):
            image2 = img2_div.find("img").get("src", "")

        filename, size = "", ""
        for txt in news_div.stripped_strings:
            if txt.startswith(config.FILE_SIZE_PREFIX):
                parts = txt[len(config.FILE_SIZE_PREFIX):].split(":")
                if len(parts) >= 2:
                    filename = parts[0].strip()
                    size = parts[1].strip()
        
        process_dt = datetime.now().strftime("%Y.%m.%d_%H.%M.%S")
        if not filename or filename == '':
            filename = f"FILE_{process_dt.replace('.', '')}"

        fileurl_dict = {}
        for p in config.FILE_PROVIDERS:
            file_list = []
            for a in news_div.find_all("a", href=True):
                if p in a["href"]:
                    file_list.append(a["href"])
            fileurl_dict[p] = file_list

        fileurl = "; ".join(f"{k}: {v}" for k, v in fileurl_dict.items())
        process_dt = datetime.now().strftime("%Y.%m.%d_%H.%M.%S")
    
        try:
            row = {field: locals()[field] for field in config.FIELDNAMES}
        except Exception as e:
            try:
                row = eval(config.ROW_HARDCODE)
                log(
                    "info",
                    (
                        f"Issue with {str(e)}. Using Hardcode: {{"
                        + ", ".join(
                            f"{key}: {value}" if len(value) < 20 else f"{key}: {value[:20]}..."
                            for key, value in row.items()
                        )
                        + "}"
                    )
                )
            except Exception as e1:
                log("error", f"Unknown error in row hardcode")

        database_op(
            data = row, 
            db_name = config.DATABASE, 
            table_name = config.TABLE_NAME, 
            table_header = config.TABLE_HEADER,
        )
        
        with open(output_file, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=config.FIELDNAMES)
            
            writer.writerow(row)

        successful_records += 1

    detail_driver.quit()
    if successful_records == 0:
        log("warning", "ZERO SUCCESSFUL RECORDS FOUND")
    else:
        log("info", f"Scraping completed. Data saved to {output_file}")
        successful_records = 0


if __name__ == "__main__":
    site_flip = 0
    page_no = 1

    while True:
        if page_no == 1:
            site = config.DEFAULT_WEBSITES[site_flip]
        else:
            site = config.WEBSITES[site_flip].replace("| PAGENO |", str(page_no))

        log("info", site)
        browser(site)

        if update_site:
            site_flip = 1 - site_flip
            update_site = False
            page_no = 1
        else:
            page_no += 1

