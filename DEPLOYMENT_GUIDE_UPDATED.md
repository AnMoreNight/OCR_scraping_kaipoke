# Render Deployment Guide - Updated with Image Attachments

This guide will help you deploy your Kaipoke OCR workflow to Render with email image attachment support.

## New Feature: Email Image Attachments

The workflow now automatically:
- ✅ **Detects image attachments** in emails
- ✅ **Processes attached images** for OCR
- ✅ **Falls back to default image** if no attachments
- ✅ **Supports multiple image formats** (.jpg, .png, .gif, .bmp, .tiff, .webp)

## Prerequisites

1. **GitHub Repository** with your code
2. **Render Account** (free tier available)
3. **All Environment Variables** ready

## Step 1: Prepare Your Code

### 1.1 Push to GitHub
Make sure all your files are committed and pushed to GitHub:

```bash
git add .
git commit -m "Added email image attachment support"
git push origin main
```

### 1.2 Verify Required Files
Ensure these files are in your repository:
- ✅ `main.py` - Main application (updated for image attachments)
- ✅ `OCR.py` - OCR functionality
- ✅ `kaipoke.py` - Kaipoke integration
- ✅ `email_listener.py` - Email monitoring (updated for image detection)
- ✅ `requirements.txt` - Dependencies
- ✅ `render.yaml` - Render configuration
- ✅ `Procfile` - Process definition
- ✅ `runtime.txt` - Python version
- ✅ `images/IMG_1281.jpeg` - Default image (fallback)

## Step 2: Deploy to Render

### 2.1 Create Render Account
1. Go to [https://render.com](https://render.com)
2. Sign up with GitHub
3. Connect your GitHub account

### 2.2 Create New Web Service

**Option A: Using render.yaml (Recommended)**
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "Blueprint"
3. Connect your GitHub repository
4. Render will automatically detect `render.yaml` and use those settings

**Option B: Manual Setup**
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure manually:
   - **Name:** `kaipoke-ocr-workflow`
   - **Environment:** `Python 3`
   - **Build Command:** 
     ```bash
     pip install -r requirements.txt
     playwright install chromium
     ```
   - **Start Command:** `python main.py`

## Step 3: Set Environment Variables

In Render dashboard, go to "Environment" tab and add these variables:

### Required Variables:

| Variable | Value | Description |
|----------|-------|-------------|
| `GOOGLE_CLOUD_PROJECT_ID` | `kaipoke-input` | Your Google Cloud project ID |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | `{"type":"service_account",...}` | Your JSON credentials (single line) |
| `OPENAI_API_KEY` | `sk-proj-...` | Your OpenAI API key |
| `KAIPOKE_CORPORATE_CODE` | `165220` | Your Kaipoke corporate code |
| `KAIPOKE_USERNAME` | `test` | Your Kaipoke username |
| `KAIPOKE_PASSWORD` | `Helloworld1` | Your Kaipoke password |
| `EMAIL_SERVER` | `imap.gmail.com` | Email server (Gmail) |
| `EMAIL_ADDRESS` | `soluna0226@gmail.com` | Your email address |
| `EMAIL_PASSWORD` | `Happysolun@0226` | Your Gmail app password |
| `EMAIL_FOLDER` | `INBOX` | Email folder to monitor |
| `DEFAULT_IMAGE_PATH` | `images/IMG_1281.jpeg` | Default image path (fallback) |

## Step 4: Deploy and Test

### 4.1 Deploy
1. Click "Create Web Service" or "Deploy"
2. Wait for build to complete (5-10 minutes)
3. Monitor the build logs for any errors

### 4.2 Check Deployment Logs
Look for these success messages:
```
✅ Using Google Cloud credentials from GOOGLE_SERVICE_ACCOUNT_JSON environment variable
📧 Connecting to email server: imap.gmail.com
📧 Email account: soluna0226@gmail.com
✅ Successfully connected to email server
🎧 Starting email listener...
📧 Monitoring: soluna0226@gmail.com
⚡ Waiting for new emails... (Press Ctrl+C to stop)
```

### 4.3 Test Email Trigger with Images

#### Test 1: Email with Image Attachment (Recommended)
Send email to: `soluna0226@gmail.com`
- **Subject:** `Test OCR Workflow with Image`
- **Body:** `This is a test email with image attachment for OCR processing.`
- **Attachment:** Include an image file (.jpg, .png, .gif, etc.) with Japanese text

**Expected Log Output:**
```
📬 Found 1 new email(s)!
==================================================================
📧 New Email Received!
From: sender@example.com
Subject: Test OCR Workflow with Image
Date: 2025-01-15 10:30:00
📎 Has Attachments: True
🖼️ Has Images: True
==================================================================
📸 Found 1 image attachment(s):
  1. document.jpg (245760 bytes)
🔄 Processing first image: document.jpg
💾 Saved image to: temp_email_image_1642248600.jpg
📸 Processing image: temp_email_image_1642248600.jpg
[OCR processing...]
🗑️ Cleaned up temporary file: temp_email_image_1642248600.jpg
```

#### Test 2: Email without Attachments
Send email to: `soluna0226@gmail.com`
- **Subject:** `Test OCR Workflow`
- **Body:** `This is a test email to trigger the OCR workflow.`

**Expected Log Output:**
```
📧 No image attachments in email
🔄 Using default image for processing...
📸 Processing default image: images/IMG_1281.jpeg
[OCR processing...]
```

## Step 5: Monitor and Maintain

### 5.1 Regular Monitoring
- Check Render logs daily
- Monitor email processing
- Verify API quotas and billing
- Check for successful image processing

### 5.2 Troubleshooting
If you encounter issues:

1. **Image Processing Errors**
   - Check if image format is supported
   - Verify image file size (not too large)
   - Check temporary file permissions

2. **Email Attachment Issues**
   - Verify email has image attachments
   - Check supported image formats
   - Ensure email is not corrupted

3. **General Issues**
   - Check environment variables
   - Verify email connection
   - Check API authentication

## New Workflow Features

### Image Attachment Processing
- ✅ **Automatic detection** of image attachments
- ✅ **Multiple format support** (.jpg, .jpeg, .png, .gif, .bmp, .tiff, .webp)
- ✅ **Temporary file handling** with cleanup
- ✅ **Fallback to default image** if no attachments
- ✅ **Error handling** for corrupted images

### Email Processing Flow
1. **Email received** → Check for image attachments
2. **If images found** → Process first image attachment
3. **If no images** → Use default image
4. **Run OCR** → Extract Japanese text
5. **AI processing** → Get structured data
6. **Kaipoke upload** → Login and navigate
7. **Cleanup** → Remove temporary files

## Production Recommendations

### For Production Use
- Monitor image file sizes (set limits)
- Implement image validation
- Add support for multiple images
- Set up proper error logging
- Consider image compression

### Security Considerations
- Validate image file types
- Check file sizes to prevent abuse
- Implement rate limiting
- Monitor for suspicious attachments

## Support

If you encounter issues:
1. Check Render logs first
2. Verify all environment variables
3. Test with simple image attachments
4. Check image file formats and sizes
5. Review this guide for troubleshooting

## Next Steps After Deployment

1. **Test with real images** containing Japanese text
2. **Monitor OCR accuracy** with different image types
3. **Verify Kaipoke integration** works with email images
4. **Set up monitoring** for image processing
5. **Optimize performance** for production use

Your Kaipoke OCR workflow now automatically processes images from email attachments! 🎉
