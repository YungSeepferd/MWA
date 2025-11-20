# Quick Start Guide

## Overview
Get MAFA up and running in 5 minutes with this streamlined setup guide. Perfect for new users who want to start searching for apartments immediately.

---

**Last Updated:** November 19, 2025  
**Version:** 1.0.0  
**Maintainer:** MAFA Development Team  
**Estimated Reading Time:** 5 minutes

---

## Prerequisites Check
Before starting, ensure you have:
- [ ] MAFA installed (see [Installation Guide](./installation.md))
- [ ] Access to web browser
- [ ] 10 minutes of your time
- [ ] Basic information about your apartment preferences

---

## 5-Minute Setup Process

### Step 1: Access MAFA Dashboard (30 seconds)

1. **Open your web browser**
   - Navigate to `http://localhost:8080` (local installation)
   - Or access your deployed instance URL

2. **Verify system status**
   - Check that the dashboard loads without errors
   - Look for green status indicators
   - If you see any red warnings, refer to [Troubleshooting](../user-guide/troubleshooting.md)

**Expected Result:** ✅ Dashboard loads successfully with status indicators

---

### Step 2: Run Setup Wizard (2 minutes)

1. **Click "Get Started" or "Setup Wizard"**
   - This launches the guided setup process

2. **Personal Information** (30 seconds)
   ```
   Required Fields:
   - Full Name: Your name as it appears on applications
   - Email Address: Where you want to receive notifications
   - Monthly Income: Gross monthly income
   - Occupation: Your profession
   - Number of Occupants: How many people will live in the apartment
   ```

3. **Search Preferences** (45 seconds)
   ```
   Required Settings:
   - Maximum Rent: Your budget ceiling
   - Minimum Rooms: Number of rooms you need
   - Preferred Districts: Select Munich districts you prefer
   - Move-in Date: When you plan to move
   ```

4. **Notification Setup** (30 seconds)
   ```
   Choose Your Method:
   - Email: Simple email notifications
   - Discord: Send to Discord channel
   - Telegram: Direct messages via Telegram bot
   ```

5. **Review & Activate** (15 seconds)
   - Review your settings summary
   - Click "Activate Search" to start

**Expected Result:** ✅ Setup wizard completes with all fields filled and search activated

---

### Step 3: Verify First Search (1 minute)

1. **Dashboard Overview**
   - Check that your configuration is saved
   - Look for active search status
   - Verify notification settings

2. **Manual Test Search** (Optional)
   - Click "Start Search Now" button
   - Wait for initial results (30-60 seconds)
   - Check that new contacts are discovered

3. **Review Test Results**
   - Navigate to "Contacts" section
   - See if any contacts were found
   - Approve or reject a test contact

**Expected Result:** ✅ Search runs successfully and discovers at least one contact

---

### Step 4: Configure Automation (1 minute)

1. **Set Up Regular Searches**
   - Go to Settings → Automation
   - Choose search frequency:
     - **Every 2 hours**: Aggressive search (recommended for active hunting)
     - **Daily**: Moderate approach (recommended for most users)
     - **Weekly**: Light monitoring

2. **Configure Notification Timing**
   - Set "Quiet Hours": When NOT to send notifications
   - Example: 22:00 - 08:00 (evening/night)
   - Choose notification frequency (immediate, digest, hourly)

**Expected Result:** ✅ Automated searches scheduled and notification timing configured

---

### Step 5: Daily Monitoring Setup (30 seconds)

1. **Bookmark Important Pages**
   - Dashboard: `http://localhost:8080`
   - Contacts Review: `http://localhost:8080/contacts`
   - Settings: `http://localhost:8080/settings`

2. **Set Up Mobile Access** (Optional)
   - If using on mobile, bookmark the dashboard
   - Or install as Progressive Web App (PWA) if available

**Expected Result:** ✅ Easy access points bookmarked for daily use

---

## What Happens Next

### Immediate (First Hour)
- MAFA will perform its first comprehensive search
- You'll receive notifications for any newly discovered listings
- System will learn and optimize search parameters

### First Day
- Multiple automated searches will run
- Contact database will start populating
- You'll receive email summaries of activity

### First Week
- System will have learned your preferences
- Search accuracy will improve
- You'll have a good collection of contacts

### First Month
- Comprehensive apartment search database
- Optimized notification preferences
- Refined search criteria based on results

---

## Daily Workflow

### Morning Routine (2 minutes)
1. **Check Dashboard**
   - Open dashboard
   - Review overnight activity
   - Check new contacts found

2. **Review New Contacts** (as needed)
   - Click "Review Contacts"
   - Quick approve/reject based on quality
   - Use bulk actions for efficiency

### Evening Review (1 minute)
1. **Check Daily Summary**
   - Review statistics for the day
   - See total contacts found
   - Check system performance

2. **Adjust if Needed**
   - Modify search criteria if results aren't relevant
   - Update notification settings if getting too many/few alerts

---

## Pro Tips for Success

### Maximize Contact Quality
- **Be Specific**: Clearly define your apartment preferences
- **Use Districts**: Select specific Munich districts you actually want to live in
- **Price Range**: Set realistic budget boundaries
- **Timeline**: Be honest about your move-in date

### Optimize Notifications
- **Start Conservative**: Begin with immediate notifications, then adjust
- **Use Quiet Hours**: Set appropriate times to avoid late-night notifications
- **Test All Methods**: Try different notification channels to see what works best

### Improve Search Results
- **Regular Reviews**: Check and adjust search criteria weekly
- **Learn from Results**: Notice which searches find the best contacts
- **Feedback Loop**: Approve/reject contacts to train the system

---

## Common Quick Fixes

### No Contacts Found
```
Check:
- Search criteria aren't too restrictive
- At least one provider is enabled
- System status shows "Running"
- Recent searches have completed
```

### Too Many Notifications
```
Solutions:
- Increase confidence threshold
- Set up quiet hours
- Switch to digest mode
- Refine search criteria
```

### Dashboard Not Loading
```
Steps:
- Check system status at http://localhost:8000/health
- Restart MAFA services
- Check browser console for errors
- Clear browser cache
```

### Search Not Running
```
Verify:
- Scheduler is running (Settings → System)
- At least one search job is active
- Database permissions are correct
- Log files for error messages
```

---

## Next Steps

After completing the quick start:

### Immediate Actions
1. **Customize Settings**: Fine-tune your preferences in [Configuration](./configuration.md)
2. **Learn Features**: Explore all dashboard features in [User Guide](../user-guide/overview.md)
3. **Set Up Monitoring**: Understand system health in [Dashboard Guide](../user-guide/dashboard.md)

### Ongoing Optimization
1. **Weekly Reviews**: Adjust search criteria based on results
2. **Monthly Optimization**: Review and update notification settings
3. **Performance Monitoring**: Track search effectiveness over time

### Advanced Usage
1. **Development Setup**: For developers, see [Development Guide](../developer-guide/development-setup.md)
2. **Production Deployment**: For server deployment, see [Operations Guide](../operations/deployment.md)
3. **API Integration**: For custom integrations, see [API Integration](../developer-guide/api/integration-guide.md)

---

## Related Documentation

- [Installation Guide](./installation.md) - Complete setup instructions
- [Configuration Reference](./configuration.md) - Detailed configuration options
- [User Guide Overview](../user-guide/overview.md) - Complete user documentation
- [Troubleshooting Guide](../user-guide/troubleshooting.md) - Solve common issues
- [Architecture Overview](../architecture/system-overview.md) - Understand the system

---

**Need Help?** If you encounter issues during quick start, check our [Troubleshooting Guide](../user-guide/troubleshooting.md) or visit our [Support Forum](https://github.com/your-org/mafa/discussions).