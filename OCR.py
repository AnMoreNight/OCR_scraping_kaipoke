"""
Google Cloud Vision API for Image Text Extraction
"""

import os
import io
import json
from typing import List, Union, Dict
from google.cloud import vision
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()


class ImageTextExtractor:
    """Extract text from images using Google Cloud Vision API"""
    
    def __init__(self):
        """Initialize the extractor with Google Cloud credentials"""
        # Initialize client with credentials from environment variables
        try:
            from google.oauth2 import service_account
            import json
            
            # Use service account JSON from environment variable (preferred method)
            service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
            if service_account_json:
                # Parse JSON from environment variable
                service_account_info = json.loads(service_account_json)
                credentials = service_account.Credentials.from_service_account_info(service_account_info)
                self.vision_client = vision.ImageAnnotatorClient(credentials=credentials)
                print("✅ Using Google Cloud credentials from GOOGLE_SERVICE_ACCOUNT_JSON environment variable")
            else:
                print("❌ No Google Cloud credentials found!")
                print("Please set GOOGLE_SERVICE_ACCOUNT_JSON environment variable")
                raise ValueError("No Google Cloud credentials configured")
        except Exception as e:
            print(f"❌ Error initializing Vision client: {e}")
            raise
        
        # Initialize OpenAI client
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            print("Warning: OPENAI_API_KEY not set in environment variables")
    
    def extract_text_from_image(self, image_path: str, merge_all: bool = True) -> Union[str, List[str]]:
        """Extract text from an image using Google Cloud Vision API"""
        with io.open(image_path, 'rb') as image_file:
            content = image_file.read()
        print("processing image...")
        image = vision.Image(content=content)
        response = self.vision_client.text_detection(image=image)
        texts = response.text_annotations
        
        if merge_all:
            # Return all text merged into a single string
            if texts:
                return texts[0].description  # First annotation contains all text
            return ""
        else:
            # Return text blocks (skip the first one as it's the full text)
            return [text.description for text in texts[1:]]
    
    def extract_structured_data(self, full_text: str) -> List[Dict[str, str]]:
        """Extract all structured data from Japanese text using AI"""
        if not self.api_key:
            print("Error: OPENAI_API_KEY not configured")
            return []
        
        try:
            prompt = f"""
Extract ALL instances of the following information from this Japanese text and return as JSON:

Text: {full_text}

Please extract ALL occurrences of:
1. Name (お名前) - the person's name
2. Date (実施日) - the implementation date  
3. Time (時間) - the time period
4. Facility Name (事業所名) - the facility/institution name
5. Disability Support Hours (障害者総合支援/身体) - extract the single number value, return 0 if empty or not found
6. Severe Comprehensive Support (重度包括) - extract the single number value, return 0 if empty or not found

Return the result as a JSON array where each object represents one complete record with keys: "name", "date", "time", "facility_name", "disability_support_hours", "severe_comprehensive_support"
If any information is not found in a record, use null for that field.

Example format:
[
    {{
        "name": "平井 里沙",
        "date": "2025 年 8 月 15 日(金)",
        "time": "11:30~14:30",
        "facility_name": "メディヴィレッジ群馬HOME",
        "disability_support_hours": 4.5,
        "severe_comprehensive_support": 0
    }},
    {{
        "name": "田中 太郎", 
        "date": "2025 年 8 月 16 日(土)",
        "time": "09:00~12:00",
        "facility_name": "メディヴィレッジ群馬HOME",
        "disability_support_hours": 3,
        "severe_comprehensive_support": 2
    }}
]

If there are multiple records, extract all of them. If there's only one record, return an array with one object.
"""
            client = OpenAI(api_key=self.api_key)
            response = client.responses.create(
                model="gpt-4-turbo",
                instructions="You are a helpful assistant that extracts structured data from Japanese text. Always respond with valid JSON only. Extract ALL records found in the text.",
                input=prompt
            )
            
            result_text = response.output_text
            print(f"AI Response: {response.output_text}")
            # Parse the JSON response exactly matching the documented AI response format.
            # Clean the response text (remove markdown formatting)
            if result_text.startswith("```json"):
                result_text = result_text.replace("```json", "").replace("```", "").strip()
            elif result_text.startswith("```"):
                result_text = result_text.replace("```", "").strip()
            
            # Parse the cleaned JSON
            results = json.loads(result_text)

            # Ensure the result is always a list, as per the AI response format
            if not isinstance(results, list):
                results = [results]

            # Each record should have "name", "date", and "time" fields,
            # but set to None (null in JSON) if missing, which matches the AI doc.
            # No need to filter out nulls, just return the list as-is.
            return results
            
        except Exception as e:
            print(f"Error extracting structured data with AI: {e}")
            print(f"Error type: {type(e).__name__}")
            return []
    
def main():
    """Example usage for text extraction"""
    extractor = ImageTextExtractor()
    image_path = "images/IMG_1260.jpeg"
    
    if not os.path.exists(image_path):
        print(f"Image file not found: {image_path}")
        return
    
    # Extract text from image first
    full_text = extractor.extract_text_from_image(image_path, merge_all=True)
    print("=========full_text=========")
    print(full_text)
    
    if full_text:
        # Extract structured data from the full text
        structured_data_list = extractor.extract_structured_data(full_text)
        
        if structured_data_list:
            print("=== Extracted Structured Data ===")
            for i, structured_data in enumerate(structured_data_list, 1):
                print(f"\n--- Record {i} ---")
                if 'name' in structured_data:
                    print(f"お名前: {structured_data['name']}")
                if 'date' in structured_data:
                    print(f"実施日: {structured_data['date']}")
                if 'time' in structured_data:
                    print(f"時間: {structured_data['time']}")
                if 'facility_name' in structured_data:
                    print(f"事業所名: {structured_data['facility_name']}")
                if 'disability_support_hours' in structured_data:
                    print(f"障害者総合支援/身体: {structured_data['disability_support_hours']}")
                if 'severe_comprehensive_support' in structured_data:
                    print(f"重度包括: {structured_data['severe_comprehensive_support']}")
        else:
            print("No structured data found in the text")
    else:
        print("No text found in the image")


if __name__ == "__main__":
    main()
