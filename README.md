# News Scraper

Automated news scraper using Selenium and BeautifulSoup to extract structured news content and downloadable file links from specified websites. The scraper is cross-platform and automatically detects your operating system and processor architecture to use the correct ChromeDriver or Chrome Headless Shell.

***

## Table of Contents

- [News Scraper](#news-scraper)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Step 1: Configure your scraping targets](#step-1-configure-your-scraping-targets)
  - [Step 2: Run the main script](#step-2-run-the-main-script)
  - [Output columns](#output-columns)
- [Configuration Reference](#configuration-reference)
  - [config.py](#configpy)
  - [config_driver.py](#config_driverpy)
- [Advanced](#advanced)
- [Troubleshooting](#troubleshooting)
- [File Structure](#file-structure)
- [License](#license)

***
## Features

- **Automatic OS & architecture detection:** Uses the correct ChromeDriver for OS/arch
- **Headless mode prompt:** User-selectable within 10 seconds or defaults to normal mode
- **Robust scraping:** Filters news items according to custom keywords (`[NEW]` must be present, `AD` excluded)
- **Detail page scraping:** Follows each valid link, extracting two images and file download links for certain providers
- **Configurable selectors & providers:** Easily adjust targets via `config.py`
- **CSV output:** Saves results to a timestamped CSV file in the `Outputs` directory

***

## Installation

1. **Clone this repository**
2. **Install Python 3.8+**
3. **Install required packages:**

    ```
    pip install -r requirements.txt
    ```

4. **Download the correct ChromeDriver(s):**
   - Place platform-specific ChromeDriver or Chrome Headless Shell binaries in the folder `chromedrivers/` following this structure:

     ```
     chromedrivers/
         chromedriver-win64/chromedriver.exe
         chromedriver-linux64/chromedriver
         chromedriver-mac-x64/chromedriver
         chrome-headless-shell-win64/chrome-headless-shell.exe
         (etc.)
     ```

   - See [ChromeDriver downloads](https://chromedriver.chromium.org/downloads) and [chrome-headless-shell documentation](https://chromium.googlesource.com/chromium/src/+/main/headless/README.md).

***

## Usage

### Step 1: **Configure your scraping targets**
- Edit `config.py` to match the desired website's HTML structure and filtering rules.

### Step 2: **Run the main script**

```bash
python news_scraper.py
```

- On launch, the tool prints your OS, asks if you want headless mode, and validates a ChromeDriver binary is present.

- You will be prompted:
    1. **"Would you like to run in headless mode? (y/N, default N):"**  
    2. **"Enter site URL to scrape:"**  

- The scraper navigates and extracts all matching news entries, following links to detail pages.

- Data is saved to a timestamped CSV in `Outputs/`, e.g.:
  ```
  Outputs/news_output_11.08.2025_02.03.05.csv
  ```

### Output columns:
- `date` – Date of news item
- `title` – News title
- `href` – Detail page URL
- `image1` – First image URL (from fisrst_sc div)
- `image2` – Second image URL (from Recipepod div)
- `filename` – Parsed filename from file size line
- `size` – Parsed file size
- `fileurl` – Semicolon-separated download links for providers

***

## Configuration Reference

### `config.py`

Edit these to quickly retarget scraping:

```python
PARENT_DIV_CLASS = "category_news_headlines"
NEWS_LIST_DIV_CLASS = "category_news"
NEWS_LIST_UL_TAG = "ul"
NEWS_ITEM_LI_TAG = "li"
TITLE_A_TAG = "a"
TITLE_A_TITLE_ATTR = "title"
TITLE_A_HREF_ATTR = "href"
NEWS_DATE_CLASS = "news_date"
DETAIL_NEWS_DIV_CLASS = "news"
DETAIL_IMAGE1_DIV_CLASS = "fisrst_sc"
DETAIL_IMAGE1_IMG_TAG = "img"
DETAIL_IMAGE2_DIV_CLASS = "Recipepod"
FILE_SIZE_PREFIX = "File size:"
FILE_PROVIDERS = ["source1", "source2", "source3", "source4"]
TITLE_FILTER_INCLUDE = "[NEW]"
TITLE_FILTER_EXCLUDE = "AD"
```

### `config_driver.py`

Handles automatic OS/platform detection and ChromeDriver/headless shell selection.
You can override the detection or structure as needed for your environment.

***

## Advanced

- **Robust to site changes:** All structural selectors and keyword filters are centrally maintained in `config.py`.
- **Supports Chrome Headless Shell:** Optionally uses headless shell if available and chosen.
- **Extensible:** Adjust output location, fields, or scraping depth by editing `news_scraper.py`.

***

## Troubleshooting

- **SessionNotCreatedException:** Make sure your ChromeDriver version exactly matches your installed Chrome browser.
- **FileNotFoundError:** Download the right ChromeDriver/shell for your platform and place in `chromedrivers/`.
- **Selector errors:** Update CSS class names or tags in `config.py` if the website's HTML structure changes.

***

## File Structure

```
│
├── news_scraper.py        # Main scraping script
├── config.py              # Site selectors & rules
├── config_driver.py       # OS/platform/driver detection logic
├── requirements.txt
├── .gitignore
│
├── chromedrivers/         # ChromeDriver binaries per architecture
│   └── chromedriver-win64/chromedriver.exe
│   └── chrome-headless-shell-win64/chrome-headless-shell.exe
│   └── ...
├── Outputs/               # (Created automatically)
│   └── news_output_.csv
```

***

## License

This project is licensed under the **ScratoLicense 1.0** - see the [LICENSE](./LICENSE) file for details.

***

**Happy scraping!**  
If you encounter an issue, please check driver compatibility and update selector configuration in `config.py`.

***

