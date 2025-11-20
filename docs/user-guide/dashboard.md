# Dashboard Guide

## Overview
The MAFA Dashboard is your central command center for apartment hunting. This comprehensive guide covers all dashboard features, real-time monitoring, contact management, and optimization tools to maximize your apartment search success.

---

**Last Updated:** November 19, 2025  
**Version:** 1.0.0  
**Maintainer:** MAFA User Experience Team  
**Estimated Reading Time:** 15-20 minutes

---

## Dashboard Access & Navigation

### Accessing the Dashboard
- **Local Installation**: `http://localhost:8080`
- **Deployed Version**: Your custom domain or server URL
- **Mobile Access**: Dashboard is fully responsive for mobile devices
- **Direct Links**: Bookmark specific sections for quick access

### Main Navigation Structure
```
Dashboard (Main)
├── Overview (Status & Quick Actions)
├── Contacts (Review & Management)
├── Search (Active Searches & Results)
├── Analytics (Performance & Insights)
├── Settings (Configuration)
└── Help (Documentation & Support)
```

### Navigation Tips
- **Breadcrumb Navigation**: Always shows your current location
- **Quick Actions**: Prominent buttons for common tasks
- **Real-time Updates**: Dashboard refreshes automatically
- **Mobile Menu**: Hamburger menu on smaller screens
- **Keyboard Shortcuts**: Use ? for help, / for search

---

## Main Dashboard Overview

### Status Cards Section

#### System Health Card
Real-time system status with color-coded indicators:

```
🟢 All Systems Operational
├── API Status: Connected
├── Database: Healthy
├── Search Engine: Active
└── Notifications: Ready

Last Check: 2 minutes ago
Auto-refresh: Every 30 seconds
```

**Status Indicators:**
- 🟢 **Green**: Everything working normally
- 🟡 **Yellow**: Minor issues, but functional
- 🔴 **Red**: Critical issues requiring attention
- ⚫ **Gray**: System offline or disconnected

#### Active Searches Card
Current search activity and progress:

```
Active Searches: 2
├── ImmoScout24: Running (Last: 5 min ago)
├── WG-Gesucht: Idle (Next: 2 hours)

Progress Today:
├── Searches Completed: 24
├── New Listings Found: 12
├── Contacts Discovered: 8
└── Quality Score: 8.5/10
```

#### Contact Queue Card
Pending contacts requiring review:

```
Pending Review: 5 contacts
├── High Quality (≥0.8): 2 contacts
├── Medium Quality (0.5-0.8): 2 contacts
└── Low Quality (<0.5): 1 contact

Quick Actions:
[Review All] [Bulk Approve] [Export]
```

#### Notification Status Card
Recent notifications and delivery status:

```
Today's Notifications: 12
├── Email: 8 delivered, 0 failed
├── Discord: 4 delivered, 0 failed
└── Telegram: 0 (disabled)

Recent Activity:
- 14:30 - High quality contact found
- 12:15 - Search completed successfully
- 09:45 - Daily digest sent
```

### Quick Actions Panel

#### Primary Actions
```
[🚀 Start New Search] [📧 Review Contacts] [⚙️ Settings] [📊 Analytics]
```

#### Secondary Actions
```
[📋 Export Data] [🔄 Refresh All] [📱 Test Notifications] [❓ Help]
```

#### Emergency Actions
```
[⏸️ Pause Search] [🚨 Emergency Stop] [🔧 System Reset]
```

### Recent Activity Feed

#### Activity Stream
Real-time feed of system activities:

```
14:35 🆕 New Contact Found
   Contact: max.schmidt@email.com (Confidence: 0.92)
   Apartment: 2-room apartment in Schwabing
   [View Details] [Contact Now]

14:32 ✅ Search Completed
   Source: ImmoScout24
   Results: 15 listings processed
   Duration: 2m 34s
   [View Results]

14:25 📧 Notification Sent
   Channel: Email
   Recipients: max.mustermann@email.com
   Subject: New apartment contact found
   [View Email]

14:20 🔍 Search Started
   Source: WG-Gesucht
   Criteria: 2-3 rooms, €800-1500, Maxvorstadt
   [Monitor Progress]
```

#### Activity Filters
Filter activity by type, time, or source:
- **All Activities** (default)
- **Searches Only**
- **Contacts Only**
- **Notifications Only**
- **System Events Only**

---

## Contact Review Interface

### Contact Cards Layout

#### Card Information Display
Each contact is presented in a detailed card format:

```
┌─────────────────────────────────────────────────────────────┐
│ [🖼️ Photo] Contact #1234                    [⭐ 0.92]     │
├─────────────────────────────────────────────────────────────┤
│ 📧 max.schmidt@email.com                              │
│ 📞 +49 176 12345678                                  │
│ 🏠 Apartment in Schwabing                              │
│ 💰 €1,200/month • 2 rooms • 65 sqm                    │
│ 📍 Move-in: 01.03.2025                               │
│ ⏰ Found: 5 minutes ago                               │
├─────────────────────────────────────────────────────────────┤
│ [👍 Approve] [👎 Reject] [📝 Edit] [🔗 View Listing]   │
└─────────────────────────────────────────────────────────────┘
```

#### Contact Quality Indicators
```
High Quality (⭐⭐⭐):
- Confidence score ≥ 0.8
- Multiple contact methods
- Complete apartment details
- Recent listing

Medium Quality (⭐⭐):
- Confidence score 0.5-0.8
- Single contact method
- Basic apartment info
- Older listing

Low Quality (⭐):
- Confidence score < 0.5
- Unclear contact info
- Incomplete details
- Possible spam
```

### Bulk Operations

#### Multi-Select Features
```
Selected: 3 contacts

Bulk Actions:
[👍 Approve All] [👎 Reject All] [📧 Email All] [📤 Export] [🏷️ Tag]
```

#### Selection Options
- **Select All**: Choose all visible contacts
- **Select High Quality**: Choose only high-confidence contacts
- **Select by Source**: Filter by apartment website
- **Custom Selection**: Manually select specific contacts

### Contact Details Modal

#### Detailed Information View
Click on any contact card to open detailed information:

```
Contact Details - #1234
┌─────────────────────────────────────────────────────────────┐
│ Apartment Information                                    │
├─────────────────────────────────────────────────────────────┤
│ Title: Moderne 2-Zimmer Wohnung                          │
│ Price: €1,200/month + €200 utilities                     │
│ Size: 65 sqm, 2 rooms, 2nd floor                        │
│ Address: Musterstraße 123, 80802 München                │
│ Provider: ImmoScout24                                    │
│ Listing URL: [View Original]                             │
├─────────────────────────────────────────────────────────────┤
│ Contact Information                                      │
├─────────────────────────────────────────────────────────────┤
│ Email: max.schmidt@email.com (verified)                  │
│ Phone: +49 176 12345678 (mobile)                        │
│ Confidence Score: 0.92/1.0                              │
│ Contact Methods: Email, Phone                            │
├─────────────────────────────────────────────────────────────┤
│ Discovery Information                                    │
├─────────────────────────────────────────────────────────────┤
│ Found: November 19, 2025 at 14:35                       │
│ Extraction Method: Email pattern + OCR                  │
│ Source Reliability: 0.95                                │
│ Validation Status: Valid email format                   │
├─────────────────────────────────────────────────────────────┤
│ Actions                                                  │
├─────────────────────────────────────────────────────────────┤
│ [📧 Send Email] [📞 Call] [🌐 View Listing] [📋 Copy]   │
│ [👍 Approve] [👎 Reject] [📝 Edit] [🗑️ Delete]         │
└─────────────────────────────────────────────────────────────┘
```

### Search and Filtering

#### Search Options
```
Search Contacts:
┌─────────────────────────────────────────────────────────────┐
│ 🔍 [Search by name, email, or address...]               │
│                                                         │
│ Filters:                                                │
│ • Quality: [All ▼]                                      │
│ • Source: [All ▼]                                       │
│ • Date: [Last 7 days ▼]                                 │
│ • Status: [All ▼]                                       │
│ • District: [All ▼]                                     │
│                                                         │
│ Sort by: [Date ▼] [Quality ▼] [Price ▼]               │
└─────────────────────────────────────────────────────────────┘
```

#### Advanced Filtering
- **Date Range**: Custom date ranges for discovery
- **Price Range**: Filter by apartment price
- **Room Count**: Filter by number of rooms
- **District**: Filter by Munich district
- **Contact Method**: Email, phone, or form-only
- **Quality Score**: Range of confidence scores
- **Status**: Approved, rejected, or pending

---

## Search Management

### Active Searches View

#### Search Status Dashboard
```
Active Searches (2/4 enabled):
┌─────────────────────────────────────────────────────────────┐
│ 🔍 ImmoScout24                      [🟢 Running]         │
│ Last Run: 5 minutes ago    Next Run: 2 hours              │
│ Results Today: 8 contacts  Quality: 8.7/10                │
│ [⏸️ Pause] [▶️ Run Now] [⚙️ Configure] [📊 Details]      │
├─────────────────────────────────────────────────────────────┤
│ 🔍 WG-Gesucht                      [⚫ Idle]             │
│ Last Run: 2 hours ago      Next Run: In 10 minutes        │
│ Results Today: 4 contacts   Quality: 7.8/10               │
│ [▶️ Enable] [⚙️ Configure] [📊 Details]                  │
├─────────────────────────────────────────────────────────────┤
│ 🔍 Manual Search                   [⏸️ Paused]           │
│ Manual trigger only                                         │
│ [▶️ Enable] [⚙️ Configure]                                │
└─────────────────────────────────────────────────────────────┘
```

### Search Configuration

#### Provider Settings
Each search provider can be configured independently:

```
ImmoScout24 Configuration:
┌─────────────────────────────────────────────────────────────┐
│ Enable Search: ☑️                                         │
│ Priority: 1 (highest)                                     │
│ Search Frequency: Every 2 hours                           │
│ Max Results: 50 per search                                │
│ Rate Limit: 100 requests/hour                             │
│ Delay Between Requests: 2 seconds                         │
├─────────────────────────────────────────────────────────────┤
│ Search Criteria:                                          │
│ • Districts: Schwabing, Maxvorstadt, Bogenhausen        │
│ • Price Range: €800 - €1500                              │
│ • Rooms: 2 - 3 rooms                                     │
│ • Size: 45 - 80 sqm                                      │
│ • Move-in: Feb - Apr 2025                                │
├─────────────────────────────────────────────────────────────┤
│ Advanced Options:                                         │
│ ☑️ Include shared apartments                              │
│ ☑️ Include furnished options                              │
│ ☑️ Exclude temporary housing                             │
│ Search Timeout: 60 seconds                               │
│ Retry Attempts: 3                                        │
└─────────────────────────────────────────────────────────────┘
```

### Search Results

#### Results Summary
```
Search Results - ImmoScout24 (Last Run)
Completed: 2 minutes ago | Duration: 3m 45s

Summary:
├── Listings Processed: 47
├── New Listings: 8
├── Duplicates Filtered: 12
├── Contacts Discovered: 8
└── High Quality Contacts: 3

Provider Performance:
├── Response Time: 1.2s average
├── Success Rate: 98%
└── Rate Limit Status: 45/100 used
```

#### Individual Results
Each search result shows detailed information:

```
┌─────────────────────────────────────────────────────────────┐
│ Search #45 - ImmoScout24                    [✅ Complete] │
├─────────────────────────────────────────────────────────────┤
│ Started: 14:32:15    Completed: 14:35:59   Duration: 3m44s │
│ Criteria: 2-3 rooms, €800-1500, Schwabing+Maxvorstadt     │
├─────────────────────────────────────────────────────────────┤
│ Results:                                                    │
│ • Total Listings: 47                                       │
│ • New Contacts: 8 (3 high quality)                        │
│ • Success Rate: 91%                                        │
├─────────────────────────────────────────────────────────────┤
│ New Contacts Found:                                        │
│ 1. max.schmidt@email.com (⭐ 0.92) - 2-room Schwabing      │
│ 2. anna.mueller@gmx.net (⭐ 0.88) - 3-room Maxvorstadt    │
│ 3. jan.petersen@web.de (⭐ 0.85) - 2-room Bogenhausen     │
│ [+ 5 more contacts]                                       │
├─────────────────────────────────────────────────────────────┤
│ [📊 View Details] [📧 Review Contacts] [🔄 Run Again]     │
└─────────────────────────────────────────────────────────────┘
```

---

## Analytics & Insights

### Performance Dashboard

#### Key Metrics Overview
```
Today's Performance:
┌─────────────────────────────────────────────────────────────┐
│ 📈 Searches: 24    📧 Contacts: 8    ⭐ Quality: 8.5/10   │
│ ⏱️ Avg Duration: 2m 34s    ✅ Success Rate: 96%           │
└─────────────────────────────────────────────────────────────┘

Week Summary:
┌─────────────────────────────────────────────────────────────┐
│ 📈 Searches: 156   📧 Contacts: 47   ⭐ Avg Quality: 8.2   │
│ 🏠 Apartments: 12   📱 Notifications: 34                   │
└─────────────────────────────────────────────────────────────┘
```

#### Charts & Visualizations

##### Contact Discovery Trends
```
Contact Discovery Over Time (Last 30 Days)
     15 ┤                                                    
     14 ┤    ●                                         ●    │
     13 ┤       ●                    ●                   │    
     12 ┤  ●        ●          ●           ●            │
     11 ┤              ●                                ● │
     10 ┤                  ●                               │
      9 ┤                     ● ●                         │
      8 ┤                        ●                        │
      7 ┤                           ●                     │
      6 ┤                              ●                 │
      5 ┤                                 ●              │
      4 ┤                                    ●          │
      3 ┤                                       ●       │
      2 ┤                                          ●    │
      1 ┤                                             ● │
         ─┬────┬────┬────┬────┬────┬────┬────┬────┬────┬─
          Nov 10 Nov 15 Nov 20 Nov 25 Nov 30 Dec 5  Dec 10 Dec 15

Best Day: Nov 20 (15 contacts)
Average: 8.2 contacts/day
Trend: ↗️ +12% improvement
```

##### Quality Score Distribution
```
Contact Quality Distribution (Last Week)
High Quality (≥0.8): 23 contacts (49%) ████████████████████
Medium Quality (0.5-0.8): 18 contacts (38%) ██████████████
Low Quality (<0.5): 6 contacts (13%) ██████

Overall Average Quality: 7.8/10
Target: 8.0/10
Status: 📈 Improving
```

##### Search Performance
```
Provider Performance Comparison (Last 7 Days)
                    Searches  Contacts  Quality  Success
ImmoScout24             45       23      8.9     98%
WG-Gesucht              38       15      8.1     96%
Manual Search            8        9      9.2    100%

Total Performance:
✅ Exceeding target quality (8.0/10)
✅ High success rate (97%)
✅ Balanced provider utilization
```

### Detailed Analytics

#### Contact Analysis
```
Contact Breakdown by Source:
• ImmoScout24: 23 contacts (49%) - High volume, good quality
• WG-Gesucht: 15 contacts (32%) - Moderate volume, good quality
• Manual Input: 9 contacts (19%) - Low volume, excellent quality

Contact Methods Discovered:
• Email addresses: 35 contacts (74%)
• Phone numbers: 28 contacts (60%)
• Contact forms: 12 contacts (26%)
• Multiple methods: 20 contacts (43%)

Quality Metrics:
• Average confidence: 0.78
• Validation success rate: 94%
• False positive rate: 6%
• Response rate estimate: 45%
```

#### Search Efficiency
```
Search Efficiency Analysis:
• Average search duration: 2m 34s
• Listings per search: 23
• Contact discovery rate: 34% (contacts/listings)
• Duplicate detection: 15% reduction
• System uptime: 99.8%

Optimization Opportunities:
→ Reduce search duration by 20% (currently 3m 45s max)
→ Increase WG-Gesucht frequency for more contacts
→ Implement smart search scheduling based on market activity
```

---

## Settings Interface

### Configuration Tabs

#### Personal Profile Tab
```
Personal Information:
┌─────────────────────────────────────────────────────────────┐
│ Full Name: Max Mustermann                         [Edit]   │
│ Email: max.mustermann@email.com                 [Edit]   │
│ Phone: +49 123 456 789                          [Edit]   │
│ Occupation: Software Developer                  [Edit]   │
│ Monthly Income: €4,500                          [Edit]   │
│ Occupants: 1                                    [Edit]   │
│                                                         │
│ [💾 Save Changes] [🔄 Reset to Defaults]                 │
└─────────────────────────────────────────────────────────────┘
```

#### Search Criteria Tab
```
Search Preferences:
┌─────────────────────────────────────────────────────────────┐
│ Price Range: €800 - €1500                        [Edit]   │
│ Rooms: 2 - 3 rooms                              [Edit]   │
│ Size: 45 - 80 sqm                               [Edit]   │
│ Districts: Schwabing, Maxvorstadt...           [Edit]   │
│ Move-in: Feb 1 - Apr 30, 2025                  [Edit]   │
│ Features: Balcony, Elevator, Pet-friendly      [Edit]   │
│                                                         │
│ [🎯 Preview Results] [💾 Save Changes]                     │
└─────────────────────────────────────────────────────────────┘
```

#### Notifications Tab
```
Notification Settings:
┌─────────────────────────────────────────────────────────────┐
│ Email: max.mustermann@email.com                [Test]    │
│   Status: ✅ Active     Last Test: 2 hours ago            │
│   Frequency: Immediate    Quiet Hours: 22:00-08:00       │
│                                                         │
│ Discord: #apartments-channel                    [Test]   │
│   Status: ✅ Active     Last Test: 1 day ago             │
│   Webhook: Connected      Messages: 34 today            │
│                                                         │
│ Telegram: @MaxMAFAbot                          [Test]   │
│   Status: ❌ Disabled                                     │
│                                                         │
│ [📱 Add Channel] [🔧 Configure] [💾 Save]                 │
└─────────────────────────────────────────────────────────────┘
```

### System Settings

#### Advanced Configuration
```
System Preferences:
┌─────────────────────────────────────────────────────────────┐
│ Search Frequency: Every 2 hours                          │
│ Max Concurrent Searches: 2                               │
│ Contact Confidence Threshold: 0.7                        │
│ Notification Quiet Hours: 22:00 - 08:00                  │
│ Auto-approve High Quality: Yes (≥0.9)                    │
│ Data Retention: 90 days                                  │
├─────────────────────────────────────────────────────────────┤
│ Performance Settings:                                    │
│ • Enable caching: Yes                                    │
│ • Optimize for speed: Balanced                           │
│ • Background processing: Enabled                         │
│ • Real-time updates: Enabled                             │
├─────────────────────────────────────────────────────────────┤
│ [🔧 Advanced Settings] [💾 Save] [🔄 Reset]                │
└─────────────────────────────────────────────────────────────┘
```

---

## Mobile Dashboard

### Mobile-Optimized Interface

#### Touch-Friendly Design
```
┌─────────────────────────────┐
│ ☰ MAFA           📱 ⚙️   │
├─────────────────────────────┤
│                             │
│  🟢 All Systems             │
│  🔍 2 Active Searches       │
│  📧 5 Contacts Review       │
│                             │
│  [📊 Dashboard]             │
│                             │
│  🔄 Last Update: 2 min ago  │
│                             │
└─────────────────────────────┘
```

#### Mobile Navigation
- **Slide-out Menu**: Access all sections with hamburger menu
- **Touch Gestures**: Swipe to navigate between sections
- **Responsive Cards**: Cards stack and adapt to screen size
- **Quick Actions**: Large touch targets for common actions

### Mobile-Specific Features

#### Swipe Actions on Contact Cards
```
Contact Card Swipe Actions:
← Swipe Left: Quick Reject
→ Swipe Right: Quick Approve
↑ Swipe Up: Mark as Favorite
↓ Swipe Down: More Options
```

#### Mobile Dashboard Widgets
- **Quick Stats**: Key metrics at a glance
- **Recent Activity**: Latest system events
- **Pending Actions**: Contacts needing review
- **Search Status**: Current search progress

---

## Keyboard Shortcuts

### Global Shortcuts
```
/         Focus search box
?         Show help overlay
Esc       Close modal/dropdown
Ctrl+R    Refresh dashboard
Ctrl+S    Save current settings
G then H  Go to dashboard
G then C  Go to contacts
G then S  Go to settings
```

### Contact Management
```
A         Approve selected contact
R         Reject selected contact
E         Edit contact
D         Delete contact
F         Toggle favorite
Space     Select/deselect contact
Ctrl+A    Select all contacts
Enter     View contact details
```

### Search Management
```
S         Start new search
P         Pause current search
Ctrl+Enter Run search immediately
T         Test search configuration
```

---

## Troubleshooting Dashboard Issues

### Common Issues

#### Dashboard Not Loading
```
Symptoms: Blank screen or loading spinner
Solutions:
1. Check system health at /health endpoint
2. Verify database connection
3. Clear browser cache and cookies
4. Check browser console for JavaScript errors
5. Restart MAFA services
```

#### Real-time Updates Not Working
```
Symptoms: Dashboard doesn't refresh automatically
Solutions:
1. Check WebSocket connection status
2. Verify browser supports WebSocket
3. Check firewall/proxy settings
4. Disable browser extensions
5. Try incognito/private mode
```

#### Slow Performance
```
Symptoms: Dashboard loads slowly or feels sluggish
Solutions:
1. Check system resources (CPU, memory)
2. Reduce number of displayed items
3. Disable animations/transitions
4. Clear browser cache
5. Use a different browser
```

### Performance Optimization

#### Dashboard Speed Tips
- **Limit Results**: Use filters to reduce displayed items
- **Disable Animations**: Turn off visual effects for speed
- **Clear Cache**: Regularly clear browser cache
- **Use Modern Browser**: Chrome, Firefox, or Safari recommended
- **Check Network**: Ensure stable internet connection

#### Data Management
- **Regular Cleanup**: Delete old contacts and data
- **Export Important Data**: Backup before cleanup
- **Archive Old Records**: Move old data to archives
- **Monitor Storage**: Keep track of disk usage

---

## Best Practices

### Daily Dashboard Usage

#### Morning Routine (2 minutes)
1. **Check System Status**: Verify all systems operational
2. **Review New Contacts**: Quick approve/reject queue
3. **Monitor Search Progress**: Check ongoing searches
4. **Review Notifications**: Confirm alerts were sent

#### Evening Review (1 minute)
1. **Daily Summary**: Check daily statistics
2. **Performance Review**: Review search effectiveness
3. **Plan Tomorrow**: Set priorities for next day
4. **System Health**: Ensure system ready for next day

### Efficiency Tips

#### Bulk Operations
- **Select Multiple Contacts**: Use checkboxes for efficiency
- **Bulk Approve/Reject**: Handle similar contacts together
- **Export Selected**: Get data for external processing
- **Filter First**: Apply filters before bulk operations

#### Search Optimization
- **Monitor Performance**: Track search effectiveness
- **Adjust Frequency**: Increase during active periods
- **Review Criteria**: Update based on market response
- **Balance Providers**: Optimize across all sources

---

## Related Documentation

- [User Guide Overview](overview.md) - Complete user guide
- [Setup Wizard Guide](setup-wizard.md) - Initial configuration
- [Configuration Reference](../getting-started/configuration.md) - Detailed settings
- [Troubleshooting Guide](troubleshooting.md) - Problem resolution
- [Architecture Overview](../architecture/system-overview.md) - Technical details

---

**Dashboard Support**: For dashboard-specific issues, check our [Dashboard FAQ](https://github.com/your-org/mafa/wiki/Dashboard-FAQ) or create an issue with your browser and system details.