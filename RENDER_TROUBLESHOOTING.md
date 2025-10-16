# Render Deployment Troubleshooting

## Common Issues and Solutions

### Issue 1: Port Scan Timeout Error

**Error Message:**
```
Port scan timeout reached, no open ports detected. Bind your service to at least one port. 
If you don't need to receive traffic on any port, create a background worker instead.
```

**Cause:** 
Your application is designed to run as a background worker (email listener) that doesn't serve HTTP requests, but you're trying to deploy it as a web service.

**Solution:**
1. **Use Background Worker instead of Web Service**
2. **Update render.yaml:**
   ```yaml
   services:
     - type: worker  # Changed from 'web' to 'worker'
       name: kaipoke-ocr-workflow
       env: python
       plan: starter
       buildCommand: |
         pip install -r requirements.txt
         playwright install chromium
       startCommand: python main.py
   ```

3. **Update Procfile:**
   ```
   worker: python main.py  # Changed from 'web:' to 'worker:'
   ```

4. **Manual Setup:**
   - Go to Render Dashboard
   - Click "New +" → "Background Worker" (not "Web Service")
   - Configure as usual

### Issue 2: Browser Automation on Free Tier

**Problem:** Browser automation may fail on Render's free tier due to memory limitations.

**Solutions:**
1. **Use headless mode** (already configured)
2. **Consider upgrading** to paid plan for better performance
3. **Monitor memory usage** in logs

### Issue 3: Email Connection Issues

**Error:** `❌ Email connection failed!`

**Solutions:**
1. **Check credentials:**
   - Verify `EMAIL_ADDRESS` and `EMAIL_PASSWORD`
   - Use Gmail App Password (not regular password)
   - Enable 2-factor authentication

2. **Check environment variables:**
   - Ensure all variables are set correctly
   - Verify JSON format for `GOOGLE_SERVICE_ACCOUNT_JSON`

### Issue 4: Google Cloud Authentication

**Error:** `❌ No Google Cloud credentials found!`

**Solutions:**
1. **Check `GOOGLE_SERVICE_ACCOUNT_JSON`:**
   - Must be single-line JSON string
   - No line breaks or formatting
   - Valid service account JSON

2. **Verify project ID:**
   - `GOOGLE_CLOUD_PROJECT_ID` must match your project

### Issue 5: Playwright Installation

**Error:** `playwright: command not found`

**Solutions:**
1. **Ensure build command includes:**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Check requirements.txt includes:**
   ```
   playwright
   ```

## Deployment Checklist

### Before Deployment
- [ ] Code pushed to GitHub
- [ ] `render.yaml` configured as `type: worker`
- [ ] `Procfile` uses `worker:` not `web:`
- [ ] All environment variables ready
- [ ] No default image dependencies

### After Deployment
- [ ] Check logs for successful startup
- [ ] Verify email connection
- [ ] Test with email containing image
- [ ] Monitor for any errors

## Service Type Comparison

| Service Type | Use Case | Port Required | Cost |
|--------------|----------|---------------|------|
| **Web Service** | HTTP API, Website | ✅ Yes | Higher |
| **Background Worker** | Email processing, Cron jobs | ❌ No | Lower |

**Your Use Case:** Email listener → Use **Background Worker**

## Quick Fix for Port Error

If you're getting the port error:

1. **Delete current service** on Render
2. **Create new Background Worker:**
   - Go to Render Dashboard
   - Click "New +" → "Background Worker"
   - Connect your GitHub repository
   - Set start command: `python main.py`
3. **Set environment variables**
4. **Deploy**

## Monitoring Your Worker

After deployment:
1. **Check logs** regularly
2. **Monitor email processing**
3. **Verify OCR functionality**
4. **Check API usage and billing**

## Support

If issues persist:
1. Check Render logs first
2. Verify all environment variables
3. Test locally before deploying
4. Review this troubleshooting guide
