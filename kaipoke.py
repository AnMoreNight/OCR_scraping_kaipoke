"""
Kaipoke Login and Data Upload Module using Playwright
"""

import os
import time
import json
from typing import List, Dict, Optional
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

# Load environment variables
load_dotenv()


class KaipokeScraper:
    """Client for Kaipoke website - handles login and data upload"""
    
    def __init__(self, headless: bool = False):
        """Initialize the Kaipoke client
        
        Args:
            headless: If True, run browser in headless mode (no GUI)
        """
        self.base_url = "https://r.kaipoke.biz"
        self.login_url = "https://r.kaipoke.biz/kaipokebiz/login/COM020102.do"
        self.target_page_url = "https://r.kaipoke.biz/kaipokebiz/business/plan_actual/MEM087101.do?conversationContext=3"
        self.is_logged_in = False
        self.headless = headless
        
        # Playwright objects
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
        # Get credentials from .env file
        self.corporate_code = os.getenv('KAIPOKE_CORPORATE_CODE')
        self.username = os.getenv('KAIPOKE_USERNAME')
        self.password = os.getenv('KAIPOKE_PASSWORD')
        
        # Initialize Playwright
        self._init_browser()
    
    def _init_browser(self):
        """Initialize Playwright browser"""
        print("Initializing Playwright browser...")
        
        try:
            # Start Playwright
            self.playwright = sync_playwright().start()
            
            # Launch browser (Chromium)
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                args=['--start-maximized']
            )
            
            # Create browser context
            self.context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # Create new page
            self.page = self.context.new_page()
            
            print("✅ Playwright browser initialized successfully")
            
        except Exception as e:
            print(f"❌ Error initializing Playwright browser: {e}")
            raise
    
    def __del__(self):
        """Cleanup: Don't automatically close browser"""
        # Browser will stay open - user must close manually
        pass
        
    def close_browser(self):
        """Close the browser"""
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            print("Browser closed")
        except Exception as e:
            print(f"Error closing browser: {e}")
    
    def login(self, corporate_code: str = None, username: str = None, password: str = None) -> bool:
        """Login to Kaipoke website using Playwright"""
        print("\n=== Logging in to Kaipoke ===")
        
        # Use provided credentials or fall back to env variables
        corporate_code = corporate_code or self.corporate_code
        username = username or self.username
        password = password or self.password
        
        if not all([corporate_code, username, password]):
            print("❌ Error: Missing credentials. Please set KAIPOKE_CORPORATE_CODE, KAIPOKE_USERNAME, and KAIPOKE_PASSWORD in .env file")
            return False
        
        try:
            # Step 1: Navigate to login page with increased timeout and less strict waiting
            print(f"📄 Opening login page: {self.login_url}")
            self.page.goto(self.login_url, wait_until='load', timeout=60000)  # 60 seconds timeout, wait for 'load' instead of 'networkidle'
            
            # Wait a bit for dynamic content to load
            time.sleep(2)
            
            # Step 2: Wait for form elements and fill them in
            print("⏳ Waiting for login form to load...")
            
            # Wait for the corporate code input to be visible
            self.page.wait_for_selector('input[id="form:corporation_id"]', state='visible', timeout=10000)
            
            # Fill in the corporate code field (法人ID)
            print("📝 Filling in 法人ID (Corporate Code)...")
            self.page.fill('input[id="form:corporation_id"]', corporate_code)
            time.sleep(0.5)
            
            # Fill in the username field (ユーザーID)
            print("📝 Filling in ユーザーID (Username)...")
            self.page.fill('input[id="form:member_login_id"]', username)
            time.sleep(0.5)
            
            # Fill in the password field (パスワード)
            print("📝 Filling in パスワード (Password)...")
            self.page.fill('input[id="form:password"]', password)
            time.sleep(0.5)
            
            # Step 3: Click the login button
            print("🖱️ Clicking login button (ログイン)...")
            
            # Wait for button to be visible
            self.page.wait_for_selector('input[id="form:logn_nochklogin"]', state='visible', timeout=5000)
            self.page.click('input[id="form:logn_nochklogin"]')
            
            # Step 4: Wait for navigation and check if login was successful
            print("⏳ Waiting for login to complete...")
            
            # Wait for URL change or timeout
            try:
                self.page.wait_for_url(lambda url: 'login' not in url.lower(), timeout=10000)
                print("✅ URL changed - login appears successful")
            except:
                print("⚠️ URL did not change, checking current page...")
            
            time.sleep(2)
            
            # Check current URL - if redirected away from login page, login was successful
            current_url = self.page.url
            print(f"📍 Current URL: {current_url}")
            
            # Check if login was successful (URL should change from login page)
            if 'login' not in current_url.lower() or 'COM020102' not in current_url:
                print("✅ Login successful!")
                self.is_logged_in = True
                return True
            else:
                # Check for error messages
                page_text = self.page.content()
                if 'エラー' in page_text or 'error' in page_text.lower():
                    print("❌ Login failed: Error message detected on page")
                else:
                    print("❌ Login failed: Still on login page")
                
                return False
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def navigate_to_target_page(self) -> bool:
        """Navigate to the plan/actual page after login"""
        if not self.is_logged_in:
            print("❌ Error: Not logged in. Please login first.")
            return False
        
        try:
            print(f"\n📄 Navigating to target page: {self.target_page_url}")
            self.page.goto(self.target_page_url, wait_until='load', timeout=60000)
            time.sleep(2)
            
            current_url = self.page.url
            print(f"✅ Successfully navigated to target page")
            print(f"📍 Current URL: {current_url}")
            
            # Keep browser open for data upload
            print("🌐 Browser will remain open - ready for data input...")
            return True
            
        except Exception as e:
            print(f"❌ Error navigating to target page: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def upload_ocr_data(self, ocr_results: List[Dict]) -> bool:
        """Upload OCR extracted data to Kaipoke"""
        if not self.is_logged_in:
            print("Error: Not logged in. Please login first.")
            return False
        
        if not ocr_results:
            print("Error: No OCR results to upload")
            return False
        
        print(f"\nUploading {len(ocr_results)} records to Kaipoke...")
        
        try:
            success_count = 0
            for i, record in enumerate(ocr_results, 1):
                print(f"\nUploading record {i}/{len(ocr_results)}...")
                print(f"Data: {record}")
                
                # TODO: Implement the actual upload logic based on Kaipoke's form structure
                # This is a placeholder - you'll need to customize based on the actual upload page
                
                # Example: Find the upload/input page URL
                # upload_url = f"{self.base_url}/home-care-record/add"  # Adjust URL as needed
                
                # Prepare the data to upload
                # upload_data = {
                #     'name': record.get('name', ''),
                #     'date': record.get('date', ''),
                #     'time': record.get('time', ''),
                # }
                
                # Submit the data
                # response = self.session.post(upload_url, data=upload_data)
                
                # For now, just print what would be uploaded
                print(f"Would upload: {record}")
                success_count += 1
                
                time.sleep(self.request_delay)
            
            print(f"\n✅ Successfully uploaded {success_count}/{len(ocr_results)} records")
            return True
            
        except Exception as e:
            print(f"❌ Error uploading data: {e}")
            return False
    
    
    def save_results(self, results: List[Dict], filename: str = "kaipoke_data.json"):
        """Save scraping results to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"Results saved to {filename}")
        except Exception as e:
            print(f"Error saving results: {e}")
    
    def process_ocr(self, image_path: str) -> List[Dict]:
        """Process OCR on image (placeholder for OCR integration)"""
        # This would integrate with your OCR functionality
        # For now, return empty list
        print(f"OCR processing for {image_path} - placeholder")
        return []
    
    def scrape_with_ocr(self, image_path: str) -> List[Dict]:
        """Combined OCR and scraping workflow"""
        print("Starting combined OCR and scraping workflow...")
        
        # Step 1: OCR processing
        ocr_results = self.process_ocr(image_path)
        
        # Step 2: Use OCR results for scraping
        if ocr_results:
            # Use OCR data to enhance scraping
            enhanced_results = []
            for ocr_data in ocr_results:
                # Use OCR data to search or filter scraping results
                search_results = self.search_with_ocr_data(ocr_data)
                enhanced_results.extend(search_results)
            
            return enhanced_results
        
        return []
    
    def search_with_ocr_data(self, ocr_data: Dict) -> List[Dict]:
        """Use OCR data to enhance scraping search"""
        # Use OCR extracted data to search for more information
        # This is a placeholder - customize based on your needs
        print(f"Searching with OCR data: {ocr_data}")
        return []


def main():
    """Example usage of KaipokeScraper"""
    scraper = KaipokeScraper()
    login = scraper.login()
    while login:
        nav = scraper.navigate_to_target_page()
        if nav:
            print("✅ Successfully navigated to target page")
        else:
            print("❌ Failed to navigate to target page")
    # else:
    #     print("❌ Failed to login")

if __name__ == "__main__":
    main()
