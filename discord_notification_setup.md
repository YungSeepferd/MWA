# Discord Notification Setup Guide

## Issue Summary
The Discord notification system is configured but not functional because the webhook URL in `config.json` is still a placeholder.

## Current Configuration Status
- ✅ Discord notifier code is working correctly
- ✅ Configuration validation is in place
- ❌ Discord webhook URL is not configured (placeholder detected)
- ❌ Notifications cannot be sent to Discord

## Steps to Fix Discord Notifications

### 1. Create a Discord Webhook

1. **Go to your Discord server**
   - Open Discord and navigate to your server

2. **Access Server Settings**
   - Click on the server name → Server Settings → Integrations

3. **Create Webhook**
   - Click on "Webhooks" → "New Webhook"
   - Give it a name (e.g., "MWA Notifications")
   - Select the channel where notifications should appear
   - Copy the Webhook URL

### 2. Update Configuration

**Option A: Update config.json directly**
```json
{
  "notification": {
    "provider": "discord",
    "discord_webhook_url": "https://discord.com/api/webhooks/YOUR_ACTUAL_WEBHOOK_ID/YOUR_ACTUAL_WEBHOOK_TOKEN"
  }
}
```

**Option B: Use environment variables**
Create a `.env` file in the project root:
```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_ACTUAL_WEBHOOK_ID/YOUR_ACTUAL_WEBHOOK_TOKEN
```

### 3. Test the Configuration

Run the test script to verify the setup:
```bash
python test_discord_notifier.py
```

### 4. Alternative Solutions

If you don't want to use Discord notifications, you can:

**Option A: Switch to another provider**
Update `config.json` to use a different notification provider:
```json
{
  "notification": {
    "provider": "telegram",
    "telegram_bot_token": "YOUR_BOT_TOKEN",
    "telegram_chat_id": "YOUR_CHAT_ID"
  }
}
```

**Option B: Disable notifications temporarily**
Comment out or remove the notification section in `config.json`:
```json
// "notification": {
//   "provider": "discord",
//   "discord_webhook_url": "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"
// }
```

## Webhook URL Format
A valid Discord webhook URL should look like:
```
https://discord.com/api/webhooks/123456789012345678/abcdefghijklmnopqrstuvwxyz1234567890abcdefghijkl
```

## Security Considerations
- Keep your webhook URL private
- Never commit real webhook URLs to version control
- Use environment variables for production deployments
- Consider using a secrets management system

## Testing the Fix

After updating the configuration:

1. **Restart the application**
   ```bash
   cd api && python main.py
   ```

2. **Test with a dry run**
   ```bash
   python run.py --dry-run
   ```

3. **Check logs for notification attempts**
   - Look for "Discord notifier initialized successfully"
   - Check for any webhook-related errors

## Troubleshooting

### Common Issues

1. **"Invalid Webhook" Error**
   - Verify the webhook URL is correct
   - Check if the webhook still exists in Discord
   - Ensure the webhook has proper permissions

2. **"Rate Limited" Error**
   - Discord has rate limits for webhooks
   - Reduce notification frequency if needed

3. **"Connection Failed" Error**
   - Check internet connectivity
   - Verify firewall/proxy settings
   - Test webhook with a simple curl command

### Debug Commands

Test webhook manually:
```bash
curl -X POST -H "Content-Type: application/json" -d '{"content":"Test message"}' YOUR_WEBHOOK_URL
```

## Next Steps

Once Discord notifications are working:
1. Test with actual property listings
2. Verify notifications appear in the correct Discord channel
3. Monitor for any delivery issues
4. Consider adding notification templates for better formatting

## Support

If you continue to experience issues:
1. Check the application logs for detailed error messages
2. Verify Discord server permissions
3. Test with a different webhook URL
4. Consider using a different notification provider