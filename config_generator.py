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
                # 'news_items': pass,
                # 'pagination': pass,
                # 'detail_structure': pass,
                # 'filters': pass,
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
            a = '\n'.join(
                f"{c['score']}, {c['class']}, {c['id']}" for c in candidates
            )

            print(a)
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