# Setup Wizard Guide

## Overview
The MAFA Setup Wizard is your step-by-step guide to configuring MAFA for optimal apartment searching. This interactive tool ensures you don't miss any important settings and helps you get the best results from your apartment hunt.

---

**Last Updated:** November 19, 2025  
**Version:** 1.0.0  
**Maintainer:** MAFA User Experience Team  
**Estimated Reading Time:** 10-15 minutes

---

## Starting the Setup Wizard

### Access Methods
1. **First Launch**: Automatically appears when you first access MAFA
2. **Dashboard Menu**: Click "Setup Wizard" in the main navigation
3. **Settings Page**: Click "Reconfigure" in the Settings section
4. **Direct URL**: Navigate to `http://localhost:8080/setup`

### Wizard Overview
- **4 Main Steps**: Personal Info, Search Preferences, Notifications, Review & Activate
- **Progress Indicator**: Shows your completion status
- **Navigation**: Previous/Next buttons to move between steps
- **Auto-Save**: Settings are saved automatically as you progress
- **Real-time Validation**: Immediate feedback on field requirements

---

## Step 1: Personal Information

### Why This Matters
Your personal information helps generate appropriate application messages and ensures MAFA can match you with suitable apartments.

### Required Fields

#### Basic Information
```
Full Name *
- How you want your name to appear on applications
- Should match your ID/documents exactly
- Example: "Max Mustermann"

Email Address *
- Primary email for notifications
- This is where you'll receive apartment alerts
- Should be professional and frequently checked
- Example: "max.mustermann@email.com"

Phone Number
- International format preferred
- Include country code for German numbers
- Example: "+49 123 456 789"

Occupation *
- Your current profession
- Used to match with employer-friendly landlords
- Example: "Software Developer"

Monthly Income (Gross) *
- Your gross monthly income in EUR
- Used to determine suitable rent ranges
- Must be realistic for Munich market
- Example: "4500"
```

#### Household Details
```
Number of Occupants *
- Total people who will live in the apartment
- Includes yourself and all others
- Affects apartment size requirements
- Example: "2" (for couple)

Employer Name
- Current employer (optional)
- May help with certain applications
- Example: "Tech Innovations GmbH"
```

### Optional Personalization

#### Application Introduction
Write a brief introduction that will be included with your applications:

```
Example Introduction:
"I am a reliable and professional tenant looking for a modern 
apartment in Munich. I work in the tech industry and have a 
stable income. I value clean, quiet living spaces and am 
looking to establish long-term tenancy. I have excellent 
references from previous landlords and maintain properties 
with care."
```

### Validation Rules
- **Email**: Must be valid email format
- **Phone**: German mobile/landline or international format
- **Income**: Must be reasonable for Munich market (€1500-8000)
- **Name**: 2-50 characters, letters and basic punctuation only

### Tips for Success
- **Be Honest**: Accurate information leads to better matches
- **Use Professional Email**: Avoid nicknames or unprofessional addresses
- **Realistic Income**: Helps prevent unsuitable apartment suggestions
- **Complete Introduction**: Shows you're a serious applicant

---

## Step 2: Search Preferences

### Apartment Requirements

#### Budget Range
```
Maximum Rent: €1500 *
- Set your absolute ceiling for rent
- Should be 30-35% of gross income for comfort
- Include utilities in your calculations
- Consider rent increases over time

Minimum Rent: €800
- Optional: set a minimum to avoid very cheap, poor quality options
- Helps filter out potentially problematic listings
```

#### Room Requirements
```
Minimum Rooms: 2 *
- Essential for your living situation
- Consider guest room/office needs
- Factor in common areas in shared apartments

Maximum Rooms: 3
- Optional: set upper limit to focus search
- Avoids overly large, expensive apartments

Room Type Preference:
- Any (default)
- Open plan preferred
- Separate bedrooms required
- Prefer loft-style
```

#### Size Requirements
```
Minimum Size: 45 sqm
- Essential for comfortable living
- Consider storage and furniture needs
- Factor in common areas

Maximum Size: 80 sqm
- Optional upper limit to control costs
- Consider maintenance and heating costs
```

### Location Preferences

#### Munich Districts
Select districts you want to live in:

```
Highly Desirable:
✓ Schwabing - Central, vibrant, good transport
✓ Maxvorstadt - University area, cafes, culture
✓ Glockenbachviertel - Trendy, nightlife, central
✓ Bogenhausen - Upscale, family-friendly
✓ Haidhausen - Authentic, good restaurants

Desirable:
✓ Neuhausen - Good value, residential
✓ Sendling - Green, family-friendly
✓ Laim - Good transport links, affordable
✓ Westend - Central, mixed development
✓ Nymphenburg - Palace area, upscale

Consider:
✓ Moosach - Affordable, improving area
✓ Neuperlach - Large development, family-focused
✓ Pasing - Good transport, developing area

Avoid:
✗ Some industrial areas
✗ Areas with poor transport links
✗ High-crime neighborhoods
```

#### Transport & Convenience
```
Public Transport Priority:
- High (within 5 minutes walk to U-Bahn/S-Bahn)
- Medium (within 10 minutes walk)
- Low (further but good bus connections)

Essential Amenities (within walking distance):
✓ Supermarket (Rewe, Edeka, etc.)
✓ Bank/ATM
✓ Pharmacy
✓ Restaurant/Cafe

Nice to Have:
✓ Gym/Fitness center
✓ Park/Green space
✓ Shopping street
✓ Cultural venues
```

### Move-in Timeline

#### Flexibility Options
```
Earliest Move-in Date: 2025-02-01 *
- When you can realistically move in
- Consider notice periods from current place
- Factor in time for apartment hunting

Latest Move-in Date: 2025-04-30 *
- Absolute deadline for move-in
- Consider lease start dates
- Have backup options ready

Flexibility: ±2 weeks
- How flexible you are on exact dates
- Helps match with landlord timelines
- Consider temporary accommodation options
```

### Property Preferences

#### Apartment Features
```
Furnished Preference:
- Unfurnished (most common, allows personalization)
- Partially furnished
- Fully furnished
- No preference

Essential Features:
☐ Balcony (very desirable in Munich)
☐ Elevator (important for upper floors)
☐ Parking space
☐ Pet-friendly (if you have pets)

Nice to Have:
☐ Garden access
☐ Modern kitchen
☐ High-speed internet ready
☐ In-unit laundry
☐ Storage space
☐ Air conditioning (rare but valuable)

Deal Breakers:
☐ No heating (but very rare in Munich)
☐ Ground floor (security/safety concerns)
☐ No internet infrastructure
☐ Poor building condition
```

#### Building & Neighborhood
```
Building Type Preference:
- Modern apartment building
- Traditional Altbau (character buildings)
- Mixed-use building
- House conversion
- No preference

Neighborhood Character:
- Quiet residential
- Vibrant nightlife area
- Family-friendly
- Young professional area
- Student area (avoid if not student)

Noise Tolerance:
- Very low (no street noise)
- Low (quiet hours respected)
- Medium (some urban noise OK)
- High (don't mind lively areas)
```

---

## Step 3: Notification Setup

### Notification Channels

#### Email Notifications
Email is the most reliable and comprehensive notification method.

```
Email Settings:
✓ Enable email notifications

Sender Address: notifications@mafa.app
(automatically configured)

Notification Frequency:
- Immediate: Get alerts as soon as contacts found
- Hourly digest: Summary every hour
- Daily digest: Summary once per day
- Weekly report: Weekly summary and insights

Quiet Hours:
✓ Enable quiet hours
22:00 - 08:00 (no notifications during sleep hours)
Timezone: Europe/Berlin

Email Content:
✓ Include apartment details
✓ Include contact information
✓ Include direct links to listings
✓ Include search criteria that matched
```

#### Discord Integration
Great for real-time community sharing and mobile notifications.

```
Discord Settings:
☐ Enable Discord notifications

Webhook URL: [Your Discord webhook]
Get this from: Discord Server Settings > Integrations > Webhooks

Notification Style:
- Simple: Just contact info and link
- Detailed: Full apartment details with images
- Embed: Rich embed format with formatting

Channel Mentions:
☐ Mention @everyone for urgent listings
☐ Include apartment photos in embeds

Message Frequency:
- Same as email settings
- Can be configured separately
```

#### Telegram Integration
Perfect for direct mobile notifications with rich formatting.

```
Telegram Settings:
☐ Enable Telegram notifications

Bot Token: [Your bot token]
Get this from: @BotFather on Telegram

Chat ID: [Your chat ID]
Find this by messaging your bot and visiting:
https://api.telegram.org/bot[TOKEN]/getUpdates

Message Format:
- Text: Simple text format
- HTML: Rich formatting with links
- Markdown: Formatted text with styling

Include Photos:
☐ Send apartment photos when available
☐ Resize large images automatically
```

### Notification Rules

#### Contact Quality Levels
```
High Quality Contacts (Confidence ≥ 0.8):
- Immediate notification via all enabled channels
- Include all available details
- Mark as "Priority" in subject lines

Medium Quality Contacts (Confidence 0.5-0.8):
- Standard notification cadence
- Include summary details
- Allow batch processing

Low Quality Contacts (Confidence < 0.5):
- Include in daily/weekly digests only
- Basic information only
- Archive automatically after 7 days
```

#### Search Status Updates
```
Search Progress Notifications:
✓ When search starts
✓ When search completes
✓ If search encounters errors
✓ Daily summary of search activity

System Health Notifications:
✓ When system goes down
✓ When services are restored
✓ Weekly system performance report
✓ Monthly usage statistics
```

---

## Step 4: Review & Activate

### Configuration Summary

#### Personal Information Review
Review all your personal details for accuracy:

```
Personal Profile:
Name: Max Mustermann
Email: max.mustermann@email.com
Phone: +49 123 456 789
Occupation: Software Developer
Income: €4500/month
Occupants: 1 person
Employer: Tech Innovations GmbH
```

#### Search Criteria Review
Verify your apartment search parameters:

```
Search Criteria:
Budget: €800 - €1500
Rooms: 2 - 3 rooms
Size: 45 - 80 sqm
Districts: Schwabing, Maxvorstadt, Glockenbachviertel
Move-in: Feb 1 - Apr 30, 2025
Features: Balcony, elevator, pet-friendly
```

#### Notification Settings Review
Confirm your notification preferences:

```
Notifications:
Email: ✓ Enabled (immediate + quiet hours)
Discord: ✓ Enabled (detailed embeds)
Telegram: ✗ Disabled
Quiet Hours: 22:00 - 08:00
Frequency: Immediate for high quality
```

### System Validation

#### Pre-Activation Checks
MAFA performs automatic validation before activation:

```
✓ Configuration validation complete
✓ Email settings tested successfully
✓ Search criteria validation passed
✓ Database connection established
✓ Notification channels ready
✓ System health check passed
```

#### Test Notifications
Send a test notification to verify everything works:

```
Test Email Sent: ✓ Success
Test Discord: ✓ Success  
Test Telegram: ✗ Skipped (not configured)

All systems ready for activation!
```

### Activation Process

#### Final Steps
1. **Review Configuration**: Double-check all settings
2. **Run Test Search**: Optional: Run immediate test search
3. **Enable Automation**: Turn on automated searching
4. **Start Monitoring**: Begin 24/7 apartment monitoring

#### What Happens Next
```
Immediate Actions:
- First search starts within 5 minutes
- You'll receive confirmation notification
- Dashboard shows active search status
- Contact discovery begins

First Hour:
- Comprehensive search across all sources
- Contact extraction from recent listings
- Initial notification if quality contacts found
- System optimization based on results

First Day:
- Multiple automated searches completed
- Contact database populated
- Performance metrics available
- Notification preferences refined
```

---

## Advanced Setup Options

### Custom Search Schedules

#### Advanced Timing
```
Search Frequency Options:
- Every 30 minutes (aggressive, may trigger rate limits)
- Every 2 hours (recommended for most users)
- Every 6 hours (conservative approach)
- Daily (light monitoring)

Custom Schedule:
Set specific times for searches:
- 06:00 - Early morning listings
- 12:00 - Midday new postings
- 18:00 - Evening additions
- 00:00 - Late night listings

Dynamic Frequency:
- Increase frequency during active hunting periods
- Reduce during vacation/away periods
- Automatically adjust based on market activity
```

### Filtering & Exclusions

#### Advanced Filters
```
Exclusion Filters:
- Exclude listings > X days old
- Exclude properties from specific landlords
- Exclude certain apartment types
- Exclude listings without required features

Quality Filters:
- Minimum listing quality score
- Maximum days since posting
- Require specific contact methods
- Exclude incomplete listings

Geographic Refinements:
- Maximum distance from public transport
- Avoid construction zones
- Stay within specific postal codes
- Proximity to work/school location
```

### Integration Options

#### Calendar Integration
```
Viewing Scheduling:
- Sync with Google Calendar
- Sync with Outlook
- Automatic reminder notifications
- Conflict detection and resolution
```

#### CRM Integration
```
Contact Management:
- Export to external CRM systems
- Sync with contact management apps
- Automatic contact categorization
- Response tracking and follow-up
```

---

## Setup Wizard Tips

### First-Time Users

#### Getting Started Quickly
- **Use Defaults**: Start with recommended settings, optimize later
- **Less is More**: Begin with basic criteria, expand gradually
- **Test Early**: Run test searches to verify functionality
- **Check Daily**: Monitor first day results closely

#### Common Mistakes to Avoid
- **Too Restrictive**: Don't make criteria too narrow initially
- **Ignoring Notifications**: Configure at least one reliable channel
- **Unrealistic Budget**: Set achievable rent expectations
- **Missing Quiet Hours**: Protect your sleep with notification scheduling

### Power User Optimization

#### Advanced Configuration
- **Multiple Criteria Sets**: Different profiles for various situations
- **Seasonal Adjustments**: Modify search during peak/low seasons
- **Performance Monitoring**: Track and optimize search effectiveness
- **Integration Setup**: Connect with your existing workflow tools

#### Efficiency Tips
- **Bulk Operations**: Use bulk actions for contact management
- **Saved Searches**: Create multiple search profiles
- **Smart Filters**: Use intelligent filtering based on results
- **Mobile Optimization**: Configure for mobile-first usage

### Troubleshooting Setup Issues

#### Common Problems
```
Email Not Working:
- Check spam folder for test emails
- Verify SMTP settings
- Try different email provider
- Check firewall/network settings

Search Returns No Results:
- Verify search criteria aren't too restrictive
- Check that providers are enabled
- Test manual search on source websites
- Review error logs for issues

Notifications Not Arriving:
- Check quiet hours settings
- Verify notification channel configuration
- Test each channel individually
- Review notification rules
```

#### Getting Help
- **Validation Messages**: Follow detailed validation feedback
- **Test Functions**: Use built-in test features
- **Documentation Links**: Access help from within wizard
- **Support Resources**: Access community and support channels

---

## Post-Setup Optimization

### Week 1: Learning Phase
- **Monitor Results**: Check search effectiveness daily
- **Adjust Criteria**: Refine based on initial results
- **Verify Notifications**: Ensure all channels work properly
- **Contact Quality**: Assess quality of discovered contacts

### Week 2-4: Optimization Phase
- **Performance Analysis**: Review search metrics
- **Criteria Refinement**: Adjust based on market response
- **Notification Tuning**: Optimize frequency and timing
- **Feature Exploration**: Try advanced features

### Month 2+: Mastery Phase
- **Advanced Usage**: Utilize all available features
- **Custom Optimization**: Create personalized workflows
- **Integration**: Connect with external tools
- **Community**: Share experiences and tips

---

## Related Documentation

- [User Guide Overview](overview.md) - Complete user guide
- [Dashboard Guide](dashboard.md) - Interface and features
- [Configuration Reference](../getting-started/configuration.md) - Detailed settings
- [Troubleshooting Guide](troubleshooting.md) - Problem resolution
- [Quick Start Guide](../getting-started/quick-start.md) - Fast setup process

---

**Need Help?** If you encounter issues during setup, check our [FAQ](https://github.com/your-org/mafa/wiki/Setup-FAQ) or visit the [Community Forum](https://github.com/your-org/mafa/discussions).