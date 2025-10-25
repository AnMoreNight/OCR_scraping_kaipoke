"""
Email Listener Module - Monitors email inbox for new messages
"""

import os
import time
import sys
import logging
from typing import List, Dict, Optional
from dotenv import load_dotenv
from imapclient import IMAPClient
import pyzmail
import json
from OCR import ImageTextExtractor
from kaipoke import KaipokeScraper
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def log_print(message):
    """Print and log message for better visibility on Render"""
    print(message, flush=True)
    # logger.info(message)

# Load environment variables
load_dotenv()


class EmailListener:
    """Monitor email inbox and trigger actions on new emails"""
    
    def __init__(self):
        """Initialize email listener"""
        # Get email credentials from .env
        self.email_server = os.getenv('EMAIL_SERVER', 'imap.gmail.com')
        self.email_address = os.getenv('EMAIL_ADDRESS')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        
        # Validate required credentials
        if not all([self.email_address, self.email_password]):
            raise ValueError("EMAIL_ADDRESS and EMAIL_PASSWORD must be set in environment variables")
        
        # Connection
        self.client = None
        self.is_connected = False
        self.max_retries = 3
        self.retry_delay = 5

        # Initialize OCR extractor
        self.extractor = ImageTextExtractor()
        
        # Initialize Kaipoke scraper
        self.kaipoke_scraper = None

        # Load last processed email ID
        self.lastid = self._load_last_id()
        
        # Stop flag for graceful shutdown
        self._stop_requested = False
    
    def _load_last_id(self) -> int:
        """Load last processed email ID from file"""
        try:
            with open("seen.json", "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            return 0
    
    def _save_last_id(self, last_id: int):
        """Save last processed email ID to file"""
        try:
            with open("seen.json", "w") as f:
                json.dump(last_id, f)
        except Exception as e:
            log_print(f"⚠️ Failed to save last ID: {e}")
    
    def stop(self):
        """Request the email listener to stop"""
        self._stop_requested = True
        log_print("🛑 メールリスナーの停止が要求されました")
    
    def connect(self) -> bool:
        """Connect to email server with improved error handling"""
        if not all([self.email_address, self.email_password]):
            log_print("❌ エラー: .envファイルにEMAIL_ADDRESSとEMAIL_PASSWORDを設定してください")
            return False
        
        try:
            log_print(f"📧 メールサーバーに接続中: {self.email_server}")
            log_print(f"📧 メールアカウント: {self.email_address}")
            
            # Connect to IMAP server with timeout settings
            self.client = IMAPClient(
                self.email_server, 
                ssl=True,
                timeout=30,  # 30 second timeout
                use_uid=True  # Use UID for better reliability
            )
            
            # Login
            self.client.login(self.email_address, self.email_password)
                        
            log_print("✅ メールサーバーに正常に接続しました")
            self.is_connected = True
            
            # Initialize for processing all emails
            self.seen_uids = set()  # Not tracking seen UIDs since we want all emails
            # log_print(f"📧 Ready to process all emails in folder")
            
            return True
            
        except Exception as e:
            log_print(f"❌ メールサーバーへの接続エラー: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Disconnect from email server"""
        if self.client:
            try:
                self.client.logout()
                log_print("📧 メールサーバーから切断しました")
            except:
                pass
        self.is_connected = False
    
    def check_connection_health(self) -> bool:
        """Check if the IMAP connection is still healthy"""
        if not self.is_connected or not self.client:
            return False
        
        try:
            # Try a simple NOOP command to check connection
            self.client.noop()
            return True
        except Exception as e:
            log_print(f"⚠️ Connection health check failed: {e}")
            self.is_connected = False
            return False
    
    def check_new_emails(self) -> List[Dict]:
        """Check for new emails with connection recovery"""
        # Check connection health first
        if not self.check_connection_health():
            log_print("⚠️ Connection unhealthy, attempting to reconnect...")
            if not self.connect():
                log_print("❌ Failed to reconnect to email server")
                return []
        
        try:
            # Search for all emails in INBOX
            select_info = self.client.select_folder("INBOX")
            
            all_uids = self.client.search()  # [u'UNSEEN']
            new_uids = [uid for uid in all_uids if uid > self.lastid]
            # INSERT_YOUR_CODE
            if(new_uids):
                json.dump(max(new_uids), open("seen.json", "w"))
                # print(f"save max uid : {max(new_uids)} to seen.json")
                self.lastid = max(new_uids)
            else:
                return []
            
            print(f"\n📬 Found {len(new_uids)} new email(s)!")
            
            # Fetch new emails
            new_emails = []
            for uid in new_uids:
                try:
                    email_data = self.get_email_details(uid)
                    if email_data:
                        new_emails.append(email_data)
                    self.seen_uids.add(uid)
                except Exception as e:
                    log_print(f"⚠️ Error processing email UID {uid}: {e}")
            
            return new_emails
            
        except Exception as e:
            log_print(f"❌ Error checking emails: {e}")
            log_print("🔄 Attempting to reconnect to email server...")
            
            # Try to reconnect
            try:
                self.disconnect()
                time.sleep(5)  # Wait 5 seconds before reconnecting
                if self.connect():
                    log_print("✅ Successfully reconnected to email server")
                    return []  # Return empty for this check, will try again next time
                else:
                    log_print("❌ Failed to reconnect to email server")
                    return []
            except Exception as reconnect_error:
                log_print(f"❌ Reconnection failed: {reconnect_error}")
                return []
    
    def get_email_details(self, uid: int) -> Optional[Dict]:
        """Get details of a specific email"""
        try:
            # Fetch the email
            raw_messages = self.client.fetch([uid], ['BODY[]', 'FLAGS'])
            raw_message = raw_messages[uid][b'BODY[]']
            
            # Parse the email
            message = pyzmail.PyzMessage.factory(raw_message)
            
            # Check for image attachments
            image_attachments = []
            # log_print(f"📧 Email has {len(message.mailparts)} parts")
            
            for i, part in enumerate(message.mailparts):
                # log_print(f"📎 Part {i}: {type(part)}")
                # log_print(f"   - Has filename: {hasattr(part, 'filename') and part.filename}")
                # log_print(f"   - Content type: {getattr(part, 'content_type', 'Unknown')}")
                # log_print(f"   - Content disposition: {getattr(part, 'content_disposition', 'Unknown')}")
                
                # Check if it's an attachment by looking at content-disposition
                is_attachment = False
                if hasattr(part, 'content_disposition'):
                    is_attachment = part.content_disposition and 'attachment' in part.content_disposition.lower()
                elif hasattr(part, 'get_content_disposition'):
                    disposition = part.get_content_disposition()
                    is_attachment = disposition and 'attachment' in disposition.lower()
                
                # Also check if it has a filename (common for attachments)
                has_filename = hasattr(part, 'filename') and part.filename
                
                if (is_attachment or has_filename) and part.filename:
                    # log_print(f"   - Found attachment: {part.filename}")
                    # Check if it's an image file
                    filename_lower = part.filename.lower()
                    if any(filename_lower.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']):
                        log_print(f"Image attachment found: {part.filename}")
                        image_attachments.append({
                            'filename': part.filename,
                            'content': part.get_payload(),
                            'size': len(part.get_payload())
                        })
            
            # Extract details
            email_data = {
                'uid': uid,
                'from': message.get_address('from'),
                'to': message.get_address('to'),
                'subject': message.get_subject(),
                'date': message.get_decoded_header('date'),
                'body_text': message.text_part.get_payload().decode(message.text_part.charset) if message.text_part else '',
                'body_html': message.html_part.get_payload().decode(message.html_part.charset) if message.html_part else '',
                'has_attachments': len(message.mailparts) > 1,
                'image_attachments': image_attachments,
                'has_images': len(image_attachments) > 0
            }
            # print("email_data:", email_data)
            return email_data
            
        except Exception as e:
            log_print(f"Error getting email details: {e}")
            return None
    
    def listen(self, check_interval: int = 60):
        """
        Listen for new emails and trigger callback function
        
        Args:
            callback: Function to call when new email arrives (receives email_data dict)
            check_interval: Seconds between email checks (default: 60)
        """
        # log_print(f"\n🎧 Starting email listener...")
        # log_print(f"📧 Monitoring: {self.email_address}")
        # log_print(f"📁 Folder: INBOX")
        # log_print(f"⏱️ Check interval: {check_interval} seconds")
        # log_print(f"\n⚡ Processing all emails... (Press Ctrl+C to stop)\n")
        
        try:
            while not self._stop_requested:
                # log_print(f"📧 Checking for all emails...")
                
                # Check for all emails
                new_emails = self.check_new_emails()
                
                if new_emails:
                    log_print(f"📬 Found {len(new_emails)} total email(s) in this check!")
                # else:
                #     log_print(f"📭 No emails found in this check")
                
                # Process each email
                for email_data in new_emails:
                    # Check for stop request before processing each email
                    if self._stop_requested:
                        break
                        
                    log_print(f"\n{'='*60}")
                    log_print(f"📧 メール処理中!")
                    log_print(f"送信者: {email_data['from']}")
                    log_print(f"件名: {email_data['subject']}")
                    log_print(f"日時: {email_data['date']}")
                    # log_print(f"画像添付ファイル: {email_data['image_attachments']}")
                    log_print(f"{'='*60}\n")
                    
                    # Process email with images
                    try:
                        log_print("⚡ メールワークフロー処理中...")
                        asyncio.run(self._process_email_with_images(email_data))
                        log_print("✅ ワークフロー完了\n")
                    except Exception as e:
                        import traceback
                        traceback.print_exc()
                
                # Check for stop request before sleeping
                if not self._stop_requested:
                    # Wait before next check
                    time.sleep(check_interval)
            
            # Log when stopped by request
            if self._stop_requested:
                log_print("🛑 メールリスナーが停止要求により停止しました")
                
        except KeyboardInterrupt:
            log_print("\n\n⚠️ ユーザーによりメールリスナーが停止されました")
            self.disconnect()
        except Exception as e:
            log_print(f"\n❌ メールリスナーエラー: {e}")
            self.disconnect()
    
    def _process_email_with_images(self, email_data: Dict):
        """Process email with image attachments"""
        if not email_data.get('image_attachments'):
            log_print("📧 メールに画像添付ファイルが見つかりません")
            return
        
        all_structured_data = []
        
        for image_attachment in email_data['image_attachments']:
            log_print(f"📸 画像処理中: {image_attachment['filename']} ({image_attachment['size']} バイト)")
            
            try:
                # Extract structured data from image
                structured_data = self.extractor.extract_structured_data_from_image(image_attachment['content'])
                
                if structured_data:
                    log_print(f"✅ {image_attachment['filename']}から{len(structured_data)}件のレコードを抽出しました")
                    all_structured_data.extend(structured_data)
                else:
                    log_print(f"⚠️ {image_attachment['filename']}に構造化データが見つかりません")
                    
            except Exception as e:
                log_print(f"❌ 画像処理エラー {image_attachment['filename']}: {e}")
                continue
        
        # Process all extracted data with Kaipoke
        if all_structured_data:
            log_print(f"🚀 Kaipokeで{len(all_structured_data)}件のレコードを処理中...")
            
        # Initialize Kaipoke scraper if not already done
            if not self.kaipoke_scraper:
                self.kaipoke_scraper = KaipokeScraper()
            try:
                self.kaipoke_scraper.process_with_ocr(all_structured_data)
                log_print("✅ Kaipoke処理完了")
                self.kaipoke_scraper.close_browser()
                self.kaipoke_scraper = None
                print("set None to kaipoke_scraper")
            except Exception as e:
                log_print(f"❌ Kaipoke処理エラー: {e}")
                self.kaipoke_scraper = None
                print("set None to kaipoke_scraper")
        else:
            log_print("⚠️ 処理する構造化データがありません")


# def main():
#     """Main function to run email listener"""
#     try:
#         log_print("🚀 Starting Email Listener Service...")
        
#         # Create and initialize email listener
#         listener = EmailListener()
        
#         # Connect to email server
#         if not listener.connect():
#             log_print("❌ Failed to connect to email server. Exiting.")
#             return
        
#         # Start listening for emails
#         log_print("📧 Email listener started successfully!")
#         listener.listen(check_interval=60)
        
#     except KeyboardInterrupt:
#         log_print("\n⚠️ Service stopped by user")
#     except Exception as e:
#         log_print(f"❌ Fatal error: {e}")
#         import traceback
#         traceback.print_exc()

# if __name__ == "__main__":
#     main()

