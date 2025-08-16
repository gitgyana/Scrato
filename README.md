# Project Scrato

Automated web scraper for extracting articles, file downloads, and metadata from configurable websites. The project is modular, robust, and supports headless browsing, JavaScript disabling, pagination, logging, and SQLite integration.

***

## Table of Contents

- [Features](#features)
- [File Structure](#file-structure)
- [Installation](#installation)
- [Usage](#usage)
  - [1: Run the Scraper](#1-run-the-scraper)
  - [2: Output](#2-output)
  - [3: Configuring](#3-configuring)
- [Advanced Features](#advanced-features)
- [Troubleshooting](#troubleshooting)
- [License](#license)

***

## Features

- **Cross-platform**: Automatically detects and uses the correct ChromeDriver for your OS/architecture
- **Flexible configuration**: All scraping selectors, filtering conditions, and websites are editable in `config.py`
- **User prompts**: Choose headless mode, JavaScript disabling, and more at runtime
- **Pagination and multi-site scraping**
- **Duplicate filtering**: Deduplication via primary keys in SQLite
- **Output to CSV and SQLite database**
- **Comprehensive logging**: All events tracked in log files by date/month

***

## File Structure

```
.
├── config.template        # Contains template for scraping selectors, field names, filtering conditions, and website list
├── driver_config.py       # Handles OS/arch autodetection, ChromeDriver selection, user prompts, and JS disabling
├── news_scraper.py        # Main scraping and data extraction logic
├── requirements.txt
├── LICENSE
├── Outputs/               # Output CSV files, auto-organized by month
├── Logs/                  # Log files, auto-organized by month
└── chromedrivers/         # ChromeDriver binaries organized by OS/arch
```

***

## Installation

1. Ensure you have **Python 3.8+**.
2. Install requirements:

    ```
    pip install -r requirements.txt
    ```

3. Download the **ChromeDriver** (and/or Chrome Headless Shell) matching your OS and Chrome version. Place it in:

    ```
     chromedrivers/
         chromedriver-win64/chromedriver.exe
         chromedriver-linux64/chromedriver
         chromedriver-mac-x64/chromedriver
         chrome-headless-shell-win64/chrome-headless-shell.exe
         (etc.)
     ```

   See [ChromeDriver downloads](https://chromedriver.chromium.org/downloads) and [chrome-headless-shell documentation](https://chromium.googlesource.com/chromium/src/+/main/headless/README.md).

4. Create a `config.py` as per `config.template` and edit it as needed to fit your target website(s) and fields.

***

## Usage

### 1. Run the Scraper

```
python news_scraper.py
```

- On startup, the program:
  - Detects your OS/architecture
  - Prompts for headless mode (`Would you like to run in headless mode?`)
  - Prompts to disable JavaScript (`Disable JavaScript?`)
  - Validates ChromeDriver presence
  - Begins scraping each configured site/page based on `config.WEBSITES` and pagination

### 2. Outputs

- **CSV files**: Saved under `Outputs/*/news_output_*.csv`.
- **Database**: Inserted/created at path given in `config.DATABASE`.
- **Logs**: Saved under `Logs/*/*.log`.

### 3. Configuration

All main scraping, filtering, and destination settings are controlled in `config.py`:

- **Selectors**: `PARENT_DIV_CLASS`, `NEWS_LIST_DIV_CLASS`, etc.
- **Providers**: `FILE_PROVIDERS`
- **Filters**: `TITLE_FILTER_INCLUDE`, `TITLE_FILTER_EXCLUDE`, etc.
- **Websites**: `WEBSITES` (ordered list with pagination placeholder)
- **Output config**: Filenames, paths, database name, table structure

Change these to adapt to a new site or data format.

***

## Advanced Features

- **JavaScript disabling**  
  Toggle via runtime user input; implemented via Chrome options in Selenium.
- **Headless shell support**  
  Runs using Chrome Headless Shell when selected (for stealth scraping).
- **SQLite deduplication**  
  Primary keys configurable for data uniqueness and update behavior.
- **Robust error handling & logging**  
  All important events/errors are timestamped and logged to disk.

***

## Troubleshooting

- **SessionNotCreatedException**: Make sure ChromeDriver matches your Chrome browser version.
- **FileNotFoundError**: Check correct driver binary and folders.
- **No records found**: Verify selectors in `config.py` match the HTML of your target site.
- **CSV/DB fields mismatch**: Update field lists and table structures in `config.py` and `news_scraper.py`.

***

## License

This project is licensed under the **ScratoLicense 1.0** - see the [LICENSE](./LICENSE) file for details.

***

**Happy scraping!**  
If you encounter an issue, please check driver compatibility and update selector configuration in `config.py`.

***