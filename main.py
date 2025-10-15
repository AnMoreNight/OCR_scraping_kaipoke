"""
Main workflow for Kaipoke OCR and Scraping
"""

import os
import time
from dotenv import load_dotenv
from typing import List, Dict
from kaipoke import KaipokeScraper
from OCR import ImageTextExtractor
from email_listener import EmailListener

# Load environment variables
load_dotenv()


def process_ocr_workflow(image_path: str):
    """Process OCR on an image and extract structured data"""
    print(f"\n=== OCR Processing: {image_path} ===")
    
    # Initialize OCR extractor
    extractor = ImageTextExtractor()
    
    # Check if image exists
    if not os.path.exists(image_path):
        print(f"Image file not found: {image_path}")
        return None
    
    try:
        # Step 1: Extract text from image
        print("Extracting text from image...")
        full_text = extractor.extract_text_from_image(image_path, merge_all=True)
        
        if not full_text:
            print("No text found in the image")
            return None
        
        print(f"\n--- Extracted Text ---\n{full_text}\n")
        
        # Step 2: Extract structured data using AI
        print("Extracting structured data using AI...")
        structured_data_list = extractor.extract_structured_data(full_text)
        
        if structured_data_list:
            print("\n=== Extracted Structured Data ===")
            for i, structured_data in enumerate(structured_data_list, 1):
                print(f"\n--- Record {i} ---")
                if 'name' in structured_data:
                    print(f"お名前: {structured_data['name']}")
                if 'date' in structured_data:
                    print(f"実施日: {structured_data['date']}")
                if 'time' in structured_data:
                    print(f"時間: {structured_data['time']}")
            
            return structured_data_list
        else:
            print("No structured data found in the text")
            return None
            
    except Exception as e:
        print(f"Error in OCR processing: {e}")
        return None


def process_upload_workflow(ocr_results: List):
    """Upload OCR results to Kaipoke"""
    print("\n=== Kaipoke Upload Workflow ===")
    
    if not ocr_results:
        print("No OCR results to upload")
        return False, None
    
    # Initialize Kaipoke client
    kaipoke_client = KaipokeScraper()
    
    try:
        # Step 1: Login to Kaipoke
        login_success = kaipoke_client.login()
        
        if not login_success:
            print("❌ Login failed. Cannot upload data.")
            return False, kaipoke_client
        
        # Step 2: Navigate to target page
        nav_success = kaipoke_client.navigate_to_target_page()
        
        if not nav_success:
            print("❌ Failed to navigate to target page.")
            return False, kaipoke_client
        
        # Step 3: Show OCR data ready for upload
        print("\n📋 OCR Results ready for upload:")
        for i, result in enumerate(ocr_results, 1):
            print(f"  {i}. {result}")
        
        print("\n⚠️ Upload/Insert functionality will be implemented here based on the target page form structure")
        
        # Return client to keep browser open
        return True, kaipoke_client
            
    except Exception as e:
        print(f"Error in upload workflow: {e}")
        return False, None


def run_workflow(image_path: str):
    """Run the complete OCR and upload workflow"""
    ocr_results = process_ocr_workflow(image_path)
    
    # Upload workflow
    if ocr_results:
        upload_success, kaipoke_client = process_upload_workflow(ocr_results)
        if upload_success:
            print("\n✅ OCR results are ready for upload to Kaipoke!")
            print("\n🌐 Browser will stay open indefinitely.")
            print("⚠️ Please close the browser window manually when you're done.")
        else:
            print("\n❌ Failed to process upload workflow")
    else:
        print("\n⚠️ No OCR results to upload")


def email_triggered_workflow(email_data: Dict):
    """Workflow triggered by email"""
    print(f"\n{'='*70}")
    print("⚡ EMAIL TRIGGERED WORKFLOW")
    print(f"{'='*70}")
    print(f"📧 Email From: {email_data['from']}")
    print(f"📧 Subject: {email_data['subject']}")
    print(f"📧 Date: {email_data['date']}")
    print(f"{'='*70}\n")
    
    # Get image path from user or use default
    image_path = os.getenv('DEFAULT_IMAGE_PATH', 'images/IMG_1281.jpeg')
    
    print(f"📸 Processing image: {image_path}")
    
    # Run the workflow
    run_workflow(image_path)


def main():
    """Main entry point"""
    print("=" * 70)
    print("=== Kaipoke OCR Workflow with Email Trigger ===")
    print("=" * 70)
    
    print("\nSelect mode:")
    print("1. Manual mode - Run workflow once")
    print("2. Email trigger mode - Wait for emails and run workflow automatically")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "2":
        # Email trigger mode
        print("\n📧 Starting Email Trigger Mode...")
        
        # Create email listener
        listener = EmailListener()
        
        # Connect to email server
        if listener.connect():
            # Start listening for emails
            listener.listen(email_triggered_workflow, check_interval=10)
        else:
            print("❌ Failed to connect to email server. Please check your .env file.")
    else:
        # Manual mode
        print("\n📋 Starting Manual Mode...")
        
        # Get image path
        image_path = input("\nEnter image path (or press Enter for default): ").strip()
        if not image_path:
            image_path = "images/IMG_1281.jpeg"
        
        # Run workflow
        run_workflow(image_path)
        
        # Keep browser open
        print("\n💡 Script completed. You can close this terminal or leave it running.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n⚠️ Ctrl+C detected. Browser will remain open.")
            print("Close the browser window manually to exit completely.")

if __name__ == "__main__":
    main()
