import time
import threading
import csv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import config
import config_driver


def create_driver(chromedriver_path):
    options = Options()
    if "headless" in chromedriver_path:
        options.add_argument("--headless=new")

    service = Service(chromedriver_path)
    return webdriver.Chrome(service=service, options=options)


def main():
    now = datetime.now()
    formatted_dt = now.strftime("%d.%m.%Y_%H.%M.%S")
    output_file = f"news_output_{formatted_dt}.csv"
    
    site = input("Enter site URL to scrape: ").strip()
    chromedriver_path = f"./{config_driver.chromedriver_path}"

    # Main browser
    driver = create_driver(chromedriver_path)
    driver.get(site)

    # Wait for main content
    # try:
    #     WebDriverWait(driver, 60).until(
    #         EC.presence_of_element_located((By.CLASS_NAME, config.PARENT_DIV_CLASS))
    #     )
    # except Exception as e:
    #     print(f"Failed to load main content: {e}")
    #     driver.quit()
    #     return

    # Parse main page
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

    # CSV setup
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            "date", "title", "href",
            "image1", "image2",
            "filename", "size", "fileurl"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

    # Loop through news items
    detail_driver = create_driver(chromedriver_path)
    for li in news_section.find_all(config.NEWS_ITEM_LI_TAG):
        title_tag = li.find(config.TITLE_A_TAG, title=True)
        title = title_tag[config.TITLE_A_TITLE_ATTR].strip() if title_tag else ""
        href = title_tag[config.TITLE_A_HREF_ATTR].strip() if title_tag else ""
        date_span = li.find("span", class_=config.NEWS_DATE_CLASS)
        date = date_span.get_text(strip=True).replace("/", ".") if date_span else ""

        # Filter titles
        if config.TITLE_FILTER_INCLUDE not in title:
            continue
        if config.TITLE_FILTER_EXCLUDE in title:
            continue

        # Open detail page for each valid href
        detail_driver.get(href)
        # try:
        #     WebDriverWait(detail_driver, 10).until(
        #         EC.presence_of_element_located((By.CLASS_NAME, config.DETAIL_NEWS_DIV_CLASS))
        #     )
        # except Exception:
        #     print(f"Timeout loading detail page: {href}")
        #     detail_driver.quit()
        #     detail_driver = create_driver(chromedriver_path)
        #     continue

        detail_soup = BeautifulSoup(detail_driver.page_source, "html.parser")

        news_div = detail_soup.find("div", class_=config.DETAIL_NEWS_DIV_CLASS)
        if not news_div:
            continue

        # Extract Image1
        img1_tag = news_div.find("div", class_=config.DETAIL_IMAGE1_DIV_CLASS)
        image1 = img1_tag.find(config.DETAIL_IMAGE1_IMG_TAG)["src"] if img1_tag and img1_tag.find(config.DETAIL_IMAGE1_IMG_TAG) else ""

        # Extract Image2
        img2_div = news_div.find("div", class_=config.DETAIL_IMAGE2_DIV_CLASS)
        image2 = ""
        if img2_div and img2_div.find("img"):
            image2 = img2_div.find("img").get("src", "")

        # Extract filename & size
        filename, size = "", ""
        for txt in news_div.stripped_strings:
            if txt.startswith(config.FILE_SIZE_PREFIX):
                parts = txt[len(config.FILE_SIZE_PREFIX):].split(":")
                if len(parts) >= 2:
                    filename = parts[0].strip()
                    size = parts[1].strip()

        # Extract file URLs by providers
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
            while True:
                try:
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
                except Exception as e:
                    print(f"Error writing row for title '{title}': {e}")
                    time.sleep(10)
                else:
                    break

    print("Scraping completed. Data saved to output.csv.")


if __name__ == "__main__":
    main()
