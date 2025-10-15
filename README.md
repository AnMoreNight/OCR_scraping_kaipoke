# Kaipoke OCR and Scraping Workflow

Extract text from images using Google Cloud Vision API and scrape data from Kaipoke website.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Playwright browsers:**
   ```bash
   playwright install chromium
   ```

3. **Get Google Cloud credentials:**
   
   **Project ID:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Your Project ID is shown in the top bar (e.g., `my-project-123456`)
   
   **Service Account Key:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Navigate to "IAM & Admin" → "Service Accounts"
   - Click "Create Service Account" or use existing one
   - Click on service account → "Keys" tab → "Add Key" → "Create new key" → "JSON"
   - Download the JSON file

4. **Create `.env` file:**
   ```env
   # Google Cloud credentials
   GOOGLE_CLOUD_PROJECT_ID=your-project-id-here
   GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json
   
   # OpenAI API
   OPENAI_API_KEY=your-openai-api-key-here
   
   # Kaipoke credentials
   KAIPOKE_CORPORATE_CODE=your-corporate-code
   KAIPOKE_USERNAME=your-username
   KAIPOKE_PASSWORD=your-password
   
   # Email credentials (for email trigger)
   EMAIL_SERVER=imap.gmail.com
   EMAIL_ADDRESS=your-email@gmail.com
   EMAIL_PASSWORD=your-app-password
   EMAIL_FOLDER=INBOX
   DEFAULT_IMAGE_PATH=images/IMG_1281.jpeg
   ```

5. **Get OpenAI API Key:**
   - Go to [OpenAI Platform](https://platform.openai.com/api-keys)
   - Create a new API key
   - Add it to your `.env` file

6. **Setup Email Trigger (Optional):**
   
   For Gmail:
   - Enable 2-factor authentication on your Google account
   - Go to [App Passwords](https://myaccount.google.com/apppasswords)
   - Create an app password for "Mail"
   - Use this app password in your `.env` file (not your regular password)

7. **Enable APIs in Google Cloud Console:**
   - Cloud Vision API

## Usage Modes

### Mode 1: Manual Mode
Run workflow once with a specific image:
```bash
python main.py
# Select option 1
# Enter image path
```

### Mode 2: Email Trigger Mode
Automatically run workflow when you receive an email:
```bash
python main.py
# Select option 2
# Script will monitor your inbox and trigger workflow on new emails
```

## Usage Examples

### OCR Processing
```python
from image_text_translator import ImageTextExtractor

# Initialize
extractor = ImageTextExtractor()

# Extract text from image first
full_text = extractor.extract_text_from_image("image.jpg", merge_all=True)

# Extract structured data from the text (returns list of all records)
structured_data_list = extractor.extract_structured_data(full_text)

# Print all structured data records
for i, structured_data in enumerate(structured_data_list, 1):
    print(f"\n--- Record {i} ---")
    if 'name' in structured_data:
        print(f"お名前: {structured_data['name']}")
    if 'date' in structured_data:
        print(f"実施日: {structured_data['date']}")
    if 'time' in structured_data:
        print(f"時間: {structured_data['time']}")
```

### Upload to Kaipoke
```python
from kaipoke import KaipokeScraper

# Initialize Kaipoke client
kaipoke = KaipokeScraper()

# Login
kaipoke.login()

# Upload OCR results
ocr_results = [{"name": "平井里沙", "date": "2025 年 8 月 29 日(金)", "time": "11:30~14:30"}]
kaipoke.upload_ocr_data(ocr_results)
```

### Complete Workflow (OCR + Upload)
```python
# Run main workflow - processes image and uploads to Kaipoke
python main.py
```

## Test Credentials

First, test if your credentials are working:

```bash
python test_credentials.py
```

## Run Example

```bash
python image_text_translator.py
```

## Requirements

- Google Cloud account
- Service account with Vision API permissions
- Python 3.7+
