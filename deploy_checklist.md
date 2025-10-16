# 🚀 Render Deployment Checklist

## Pre-Deployment Checklist

### ✅ Code Files
- [x] `main.py` - Main application
- [x] `OCR.py` - OCR functionality (updated for environment variables)
- [x] `kaipoke.py` - Kaipoke integration
- [x] `email_listener.py` - Email monitoring
- [x] `requirements.txt` - Dependencies
- [x] `images/IMG_1281.jpeg` - Default image

### ✅ Deployment Files
- [x] `render.yaml` - Render configuration
- [x] `Procfile` - Process definition
- [x] `runtime.txt` - Python version
- [x] `DEPLOYMENT_GUIDE.md` - Deployment instructions

### ✅ Environment Variables Ready
- [x] `GOOGLE_CLOUD_PROJECT_ID=kaipoke-input`
- [x] `GOOGLE_SERVICE_ACCOUNT_JSON={...}` (JSON string)
- [x] `OPENAI_API_KEY=sk-proj-...`
- [x] `KAIPOKE_CORPORATE_CODE=165220`
- [x] `KAIPOKE_USERNAME=test`
- [x] `KAIPOKE_PASSWORD=Helloworld1`
- [x] `EMAIL_SERVER=imap.gmail.com`
- [x] `EMAIL_ADDRESS=soluna0226@gmail.com`
- [x] `EMAIL_PASSWORD=Happysolun@0226`
- [x] `EMAIL_FOLDER=INBOX`
- [x] `DEFAULT_IMAGE_PATH=images/IMG_1281.jpeg`

## Deployment Steps

### 1. Push to GitHub
```bash
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

### 2. Create Render Account
- Go to [https://render.com](https://render.com)
- Sign up with GitHub
- Connect your repository

### 3. Deploy Service
- Use "Blueprint" option (recommended)
- Render will auto-detect `render.yaml`
- Or create "Web Service" manually

### 4. Set Environment Variables
Copy all variables from your `.env` file to Render dashboard

### 5. Deploy and Test
- Wait for build to complete
- Check logs for success messages
- Send test email to trigger workflow

## Expected Success Logs
```
✅ Using Google Cloud credentials from GOOGLE_SERVICE_ACCOUNT_JSON environment variable
📧 Connecting to email server: imap.gmail.com
📧 Email account: soluna0226@gmail.com
✅ Successfully connected to email server
🎧 Starting email listener...
📧 Monitoring: soluna0226@gmail.com
⚡ Waiting for new emails... (Press Ctrl+C to stop)
```

## Test Email Trigger
Send email to: `soluna0226@gmail.com`
Subject: `Test OCR Workflow`
Body: `This is a test email to trigger the OCR workflow.`

## Troubleshooting
- Check Render logs for errors
- Verify all environment variables are set
- Ensure Gmail App Password is used (not regular password)
- Test locally first if issues occur

## Ready to Deploy! 🎯
All files are prepared and ready for Render deployment.
