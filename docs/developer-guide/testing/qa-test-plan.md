# MAFA QA Test Plan

## Executive Summary

Critical startup blocker identified: Missing `Optional` import in [`mafa/providers/immoscout.py`](mafa/providers/immoscout.py:2) prevents application initialization. Comprehensive QA testing required across all application layers.

## Critical Issues Found

### 🔴 BLOCKER: Missing Type Import
- **Location**: [`mafa/providers/immoscout.py:153`](mafa/providers/immoscout.py:153)
- **Issue**: `Optional` type hint used but not imported
- **Impact**: Complete application startup failure
- **Fix Required**: Add `Optional` to imports from `typing` module

```python
# Current (broken):
from typing import List, Dict

# Fixed:
from typing import List, Dict, Optional
```

## Test Coverage Matrix

### 1. Unit Tests
| Component | Test Cases | Priority | Status |
|-----------|------------|----------|--------|
| Provider Imports | Verify all provider modules import without errors | 🔴 Critical | ❌ Failing |
| Configuration Loading | Test config validation, fallback, error handling | 🔴 Critical | ⚠️ Unknown |
| Database Operations | CRUD operations, connection handling, error recovery | 🟡 High | ⚠️ Unknown |
| Security Validation | Input sanitization, XSS prevention, SQL injection | 🟡 High | ⚠️ Unknown |
| Notification System | Discord webhook integration, error handling | 🟢 Medium | ⚠️ Unknown |

### 2. Integration Tests
| Component | Test Cases | Priority | Status |
|-----------|------------|----------|--------|
| Provider Orchestration | Multiple providers, error isolation, retry logic | 🔴 Critical | ❌ Blocked |
| Database Persistence | Data consistency, transaction handling | 🟡 High | ⚠️ Unknown |
| End-to-End Scraping | Full flow: scrape → filter → persist → notify | 🔴 Critical | ❌ Blocked |
| Error Recovery | Provider failures, network issues, timeouts | 🟡 High | ⚠️ Unknown |

### 3. API Tests
| Endpoint | Test Cases | Priority | Status |
|----------|------------|----------|--------|
| `GET /health` | Basic health check, dependency verification | 🔴 Critical | ⚠️ Unknown |
| `GET /api/v1/config` | Configuration retrieval, validation | 🟡 High | ⚠️ Unknown |
| `POST /api/v1/scraper` | Scraper control, job management | 🟡 High | ⚠️ Unknown |
| `GET /api/v1/listings` | Listing retrieval, filtering, pagination | 🟢 Medium | ⚠️ Unknown |
| `GET /api/v1/contacts` | Contact management, validation | 🟢 Medium | ⚠️ Unknown |

### 4. Performance Tests
| Metric | Target | Priority | Status |
|--------|--------|----------|--------|
| Startup Time | < 5 seconds | 🟡 High | ❌ Failing (infinite) |
| Scrape Operation | < 30 seconds per provider | 🟡 High | ⚠️ Unknown |
| API Response Time | < 200ms per endpoint | 🟢 Medium | ⚠️ Unknown |
| Database Query Time | < 100ms per query | 🟢 Medium | ⚠️ Unknown |

### 5. Security Tests
| Test | Priority | Status |
|------|----------|--------|
| Input Validation | 🔴 Critical | ⚠️ Unknown |
| SQL Injection Prevention | 🔴 Critical | ⚠️ Unknown |
| XSS Prevention | 🔴 Critical | ⚠️ Unknown |
| Configuration Security | 🟡 High | ⚠️ Unknown |
| Dependency Vulnerabilities | 🟡 High | ⚠️ Unknown |

## Test Execution Strategy

### Phase 1: Critical Path Testing
1. **Fix import error** in [`mafa/providers/immoscout.py`](mafa/providers/immoscout.py:2)
2. **Verify all provider imports** work correctly
3. **Test basic orchestrator functionality** with dry-run mode
4. **Validate configuration loading** and error handling

### Phase 2: Integration Testing
1. **Test provider orchestration** with mock data
2. **Verify database operations** and persistence
3. **Test notification system** integration
4. **Validate error handling** and recovery mechanisms

### Phase 3: API & UX Testing
1. **Test all API endpoints** with Playwright
2. **Verify dashboard functionality** and responsiveness
3. **Test WebSocket connections** and real-time features
4. **Validate user workflows** and error messages

### Phase 4: Performance & Security
1. **Load testing** for API endpoints
2. **Security scanning** for vulnerabilities
3. **Performance profiling** for scraping operations
4. **Stress testing** for concurrent operations

## Playwright Test Scenarios

### 1. Dashboard UX Tests
```javascript
// Test dashboard loading and navigation
test('dashboard loads successfully', async ({ page }) => {
  await page.goto('http://localhost:8000');
  await expect(page.locator('h1')).toContainText('MWA Core API');
});

// Test API documentation access
test('API docs are accessible', async ({ page }) => {
  await page.goto('http://localhost:8000/docs');
  await expect(page.locator('.swagger-ui')).toBeVisible();
});
```

### 2. API Endpoint Tests
```javascript
// Test health endpoint
test('health endpoint returns healthy status', async ({ request }) => {
  const response = await request.get('http://localhost:8000/health');
  expect(response.ok()).toBeTruthy();
  const data = await response.json();
  expect(data.status).toBe('healthy');
});

// Test configuration endpoint
test('config endpoint returns valid data', async ({ request }) => {
  const response = await request.get('http://localhost:8000/api/v1/config');
  expect(response.ok()).toBeTruthy();
  const data = await response.json();
  expect(data).toHaveProperty('personal_profile');
});
```

### 3. Error Handling Tests
```javascript
// Test 404 handling
test('invalid endpoint returns 404', async ({ request }) => {
  const response = await request.get('http://localhost:8000/invalid');
  expect(response.status()).toBe(404);
});

// Test error response format
test('error responses have correct format', async ({ request }) => {
  const response = await request.get('http://localhost:8000/invalid');
  const data = await response.json();
  expect(data).toHaveProperty('error');
  expect(data.error).toHaveProperty('status_code');
});
```

## Test Data Requirements

### Mock Data
- **Valid listings**: 10+ sample listings with proper structure
- **Invalid listings**: Malformed data for error testing
- **Configuration variants**: Valid, invalid, and edge-case configs
- **Provider responses**: Mock HTML responses for testing

### Test Environment
- **Isolated database**: Separate test database
- **Mock external services**: Webhook endpoints, scraping targets
- **Clean state**: Reset between test runs
- **Monitoring**: Log collection and metrics

## Success Criteria

### Must Have (Critical)
- [ ] Application starts without import errors
- [ ] All providers can be imported and initialized
- [ ] Configuration loads and validates correctly
- [ ] Basic scraping works in dry-run mode
- [ ] API health endpoint responds correctly

### Should Have (High Priority)
- [ ] Database operations work correctly
- [ ] Notification system integrates properly
- [ ] Error handling works as expected
- [ ] API endpoints return correct data
- [ ] Performance meets targets

### Nice to Have (Medium Priority)
- [ ] Dashboard is fully functional
- [ ] WebSocket connections work
- [ ] Advanced filtering works correctly
- [ ] Performance optimizations in place

## Risk Assessment

### High Risk
- **Import errors** blocking all functionality
- **Database corruption** during operations
- **Security vulnerabilities** in input handling
- **Provider failures** affecting reliability

### Medium Risk
- **Performance degradation** under load
- **Configuration errors** causing silent failures
- **Notification failures** missing important updates
- **API rate limiting** affecting usability

### Low Risk
- **Cosmetic UI issues** in dashboard
- **Documentation gaps** affecting development
- **Minor performance optimizations** needed

## Next Steps

1. **Immediate**: Fix import error in [`mafa/providers/immoscout.py`](mafa/providers/immoscout.py:2)
2. **Short-term**: Run unit tests for all modules
3. **Medium-term**: Implement integration tests
4. **Long-term**: Set up automated Playwright testing pipeline