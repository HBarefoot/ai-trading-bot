# Authentication Setup Guide

## Overview
The dashboard now requires password authentication before access. This protects your trading bot data and controls.

## Local Development

### Quick Start (Default Password)
The dashboard works out of the box with default password: `trading2024`

### Custom Password (Recommended)
1. Create `.streamlit/secrets.toml` in the project root:
   ```bash
   mkdir -p .streamlit
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```

2. Edit `.streamlit/secrets.toml`:
   ```toml
   app_password = "your-secure-password-here"
   ```

3. Restart the dashboard

## Streamlit Cloud Deployment

### Setting Password on Cloud
1. Go to your app on Streamlit Cloud
2. Click **Settings** (⚙️) → **Secrets**
3. Add this content:
   ```toml
   app_password = "your-secure-password-here"
   ```
4. Click **Save**
5. App will restart automatically

### Security Best Practices
- ✅ Use a strong password (12+ characters, mix of letters/numbers/symbols)
- ✅ Don't share the password in chat/email
- ✅ Change password regularly (every 90 days)
- ✅ Use different passwords for dev/staging/production
- ❌ Never commit `.streamlit/secrets.toml` to git

## Features

- 🔒 **Password Protected**: All dashboard access requires authentication
- 💾 **Session Persistence**: Stay logged in during your browser session
- 🎨 **Styled Login**: Beautiful purple gradient login page
- 🔄 **Auto Redirect**: Seamless redirect after successful login

## Troubleshooting

### "Incorrect password" error
- Check for typos in password
- Verify `secrets.toml` file exists and is formatted correctly
- Restart Streamlit app after changing secrets

### Password not working on Streamlit Cloud
- Ensure you set `app_password` in Cloud Secrets (not locally)
- Wait 10-20 seconds for app to restart after saving secrets
- Check Cloud logs for any error messages

### Can't access secrets file
- File should be at: `.streamlit/secrets.toml`
- Check file permissions: `chmod 600 .streamlit/secrets.toml`
- Ensure `.streamlit` directory exists

## Upgrading Authentication

This simple password auth is great for getting started. For production, consider:

1. **Multi-user with roles**: Different passwords for different users
2. **OAuth (Google/GitHub)**: Professional social login
3. **JWT with FastAPI**: Full integration with your backend
4. **2FA**: Extra security layer with TOTP codes

See `docs/AUTHENTICATION_UPGRADE.md` for implementation guides.

## Default Credentials

⚠️ **IMPORTANT**: The default password (`trading2024`) is for **local development only**. Always set a custom password in production!

**Local Dev Default:**
- Password: `trading2024`

**Production:**
- Set via Streamlit Cloud Secrets
- Minimum 12 characters recommended
