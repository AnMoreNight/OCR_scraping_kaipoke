"""
Kaipoke Login and Data Upload Module using Playwright
"""

import os
import time
import json
import sys
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
        print("Playwrightブラウザを初期化しています...")
        
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
            
            print("✅ Playwrightブラウザの初期化に成功しました")
            
        except Exception as e:
            print(f"❌ Playwrightブラウザの初期化中にエラーが発生しました: {e}")
            raise
    
    def __del__(self):
        """Cleanup: Close browser when object is destroyed"""
        try:
            if hasattr(self, 'page') and self.page:
                self.page.close()
            if hasattr(self, 'context') and self.context:
                self.context.close()
            if hasattr(self, 'browser') and self.browser:
                self.browser.close()
            if hasattr(self, 'playwright') and self.playwright:
                self.playwright.stop()
        except Exception as e:
            # Silently handle cleanup errors to avoid issues during garbage collection
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
            print("ブラウザが閉じられました")
        except Exception as e:
            print(f"ブラウザを閉じる際にエラーが発生しました: {e}")
    
    def login(self, corporate_code: str = None, username: str = None, password: str = None) -> bool:
        """Login to Kaipoke website using Playwright"""
        print("\n=== Kaipokeにログイン中 ===")
        
        # Use provided credentials or fall back to env variables
        corporate_code = corporate_code or self.corporate_code
        username = username or self.username
        password = password or self.password
        
        if not all([corporate_code, username, password]):
            print("❌ エラー: 認証情報が不足しています。.envファイルでKAIPOKE_CORPORATE_CODE、KAIPOKE_USERNAME、KAIPOKE_PASSWORDを設定してください")
            return False
        
        try:
            # Step 1: Navigate to login page with increased timeout and less strict waiting
            print(f"📄 ログインページを開いています: {self.login_url}")
            self.page.goto(self.login_url, wait_until='load', timeout=60000)  # 60 seconds timeout, wait for 'load' instead of 'networkidle'
            
            # Wait a bit for dynamic content to load
            time.sleep(2)
            
            # Step 2: Wait for form elements and fill them in
            print("⏳ ログインフォームの読み込みを待機中...")
            
            # Wait for the corporate code input to be visible
            self.page.wait_for_selector('input[id="form:corporation_id"]', state='visible', timeout=10000)
            
            # Fill in the corporate code field (法人ID)
            print("📝 法人IDを入力中...")
            self.page.fill('input[id="form:corporation_id"]', corporate_code)
            time.sleep(0.5)
            
            # Fill in the username field (ユーザーID)
            print("📝 ユーザーIDを入力中...")
            self.page.fill('input[id="form:member_login_id"]', username)
            time.sleep(0.5)
            
            # Fill in the password field (パスワード)
            print("📝 パスワードを入力中...")
            self.page.fill('input[id="form:password"]', password)
            time.sleep(0.5)
            
            # Step 3: Click the login button
            print("🖱️ ログインボタンをクリック中...")
            
            # Wait for button to be visible
            self.page.wait_for_selector('input[id="form:logn_nochklogin"]', state='visible', timeout=5000)
            self.page.click('input[id="form:logn_nochklogin"]')
            
            # Step 4: Wait for navigation and check if login was successful
            print("⏳ ログイン完了を待機中...")
            
            # Wait for URL change or timeout
            try:
                self.page.wait_for_url(lambda url: 'login' not in url.lower(), timeout=10000)
                print("✅ URLが変更されました - ログインが成功したようです")
            except:
                print("⚠️ URLが変更されませんでした。現在のページを確認中...")
            
            time.sleep(2)
            
            # Check current URL - if redirected away from login page, login was successful
            current_url = self.page.url
            print(f"📍 現在のURL: {current_url}")
            
            # Check if login was successful (URL should change from login page)
            if 'login' not in current_url.lower() or 'COM020102' not in current_url:
                print("✅ ログインに成功しました！")
                self.is_logged_in = True
                return True
            else:
                # Check for error messages
                page_text = self.page.content()
                if 'エラー' in page_text or 'error' in page_text.lower():
                    print("❌ ログインに失敗しました: ページにエラーメッセージが検出されました")
                else:
                    print("❌ ログインに失敗しました: まだログインページにいます")
                
                return False
                
        except Exception as e:
            print(f"❌ ログインエラー: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def navigate_to_Receipt_page(self) -> bool:
        """Navigate to the Receipt page after login"""
        if not self.is_logged_in:
            print("❌ エラー: ログインしていません。まずログインしてください。")
            return False
        
        try:
            print(f"\n📄 レシートページに遷移中: {self.Receipt_page_url}")
            self.page.goto(self.Receipt_page_url, wait_until='load', timeout=60000)
            time.sleep(10)
            
            current_url = self.page.url
            print(f"✅ レシートページへの遷移に成功しました")
            print(f"📍 現在のURL: {current_url}")
            
            # Keep browser open for data upload
            print("🌐 ブラウザは開いたまま - データ入力の準備ができています...")
            return True
            
        except Exception as e:
            print(f"❌ レシートページへの遷移中にエラーが発生しました: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def navigate_to_ask_page(self, link_text: str) -> bool:
        """Navigate to the Ask page by clicking the specific navigation link"""
        if not self.is_logged_in:
            print("❌ エラー: ログインしていません。まずログインしてください。")
            return False
        
        try:
            print(f"\n📄 Askページに遷移中...")
            
            # Wait for the page to load completely
            time.sleep(3)
            
            # Click the specific link
            print(f"🖱️ {link_text}リンクをクリック中...")
            link_element = self.page.locator(f'a:has-text("{link_text}")')
            
            if link_element.count() > 0:
                link_element.click()
                
                # Wait for navigation to complete
                print("⏳ 遷移完了を待機中...")
                time.sleep(5)
                
                print("✅ Askページへの遷移に成功しました！")
                return True
            else:
                print(f"❌ {link_text}リンクが見つかりませんでした")
                return False
            
        except Exception as e:
            print(f"❌ Askページへの遷移中にエラーが発生しました: {e}")
            import traceback
            traceback.print_exc()
            
            # Try alternative approach - look for the link by text content
            try:
                print(f"🔄 代替アプローチを試行中 - {link_text}リンクを検索中...")
                
                # Look for the link containing the specific text
                link_element = self.page.locator(f'a:has-text("{link_text}")')
                
                if link_element.count() > 0:
                    print(f"✅ {link_text}リンクを発見")
                    
                    # Click the link
                    link_element.click()
                    time.sleep(5)
                    
                    print("✅ 代替遷移に成功しました！")
                    return True
                else:
                    print(f"❌ {link_text}リンクが見つかりませんでした")
                    return False
                    
            except Exception as alt_e:
                 print(f"❌ 代替アプローチも失敗しました: {alt_e}")
                 return False
     
    def navigate_to_user_schedule_registration(self) -> Optional[str]:
         """Navigate to User-specific Schedule/Performance Registration page"""
         if not self.is_logged_in:
             print("❌ エラー: ログインしていません。まずログインしてください。")
             return None
         
         try:
             print(f"\n📄 利用者別予実登録ページに遷移中...")
             
             # Wait for the page to load completely
             time.sleep(3)
             
             # Look for the specific menu item: 利用者別予実登録
             print("🔍 メニュー項目を検索中: 利用者別予実登録...")
             
             # First, we need to hover over the parent menu to make the submenu visible
             # The parent menu has alt="予定・実績管理"
             parent_menu_selector = 'img[alt="予定・実績管理"]'
             
             print("⏳ 親メニューの表示を待機中...")
             self.page.wait_for_selector(parent_menu_selector, state='visible', timeout=15000)
             
             # Hover over the parent menu to make submenu visible
             print("🖱️ サブメニューを表示するため親メニューにホバー中...")
             self.page.hover(parent_menu_selector)
             time.sleep(2)  # Wait for submenu to appear
             
             # Now look for the specific submenu item
             # The link contains: 利用者別予実登録 with specific onclick handler
             link_selector = 'a[onclick*="MEM087101"]'
             
             print("⏳ サブメニュー項目の表示を待機中...")
             self.page.wait_for_selector(link_selector, state='visible', timeout=10000)
             
             # Get the current URL before clicking
             current_url_before = self.page.url
             print(f"📍 遷移前のURL: {current_url_before}")
             
             # Click the specific menu item
             print("🖱️ 利用者別予実登録をクリック中...")
             self.page.click(link_selector)
             
             # Wait for navigation to complete
             print("⏳ 遷移完了を待機中...")
             time.sleep(5)
             
             # Get the new URL after navigation
             current_url_after = self.page.url
             print(f"📍 遷移後のURL: {current_url_after}")
             
             # Check if navigation was successful (URL should have changed)
             if current_url_after != current_url_before:
                 print("✅ 利用者別予実登録ページへの遷移に成功しました！")
                 print(f"📍 新しいページURL: {current_url_after}")
                 return current_url_after
             else:
                 print("⚠️ URLが変更されませんでした - 遷移に失敗した可能性があります")
                 # Check if we're still on the same page or if there was an error
                 page_title = self.page.title()
                 print(f"📄 ページタイトル: {page_title}")
                 return current_url_after
             
         except Exception as e:
             print(f"❌ 利用者別予実登録ページへの遷移中にエラーが発生しました: {e}")
             import traceback
             traceback.print_exc()
             
             # Try alternative approach - look for the link by text content
             try:
                 print("🔄 代替アプローチを試行中 - リンクテキストで検索...")
                 
                 # First hover over parent menu
                 parent_menu_selector = 'img[alt="予定・実績管理"]'
                 self.page.hover(parent_menu_selector)
                 time.sleep(2)
                 
                 # Look for the link containing the specific text
                 link_text = "利用者別予実登録"
                 link_element = self.page.locator(f'a:has-text("{link_text}")')
                 
                 if link_element.count() > 0:
                     print(f"✅ テキストでリンクを発見: {link_text}")
                     current_url_before = self.page.url
                     
                     # Click the link
                     link_element.click()
                     time.sleep(5)
                     
                     current_url_after = self.page.url
                     print(f"📍 遷移結果: {current_url_after}")
                     
                     if current_url_after != current_url_before:
                         print("✅ 代替遷移に成功しました！")
                         return current_url_after
                     else:
                         print("⚠️ 代替遷移 - URLが変更されませんでした")
                         return current_url_after
                 else:
                     print(f"❌ テキストでリンクが見つかりませんでした: {link_text}")
                     return None
                     
             except Exception as alt_e:
                 print(f"❌ 代替アプローチも失敗しました: {alt_e}")
                 return None
     
    def select_service_offer_month(self, input_date: str) -> bool:
        """Select the service offer month based on input date (e.g., '2025年 11月 11日' -> '令和7年11月')"""
        if not self.is_logged_in:
            print("❌ エラー: ログインしていません。まずログインしてください。")
            return False
        
        try:
            print(f"📅 サービス提供月を選択中: {input_date}")
            
            # Parse the input date to extract year and month
            # Expected format: "2025年 11月 11日" -> year: 2025, month: 11
            import re
            
            # Extract year and month from the input date
            date_match = re.search(r'(\d{4})\s*年\s*(\d{1,2})\s*月', input_date)
            if not date_match:
                print(f"❌ 日付形式を解析できませんでした: {input_date}")
                print("💡 期待される形式: '2025年 11月 11日'")
                return False
            
            year = int(date_match.group(1))
            month = int(date_match.group(2))
            
            print(f"📊 解析された日付 - 年: {year}, 月: {month}")
            
            # Convert to Reiwa era and format for dropdown value
            # Reiwa 7 = 2025, Reiwa 6 = 2024, etc.
            reiwa_year = year - 2018  # 2025 - 2018 = 7 (Reiwa 7)
            dropdown_value = f"{year}{month:02d}"  # e.g., "202511" for November 2025
            
            print(f"🗓️ 対象: 令和{reiwa_year}年{month}月 (値: {dropdown_value})")
            
            # Wait for the dropdown to be available
            time.sleep(2)
            
            # Find and select the service offer month dropdown
            month_select = self.page.locator('select[id="form:serviceOfferYmSelectId"]')
            
            if month_select.count() > 0:
                try:
                    # Select the option by value
                    month_select.select_option(value=dropdown_value)
                    print(f"✅ サービス提供月を選択しました: 令和{reiwa_year}年{month}月")
                    time.sleep(3)  # Wait for AJAX to complete and page to update
                    return True
                except Exception as e:
                    print(f"⚠️ 月ドロップダウンを選択できませんでした: {e}")
                    return False
            else:
                print("❌ サービス提供月ドロップダウンが見つかりませんでした")
                return False
                
        except Exception as e:
            print(f"❌ サービス提供月の選択中にエラーが発生しました: {e}")
            import traceback
            traceback.print_exc()
            return False

    def find_and_click_user(self, user_name: str) -> Optional[str]:
         """Find a user by name in the table and click on their row"""
         if not self.is_logged_in:
             print("❌ エラー: ログインしていません。まずログインしてください。")
             return None
         
         try:
             print(f"\n🔍 利用者を検索中: {user_name}")
             
             # Wait for the page to load completely
             time.sleep(3)
             
             # Look for the table containing user data
             print("⏳ 利用者テーブルの読み込みを待機中...")
             
             # Look for the specific table with class "tbl1"
             print("🔍 'tbl1'クラスのテーブルを検索中...")
             try:
                 # Wait for the table to be visible
                 self.page.wait_for_selector('table.tbl1 tbody tr', state='visible', timeout=15000)
                 rows = self.page.locator('table.tbl1 tbody tr')
                 row_count = rows.count()
                 print(f"📊 table.tbl1で{row_count}行を発見しました")
                 
                 # Skip the header row (first row)
                 if row_count > 1:
                     print(f"📋 {row_count - 1}行の利用者データを処理中（ヘッダー除く）")
                 else:
                     print("❌ テーブルに利用者行が見つかりませんでした")
                     return None
                     
             except Exception as e:
                 print(f"⚠️ table.tbl1が見つかりませんでした: {e}")
                 
                 # Try alternative selectors
                 alternative_selectors = [
                     'table tbody tr',
                     'tbody tr',
                     'tr'
                 ]
                 
                 for selector in alternative_selectors:
                     try:
                         print(f"🔍 代替セレクターを試行中: {selector}")
                         self.page.wait_for_selector(selector, state='visible', timeout=10000)
                         rows = self.page.locator(selector)
                         row_count = rows.count()
                         print(f"📊 セレクターで{row_count}行を発見: {selector}")
                         
                         if row_count > 1:
                             break
                     except Exception as alt_e:
                         print(f"⚠️ 代替セレクター '{selector}' が失敗しました: {alt_e}")
                         continue
                 
                 if row_count <= 1:
                     print("❌ 利用者行が見つかりませんでした")
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
                        print(f"🔍 行{i}をチェック中: {link_text}")
                        
                        # Check if this row contains the user we're looking for (compare without spaces)
                        if user_name.replace(" ", "") in link_text.replace(" ", ""):
                             print(f"✅ 行{i}で利用者 '{user_name}' を発見しました")
                             
                             # Get the current URL before clicking
                             current_url_before = self.page.url
                             print(f"📍 遷移前のURL: {current_url_before}")
                             
                             # Click on the user's link
                             print(f"🖱️ 利用者をクリック中: {user_name}")
                             user_link.click()
                             
                             # Wait for navigation to complete
                             print("⏳ 遷移完了を待機中...")
                             time.sleep(5)
                             
                             # Get the new URL after navigation
                             current_url_after = self.page.url
                             print(f"📍 遷移後のURL: {current_url_after}")
                             
                             # Check if navigation was successful (URL should have changed)
                             if current_url_after != current_url_before:
                                 print(f"✅ 利用者 '{user_name}' のページへの遷移に成功しました！")
                                 print(f"📍 新しいページURL: {current_url_after}")
                                 return current_url_after
                             else:
                                 print("⚠️ URLが変更されませんでした - 遷移に失敗した可能性があります")
                                 # Check if we're still on the same page or if there was an error
                                 page_title = self.page.title()
                                 print(f"📄 ページタイトル: {page_title}")
                                 return current_url_after
                     
                except Exception as e:
                    print(f"⚠️ 行{i}の処理中にエラーが発生しました: {e}")
                    continue
             
             # If we get here, the user was not found in table rows
             print(f"❌ テーブル行で利用者 '{user_name}' が見つかりませんでした")
             
             # Try alternative approach - search entire page for the user name
             print("🔄 代替アプローチを試行中 - ページ全体を検索...")
             try:
                 # Look for any link containing the user name
                 page_link = self.page.locator(f'a:has-text("{user_name}")')
                 if page_link.count() > 0:
                     print(f"✅ ページで利用者 '{user_name}' のリンクを発見しました")
                     
                     # Get the current URL before clicking
                     current_url_before = self.page.url
                     print(f"📍 遷移前のURL: {current_url_before}")
                     
                     # Click on the user's link
                     print(f"🖱️ 利用者をクリック中: {user_name}")
                     page_link.click()
                     
                     # Wait for navigation to complete
                     print("⏳ 遷移完了を待機中...")
                     time.sleep(5)
                     
                     # Get the new URL after navigation
                     current_url_after = self.page.url
                     print(f"📍 遷移後のURL: {current_url_after}")
                     
                     # Check if navigation was successful
                     if current_url_after != current_url_before:
                         print(f"✅ 利用者 '{user_name}' のページへの遷移に成功しました！")
                         print(f"📍 新しいページURL: {current_url_after}")
                         return current_url_after
                     else:
                         print("⚠️ URLが変更されませんでした - 遷移に失敗した可能性があります")
                         return current_url_after
                 else:
                     print(f"❌ ページのどこにも利用者 '{user_name}' が見つかりませんでした")
             except Exception as alt_e:
                 print(f"❌ 代替アプローチが失敗しました: {alt_e}")
             
             # Print available users for reference
             print("\n📋 テーブル内の利用可能な利用者:")
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
                 print(f"  ... さらに{row_count - 11}人の利用者")
             
             return None
             
         except Exception as e:
             print(f"❌ 利用者 '{user_name}' の検索中にエラーが発生しました: {e}")
             import traceback
             traceback.print_exc()
             return None
     
    def add_new_service(self, day: int, disability_support_hours: float, severe_comprehensive_support: float, start_time: int, end_time: int, severe_visitation: float, housework: float) -> bool:
        """Add a new service by filling out the service registration form"""
        if not self.is_logged_in:
            print("❌ エラー: ログインしていません。まずログインしてください。")
            return False
        
        try:      
            # Step 1: Click the "新規追加する" (New Addition) button
            print("🖱️ '新規追加する'ボタンをクリック中...")
            
            # Look for the button by its alt text
            new_addition_button = self.page.locator('img[alt="新規追加する"]')
            
            if new_addition_button.count() > 0:
                new_addition_button.click()
                print("✅ '新規追加する'ボタンをクリックしました")
                time.sleep(3)  # Wait for popup to appear
            else:
                print("❌ '新規追加する'ボタンが見つかりませんでした")
                return False
            
            # Step 2: Select "重度訪問介護" from service kind dropdown
            print("📋 サービス種別ドロップダウンを処理中...")
            
            # Wait for the dropdown to appear (it might be loaded via AJAX)
            time.sleep(4)
            
            # Look for the service kind dropdown
            service_kind_select = self.page.locator('select[id="formPopup:serviceKind"]')
            
            if service_kind_select.count() > 0:
                # Select the option by value
                if disability_support_hours > 0:
                    service_kind_select.select_option(value="40")
                    print("✅ '居宅介護'を選択しました (値=40)")
                    time.sleep(2)  # Wait for AJAX to complete
                    
                    # Step 3: Select "身体介護" from service division dropdown
                    print("📋 サービス区分ドロップダウンから'身体介護'を選択中...")
                    
                    # Wait for service division dropdown to load
                    time.sleep(2)
                    
                    # Look for the service division dropdown
                    service_division_select = self.page.locator('select[id="formPopup:serviceDivision"]')
                    
                    if service_division_select.count() > 0:
                        # Select the option by value
                        service_division_select.select_option(value="01")
                        print("✅ '身体介護'を選択しました (値=01)")
                        time.sleep(2)  # Wait for AJAX to complete
                    else:
                        print("❌ サービス区分ドロップダウンが見つかりませんでした")
                        return False
                        
                elif severe_visitation > 0:
                    service_kind_select.select_option(value="41")
                    print("✅ '重度訪問介護'を選択しました (値=41)")
                    time.sleep(2)  # Wait for AJAX to complete
                    # Step 3: Select "重度訪問介護（障害支援区分６）" from service division dropdown
                    print("📋 サービス区分ドロップダウンから'重度訪問介護（障害支援区分６）'を選択中...")
                    
                    # Wait for service division dropdown to load
                    time.sleep(2)
                    
                    # Look for the service division dropdown
                    service_division_select = self.page.locator('select[id="formPopup:serviceDivision"]')
                    
                    if service_division_select.count() > 0:
                        # Select the option by value
                        service_division_select.select_option(value="07")
                        print("✅ '重度訪問介護（障害支援区分６）'を選択しました (値=07)")
                        time.sleep(2)  # Wait for AJAX to complete
                    else:
                        print("❌ サービス区分ドロップダウンが見つかりませんでした")
                        return False
            else:
                print("❌ サービス種別ドロップダウンが見つかりませんでした")
                return False
            
            # Step 4: Fill in start and end time using text inputs
            print("⏰ テキスト入力で開始時刻と終了時刻を設定中...")
            
            # Start time: start_time
            print(f"🕐 開始時刻を設定中: {start_time}...")
            start_time_input = self.page.locator('input[id="formPopup:txtStartEndTime"]')
            
            if start_time_input.count() > 0:
                start_time_input.fill(start_time)
                print(f"✅ 開始時刻を設定しました: {start_time}")
                time.sleep(2)  # Wait for AJAX to complete
            else:
                print("⚠️ 開始時刻入力フィールドが見つかりませんでした")
            
            # End time: end_time
            print(f"🕐 終了時刻を設定中: {end_time}...")
            end_time_input = self.page.locator('input[id="formPopup:txtEndTime"]')
            
            if end_time_input.count() > 0:
                end_time_input.fill(end_time)
                print(f"✅ 終了時刻を設定しました: {end_time}")
                time.sleep(2)  # Wait for AJAX to complete
            else:
                print("⚠️ 終了時刻入力フィールドが見つかりませんでした")
            
            print(f"✅ 開始時刻: {start_time}, 終了時刻: {end_time}を設定しました")

            # step 5: select  実績
            try:
                print("✅ '予定・実績'のラジオボタンを'実績'に設定中...")
                # Prefer checking the radio input directly
                achievement_radio = self.page.locator('input[id="formPopup:planAchievementRadio:1"][type="radio"][value="02"]')
                if achievement_radio.count() > 0:
                    achievement_radio.check()
                    print("✅ '実績'ラジオボタンを選択しました")
                    time.sleep(1)
                else:
                    # Fallback: click the label associated with the radio
                    achievement_label = self.page.locator('label[for="formPopup:planAchievementRadio:1"]')
                    if achievement_label.count() > 0:
                        achievement_label.click()
                        print("✅ '実績'ラベルをクリックして選択しました")
                        time.sleep(1)
                    else:
                        print("⚠️ '実績'のラジオボタンが見つかりませんでした")
            except Exception as e:
                print(f"⚠️ '実績'ラジオボタンの設定に失敗しました: {e}")
                # Continue, this might not be critical depending on flow

            
            # Step 6: Select specific date from calendar (day)
            print("📅 カレンダーから特定の日付を選択中...")
            
            # Wait for calendar to be visible
            time.sleep(3)
            
            # Look for the specific day in the calendar using the correct structure
            # Target: <a class="ui-state-default" href="#">day</a> within the calendar table
            # Try multiple selectors to find the exact date (not partial matches)
            selectors = [
                f'table.ui-datepicker-calendar a.ui-state-default:text-is("{day}")',
                f'.ui-datepicker-calendar a.ui-state-default:text-is("{day}")',
                f'a.ui-state-default:text-is("{day}")',
                f'td[data-handler="selectDay"] a.ui-state-default:text-is("{day}")'
            ]
            
            target_date = None
            for selector in selectors:
                try:
                    target_date = self.page.locator(selector)
                    if target_date.count() > 0:
                        print(f"🔍 セレクターで日付を発見: {selector}")
                        break
                except:
                    continue
            
            if target_date and target_date.count() > 0:
                try:
                    target_date.click()
                    print(f"✅ {day}を選択しました")
                    time.sleep(3)  # Wait for AJAX to complete
                except Exception as e:
                    print(f"⚠️ {day}をクリックできませんでした: {e}")
                    # Fallback: try to find any date with the exact day text in the datepicker
                    try:
                        fallback_date = self.page.locator(f'a.ui-state-default:text-is("{day}")')
                        if fallback_date.count() > 0:
                            fallback_date.click()
                            print(f"✅ 日付{day}を選択しました（代替方法）")
                            time.sleep(1)
                        else:
                            print(f"⚠️ カレンダーで日付{day}が見つかりませんでした")
                    except Exception as e2:
                        print(f"❌ 日付の選択に失敗しました: {e2}")
            else:
                print(f"⚠️ カレンダーで{day}が見つかりませんでした")
                # Fallback: try to find today's date (highlighted)
                try:
                    today_date = self.page.locator('a.ui-state-highlight')
                    if today_date.count() > 0:
                        today_date.click()
                        print("✅ 今日の日付を選択しました（代替方法）")
                        time.sleep(1)
                    else:
                        print("⚠️ カレンダーで選択可能な日付が見つかりませんでした")
                except Exception as e3:
                    print(f"❌ 代替日付の選択に失敗しました: {e3}")            
            
            # Step 7: Click the "登録する" (Register) button
            print("🖱️ '登録する'ボタンをクリック中...")
            register_button = self.page.locator('input[id="formPopup:regist"]')
            
            if register_button.count() > 0:
                try:
                    register_button.click()
                    print("✅ '登録する'ボタンをクリックしました")
                    time.sleep(3)  # Wait for registration to complete
                    
                    # Check for validation errors
                    print("🔍 バリデーションエラーをチェック中...")
                    error_container = self.page.locator('div.txt-attend ul.error_message')
                    
                    if error_container.count() > 0:
                        # Get all error messages
                        error_messages = []
                        error_items = self.page.locator('div.txt-attend ul.error_message li')
                        for i in range(error_items.count()):
                            error_text = error_items.nth(i).inner_text().strip()
                            error_messages.append(error_text)
                        
                        if error_messages:
                            print("❌ バリデーションエラーが検出されました:")
                            for error in error_messages:
                                print(f"   - {error}")

                            # Close the modal so we can continue processing other records
                            close_button = self.page.locator('a#closeModal.simplemodal-close')
                            if close_button.count() > 0:
                                try:
                                    close_button.click()
                                    print("✅ エラーモーダルを閉じました")
                                    time.sleep(1)
                                except Exception as close_err:
                                    print(f"⚠️ エラーモーダルを閉じる際に問題が発生しました: {close_err}")
                            else:
                                print("⚠️ エラーモーダルの閉じるボタンが見つかりませんでした")

                        else : 
                             # Check if registration was successful
                            print("✅ サービス登録が正常に完了しました！")
                    return True
                except Exception as e:
                    print(f"⚠️ 登録ボタンをクリックできませんでした: {e}")
                    # Fallback: try to find by alt text
                    try:
                        fallback_button = self.page.locator('input[alt="登録する"]')
                        if fallback_button.count() > 0:
                            fallback_button.click()
                            print("✅ '登録する'ボタンをクリックしました（代替方法）")
                            time.sleep(3)
                            
                            # Check for validation errors in fallback case too
                            print("🔍 バリデーションエラーをチェック中（代替方法）...")
                            error_container = self.page.locator('div.txt-attend ul.error_message')
                            
                            if error_container.count() > 0:
                                # Get all error messages
                                error_messages = []
                                error_items = self.page.locator('div.txt-attend ul.error_message li')
                                for i in range(error_items.count()):
                                    error_text = error_items.nth(i).inner_text().strip()
                                    error_messages.append(error_text)
                                
                                if error_messages:
                                    print("❌ バリデーションエラーが検出されました（代替方法）:")
                                    for error in error_messages:
                                        print(f"   - {error}")

                                    close_button = self.page.locator('a#closeModal.simplemodal-close')
                                    if close_button.count() > 0:
                                        try:
                                            close_button.click()
                                            print("✅ エラーモーダルを閉じました")
                                            time.sleep(1)
                                        except Exception as close_err:
                                            print(f"⚠️ エラーモーダルを閉じる際に問題が発生しました: {close_err}")
                                    else:
                                        print("⚠️ エラーモーダルの閉じるボタンが見つかりませんでした")
                            else:
                                print("✅ サービス登録が正常に完了しました！")
                                return True
                        else:
                            print("❌ 代替方法で登録ボタンが見つかりませんでした")
                    except Exception as e2:
                        print(f"❌ 登録ボタンのクリックに失敗しました: {e2}")
            else:
                print("❌ '登録する'ボタンが見つかりませんでした")
                return False
            
        except Exception as e:
            print(f"❌ 新しいサービスの追加中にエラーが発生しました: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def process_with_ocr(self, records: List[Dict[str, str]]) -> bool:
        """Process the records with OCR - optimized workflow"""
        if not records:
            print("⚠️ No records to process")
            return False
        
        print(f"🚀 Kaipokeで{len(records)}件のレコードを処理中...")
        
        try:
            # Initialize browser session
            if not self.login():
                print("❌ Kaipokeへのログインに失敗しました")
                return False
                                   
            # Process each record
            success_count = 0
            for i, record in enumerate(records, 1):
                print(f"\n📋 レコード {i}/{len(records)} を処理中")
                try:
                    if self._process_single_record(record):
                        success_count += 1
                        print(f"✅ レコード {i} の処理に成功しました")
                    else:
                        print(f"❌ レコード {i} の処理に失敗しました")
                except Exception as e:
                    print(f"❌ レコード {i} の処理中にエラーが発生しました: {e}")
                    continue
            
            print(f"\n📊 処理サマリー: {success_count}/{len(records)} 件のレコードが成功しました")
            print("🔒 OCR処理後にブラウザを閉じています...") 
            return True
            
        except Exception as e:
            print(f"❌ process_with_ocr内でエラーが発生しました: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # Ensure browser is closed after all processes or errors
            print("🔒 OCR処理後にブラウザを閉じています...")
            self.close_browser()
            print("✅ Browser closed successfully")
    
    def _process_single_record(self, record: Dict[str, str]) -> bool:
        """Process a single OCR record"""
        try:
            
            # Extract and validate data
            date = record.get('date')
            name = record.get('name')
            facility_name = record.get('facility_name')
            disability_support_hours = record.get('disability_support_hours', 0)
            severe_comprehensive_support = record.get('severe_comprehensive_support', 0)
            ocr_time = record.get('time')
            severe_visitation = record.get('severe_visitation', 0)
            housework = record.get('housework', 0)

            facility_link_map = {
                "メディヴィレッジ群馬 HOME": '障害者総合支援(訪問系)/1010202867',
                "メディケア大宮桜木": '障害者総合支援(訪問系)/1116513696',
            }
            link_text = facility_link_map.get(facility_name)

            # Navigate to required pages
            if not self.navigate_to_Receipt_page():
                print("❌ レシートページへの遷移に失敗しました")
                return False
            
            if not self.navigate_to_ask_page(link_text):
                print("❌ Askページへの遷移に失敗しました")
                return False
            
            schedule_registration_url = self.navigate_to_user_schedule_registration()
            if not schedule_registration_url:
                print("❌ 利用者別予実登録ページへの遷移に失敗しました")
                return False

            # Validate required fields
            if not all([date, name, ocr_time]):
                print(f"⚠️ 必須フィールドが不足しているためレコードをスキップします: {record}")
                return False

            # Validate time format
            if '~' not in ocr_time:
                print(f"⚠️ 無効な時刻形式のためレコードをスキップします: {ocr_time}")
                return False

            # Parse time
            start_time, end_time = ocr_time.split('~')
            start_time = start_time.strip().replace(':', '').zfill(4)
            end_time = end_time.strip().replace(':', '').zfill(4)
            
            # Select service offer month
            if not self.select_service_offer_month(date):
                print(f"⚠️ {date}のサービス提供月の選択に失敗しました")
            
            # Find and click user
            if not self.find_and_click_user(name):
                print(f"❌ 利用者の検索に失敗しました: {name}")
                return False
            # Extract day as integer from date string like "2025年10月6日"
            import re
            date_no_spaces = str(date).replace(" ", "")
            match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_no_spaces)
            if match:
                year = int(match.group(1))
                month = int(match.group(2))
                day = int(match.group(3))
            else:
                print(f"⚠️ 日付形式が無効です: {date}")
                return False
            # Add service(s)
            if start_time > end_time:
                # Overnight service - split into two
                print("🌙 深夜サービスを処理中...")
                
                success1 = self.add_new_service(day, disability_support_hours, severe_comprehensive_support, start_time, '2400', severe_visitation, housework)
                if success1:
                    time.sleep(5)
                    success2 = self.add_new_service(day+1, disability_support_hours, severe_comprehensive_support, '0000', end_time, severe_visitation, housework)
                    return success1 and success2
                return False
            else:
                # Single service
                return self.add_new_service(day, disability_support_hours, severe_comprehensive_support, start_time, end_time, severe_visitation, housework)
                
        except Exception as e:
            print(f"❌ レコード処理中に重大なエラーが発生しました: {e}")
            import traceback
            traceback.print_exc()
            # For critical errors, we don't close browser here as it's handled by the calling method
            return False

def main():
    """Example usage of KaipokeScraper"""
    scraper = None
    try:
        scraper = KaipokeScraper()
        login = scraper.login()
        if login:
            nav = scraper.navigate_to_Receipt_page()
            if nav:
                # Example link text - should match one of the facility links
                link_text = '障害者総合支援(訪問系)/1116513696'
                ask_page_success = scraper.navigate_to_ask_page(link_text)
                if ask_page_success:
                    print(f"✅ Askページへの遷移に成功しました")
                    
                    # Navigate to User-specific Schedule/Performance Registration
                    schedule_registration_url = scraper.navigate_to_user_schedule_registration()
                    if schedule_registration_url:
                        print(f"✅ 利用者別予実登録ページへの遷移に成功しました: {schedule_registration_url}")
                        
                        # Select service offer month based on OCR date
                        # Example: "2025年 11月 11日" -> "令和7年11月"
                        ocr_date = "2025年 11月 11日"  # This should come from OCR results
                        month_selected = scraper.select_service_offer_month(ocr_date)
                        if month_selected:
                            print(f"✅ サービス提供月の選択に成功しました: {ocr_date}")
                        else:
                            print(f"⚠️ サービス提供月の選択に失敗しました: {ocr_date}")
                            # Continue anyway, as this might not be critical
                        
                        # Find and click on a specific user (example: 平井 里沙)
                        user_name = "行政 太郎"  # You can change this to any user name
                        user_page_url = scraper.find_and_click_user(user_name)
                        if user_page_url:
                            print(f"✅ 利用者 '{user_name}' のページへの遷移に成功しました: {user_page_url}")
                            
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
                            print(f"❌ 利用者 '{user_name}' の検索または遷移に失敗しました")
                    else:
                        print("❌ 利用者別予実登録ページへの遷移に失敗しました")
                else:
                    print("❌ Askページへの遷移に失敗しました")
    except Exception as e:
        print(f"❌ メインプロセスでエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Ensure browser is closed after all processes or errors
        if scraper:
            print("🔒 ブラウザを閉じています...")
            scraper.close_browser()
            print("✅ ブラウザが正常に閉じられました")

if __name__ == "__main__":
    main()
