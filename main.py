"""
Main workflow for Kaipoke OCR and Scraping
"""

import os
import time
import threading
import sys
import logging
from dotenv import load_dotenv
from typing import List, Dict
from kaipoke import KaipokeScraper
from OCR import ImageTextExtractor
from email_listener import EmailListener

# Load environment variables
load_dotenv()

# Configure logging for Render
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


def process_ocr_workflow(image_path: str):
    """Process OCR on an image and extract structured data"""
    log_print(f"\n=== OCR Processing: {image_path} ===")

    # Initialize OCR extractor
    extractor = ImageTextExtractor()

    # Check if image exists
    if not os.path.exists(image_path):
        log_print(f"Image file not found: {image_path}")
        return None

    try:
        # Step 1: Extract text from image
        log_print("Extracting text from image...")
        full_text = extractor.extract_text_from_image(image_path, merge_all=True)

        if not full_text:
            log_print("No text found in the image")
            return None

        log_print(f"\n--- Extracted Text ---\n{full_text}\n")

        # Step 2: Extract structured data using AI
        log_print("Extracting structured data using AI...")
        structured_data_list = extractor.extract_structured_data(full_text)

        if structured_data_list:
            log_print("\n=== Extracted Structured Data ===")
            for i, structured_data in enumerate(structured_data_list, 1):
                log_print(f"\n--- Record {i} ---")
                if 'name' in structured_data:
                    log_print(f"お名前: {structured_data['name']}")
                if 'date' in structured_data:
                    log_print(f"実施日: {structured_data['date']}")
                if 'time' in structured_data:
                    log_print(f"時間: {structured_data['time']}")

            return structured_data_list
        else:
            log_print("No structured data found in the text")
            return None

    except Exception as e:
        log_print(f"Error in OCR processing: {e}")
        return None


def process_upload_workflow(ocr_results: List):
    """Upload OCR results to Kaipoke"""
    log_print("\n=== Kaipoke Upload Workflow ===")

    if not ocr_results:
        log_print("No OCR results to upload")
        return False, None

    # Initialize Kaipoke client
    kaipoke_client = KaipokeScraper()

    try:
        # Step 1: Login to Kaipoke
        log_print("Attempting to login to Kaipoke...")
        login_success = kaipoke_client.login()

        if not login_success:
            log_print("❌ Login failed. Cannot upload data.")
            return False, kaipoke_client

        # Step 2: Navigate to target page
        log_print("Navigating to target page...")
        nav_success = kaipoke_client.navigate_to_target_page()

        if not nav_success:
            log_print("❌ Failed to navigate to target page.")
            return False, kaipoke_client

        # Step 3: Show OCR data ready for upload
        log_print("\n📋 OCR Results ready for upload:")
        for i, result in enumerate(ocr_results, 1):
            log_print(f"  {i}. {result}")

        log_print("\n⚠️ Upload/Insert functionality will be implemented here based on the target page form structure")

        # Return client to keep browser open
        return True, kaipoke_client

    except Exception as e:
        log_print(f"Error in upload workflow: {e}")
        return False, None


def run_workflow(image_path: str):
    """Run the complete OCR and upload workflow"""
    ocr_results = process_ocr_workflow(image_path)
    
    # Upload workflow
    if ocr_results:
        upload_success, kaipoke_client = process_upload_workflow(ocr_results)
        if upload_success:
            log_print("\n✅ OCR results are ready for upload to Kaipoke!")
            log_print("\n🌐 Browser will stay open indefinitely.")
            log_print("⚠️ Please close the browser window manually when you're done.")
        else:
            log_print("\n❌ Failed to process upload workflow")
    else:
        log_print("\n⚠️ No OCR results to upload")


def email_triggered_workflow(email_data: Dict):
    """Workflow triggered by email"""
    log_print(f"\n{'='*70}")
    log_print("⚡ EMAIL TRIGGERED WORKFLOW")
    log_print(f"{'='*70}")
    log_print(f"📧 Email From: {email_data['from']}")
    log_print(f"📧 Subject: {email_data['subject']}")
    log_print(f"📧 Date: {email_data['date']}")
    log_print(f"📎 Has Attachments: {email_data.get('has_attachments', False)}")
    log_print(f"🖼️ Has Images: {email_data.get('has_images', False)}")
    log_print(f"{'='*70}\n")
    
    # Check if email has image attachments
    if email_data.get('has_images', False):
        image_attachments = email_data.get('image_attachments', [])
        log_print(f"📸 Found {len(image_attachments)} image attachment(s):")
        
        for i, img in enumerate(image_attachments, 1):
            log_print(f"  {i}. {img['filename']} ({img['size']} bytes)")
        
        # Process the first image attachment
        if image_attachments:
            first_image = image_attachments[0]
            log_print(f"\n🔄 Processing first image: {first_image['filename']}")
            
            # Save image attachment to temporary file
            temp_image_path = f"temp_email_image_{int(time.time())}.jpg"
            try:
                with open(temp_image_path, 'wb') as f:
                    f.write(first_image['content'])
                log_print(f"💾 Saved image to: {temp_image_path}")
                
                # Run the workflow with the email image
                run_workflow(temp_image_path)
                
                # Clean up temporary file
                try:
                    os.remove(temp_image_path)
                    log_print(f"🗑️ Cleaned up temporary file: {temp_image_path}")
                except:
                    log_print(f"⚠️ Could not delete temporary file: {temp_image_path}")
                    
            except Exception as e:
                log_print(f"❌ Error processing email image: {e}")
                log_print("💡 Please check the image file and try again")
        else:
            log_print("❌ No image attachments found, skipping workflow")
    else:
        log_print("📧 No image attachments in email")
        log_print("❌ Skipping workflow - no images to process")
        log_print("💡 Please send an email with an image attachment to process")


def start_email_listener():
    """Start email listener in background thread"""
    log_print("\n📧 Starting Email Listener in background...")
    
    # Create email listener
    listener = EmailListener()
    
    # Connect to email server
    if listener.connect():
        log_print("✅ Email listener connected successfully!")
        # Start listening for emails
        listener.listen(email_triggered_workflow, check_interval=10)
    else:
        log_print("❌ Failed to connect to email server. Please check your .env file.")
        log_print("\nTroubleshooting:")
        log_print("1. Check EMAIL_ADDRESS and EMAIL_PASSWORD in .env")
        log_print("2. For Gmail, use App Password (not regular password)")
        log_print("3. Enable 2-factor authentication on Gmail")
        log_print("4. Generate App Password at: https://myaccount.google.com/apppasswords")


def main():
    """Main entry point - Web Service with Email Listener"""
    log_print("=" * 70)
    log_print("=== Kaipoke OCR Workflow with Email Trigger ===")
    log_print("=" * 70)
    log_print("🌐 Web Service Mode - Processing images from email attachments")
    log_print("=" * 70)
    
    # Start email listener in background thread
    log_print("🚀 Starting email listener thread...")
    email_thread = threading.Thread(target=start_email_listener, daemon=True)
    email_thread.start()
    
    # Simple HTTP server to keep service alive
    try:
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import json
        
        class HealthHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/health':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    response = {
                        "status": "healthy",
                        "service": "Kaipoke OCR Email Listener",
                        "message": "Email listener is running in background"
                    }
                    self.wfile.write(json.dumps(response).encode())
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def log_message(self, format, *args):
                # Suppress default logging
                pass
        
        # Start HTTP server on port 10000 (Render's assigned port)
        port = int(os.environ.get('PORT', 10000))
        server = HTTPServer(('0.0.0.0', port), HealthHandler)
        log_print(f"🌐 HTTP server started on port {port}")
        log_print(f"📧 Email listener running in background")
        log_print(f"💡 Service will stay alive and process emails")
        log_print(f"🔗 Health check available at: http://localhost:{port}/health")
        
        # Keep server running
        server.serve_forever()
        
    except Exception as e:
        log_print(f"❌ Error starting HTTP server: {e}")
        log_print("🔄 Falling back to simple keep-alive loop...")
        
        # Fallback: simple keep-alive loop
        try:
            while True:
                time.sleep(60)  # Sleep for 1 minute
                log_print("💓 Service alive - checking emails...")
        except KeyboardInterrupt:
            log_print("\n⚠️ Service stopped")

if __name__ == "__main__":
    main()
