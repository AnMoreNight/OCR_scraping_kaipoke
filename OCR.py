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
                # imageContext = vision.ImageContext(language_hints=["ja"])
                self.vision_client = vision.ImageAnnotatorClient(credentials=credentials)
                # print("✅ Using Google Cloud credentials from GOOGLE_SERVICE_ACCOUNT_JSON environment variable")
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
1. Name (お名前) - the person's name(there can be 2 names in Text but お名前 is the first one)
2. Date (実施日) - the implementation date(It can't be earlier than last year, if it's earlier, please fix it to the current year)
3. Time (時間) : this is the ms
    - :00 20 such format means 20:00. it's time format
    - time format only :00 or :30, if didn't match have to update with this format.
    - can't be arranged "(" or ")" before the time. if there is "(" or ")" before the time, it's "1" in the time so add "1" to the time.
    for example "(7:30" is "17:30" not 07:30 or 7:30.
    - there are even times(first one is the start time, second one is the end time, third one is the start time, fourth one is the end time, and so on, end time can be earlier than start time)
4. Facility Name (事業所名) - the facility/institution name
5. Disability Support Hours (障害者総合支援/身体) - extract the single number value, return 0 if empty or not found
6. Severe Comprehensive Support (重度包括) - extract the single number value, return 0 if empty or not found

Return the result as a JSON array where each object represents one complete record with keys: "name", "date", "time", "facility_name", "disability_support_hours", "severe_comprehensive_support"
If any information is not found in a record, use null for that field.

reference this Example format:
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
        "time": "20:00~09:00",
        "facility_name": "メディヴィレッジ群馬HOME",
        "disability_support_hours": 3,
        "severe_comprehensive_support": 2
    }}
]

If there are multiple records, extract all of them. If there's only one record, return an array with one object.
"""
            client = OpenAI(api_key=self.api_key)
            response = client.responses.create(
                model="gpt-5",
                instructions="You are a helpful assistant that extracts structured data from Japanese text. Always respond with valid JSON only. Extract ALL records found in the text.",
                input=prompt
            )
            
            result_text = response.output_text
            
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
    
    def extract_structured_data_from_image(self, image_data: bytes):
        """Extract structured data from image bytes"""
        
        # Save image data to temporary file
        import tempfile
        import os
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            temp_file.write(image_data)
            temp_image_path = temp_file.name
        
        try:
            # Extract text from image first
            full_text = self.extract_text_from_image(temp_image_path, merge_all=True)
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_image_path)
            except:
                pass
        
        if full_text:
            print("=============== full text ==================")
            print(full_text)
            # Extract structured data from the full text
            structured_data_list = self.extract_structured_data(full_text)
            
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
                return structured_data_list
            else:
                print("No structured data found in the text")
                return []
        else:
            print("No text found in the image")
            return []

    def extract_text_from_image_openai(self, image_path: str) -> str:
        """Extract text from an image using OpenAI's Vision (GPT-4-vision) API"""
        if not self.api_key:
            print("Error: OPENAI_API_KEY not set in environment variables")
            return ""
        import base64
        from openai import OpenAI

        try:
            with open(image_path, "rb") as f:
                image_data = f.read()
            b64_image = base64.b64encode(image_data).decode()

            client = OpenAI(api_key=self.api_key)
            # GPT-4-vision endpoint as of late 2023
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful AI that reads Japanese documents and returns only the full readable text from the image."},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Extract all Japanese readable text from this image. Respond with ONLY text, no explanations."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}}
                        ]
                    }
                ],
                max_tokens=2048
            )
            text = response.choices[0].message.content.strip()
            return text
        except Exception as e:
            print(f"Error extracting text with OpenAI Vision: {e}")
            return ""


if __name__ == "__main__":
    USE_OPENAI_OCR = False  # Set this to False to use Google OCR
    with open("images/4.jpeg", "rb") as f:
        image_data = f.read()
    extractor = ImageTextExtractor()

    if USE_OPENAI_OCR:
        # New: Use OpenAI Vision OCR
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            tmp.write(image_data)
            tmp_path = tmp.name
        try:
            print("Using OpenAI Vision for OCR...")
            full_text = extractor.extract_text_from_image_openai(tmp_path)
            print("=============== full text (OpenAI Vision) ==================")
            print(full_text)
            structured_data = extractor.extract_structured_data(full_text)
        finally:
            import os
            os.unlink(tmp_path)
    else:
        # Original: Google OCR
        structured_data = extractor.extract_structured_data_from_image(image_data)

    print("=== Extracted Structured Data ===")
    for i, structured_data in enumerate(structured_data, 1):
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
