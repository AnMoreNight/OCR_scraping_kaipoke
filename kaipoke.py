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
            ocr_data: List of dictionaries containing extracted OCR data
            headless: If True, run browser in headless mode (no GUI)
        """
        self.base_url = "https://r.kaipoke.biz"
        self.login_url = "https://r.kaipoke.biz/kaipokebiz/login/COM020102.do"
        self.Receipt_page_url = "https://r.kaipoke.biz/kaipokebiz/common/COM020101.do?fromBP=true"
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
    
    def navigate_to_Receipt_page(self) -> bool:
        """Navigate to the Receipt page after login"""
        if not self.is_logged_in:
            print("❌ Error: Not logged in. Please login first.")
            return False
        
        try:
            print(f"\n📄 Navigating to Receipt page: {self.Receipt_page_url}")
            self.page.goto(self.Receipt_page_url, wait_until='load', timeout=60000)
            time.sleep(10)
            
            current_url = self.page.url
            print(f"✅ Successfully navigated to Receipt page")
            print(f"📍 Current URL: {current_url}")
            
            # Keep browser open for data upload
            print("🌐 Browser will remain open - ready for data input...")
            return True
            
        except Exception as e:
            print(f"❌ Error navigating to Receipt page: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def navigate_to_ask_page(self) -> Optional[str]:
        """Navigate to the Ask page by clicking the specific navigation link"""
        if not self.is_logged_in:
            print("❌ Error: Not logged in. Please login first.")
            return None
        
        try:
            print(f"\n📄 Navigating to Ask page...")
            
            # Wait for the page to load completely
            time.sleep(3)
            
            # Look for the specific link with the onclick handler
            # The link contains: 障害者総合支援(訪問系)/1116513696
            print("🔍 Looking for the navigation link...")
            
            # Try to find the link by its text content
            link_selector = 'a[onclick*="onesCompanyPlantInternalId"][onclick*="168937"]'
            
            # Wait for the link to be visible
            print("⏳ Waiting for navigation link to be visible...")
            self.page.wait_for_selector(link_selector, state='visible', timeout=15000)
            
            # Get the current URL before clicking
            current_url_before = self.page.url
            print(f"📍 Current URL before navigation: {current_url_before}")
            
            # Click the specific link
            print("🖱️ Clicking on 障害者総合支援(訪問系)/1116513696 link...")
            self.page.click(link_selector)
            
            # Wait for navigation to complete
            print("⏳ Waiting for navigation to complete...")
            time.sleep(5)
            
            # Get the new URL after navigation
            current_url_after = self.page.url
            print(f"📍 Current URL after navigation: {current_url_after}")
            
            # Check if navigation was successful (URL should have changed)
            if current_url_after != current_url_before:
                print("✅ Successfully navigated to Ask page!")
                print(f"📍 New page URL: {current_url_after}")
                return current_url_after
            else:
                print("⚠️ URL did not change - navigation may have failed")
                # Check if we're still on the same page or if there was an error
                page_title = self.page.title()
                print(f"📄 Page title: {page_title}")
                return current_url_after
            
        except Exception as e:
            print(f"❌ Error navigating to Ask page: {e}")
            import traceback
            traceback.print_exc()
            
            # Try alternative approach - look for the link by text content
            try:
                print("🔄 Trying alternative approach - searching by link text...")
                
                # Look for the link containing the specific text
                link_text = "障害者総合支援(訪問系)/1116513696"
                link_element = self.page.locator(f'a:has-text("{link_text}")')
                
                if link_element.count() > 0:
                    print(f"✅ Found link with text: {link_text}")
                    current_url_before = self.page.url
                    
                    # Click the link
                    link_element.click()
                    time.sleep(5)
                    
                    current_url_after = self.page.url
                    print(f"📍 Navigation result: {current_url_after}")
                    
                    if current_url_after != current_url_before:
                        print("✅ Alternative navigation successful!")
                        return current_url_after
                    else:
                        print("⚠️ Alternative navigation - URL unchanged")
                        return current_url_after
                else:
                    print(f"❌ Could not find link with text: {link_text}")
                    return None
                    
            except Exception as alt_e:
                 print(f"❌ Alternative approach also failed: {alt_e}")
                 return None
     
    def navigate_to_user_schedule_registration(self) -> Optional[str]:
         """Navigate to User-specific Schedule/Performance Registration page"""
         if not self.is_logged_in:
             print("❌ Error: Not logged in. Please login first.")
             return None
         
         try:
             print(f"\n📄 Navigating to User-specific Schedule/Performance Registration...")
             
             # Wait for the page to load completely
             time.sleep(3)
             
             # Look for the specific menu item: 利用者別予実登録
             print("🔍 Looking for the menu item: 利用者別予実登録...")
             
             # First, we need to hover over the parent menu to make the submenu visible
             # The parent menu has alt="予定・実績管理"
             parent_menu_selector = 'img[alt="予定・実績管理"]'
             
             print("⏳ Waiting for parent menu to be visible...")
             self.page.wait_for_selector(parent_menu_selector, state='visible', timeout=15000)
             
             # Hover over the parent menu to make submenu visible
             print("🖱️ Hovering over parent menu to show submenu...")
             self.page.hover(parent_menu_selector)
             time.sleep(2)  # Wait for submenu to appear
             
             # Now look for the specific submenu item
             # The link contains: 利用者別予実登録 with specific onclick handler
             link_selector = 'a[onclick*="MEM087101"]'
             
             print("⏳ Waiting for submenu item to be visible...")
             self.page.wait_for_selector(link_selector, state='visible', timeout=10000)
             
             # Get the current URL before clicking
             current_url_before = self.page.url
             print(f"📍 Current URL before navigation: {current_url_before}")
             
             # Click the specific menu item
             print("🖱️ Clicking on 利用者別予実登録 (User-specific Schedule/Performance Registration)...")
             self.page.click(link_selector)
             
             # Wait for navigation to complete
             print("⏳ Waiting for navigation to complete...")
             time.sleep(5)
             
             # Get the new URL after navigation
             current_url_after = self.page.url
             print(f"📍 Current URL after navigation: {current_url_after}")
             
             # Check if navigation was successful (URL should have changed)
             if current_url_after != current_url_before:
                 print("✅ Successfully navigated to User-specific Schedule/Performance Registration!")
                 print(f"📍 New page URL: {current_url_after}")
                 return current_url_after
             else:
                 print("⚠️ URL did not change - navigation may have failed")
                 # Check if we're still on the same page or if there was an error
                 page_title = self.page.title()
                 print(f"📄 Page title: {page_title}")
                 return current_url_after
             
         except Exception as e:
             print(f"❌ Error navigating to User-specific Schedule/Performance Registration: {e}")
             import traceback
             traceback.print_exc()
             
             # Try alternative approach - look for the link by text content
             try:
                 print("🔄 Trying alternative approach - searching by link text...")
                 
                 # First hover over parent menu
                 parent_menu_selector = 'img[alt="予定・実績管理"]'
                 self.page.hover(parent_menu_selector)
                 time.sleep(2)
                 
                 # Look for the link containing the specific text
                 link_text = "利用者別予実登録"
                 link_element = self.page.locator(f'a:has-text("{link_text}")')
                 
                 if link_element.count() > 0:
                     print(f"✅ Found link with text: {link_text}")
                     current_url_before = self.page.url
                     
                     # Click the link
                     link_element.click()
                     time.sleep(5)
                     
                     current_url_after = self.page.url
                     print(f"📍 Navigation result: {current_url_after}")
                     
                     if current_url_after != current_url_before:
                         print("✅ Alternative navigation successful!")
                         return current_url_after
                     else:
                         print("⚠️ Alternative navigation - URL unchanged")
                         return current_url_after
                 else:
                     print(f"❌ Could not find link with text: {link_text}")
                     return None
                     
             except Exception as alt_e:
                 print(f"❌ Alternative approach also failed: {alt_e}")
                 return None
     
    def select_service_offer_month(self, input_date: str) -> bool:
        """Select the service offer month based on input date (e.g., '2025年 11月 11日' -> '令和7年11月')"""
        if not self.is_logged_in:
            print("❌ Error: Not logged in. Please login first.")
            return False
        
        try:
            print(f"📅 Selecting service offer month for date: {input_date}")
            
            # Parse the input date to extract year and month
            # Expected format: "2025年 11月 11日" -> year: 2025, month: 11
            import re
            
            # Extract year and month from the input date
            date_match = re.search(r'(\d{4})年\s*(\d{1,2})月', input_date)
            if not date_match:
                print(f"❌ Could not parse date format: {input_date}")
                print("💡 Expected format: '2025年 11月 11日'")
                return False
            
            year = int(date_match.group(1))
            month = int(date_match.group(2))
            
            print(f"📊 Parsed date - Year: {year}, Month: {month}")
            
            # Convert to Reiwa era and format for dropdown value
            # Reiwa 7 = 2025, Reiwa 6 = 2024, etc.
            reiwa_year = year - 2018  # 2025 - 2018 = 7 (Reiwa 7)
            dropdown_value = f"{year}{month:02d}"  # e.g., "202511" for November 2025
            
            print(f"🗓️ Target: 令和{reiwa_year}年{month}月 (value: {dropdown_value})")
            
            # Wait for the dropdown to be available
            time.sleep(2)
            
            # Find and select the service offer month dropdown
            month_select = self.page.locator('select[id="form:serviceOfferYmSelectId"]')
            
            if month_select.count() > 0:
                try:
                    # Select the option by value
                    month_select.select_option(value=dropdown_value)
                    print(f"✅ Selected service offer month: 令和{reiwa_year}年{month}月")
                    time.sleep(3)  # Wait for AJAX to complete and page to update
                    return True
                except Exception as e:
                    print(f"⚠️ Could not select month dropdown: {e}")
                    return False
            else:
                print("❌ Could not find service offer month dropdown")
                return False
                
        except Exception as e:
            print(f"❌ Error selecting service offer month: {e}")
            import traceback
            traceback.print_exc()
            return False

    def find_and_click_user(self, user_name: str) -> Optional[str]:
         """Find a user by name in the table and click on their row"""
         if not self.is_logged_in:
             print("❌ Error: Not logged in. Please login first.")
             return None
         
         try:
             print(f"\n🔍 Searching for user: {user_name}")
             
             # Wait for the page to load completely
             time.sleep(3)
             
             # Look for the table containing user data
             print("⏳ Waiting for user table to load...")
             
             # Look for the specific table with class "tbl1"
             print("🔍 Looking for table with class 'tbl1'...")
             try:
                 # Wait for the table to be visible
                 self.page.wait_for_selector('table.tbl1 tbody tr', state='visible', timeout=15000)
                 rows = self.page.locator('table.tbl1 tbody tr')
                 row_count = rows.count()
                 print(f"📊 Found {row_count} rows in table.tbl1")
                 
                 # Skip the header row (first row)
                 if row_count > 1:
                     print(f"📋 Processing {row_count - 1} user rows (excluding header)")
                 else:
                     print("❌ No user rows found in table")
                     return None
                     
             except Exception as e:
                 print(f"⚠️ Could not find table.tbl1: {e}")
                 
                 # Try alternative selectors
                 alternative_selectors = [
                     'table tbody tr',
                     'tbody tr',
                     'tr'
                 ]
                 
                 for selector in alternative_selectors:
                     try:
                         print(f"🔍 Trying alternative selector: {selector}")
                         self.page.wait_for_selector(selector, state='visible', timeout=10000)
                         rows = self.page.locator(selector)
                         row_count = rows.count()
                         print(f"📊 Found {row_count} rows with selector: {selector}")
                         
                         if row_count > 1:
                             break
                     except Exception as alt_e:
                         print(f"⚠️ Alternative selector '{selector}' failed: {alt_e}")
                         continue
                 
                 if row_count <= 1:
                     print("❌ Could not find any user rows")
                     return None
             
             # Search through each row for the user name (skip header row)
             for i in range(1, row_count):  # Start from 1 to skip header row
                row = rows.nth(i)
                
                # Look for the user name link in the first cell (td with class "text-left")
                try:
                    # Get the first cell which contains the user name link
                    first_cell = row.locator('td.text-left:first-child')
                    user_link = first_cell.locator('a')
                    
                    if user_link.count() > 0:
                        # Get the text content of the link
                        link_text = user_link.inner_text().strip()
                        print(f"🔍 Checking row {i}: {link_text}")
                        
                        # Check if this row contains the user we're looking for (compare without spaces)
                        if user_name.replace(" ", "") in link_text.replace(" ", ""):
                             print(f"✅ Found user '{user_name}' in row {i}")
                             
                             # Get the current URL before clicking
                             current_url_before = self.page.url
                             print(f"📍 Current URL before navigation: {current_url_before}")
                             
                             # Click on the user's link
                             print(f"🖱️ Clicking on user: {user_name}")
                             user_link.click()
                             
                             # Wait for navigation to complete
                             print("⏳ Waiting for navigation to complete...")
                             time.sleep(5)
                             
                             # Get the new URL after navigation
                             current_url_after = self.page.url
                             print(f"📍 Current URL after navigation: {current_url_after}")
                             
                             # Check if navigation was successful (URL should have changed)
                             if current_url_after != current_url_before:
                                 print(f"✅ Successfully navigated to user '{user_name}' page!")
                                 print(f"📍 New page URL: {current_url_after}")
                                 return current_url_after
                             else:
                                 print("⚠️ URL did not change - navigation may have failed")
                                 # Check if we're still on the same page or if there was an error
                                 page_title = self.page.title()
                                 print(f"📄 Page title: {page_title}")
                                 return current_url_after
                     
                except Exception as e:
                    print(f"⚠️ Error processing row {i}: {e}")
                    continue
             
             # If we get here, the user was not found in table rows
             print(f"❌ User '{user_name}' not found in table rows")
             
             # Try alternative approach - search entire page for the user name
             print("🔄 Trying alternative approach - searching entire page...")
             try:
                 # Look for any link containing the user name
                 page_link = self.page.locator(f'a:has-text("{user_name}")')
                 if page_link.count() > 0:
                     print(f"✅ Found user '{user_name}' link on page")
                     
                     # Get the current URL before clicking
                     current_url_before = self.page.url
                     print(f"📍 Current URL before navigation: {current_url_before}")
                     
                     # Click on the user's link
                     print(f"🖱️ Clicking on user: {user_name}")
                     page_link.click()
                     
                     # Wait for navigation to complete
                     print("⏳ Waiting for navigation to complete...")
                     time.sleep(5)
                     
                     # Get the new URL after navigation
                     current_url_after = self.page.url
                     print(f"📍 Current URL after navigation: {current_url_after}")
                     
                     # Check if navigation was successful
                     if current_url_after != current_url_before:
                         print(f"✅ Successfully navigated to user '{user_name}' page!")
                         print(f"📍 New page URL: {current_url_after}")
                         return current_url_after
                     else:
                         print("⚠️ URL did not change - navigation may have failed")
                         return current_url_after
                 else:
                     print(f"❌ User '{user_name}' not found anywhere on the page")
             except Exception as alt_e:
                 print(f"❌ Alternative approach failed: {alt_e}")
             
             # Print available users for reference
             print("\n📋 Available users in the table:")
             for i in range(1, min(row_count, 11)):  # Show first 10 users (skip header)
                 row = rows.nth(i)
                 
                 try:
                     # Get the first cell which contains the user name link
                     first_cell = row.locator('td.text-left:first-child')
                     user_link = first_cell.locator('a')
                     
                     if user_link.count() > 0:
                         link_text = user_link.inner_text().strip()
                         if link_text:
                             print(f"  - {link_text}")
                 except:
                     continue
             
             if row_count > 11:  # 1 header + 10 users shown
                 print(f"  ... and {row_count - 11} more users")
             
             return None
             
         except Exception as e:
             print(f"❌ Error finding user '{user_name}': {e}")
             import traceback
             traceback.print_exc()
             return None
     
    def add_new_service(self, day: int, disability_support_hours: float, severe_comprehensive_support: float, start_time: int, end_time: int) -> bool:
        """Add a new service by filling out the service registration form"""
        if not self.is_logged_in:
            print("❌ Error: Not logged in. Please login first.")
            return False
        
        try:            
            # Step 1: Click the "新規追加する" (New Addition) button
            print("🖱️ Clicking '新規追加する' button...")
            
            # Look for the button by its alt text
            new_addition_button = self.page.locator('img[alt="新規追加する"]')
            
            if new_addition_button.count() > 0:
                new_addition_button.click()
                print("✅ Clicked '新規追加する' button")
                time.sleep(3)  # Wait for popup to appear
            else:
                print("❌ Could not find '新規追加する' button")
                return False
            
            # Step 3: Select "重度訪問介護" from service kind dropdown
            print("📋 Selecting '重度訪問介護' from service kind dropdown...")
            
            # Wait for the dropdown to appear (it might be loaded via AJAX)
            time.sleep(4)
            
            # Look for the service kind dropdown
            service_kind_select = self.page.locator('select[id="formPopup:serviceKind"]')
            
            if service_kind_select.count() > 0:
                # Select the option by value
                if disability_support_hours > 0:
                    service_kind_select.select_option(value="40")
                    print("✅ Selected '居宅介護' (value=40)")
                    time.sleep(2)  # Wait for AJAX to complete
                    
                    # Step 4: Select "身体介護" from service division dropdown
                    print("📋 Selecting '身体介護' from service division dropdown...")
                    
                    # Wait for service division dropdown to load
                    time.sleep(2)
                    
                    # Look for the service division dropdown
                    service_division_select = self.page.locator('select[id="formPopup:serviceDivision"]')
                    
                    if service_division_select.count() > 0:
                        # Select the option by value
                        service_division_select.select_option(value="01")
                        print("✅ Selected '身体介護' (value=01)")
                        time.sleep(2)  # Wait for AJAX to complete
                    else:
                        print("❌ Could not find service division dropdown")
                        return False
                        
                elif severe_comprehensive_support > 0:
                    service_kind_select.select_option(value="41")
                    print("✅ Selected '重度訪問介護' (value=41)")
                    time.sleep(2)  # Wait for AJAX to complete
                    # Step 4: Select "重度訪問介護（障害支援区分６）" from service division dropdown
                    print("📋 Selecting '重度訪問介護（障害支援区分６）' from service division dropdown...")
                    
                    # Wait for service division dropdown to load
                    time.sleep(2)
                    
                    # Look for the service division dropdown
                    service_division_select = self.page.locator('select[id="formPopup:serviceDivision"]')
                    
                    if service_division_select.count() > 0:
                        # Select the option by value
                        service_division_select.select_option(value="07")
                        print("✅ Selected '重度訪問介護（障害支援区分６）' (value=07)")
                        time.sleep(2)  # Wait for AJAX to complete
                    else:
                        print("❌ Could not find service division dropdown")
                        return False
            else:
                print("❌ Could not find service kind dropdown")
                return False
            
            # Step 5: Fill in start and end time using text inputs
            print("⏰ Setting start and end time using text inputs...")
            
            # Start time: start_time
            print(f"🕐 Setting start time: {start_time}...")
            start_time_input = self.page.locator('input[id="formPopup:txtStartEndTime"]')
            
            if start_time_input.count() > 0:
                start_time_input.fill(start_time)
                print(f"✅ Set start time: {start_time}")
                time.sleep(2)  # Wait for AJAX to complete
            else:
                print("⚠️ Could not find start time input field")
            
            # End time: end_time
            print(f"🕐 Setting end time: {end_time}...")
            end_time_input = self.page.locator('input[id="formPopup:txtEndTime"]')
            
            if end_time_input.count() > 0:
                end_time_input.fill(end_time)
                print(f"✅ Set end time: {end_time}")
                time.sleep(2)  # Wait for AJAX to complete
            else:
                print("⚠️ Could not find end time input field")
            
            print(f"✅ Set start time: {start_time}, end time: {end_time}")
                  
            # Step 6: Select specific date from calendar (day)
            print("📅 Selecting specific date from calendar...")
            
            # Look for the specific day in the calendar within multi_datepicker
            # Target: <a class="ui-state-default" href="#">day</a> within the calendar table
            target_date = self.page.locator(f'#multi_datepicker table.ui-datepicker-calendar a:has-text("{day}")')
            time.sleep(3)
            if target_date.count() > 0:
                try:
                    target_date.click()
                    print(f"✅ Selected {day}")
                    time.sleep(3)  # Wait for AJAX to complete
                except Exception as e:
                    print(f"⚠️ Could not click on {day}: {e}")
                    # Fallback: try to find any date with the day text in the datepicker
                    try:
                        fallback_date = self.page.locator(f'#multi_datepicker a:has-text("{day}")')
                        if fallback_date.count() > 0:
                            fallback_date.click()
                            print(f"✅ Selected date {day} (fallback method)")
                            time.sleep(1)
                        else:
                            print(f"⚠️ Could not find date {day} in calendar")
                    except Exception as e2:
                        print(f"❌ Failed to select any date: {e2}")
            else:
                print(f"⚠️ Could not find {day} in calendar")
                # Fallback: try to find today's date (highlighted)
                try:
                    today_date = self.page.locator('#multi_datepicker a.ui-state-highlight')
                    if today_date.count() > 0:
                        today_date.click()
                        print("✅ Selected today's date (fallback)")
                        time.sleep(1)
                    else:
                        print("⚠️ Could not find any selectable date in calendar")
                except Exception as e3:
                    print(f"❌ Failed to select fallback date: {e3}")            
            
            # Step 7: Click the "登録する" (Register) button
            print("🖱️ Clicking '登録する' (Register) button...")
            register_button = self.page.locator('input[id="formPopup:regist"]')
            
            if register_button.count() > 0:
                try:
                    register_button.click()
                    print("✅ Clicked '登録する' button")
                    time.sleep(3)  # Wait for registration to complete
                    
                    # Check if registration was successful
                    print("✅ Service registration completed successfully!")
                    return True
                except Exception as e:
                    print(f"⚠️ Could not click register button: {e}")
                    # Fallback: try to find by alt text
                    try:
                        fallback_button = self.page.locator('input[alt="登録する"]')
                        if fallback_button.count() > 0:
                            fallback_button.click()
                            print("✅ Clicked '登録する' button (fallback method)")
                            time.sleep(3)
                            print("✅ Service registration completed successfully!")
                            return True
                        else:
                            print("❌ Could not find register button with fallback method")
                            return False
                    except Exception as e2:
                        print(f"❌ Failed to click register button: {e2}")
                        return False
            else:
                print("❌ Could not find '登録する' button")
                return False
            
        except Exception as e:
            print(f"❌ Error adding new service: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def process_with_ocr(self, records: List[Dict[str, str]]) -> bool:
        """Process the records with OCR"""
        self.login()
        self.navigate_to_Receipt_page()
        self.navigate_to_ask_page()
        schedule_registration_url = self.navigate_to_user_schedule_registration()
        for record in records:
            date = record.get('date')
            name = record.get('name')
            disability_support_hours = record.get('disability_support_hours')
            severe_comprehensive_support = record.get('severe_comprehensive_support')
            ocr_time = record.get('time')

            # If time is missing or badly formatted, skip this record
            if not ocr_time or '~' not in ocr_time:
                print(f"⚠️ Skipping record due to invalid or missing time: {record}")
                continue

            start_time, end_time = ocr_time.split('~')
            start_time = start_time.strip().replace(':', '').zfill(4)
            end_time = end_time.strip().replace(':', '').zfill(4)
            self.select_service_offer_month(date)
            self.find_and_click_user(name)
            if start_time > end_time:
                self.add_new_service(date, disability_support_hours, severe_comprehensive_support, start_time, '2400')
                time.sleep(10)
                self.add_new_service(date+1, disability_support_hours, severe_comprehensive_support, '0000', end_time)
                time.sleep(10)
            else:
                self.add_new_service(date, disability_support_hours, severe_comprehensive_support, start_time, end_time)
                time.sleep(10)
            self.page.goto(schedule_registration_url, timeout=5000)
        return True

def main():
    """Example usage of KaipokeScraper"""
    scraper = KaipokeScraper()
    login = scraper.login()
    if login:
        nav = scraper.navigate_to_Receipt_page()
        if nav:
            ask_page_url = scraper.navigate_to_ask_page()
            if ask_page_url:
                print(f"✅ Successfully navigated to Ask page: {ask_page_url}")
                
                # Navigate to User-specific Schedule/Performance Registration
                schedule_registration_url = scraper.navigate_to_user_schedule_registration()
                if schedule_registration_url:
                    print(f"✅ Successfully navigated to User Schedule Registration: {schedule_registration_url}")
                    
                    # Select service offer month based on OCR date
                    # Example: "2025年 11月 11日" -> "令和7年11月"
                    ocr_date = "2025年 11月 11日"  # This should come from OCR results
                    month_selected = scraper.select_service_offer_month(ocr_date)
                    if month_selected:
                        print(f"✅ Successfully selected service offer month for: {ocr_date}")
                    else:
                        print(f"⚠️ Failed to select service offer month for: {ocr_date}")
                        # Continue anyway, as this might not be critical
                    
                    # Find and click on a specific user (example: 平井 里沙)
                    user_name = "行政 太郎"  # You can change this to any user name
                    user_page_url = scraper.find_and_click_user(user_name)
                    if user_page_url:
                        print(f"✅ Successfully navigated to user '{user_name}' page: {user_page_url}")
                        
                        # Add a new service for the user
                        date = "2025 年 8 月 24 日(日)"
                        # extract year, month and date as string
                        import re
                        date_str = date
                        # Match the first set of 4 digits as year, followed by "年", number as month, and number as day
                        match = re.search(r'(\d{4})\s*年\s*(\d+)\s*月\s*(\d+)\s*日', date_str)
                        if match:
                            year = match.group(1)
                            month = str(int(match.group(2)) - 1 if int(match.group(2)) > 1 else 12)
                            day = int(match.group(3))  # day can be used as int for add_new_service
                        else:
                            raise ValueError(f"Could not extract year/month/day from: {date_str}")

                        disability_support_hours = 4.5
                        severe_comprehensive_support = 0
                        ocr_time = "20:00~08:00"
                        start_time, end_time = ocr_time.split('~')
                        start_time = start_time.strip().replace(':', '').zfill(4)
                        end_time = end_time.strip().replace(':', '').zfill(4)
                        
                        if start_time > end_time:
                            service_added1 = scraper.add_new_service(day, disability_support_hours, severe_comprehensive_support, start_time, '2400')
                            time.sleep(10)
                            service_added2 = scraper.add_new_service(day+1, disability_support_hours, severe_comprehensive_support, '0000', end_time)
                        else:
                            service_added = scraper.add_new_service(day, disability_support_hours, severe_comprehensive_support, start_time, end_time)
                    else:
                        print(f"❌ Failed to find or navigate to user '{user_name}'")
                else:
                    print("❌ Failed to navigate to User Schedule Registration")
            else:
                print("❌ Failed to navigate to Ask page")

if __name__ == "__main__":
    main()
