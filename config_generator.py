"""
Intelligent Auto-Config Generator
Automatically analyzes any website and generates optimal scraping configuration
Designed to work with most of news/content websites without user input


[WIP]: WORK IN PROGRESS
"""

import os
import re
import time
import json
from datetime import datetime
from collections import Counter, defaultdict
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup, NavigableString
from datetime import datetime
import driver_config

class ConfigGenerator:
    def __init__(self):
        self.process_indent = ' ' * 4
        self.driver = None
        self.config_data = {}
        self.analyzed_sites = []

        # Possible date patterns
        # Numeric Date Patterns (Flexible Formats)
        self.DATE_PATTERNS = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',    # MM/DD/YYYY or D/M/YY
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',      # YYYY/MM/DD
            r'^[0-3]?[0-9][./-][0-3]?[0-9][./-](?:\d{2})?\d{2}$',        # D.M.Y
            r'^(?:0[1-9]|1[0-2])[/-](?:0[1-9]|[12]\d|3[01])[/-]\d{4}$',  # strict MM/DD/YYYY
            r'^(?:0[1-9]|[12]\d|3[01])[/-](?:0[1-9]|1[0-2])[/-]\d{4}$',  # strict DD/MM/YYYY
        ]
        # Dates with Month Names (Short & Long)
        self.DATE_PATTERNS += [
            r'\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*,?\s*\d{2,4}',  # "10 Jan, 2025"
            r'(Jan|Feb|...|Dec)\s+\d{1,2},?\s*\d{2,4}',                                     # "Jan 10, 2025"
            r'\d{1,2}\s+(January|...|December)\s*,?\s*\d{2,4}',    # "10 January, 2025"
            r'(January|...)\s+\d{1,2},?\s*\d{2,4}',                # "January 10, 2025"
        ]
        # Leap-Year Aware Patterns (DD/MM/YYYY with Checks)
        self.DATE_PATTERNS += [
            r'^(?:(?:31([\/\-.])(?:0?[13578]|1[02]))\1|'
            r'(?:(?:29|30)\1(?:0?[13-9]|1[0-2]))\1)'
            r'(?:(?:1[6-9]|[2-9]\d)?\d{2})$|'
            r'^(?:29([\/\-.])0?2\2'
            r'(?:(?:(?:1[6-9]|[2-9]\d)?(?:0[48]|[2468][048]|[13579][26]))|'
            r'(?:(?:16|[2468][048]|[3579][26])00)))$|'
            r'^(?:0?[1-9]|1\d|2[0-8])([\/\-.])'
            r'(?:(?:0?[1-9])|(?:1[0-2]))\3'
            r'(?:(?:1[6-9]|[2-9]\d)?\d{2})$',
        ]
        # ISO 8601 & Timestamp Formats
        self.DATE_PATTERNS += [
            r'^\d{4}-\d{2}-\d{2}$',                              # YYYY-MM-DD
            r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$',            # ISO datetime
            r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z?$',     # With milliseconds and optional Z
        ]
        # RFC 2822 & Ordinal Day Formats
        self.DATE_PATTERNS += [
            r'^(Mon|Tue|...|Sun),\s\d{2}\s(?:Jan|...|Dec)\s\d{4}\s'
            r'(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d\s'
            r'(?:[+-]\d{4}|UT|GMT)$',
            r'\d{1,2}(st|nd|rd|th)\s+(Jan|...|Dec)\s+\d{4}',
            r'(Jan|...|Dec)\s+\d{1,2}(st|nd|rd|th),\s+\d{4}',
        ]
        # Relative Dates & Simple Relative Words
        self.DATE_PATTERNS += [
            r'\d+\s+(hours?|days?|weeks?|months?)\s+ago',
            r'^(?:today|yesterday|tomorrow)$',
            r'^(?:last|next)\s+(week|month|year)$',
        ]

        # Common patterns for different content types
        self.NEWS_INDICATORS = [
            'news', 'article', 'post', 'story', 'item', 'entry', 'content',
            'feed', 'list', 'grid', 'card', 'tile', 'block'
        ]

        self.CONTAINER_INDICATORS = [
            'container', 'wrapper', 'main', 'content', 'section', 'area',
            'zone', 'region', 'panel', 'box', 'frame'
        ]

        self.TITLE_INDICATORS = [
            'title', 'headline', 'header', 'subject', 'name', 'caption'
        ]

        self.DATE_INDICATORS = [
            'date', 'time', 'published', 'created', 'updated', 'ago',
            'timestamp', 'when', 'day', 'month', 'year'
        ]

        self.FILE_PROVIDERS = [
            'rapidgator', 'mega', 'mediafire', 'dropbox', 'drive.google',
            'onedrive', 'box.com', 'sendspace', 'zippyshare', 'uploaded',
            'turbobit', 'nitroflare', 'keep2share', 'k2s', 'subyshare'
        ]

        # Common exclude patterns for filtering
        self.EXCLUDE_WORDS = ['ad', 'ads', 'sponsored', 'promo', 'advertisement']


    def setup_browser(self):
        """Initialize browser for analysis"""
        print("Setting up intelligent browser...")
        
        chromedriver_path = f"./{driver_config.chromedriver_path}"

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
            
        self.driver = webdriver.Chrome(service=service, options=options)
        print("Browser ready for intelligent analysis\n")


    def analyze_website_structure(self, url):
        """Analyze website structure and identify key elements"""
        print(f"\nAnalyzing website structure: {url}")
        
        try:
            self.driver.get(url)
            time.sleep(3)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            analysis = {
                'url': url,
                'title': soup.title.get_text() if soup.title else '',
                'main_container': self.find_main_container(soup),
                'news_items': self.find_news_items(soup),
                'pagination': self.detect_pagination(soup, url),
                'filters': self.detect_content_filters(soup),
            }


            return analysis
            
        except Exception as e:
            print(f"{self.process_indent}Error analyzing {url}: {e}")
            return None


    def find_main_container(self, soup):
        """Find the main container holding all content items"""
        print("Finding main content container...")
        
        candidates = []
        
        for tag in soup.find_all(['div', 'section', 'main', 'article']):
            score = 0
            classes = ' '.join(tag.get('class', [])).lower()
            tag_id = tag.get('id', '').lower()
            
            for indicator in self.NEWS_INDICATORS + self.CONTAINER_INDICATORS:
                if indicator in classes or indicator in tag_id:
                    score += 10
            
            children = tag.find_all(['div', 'article', 'li'])
            if 5 <= len(children) <= 100:
                score += len(children)
            
            text_content = len(tag.get_text().strip())
            if text_content > 500:
                score += min(text_content // 100, 20)
            
            if score > 15:
                candidates.append({
                    'element': tag,
                    'score': score,
                    'selector': self.generate_css_selector(tag),
                    'class': ' '.join(tag.get('class', [])),
                    'id': tag.get('id', '')
                })
        
        if candidates:
            best = max(candidates, key=lambda x: x['score'])
            print(f"{self.process_indent}Found main container: {best['selector']} (score: {best['score']})")
            return best
        
        print(f"{self.process_indent}!!Using body as fallback container")
        return {'selector': 'body', 'class': '', 'id': ''}

    
    def generate_css_selector(self, element):
        """Generate a reliable CSS selector for an element"""
        if element.get('id'):
            return f"#{element['id']}"
        
        classes = element.get('class', [])
        if classes:
            for cls in classes:
                if len(cls) > 2 and not cls.startswith(('col-', 'row-', 'pull-', 'push-')):
                    return f".{cls}"
        
        if classes:
            return f"{element.name}.{classes[0]}"
        
        return element.name


    def find_news_items(self, soup):
        """Automatically detect individual news/content items"""
        print("Detecting news items...")
        
        item_candidates = defaultdict(list)
        
        for tag_name in ['div', 'article', 'li', 'section']:
            elements = soup.find_all(tag_name)
            
            for element in elements:
                if self.looks_like_news_item(element):
                    classes = tuple(sorted(element.get('class', [])))
                    if not classes:
                        classes = self.get_nearest_class(element)

                    item_candidates[classes].append(element)
        
        best_pattern = None
        max_count = 0
        
        for classes, elements in item_candidates.items():
            if len(elements) >= 3:
                if len(elements) > max_count:
                    max_count = len(elements)
                    best_pattern = (classes, elements)
        
        if best_pattern:
            classes, elements = best_pattern
            sample_element = elements[0]
            
            result = {
                'tag': sample_element.name,
                'class': ' '.join(classes),
                'selector': self.generate_css_selector(sample_element),
                'count': len(elements),
                'title_element': self.find_title_in_item(sample_element),
                'date_element': self.find_date_in_item(sample_element),
                'link_element': self.find_link_in_item(sample_element)
            }
            
            print(f"{self.process_indent}Found {result['count']} news items: {result['selector']}")
            return result
        
        print(f"{self.process_indent}!! Could not detect consistent news item pattern")
        return None


    def looks_like_news_item(self, element):
        """Determine if an element looks like a news item"""
        if len(element.get_text().strip()) < 20:
            return False
        
        if not element.find('a'):
            return False
        
        text_length = len(element.get_text())
        if text_length < 50 or text_length > 2000:
            return False
        
        classes = ' '.join(element.get('class', [])).lower()
        element_id = element.get('id', '').lower()
        
        score = 0
        for indicator in self.NEWS_INDICATORS:
            if indicator in classes or indicator in element_id:
                score += 1
        
        return score > 0 or len(element.get_text()) > 100

    
    def find_title_in_item(self, item):
        """Find the title element within a news item"""
        links = item.find_all('a')
        
        for link in links:
            text = link.get_text().strip()
            if 20 <= len(text) <= 200:
                return {
                    'tag': link.name,
                    'selector': self.generate_css_selector(link),
                    'attribute': 'title' if link.get('title') else 'text',
                    'href_attr': 'href'
                }
        
        # Fallback
        for tag in item.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = tag.get_text().strip()
            if 10 <= len(text) <= 200:
                return {
                    'tag': tag.name,
                    'selector': self.generate_css_selector(tag),
                    'attribute': 'text',
                    'href_attr': 'href'
                }
        
        return None


    def find_date_in_item(self, item):
        """Find the date element within a news item"""
        for element in item.find_all(['span', 'div', 'time', 'p']):
            text = element.get_text().strip()
            classes = ' '.join(element.get('class', [])).lower()
            
            for pattern in self.DATE_PATTERNS:
                if re.search(pattern, text, re.IGNORECASE):
                    return {
                        'tag': element.name,
                        'class': ' '.join(element.get('class', [])),
                        'selector': self.generate_css_selector(element)
                    }
            
            for indicator in self.DATE_INDICATORS:
                if indicator in classes and len(text) > 5:
                    return {
                        'tag': element.name,
                        'class': ' '.join(element.get('class', [])),
                        'selector': self.generate_css_selector(element)
                    }
        
        return None

    
    def find_link_in_item(self, item):
        """Find the main link within a news item"""
        links = item.find_all('a', href=True)
        
        for link in links:
            href = link.get('href')
            text = link.get_text().strip()
            
            if len(text) >= 20:
                return {
                    'tag': link.name,
                    'selector': self.generate_css_selector(link),
                    'href': href
                }
        
        # Fallback: first link
        if links:
            return {
                'tag': links[0].name,
                'selector': self.generate_css_selector(links),
                'href': links.get('href')
            }
        
        return None

    
    def get_nearest_class(self, element, max_depth=3):
        depth = 0
        while element and depth < max_depth:
            classes = element.get('class', [])
            if classes:
                return tuple(sorted(classes))
            element = element.parent
            depth += 1

        # Fallback
        return ()


    def detect_pagination(self, soup, url):
        """Detect pagination patterns"""
        print("Detecting pagination...")
        
        pagination_indicators = ['page', 'next', 'prev', 'more', 'load']
        pagination_elements = []
        
        for element in soup.find_all(['a', 'button', 'span']):
            text = element.get_text().lower().strip()
            classes = ' '.join(element.get('class', [])).lower()
            href = element.get('href', '')
            
            for indicator in pagination_indicators:
                if indicator in text or indicator in classes:
                    pagination_elements.append(element)
                    break
        
        page_numbers = []
        for element in soup.find_all('a', href=True):
            href = element.get('href')
            text = element.get_text().strip()
            
            if text.isdigit() and int(text) > 1:
                page_numbers.append((int(text), href))
        
        if page_numbers:
            page_numbers.sort()
            if len(page_numbers) >= 2:
                url1 = page_numbers[0][1]
                url2 = page_numbers[1][1]
                
                pattern = self.extract_pagination_pattern(url, url1, url2)
                if pattern:
                    print(f"{self.process_indent}'pattern': {pattern}, 'max_detected': {max(p[0] for p in page_numbers)}")
                    return {'pattern': pattern, 'max_detected': max(p[0] for p in page_numbers)}
        
        print(f"{self.process_indent}No clear pagination pattern detected")
        return None

    
    def extract_pagination_pattern(self, base_url, url1, url2):
        """Extract pagination pattern from URLs"""
        try:
            url1 = urljoin(base_url, url1)
            url2 = urljoin(base_url, url2)
            
            for i, (c1, c2) in enumerate(zip(url1, url2)):
                if c1 != c2:
                    for j in range(i, min(len(url1), len(url2))):
                        if url1[j] == url2[j]:
                            return url1[:i] + "| PAGENO |" + url1[j:]
                    
                    return url1[:i] + "| PAGENO |" + url1[min(len(url1), len(url2)):]

        except:
            print(f"{self.process_indent}!!Unable to extract pagination pattern")
        
        return None

    
    def detect_content_filters(self, soup):
        """Automatically detect content filtering patterns"""
        print("Detecting content filters...")
        
        titles = []
        for link in soup.find_all('a'):
            text = link.get_text().strip()
            if 20 <= len(text) <= 200:
                titles.append(text)
        
        bracket_patterns = []
        for title in titles:
            matches = re.findall(r'\[([^\]]+)\]', title)
            bracket_patterns.extend(matches)
        
        pattern_counts = Counter(bracket_patterns)
        
        filters = {
            'include_patterns': [],
            'exclude_patterns': []
        }
        
        if pattern_counts:
            most_common = pattern_counts.most_common(3)
            for pattern, count in most_common:
                if count >= 2:
                    filters['include_patterns'].append(f'[{pattern}]')
        
        for title in titles:
            for word in self.EXCLUDE_WORDS:
                if word.lower() in title.lower():
                    filters['exclude_patterns'].append(word.upper())
                    break

        print(f"{self.process_indent}Include: {filters['include_patterns']}")
        print(f"{self.process_indent}Exclude: {filters['exclude_patterns']}")
        return filters

    
    def run_auto_generator(self):
        """Main entry point for automatic config generation"""
        print("AUTO-CONFIG GENERATOR")
        print("="*50)
        print("This tool will automatically analyze your website(s)")
        print("and create an optimal scraping configuration.")
        print("Just provide website URLs and we'll handle the rest.")
        
        websites = []
        while True:
            url = input(f"\n{self.process_indent}Enter website URL {len(websites)+1} (or ENTER to continue): ").strip()
            if not url:
                if websites:
                    break
                else:
                    print(f"{self.process_indent}Please enter at least one website URL")
                    continue
            
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            websites.append(url)
            print(f"{self.process_indent}Added: {url}")
        
        # Setup browser
        self.setup_browser()
            
        # Analyze each website
        analyses = []
        for i, url in enumerate(websites, 1):
            print(f"\n{'='*20} ANALYSIS {i}/{len(websites)} {'='*20}")
            analysis = self.analyze_website_structure(url)
            if analysis:
                analyses.append(analysis)
                self.analyzed_sites.append(url)
            
            time.sleep(2)



if __name__ == "__main__":
    try:
        generator = ConfigGenerator()
        generator.run_auto_generator()
    except KeyboardInterrupt:
        print("\n\nProcess cancelled by user")
    except Exception as e:
        print(f"\nFatal error: {e}")