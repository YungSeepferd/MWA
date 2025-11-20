# MAFA User Guide Overview

## Welcome to MAFA
This comprehensive user guide covers all aspects of using MAFA (MüncheWohnungsAssistent) to find your perfect apartment in Munich. Whether you're a first-time user or looking to optimize your apartment search, this guide will help you make the most of MAFA's powerful features.

---

**Last Updated:** November 19, 2025  
**Version:** 1.0.0  
**Maintainer:** MAFA User Experience Team  
**Estimated Reading Time:** 10 minutes

---

## What is MAFA?

MAFA is an intelligent apartment hunting assistant designed specifically for Munich's rental market. It automates the tedious process of searching for apartments, discovering contact information, and managing your apartment hunt workflow.

### Key Capabilities

#### 🔍 **Automated Search**
- Monitors ImmoScout24 and WG-Gesucht continuously
- Searches based on your personalized criteria
- Runs 24/7 without requiring manual intervention
- Intelligent filtering to avoid irrelevant listings

#### 📧 **Contact Discovery**
- Automatically extracts contact information from listings
- Finds emails, phone numbers, and contact forms
- Uses advanced OCR technology for image-based contacts
- Validates and scores contact reliability

#### 📱 **Smart Notifications**
- Real-time alerts via Email, Discord, or Telegram
- Customizable notification frequency and quiet hours
- Detailed apartment information with direct contact details
- Digest mode for summary-style updates

#### 📊 **Intelligent Analytics**
- Tracks search performance and success metrics
- Provides insights on market trends
- Analyzes contact quality and response rates
- Optimizes search criteria based on results

#### 🎯 **User-Friendly Interface**
- Intuitive dashboard with real-time updates
- Guided setup wizard for easy configuration
- Mobile-responsive design for on-the-go access
- Bulk operations for efficient contact management

---

## Who Should Use MAFA?

### Perfect For
- **Busy Professionals**: Don't have time to check listings manually
- **Relocation Newcomers**: Unfamiliar with Munich's rental market
- **Systematic Hunters**: Want organized, data-driven apartment search
- **Mobile Users**: Need apartment hunting on-the-go
- **International Users**: Benefit from automated contact discovery

### Also Suitable For
- **Budget-Conscious Renters**: Find best deals without manual searching
- **Specific Requirements**: Search for unique apartment features
- **Time-Sensitive Moves**: Need quick apartment acquisition
- **Quality Control**: Want to review all contacts before applying

---

## How MAFA Works

### The MAFA Process Flow

```
1. Setup & Configuration
   ↓
2. Automated Search
   ↓
3. Data Extraction
   ↓
4. Contact Discovery
   ↓
5. Quality Scoring
   ↓
6. Notification Delivery
   ↓
7. User Review & Action
```

#### Step 1: Setup & Configuration
- Complete the guided setup wizard
- Configure your apartment preferences
- Set up notification channels
- Define search criteria and filters

#### Step 2: Automated Search
- MAFA continuously monitors apartment websites
- Runs searches based on your criteria
- Handles rate limiting and anti-detection
- Manages search schedules automatically

#### Step 3: Data Extraction
- Parses listing details and images
- Extracts key apartment information
- Identifies contact methods and details
- Handles various listing formats

#### Step 4: Contact Discovery
- Finds email addresses (including obfuscated ones)
- Discovers phone numbers
- Identifies contact forms
- Uses OCR for image-based contacts

#### Step 5: Quality Scoring
- Assigns confidence scores to discovered contacts
- Validates email and phone number formats
- Considers source reliability
- Filters out low-quality contacts

#### Step 6: Notification Delivery
- Sends alerts via your preferred channels
- Includes apartment details and contact information
- Respects your notification preferences
- Provides direct links for quick action

#### Step 7: User Review & Action
- Review discovered contacts in dashboard
- Approve or reject contacts based on quality
- Use bulk operations for efficiency
- Take action on promising apartments

---

## Getting Started Roadmap

### For New Users

#### 📋 **Step 1: Installation** (5 minutes)
- Follow [Installation Guide](../getting-started/installation.md)
- Choose Docker or source installation
- Verify system is running correctly

#### 🚀 **Step 2: Quick Start** (5 minutes)
- Complete [Quick Start Guide](../getting-started/quick-start.md)
- Run the setup wizard
- Configure basic settings

#### ⚙️ **Step 3: Configuration** (10 minutes)
- Review [Configuration Reference](../getting-started/configuration.md)
- Fine-tune your search criteria
- Set up notification preferences

#### 🎯 **Step 4: Dashboard Mastery** (15 minutes)
- Learn [Dashboard Usage](dashboard.md)
- Understand all interface elements
- Practice contact review workflow

#### 🧙 **Step 5: Setup Wizard Deep Dive** (10 minutes)
- Explore [Setup Wizard Guide](setup-wizard.md)
- Master advanced configuration options
- Optimize your settings

### For Power Users

#### 📈 **Optimization**
- Review search performance regularly
- Adjust criteria based on results
- Monitor contact quality metrics
- Fine-tune notification settings

#### 🔧 **Advanced Features**
- Set up custom search schedules
- Configure multiple notification channels
- Use bulk operations efficiently
- Export data for external analysis

#### 📊 **Analytics & Insights**
- Monitor search effectiveness
- Analyze contact response rates
- Track market trends
- Identify best-performing criteria

---

## Core User Workflows

### Daily Monitoring Workflow
```
Morning (2 minutes):
1. Check dashboard for overnight activity
2. Review new contacts found
3. Approve/reject contacts as needed
4. Check search performance metrics

Evening (1 minute):
1. Review daily summary
2. Adjust settings if needed
3. Plan next day's actions
```

### Weekly Optimization Workflow
```
Weekly Review (10 minutes):
1. Analyze search effectiveness
2. Review contact quality trends
3. Adjust search criteria if needed
4. Update notification preferences
5. Plan apartment viewing schedule
```

### Monthly Deep Dive
```
Monthly Analysis (30 minutes):
1. Comprehensive performance review
2. Export data for analysis
3. Optimize search parameters
4. Plan next month's strategy
5. Update personal profile if needed
```

---

## Understanding MAFA's Intelligence

### Smart Contact Discovery

MAFA uses multiple techniques to find contact information:

#### Email Detection
- **Standard Patterns**: Recognizes common email formats
- **Obfuscation Handling**: Deconstructs "name [at] domain [dot] com"
- **Base64 Decoding**: Extracts encoded email addresses
- **JavaScript Evaluation**: Handles dynamic email generation

#### Phone Number Extraction
- **German Formats**: Recognizes German phone number patterns
- **International Formats**: Handles various country codes
- **Mobile Preference**: Prioritizes mobile numbers
- **Validation**: Checks format validity

#### Contact Form Analysis
- **Form Detection**: Identifies contact forms in listings
- **Field Recognition**: Understands form purpose and fields
- **Method Prioritization**: Prefers email > phone > form

### Quality Scoring System

Each discovered contact receives a confidence score based on:

| Factor | Weight | Description |
|--------|--------|-------------|
| **Source Reliability** | 30% | Website credibility and listing quality |
| **Extraction Confidence** | 40% | How clearly contact info is presented |
| **Validation Score** | 30% | Format validation and verification |

**Scoring Levels:**
- **0.9-1.0**: Excellent - Immediate notification
- **0.7-0.9**: Good - Standard notification
- **0.5-0.7**: Fair - Digest inclusion
- **0.3-0.5**: Poor - Archive only
- **0.0-0.3**: Rejected - Not notified

---

## MAFA vs Manual Search

| Feature | Manual Search | MAFA |
|---------|---------------|------|
| **Time Investment** | 2-4 hours daily | 5-15 minutes daily |
| **Coverage** | Limited to active checking | 24/7 monitoring |
| **Contact Discovery** | Manual scanning | Automated extraction |
| **Organization** | Spreadsheets/notes | Structured database |
| **Notifications** | Manual checking | Instant alerts |
| **Data Quality** | Human error prone | Validated and scored |
| **Mobile Access** | Browser dependent | Native mobile interface |
| **Learning** | No adaptation | Improves with use |

---

## Supported Platforms & Channels

### Web Dashboard
- **URL**: `http://localhost:8080` (local) or your deployed URL
- **Features**: Full feature access, real-time updates
- **Best For**: Setup, configuration, bulk operations

### Notification Channels
- **Email**: SMTP-based email notifications
- **Discord**: Webhook-based Discord messages
- **Telegram**: Bot-based direct messages
- **Digest**: Summary emails with multiple contacts

### Mobile Access
- **Responsive Design**: Works on all mobile devices
- **Progressive Web App**: Can be installed as PWA
- **Touch Optimized**: Optimized for mobile interaction
- **Offline Capability**: View cached data offline

---

## Success Metrics & KPIs

### Personal Success Indicators
- **Contacts Discovered**: Number of unique contacts found
- **Response Rate**: Percentage of contacts that respond
- **Viewings Scheduled**: Number of apartment viewings booked
- **Applications Submitted**: Actual applications sent
- **Apartments Found**: Successful apartment acquisition

### System Performance Metrics
- **Search Coverage**: Percentage of relevant listings found
- **Contact Quality**: Average confidence scores
- **False Positives**: Percentage of invalid contacts
- **System Uptime**: Availability and reliability
- **Search Frequency**: How often searches run

### Optimization Targets
| Metric | Good | Excellent |
|--------|------|-----------|
| Contacts/Week | 20+ | 50+ |
| Response Rate | 30%+ | 50%+ |
| Search Coverage | 80%+ | 95%+ |
| Contact Quality | 0.7+ | 0.8+ |
| False Positive Rate | <20% | <10% |

---

## Community & Support

### Getting Help
- **Documentation**: Comprehensive guides and references
- **FAQ**: Common questions and solutions
- **Community Forum**: User discussions and tips
- **GitHub Issues**: Bug reports and feature requests

### Contributing to MAFA
- **User Feedback**: Share your experience and suggestions
- **Bug Reports**: Help improve MAFA by reporting issues
- **Feature Requests**: Suggest new capabilities
- **Documentation**: Contribute to user guides

### Community Resources
- **User Stories**: Success stories from other users
- **Best Practices**: Tips from experienced users
- **Market Insights**: Munich rental market analysis
- **Configuration Sharing**: Community-configured settings

---

## What You'll Learn

This user guide covers:

### 📖 **Setup & Configuration**
- Installation and initial setup
- Dashboard navigation
- Configuration optimization
- Notification setup

### 🎯 **Daily Usage**
- Contact review workflow
- Search management
- Notification handling
- Mobile usage

### 📊 **Advanced Features**
- Analytics and insights
- Bulk operations
- Data export
- Performance optimization

### 🔧 **Troubleshooting**
- Common issues and solutions
- Performance problems
- Configuration debugging
- Error recovery

### 💡 **Tips & Best Practices**
- Optimization strategies
- Efficiency improvements
- Feature utilization
- Success patterns

---

## Next Steps

### Ready to Start?
1. **[Installation Guide](../getting-started/installation.md)** - Get MAFA running on your system
2. **[Quick Start Guide](../getting-started/quick-start.md)** - 5-minute setup to get searching
3. **[Setup Wizard Guide](setup-wizard.md)** - Master the configuration process
4. **[Dashboard Guide](dashboard.md)** - Learn to use the interface effectively

### Need Help?
- **[Troubleshooting Guide](troubleshooting.md)** - Solve common issues
- **[Configuration Reference](../getting-started/configuration.md)** - Detailed settings
- **[Architecture Overview](../architecture/system-overview.md)** - Technical details

### Want to Contribute?
- **[Developer Guide](../developer-guide/development-setup.md)** - Set up development environment
- **[Contributing Guidelines](../developer-guide/contributing.md)** - How to contribute
- **[Code Style Guide](../developer-guide/code-style.md)** - Development standards

---

## Related Documentation

- [Installation Guide](../getting-started/installation.md) - Complete setup instructions
- [Quick Start Guide](../getting-started/quick-start.md) - Get started in 5 minutes
- [Configuration Reference](../getting-started/configuration.md) - Detailed configuration
- [Setup Wizard Guide](setup-wizard.md) - Guided configuration process
- [Dashboard Guide](dashboard.md) - Interface and features
- [Troubleshooting Guide](troubleshooting.md) - Problem resolution
- [Architecture Overview](../architecture/system-overview.md) - Technical architecture

---

**Welcome to MAFA!** We're excited to help you find your perfect apartment in Munich. Start with the quick start guide and you'll be searching for apartments within minutes!