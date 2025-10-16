# Render Deployment Guide

This guide will help you deploy your Kaipoke OCR workflow to Render.

## Prerequisites

1. **GitHub Repository** with your code
2. **Render Account** (free tier available)
3. **All Environment Variables** ready

## Step 1: Prepare Your Code

### 1.1 Push to GitHub
Make sure all your files are committed and pushed to GitHub:

```bash
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

### 1.2 Verify Required Files
Ensure these files are in your repository:
- ✅ `main.py` - Main application
- ✅ `OCR.py` - OCR functionality
- ✅ `kaipoke.py` - Kaipoke integration
- ✅ `email_listener.py` - Email monitoring
- ✅ `requirements.txt` - Dependencies
- ✅ `render.yaml` - Render configuration
- ✅ `Procfile` - Process definition
- ✅ `runtime.txt` - Python version
- ✅ `images/IMG_1281.jpeg` - Default image

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
| `DEFAULT_IMAGE_PATH` | `images/IMG_1281.jpeg` | Default image path |

### Important Notes:
- **GOOGLE_SERVICE_ACCOUNT_JSON**: Use the exact JSON string from your `.env` file
- **EMAIL_PASSWORD**: Use Gmail App Password, not your regular password
- **All values**: Copy exactly from your working `.env` file

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

### 4.3 Test Email Trigger
1. **Send a test email** to `soluna0226@gmail.com`
2. **Check Render logs** for trigger messages
3. **Verify OCR processing** works
4. **Check Kaipoke login** and navigation

## Step 5: Monitor and Maintain

### 5.1 Regular Monitoring
- Check Render logs daily
- Monitor email processing
- Verify API quotas and billing

### 5.2 Troubleshooting
If you encounter issues:

1. **Check Environment Variables**
   - Verify all variables are set correctly
   - Ensure JSON format is valid

2. **Check Logs**
   - Look for error messages
   - Verify email connection
   - Check API authentication

3. **Test Locally**
   - Run `python main.py` locally
   - Verify everything works before deploying

## Important Considerations

### Render Free Tier Limitations
- **Memory**: Limited memory for browser automation
- **Timeout**: 15-minute timeout limits
- **CPU**: Limited CPU resources
- **Headless Mode**: Browser runs in headless mode (no GUI)

### Production Recommendations
For production use, consider:
- Upgrading to Render's paid plans
- Using dedicated VPS for browser automation
- Implementing proper error handling and retries
- Setting up monitoring and alerting

## Security Notes

- Never commit credentials to Git
- Use environment variables for all sensitive data
- Regularly rotate API keys and passwords
- Monitor usage to avoid unexpected charges

## Support

If you encounter issues:
1. Check Render logs first
2. Verify all environment variables
3. Test locally before deploying
4. Review this guide for troubleshooting

## Next Steps After Deployment

1. **Test email trigger** by sending emails
2. **Monitor logs** for any errors
3. **Verify OCR processing** works correctly
4. **Check Kaipoke integration** functions properly
5. **Set up monitoring** for production use

Your Kaipoke OCR workflow will now run 24/7 on Render, automatically processing emails and extracting data from images!
