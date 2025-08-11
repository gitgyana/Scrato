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


def create_driver(chromedriver_path):
    """
    Create and configure a Selenium Chrome WebDriver instance.

    Detects if the path points to a Chrome Headless Shell binary
    and sets up `options.binary_location` accordingly. Otherwise,
    treats the supplied path as a ChromeDriver executable and
    applies headless mode if indicated by the filename.

    Args:
        chromedriver_path (str): Path to ChromeDriver or Chrome Headless Shell binary.

    Returns:
        webdriver.Chrome: A configured Chrome WebDriver ready to use.
    """
    options = Options()

    if "chrome-headless-shell" in chromedriver_path:
        os_arch = driver_config.detect_os_arch()
        standard_driver_path = driver_config.build_chromedriver_path(os_arch, headless=False)

        options.binary_location = os.path.abspath(chromedriver_path)

        service = Service(standard_driver_path)
        return webdriver.Chrome(service=service, options=options)
    else:
        if "headless" in chromedriver_path.lower():
            options.add_argument("--headless=new")

        service = Service(chromedriver_path)
        return webdriver.Chrome(service=service, options=options)


def browser(site=None):
    """
    Main entry point for the news scraper.

    Steps:
        1. Prompt for target site URL and get ChromeDriver path from driver_config.
        2. Launch a browser instance and load the main page.
        3. Wait for and parse the main content section.
        4. Loop through news entries matching config.py selectors.
        5. Apply filters: include keyword must be present, exclude keyword absent.
        6. For each valid news link, fetch detail page and extract:
            - Image1 (first image section)
            - Image2 (recipepod image section)
            - Filename and file size
            - Download links for configured providers
        7. Save results to a CSV file with timestamp in filename.

    Output:
        A `news_output_<DD.MM.YYYY>_<HH.MM.SS>.csv` file in the Outputs directory.
    """
    now = datetime.now()
    formatted_ym = now.strftime("%Y.%m")
    
    formatted_dt = config.OUTPUT_DATETIME
    if not formatted_dt:
        formatted_dt = now.strftime("%Y.%m.%d_%H.%M.%S")

    os.makedirs(os.path.join("Outputs", formatted_ym), exist_ok=True)
    output_file = os.path.join("Outputs", formatted_ym, f"news_output_{formatted_dt}.csv")
    
    if not site:
        site = input("Enter site URL to scrape: ").strip()

    chromedriver_path = f"./{driver_config.chromedriver_path}"

    # Main browser
    driver = create_driver(chromedriver_path)
    driver.get(site)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    parent_div = soup.find("div", class_=config.PARENT_DIV_CLASS)
    if not parent_div:
        print("Can't find main content div.")
        return

    news_section_div = parent_div.find("div", class_=config.NEWS_LIST_DIV_CLASS)
    if not news_section_div:
        print("Can't find news list div.")
        return

    news_section = news_section_div.find(config.NEWS_LIST_UL_TAG)
    if not news_section:
        print("Can't find news list section.")
        return

    fieldnames = ["date", "title", "href", "image1", "image2", "filename", "size", "fileurl"]

    if not os.path.isfile(output_file):
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

    detail_driver = create_driver(chromedriver_path)

    for li in news_section.find_all(config.NEWS_ITEM_LI_TAG):
        title_tag = li.find(config.TITLE_A_TAG, title=True)
        title = title_tag[config.TITLE_A_TITLE_ATTR].strip() if title_tag else ""
        href = title_tag[config.TITLE_A_HREF_ATTR].strip() if title_tag else ""
        date_span = li.find("span", class_=config.NEWS_DATE_CLASS)
        date = date_span.get_text(strip=True).replace("/", ".") if date_span else ""

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

        fileurl_dict = {}
        for p in config.FILE_PROVIDERS:
            file_list = []
            for a in news_div.find_all("a", href=True):
                if p in a["href"]:
                    file_list.append(a["href"])
            fileurl_dict[p] = file_list

        fileurl = "; ".join(f"{k}: {v}" for k, v in fileurl_dict.items())

        with open(output_file, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerow({
                "date": date,
                "title": title,
                "href": href,
                "image1": image1,
                "image2": image2,
                "filename": filename,
                "size": size,
                "fileurl": fileurl
            })

            print(f"Completed: {date}: {filename}")

    detail_driver.quit()
    print(f"Scraping completed. Data saved to {output_file}")


if __name__ == "__main__":
    for i in range(1, 3000):
        browser(config.WEBSITE.replace("| PAGENO |", str(i)))
