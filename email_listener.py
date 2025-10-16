"""
Email Listener Module - Monitors email inbox for new messages
"""

import os
import time
import email
import sys
import logging
from typing import List, Dict, Optional, Callable
from dotenv import load_dotenv
from imapclient import IMAPClient
import pyzmail

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
    logger.info(message)

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
        self.email_folder = os.getenv('EMAIL_FOLDER', 'INBOX')
        
        # Connection
        self.client = None
        self.is_connected = False
        
        # Tracking
        self.seen_uids = set()
        
    def connect(self) -> bool:
        """Connect to email server"""
        if not all([self.email_address, self.email_password]):
            log_print("❌ Error: EMAIL_ADDRESS and EMAIL_PASSWORD must be set in .env file")
            return False
        
        try:
            log_print(f"📧 Connecting to email server: {self.email_server}")
            log_print(f"📧 Email account: {self.email_address}")
            
            # Connect to IMAP server
            self.client = IMAPClient(self.email_server, ssl=True)
            
            # Login
            self.client.login(self.email_address, self.email_password)
            
            # Select folder
            self.client.select_folder(self.email_folder)
            
            log_print("✅ Successfully connected to email server")
            self.is_connected = True
            
            # Get existing email UIDs to avoid processing old emails
            messages = self.client.search(['ALL'])
            self.seen_uids = set(messages)
            log_print(f"📧 Found {len(self.seen_uids)} existing emails (will be ignored)")
            
            return True
            
        except Exception as e:
            log_print(f"❌ Error connecting to email server: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from email server"""
        if self.client:
            try:
                self.client.logout()
                log_print("📧 Disconnected from email server")
            except:
                pass
        self.is_connected = False
    
    def check_new_emails(self) -> List[Dict]:
        """Check for new emails"""
        if not self.is_connected:
            return []
        
        try:
            # Search for all emails
            messages = self.client.search(['ALL'])
            
            # Find new emails
            new_uids = set(messages) - self.seen_uids
            
            if not new_uids:
                return []
            
            log_print(f"\n📬 Found {len(new_uids)} new email(s)!")
            
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
            for part in message.mailparts:
                if part.is_attachment and part.filename:
                    # Check if it's an image file
                    filename_lower = part.filename.lower()
                    if any(filename_lower.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']):
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
            
            return email_data
            
        except Exception as e:
            log_print(f"Error getting email details: {e}")
            return None
    
    def listen(self, callback: Callable, check_interval: int = 10):
        """
        Listen for new emails and trigger callback function
        
        Args:
            callback: Function to call when new email arrives (receives email_data dict)
            check_interval: Seconds between email checks (default: 10)
        """
        log_print(f"\n🎧 Starting email listener...")
        log_print(f"📧 Monitoring: {self.email_address}")
        log_print(f"📁 Folder: {self.email_folder}")
        log_print(f"⏱️ Check interval: {check_interval} seconds")
        log_print(f"\n⚡ Waiting for new emails... (Press Ctrl+C to stop)\n")
        
        try:
            while True:
                # Check for new emails
                new_emails = self.check_new_emails()
                
                # Process each new email
                for email_data in new_emails:
                    log_print(f"\n{'='*60}")
                    log_print(f"📧 New Email Received!")
                    log_print(f"From: {email_data['from']}")
                    log_print(f"Subject: {email_data['subject']}")
                    log_print(f"Date: {email_data['date']}")
                    log_print(f"{'='*60}\n")
                    
                    # Trigger callback
                    try:
                        log_print("⚡ Triggering workflow...")
                        callback(email_data)
                        log_print("✅ Workflow completed\n")
                    except Exception as e:
                        log_print(f"❌ Error in workflow: {e}\n")
                
                # Wait before next check
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            log_print("\n\n⚠️ Email listener stopped by user")
            self.disconnect()
        except Exception as e:
            log_print(f"\n❌ Email listener error: {e}")
            self.disconnect()


def main():
    """Test email listener"""
    def test_callback(email_data):
        """Test callback function"""
        print(f"Callback triggered for email: {email_data['subject']}")
    
    # Create listener
    listener = EmailListener()
    
    # Connect to email server
    if listener.connect():
        # Start listening
        listener.listen(test_callback, check_interval=10)


if __name__ == "__main__":
    main()
