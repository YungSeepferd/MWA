# MWA-MüncheWohnungsAssistent Comprehensive Fix Plan
## Analysis Date: 2025-11-20
## Critical Issues Identified

### 1. Chrome Driver Configuration Error
**Issue**: `Failed to resolve Chrome driver: name 'os' is not defined` and `cannot import name 'ChromeType' from 'webdriver_manager.core.utils'`

**Root Causes**:
- Missing `import os` statement in [`mafa/driver.py`](mafa/driver.py:127)
- Outdated WebDriver Manager import (`ChromeType` no longer exists in current versions)
- `os.access()` calls without proper import

**Files Affected**:
- [`mafa/driver.py`](mafa/driver.py) - Lines 127, 135, 145, 158, 21
- [`mwa_core/scraper/providers/immoscout.py`](mwa_core/scraper/providers/immoscout.py) - Import dependency
- [`mwa_core/scraper/providers/wg_gesucht.py`](mwa_core/scraper/providers/wg_gesucht.py) - Import dependency

**Fix Strategy**:
1. Add `import os` to [`mafa/driver.py`](mafa/driver.py)
2. Update WebDriver Manager import to use current API
3. Test Chrome driver initialization

### 2. Database Schema Issues
**Issue**: ScrapingRun model missing 'created_at' attribute

**Root Causes**:
- [`ScrapingRun`](mwa_core/storage/models.py:354) model uses `started_at` but some code expects `created_at`
- Potential session binding issues in database operations

**Files Affected**:
- [`mwa_core/storage/models.py`](mwa_core/storage/models.py) - ScrapingRun model definition
- [`mwa_core/storage/operations.py`](mwa_core/storage/operations.py) - Database operations
- [`mwa_core/storage/relationships.py`](mwa_core/storage/relationships.py) - Relationship queries

**Fix Strategy**:
1. Add `created_at` field to ScrapingRun model for backward compatibility
2. Ensure proper session binding in all database operations
3. Update migration scripts if needed

### 3. Notification System Error
**Issue**: Discord notifications not functional

**Root Causes**:
- Configuration mismatch between legacy MAFA and MWA Core notification systems
- Webhook URL validation issues
- Initialization errors in orchestrator

**Files Affected**:
- [`mafa/notifier/discord.py`](mafa/notifier/discord.py) - Legacy Discord notifier
- [`mwa_core/notifier/discord.py`](mwa_core/notifier/discord.py) - Enhanced Discord notifier
- [`mafa/orchestrator/__init__.py`](mafa/orchestrator/__init__.py) - Notifier initialization

**Fix Strategy**:
1. Standardize configuration format between systems
2. Fix webhook URL validation
3. Test notification delivery with mock webhook

### 4. Frontend Accessibility Issue
**Issue**: Frontend application not accessible on port 5173

**Root Causes**:
- Service running but port not accessible
- Potential CORS configuration issues
- Frontend build or preview configuration problems

**Files Affected**:
- [`svelte-market-intelligence/package.json`](svelte-market-intelligence/package.json) - Build scripts
- [`api/main.py`](api/main.py) - CORS configuration
- Frontend configuration files

**Fix Strategy**:
1. Check frontend service status and port binding
2. Verify CORS configuration in backend
3. Test frontend-backend communication

### 5. Selenium Selector Errors
**Issue**: `invalid selector: An invalid or illegal selector was specified`

**Root Causes**:
- Outdated CSS selectors in provider scrapers
- Website structure changes not reflected in selectors
- Dynamic content loading issues

**Files Affected**:
- [`mwa_core/providers/immoscout.py`](mwa_core/providers/immoscout.py) - ImmoScout selectors
- [`mwa_core/providers/wg_gesucht.py`](mwa_core/providers/wg_gesucht.py) - WG-Gesucht selectors

**Fix Strategy**:
1. Update CSS selectors to match current website structures
2. Implement robust element waiting strategies
3. Add selector validation and fallback mechanisms

## Implementation Plan

### Phase 1: Immediate Chrome Driver Fixes (Priority: Critical)
```python
# Fix for mafa/driver.py
import os  # Add this import
from webdriver_manager.chrome import ChromeDriverManager
# Remove ChromeType import - use current WebDriver Manager API
```

### Phase 2: Database Schema Resolution
```python
# Add to ScrapingRun model in mwa_core/storage/models.py
created_at = Column(DateTime, nullable=False, default=func.now())
```

### Phase 3: Notification System Repair
- Update configuration validation
- Test with mock Discord webhook
- Ensure proper error handling

### Phase 4: Frontend Accessibility
- Check `npm run preview` configuration
- Verify Vite dev server settings
- Test API connectivity

### Phase 5: Selector Updates
- Research current website structures
- Update CSS selectors in providers
- Implement comprehensive testing

## Testing Strategy

### Unit Tests
- Chrome driver initialization
- Database model operations
- Notification delivery
- Selector functionality

### Integration Tests
- End-to-end scraping workflow
- Frontend-backend communication
- Real-time notification delivery

### End-to-End Tests
- Complete property search flow
- Contact discovery process
- Dashboard functionality

## Rollback Procedures

### Chrome Driver Rollback
- Revert import changes
- Use compatible WebDriver Manager version
- Test with known working configuration

### Database Rollback
- Backup current database
- Use migration rollback scripts
- Verify data integrity

## Timeline Estimates

| Phase | Estimated Time | Priority |
|-------|----------------|----------|
| Chrome Driver Fix | 1-2 hours | Critical |
| Database Schema | 2-3 hours | High |
| Notification System | 2-3 hours | Medium |
| Frontend Accessibility | 1-2 hours | High |
| Selector Updates | 3-4 hours | Medium |
| Testing & Validation | 2-3 hours | Critical |

## Success Criteria

1. **Chrome Driver**: Successful initialization and basic navigation
2. **Database**: ScrapingRun operations work without errors
3. **Notifications**: Discord webhook test passes
4. **Frontend**: Accessible on port 5173 with API connectivity
5. **Scraping**: Providers successfully extract listing data

## Risk Assessment

### High Risk
- WebDriver Manager API changes may require significant refactoring
- Website structure changes may break existing selectors

### Medium Risk
- Database schema changes may affect existing data
- Notification system configuration complexity

### Low Risk
- Frontend accessibility issues (typically configuration-related)

## Dependencies

- Chrome browser installation
- WebDriver Manager compatibility
- Discord webhook configuration
- Database migration tools

## Monitoring and Validation

- Implement comprehensive logging
- Create health check endpoints
- Set up automated testing pipeline
- Monitor scraping success rates

This plan provides a comprehensive approach to resolving the critical issues identified during manual testing. Each fix is prioritized based on impact and includes specific implementation details.