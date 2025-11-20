# MAFA UX Testing Scenarios

## Overview

Comprehensive UX testing scenarios for the MWA (Munich Apartment Finder Assistant) application using Playwright. These scenarios cover user workflows, error handling, accessibility, and performance from a user experience perspective.

## Test Environment Setup

### Prerequisites
- Application running on `http://localhost:8000`
- Test database with sample data
- Mock external services (webhooks, scraping targets)
- Playwright configured with proper timeouts

### Test Data
- Sample listings with various price ranges and locations
- Test user configurations
- Mock contact information
- Error simulation data

## Core User Workflows

### 1. First-Time User Experience

#### Scenario 1.1: Landing Page Navigation
```javascript
test('first-time user explores landing page', async ({ page }) => {
  // Navigate to application
  await page.goto('http://localhost:8000');
  
  // Verify page loads correctly
  await expect(page.locator('h1')).toContainText('MWA Core API');
  
  // Check key elements are present
  await expect(page.locator('.stats')).toBeVisible();
  await expect(page.locator('.endpoint')).toHaveCount.at.least(7);
  
  // Verify documentation links work
  const docsLink = page.locator('a[href="/docs"]');
  await expect(docsLink).toBeVisible();
  await docsLink.click();
  await expect(page).toHaveURL('/docs');
  
  // Verify Swagger UI loads
  await expect(page.locator('.swagger-ui')).toBeVisible();
});
```

#### Scenario 1.2: API Discovery
```javascript
test('user discovers available API endpoints', async ({ page }) => {
  await page.goto('http://localhost:8000/api/info');
  
  // Verify API information structure
  const response = await page.textContent('body');
  const apiInfo = JSON.parse(response);
  
  expect(apiInfo).toHaveProperty('name', 'MWA Core API');
  expect(apiInfo).toHaveProperty('routers');
  expect(apiInfo.routers).toHaveProperty('config');
  expect(apiInfo.routers).toHaveProperty('listings');
  expect(apiInfo.routers).toHaveProperty('contacts');
  
  // Test router listing endpoint
  await page.goto('http://localhost:8000/api/routers');
  const routersResponse = await page.textContent('body');
  const routers = JSON.parse(routersResponse);
  
  expect(routers.routers).toHaveLength(7);
  expect(routers.routers[0]).toHaveProperty('name');
  expect(routers.routers[0]).toHaveProperty('prefix');
});
```

### 2. Configuration Management

#### Scenario 2.1: Configuration Retrieval
```javascript
test('user retrieves current configuration', async ({ page }) => {
  await page.goto('http://localhost:8000/api/v1/config');
  
  // Verify configuration structure
  const response = await page.textContent('body');
  const config = JSON.parse(response);
  
  // Check required sections exist
  expect(config).toHaveProperty('personal_profile');
  expect(config).toHaveProperty('search_criteria');
  expect(config).toHaveProperty('notification');
  
  // Validate personal profile structure
  expect(config.personal_profile).toHaveProperty('my_full_name');
  expect(config.personal_profile).toHaveProperty('net_household_income_monthly');
  expect(config.personal_profile).toHaveProperty('total_occupants');
  
  // Validate search criteria
  expect(config.search_criteria).toHaveProperty('max_price');
  expect(config.search_criteria).toHaveProperty('zip_codes');
  expect(Array.isArray(config.search_criteria.zip_codes)).toBeTruthy();
});
```

#### Scenario 2.2: Configuration Validation
```javascript
test('configuration validation handles errors gracefully', async ({ page, request }) => {
  // Test with invalid configuration
  const invalidConfig = {
    personal_profile: {
      my_full_name: "",  // Invalid: empty name
      net_household_income_monthly: -1000  // Invalid: negative income
    }
    // Missing required sections
  };
  
  const response = await request.post('http://localhost:8000/api/v1/config', {
    data: invalidConfig
  });
  
  expect(response.status()).toBe(400);
  const errorData = await response.json();
  expect(errorData).toHaveProperty('error');
  expect(errorData.error).toHaveProperty('detail');
  expect(errorData.error.detail).toContain('validation');
});
```

### 3. Listing Management

#### Scenario 3.1: Browse Listings
```javascript
test('user browses available listings', async ({ page, request }) => {
  // Get listings
  const response = await request.get('http://localhost:8000/api/v1/listings');
  expect(response.ok()).toBeTruthy();
  
  const listings = await response.json();
  expect(Array.isArray(listings.listings)).toBeTruthy();
  
  if (listings.listings.length > 0) {
    const firstListing = listings.listings[0];
    
    // Verify listing structure
    expect(firstListing).toHaveProperty('title');
    expect(firstListing).toHaveProperty('price');
    expect(firstListing).toHaveProperty('source');
    expect(firstListing).toHaveProperty('timestamp');
    
    // Verify data quality
    expect(firstListing.title).toBeTruthy();
    expect(firstListing.title.length).toBeGreaterThan(0);
    expect(firstListing.price).toBeTruthy();
  }
});
```

#### Scenario 3.2: Filter Listings
```javascript
test('user filters listings by criteria', async ({ page, request }) => {
  // Test price filtering
  const response = await request.get('http://localhost:8000/api/v1/listings?max_price=1000');
  expect(response.ok()).toBeTruthy();
  
  const listings = await response.json();
  
  // Verify all listings meet price criteria
  for (const listing of listings.listings) {
    const price = parseInt(listing.price.replace(/[^\d]/g, ''));
    expect(price).toBeLessThanOrEqual(1000);
  }
  
  // Test location filtering
  const locationResponse = await request.get('http://localhost:8000/api/v1/listings?zip_codes=80331,80333');
  expect(locationResponse.ok()).toBeTruthy();
  
  const locationListings = await locationResponse.json();
  // Verify location filtering logic
});
```

### 4. Contact Management

#### Scenario 4.1: View Discovered Contacts
```javascript
test('user views discovered contacts', async ({ page, request }) => {
  const response = await request.get('http://localhost:8000/api/v1/contacts');
  expect(response.ok()).toBeTruthy();
  
  const contacts = await response.json();
  expect(contacts).toHaveProperty('contacts');
  expect(Array.isArray(contacts.contacts)).toBeTruthy();
  
  if (contacts.contacts.length > 0) {
    const firstContact = contacts.contacts[0];
    
    // Verify contact structure
    expect(firstContact).toHaveProperty('id');
    expect(firstContact).toHaveProperty('contact_type');
    expect(firstContact).toHaveProperty('value');
    expect(firstContact).toHaveProperty('source');
    
    // Verify contact types
    expect(['email', 'phone', 'form']).toContain(firstContact.contact_type);
  }
});
```

#### Scenario 4.2: Contact Validation
```javascript
test('contact validation works correctly', async ({ page, request }) => {
  // Test with invalid contact data
  const invalidContact = {
    contact_type: 'email',
    value: 'invalid-email',  // Invalid email format
    source: 'test'
  };
  
  const response = await request.post('http://localhost:8000/api/v1/contacts', {
    data: invalidContact
  });
  
  expect(response.status()).toBe(400);
  const errorData = await response.json();
  expect(errorData.error.detail).toContain('email');
});
```

### 5. Scraper Control

#### Scenario 5.1: Start Scraper Job
```javascript
test('user starts scraper job', async ({ page, request }) => {
  const startResponse = await request.post('http://localhost:8000/api/v1/scraper/start', {
    data: {
      providers: ['immoscout'],
      dry_run: true
    }
  });
  
  expect(startResponse.ok()).toBeTruthy();
  const jobData = await startResponse.json();
  
  expect(jobData).toHaveProperty('job_id');
  expect(jobData).toHaveProperty('status');
  expect(jobData.status).toBe('started');
  
  // Check job status
  const statusResponse = await request.get(`http://localhost:8000/api/v1/scraper/status/${jobData.job_id}`);
  expect(statusResponse.ok()).toBeTruthy();
  
  const statusData = await statusResponse.json();
  expect(statusData).toHaveProperty('status');
  expect(statusData).toHaveProperty('progress');
});
```

#### Scenario 5.2: Scraper Error Handling
```javascript
test('scraper handles errors gracefully', async ({ page, request }) => {
  // Test with invalid provider
  const response = await request.post('http://localhost:8000/api/v1/scraper/start', {
    data: {
      providers: ['invalid_provider'],
      dry_run: true
    }
  });
  
  expect(response.status()).toBe(400);
  const errorData = await response.json();
  expect(errorData.error.detail).toContain('provider');
});
```

### 6. System Monitoring

#### Scenario 6.1: Health Check
```javascript
test('system health check provides useful information', async ({ page, request }) => {
  const response = await request.get('http://localhost:8000/health');
  expect(response.ok()).toBeTruthy();
  
  const healthData = await response.json();
  expect(healthData).toHaveProperty('status', 'healthy');
  expect(healthData).toHaveProperty('service', 'MWA Core API');
  expect(healthData).toHaveProperty('version');
  expect(healthData).toHaveProperty('timestamp');
  
  // Verify timestamp format
  const timestamp = new Date(healthData.timestamp);
  expect(timestamp.getTime()).not.toBeNaN();
});
```

#### Scenario 6.2: System Status
```javascript
test('system status provides detailed metrics', async ({ page, request }) => {
  const response = await request.get('http://localhost:8000/api/v1/system/status');
  expect(response.ok()).toBeTruthy();
  
  const statusData = await response.json();
  expect(statusData).toHaveProperty('system');
  expect(statusData).toHaveProperty('database');
  expect(statusData).toHaveProperty('providers');
  expect(statusData).toHaveProperty('metrics');
  
  // Verify system information
  expect(statusData.system).toHaveProperty('uptime');
  expect(statusData.system).toHaveProperty('memory_usage');
  expect(statusData.system).toHaveProperty('cpu_usage');
  
  // Verify database status
  expect(statusData.database).toHaveProperty('connected');
  expect(statusData.database).toHaveProperty('size');
});
```

## Error Handling & Edge Cases

### 7. Error Scenarios

#### Scenario 7.1: Network Errors
```javascript
test('application handles network errors gracefully', async ({ page }) => {
  // Simulate network failure
  await page.route('**/api/v1/listings', route => {
    route.abort('failed');
  });
  
  await page.goto('http://localhost:8000');
  
  // Try to fetch listings
  const response = await page.evaluate(async () => {
    try {
      const resp = await fetch('/api/v1/listings');
      return { status: resp.status, ok: resp.ok };
    } catch (error) {
      return { error: error.message };
    }
  });
  
  expect(response.error).toBeTruthy();
  
  // Verify error handling UI
  await expect(page.locator('.error-message')).toBeVisible();
});
```

#### Scenario 7.2: Timeout Handling
```javascript
test('application handles timeouts gracefully', async ({ page }) => {
  // Simulate slow response
  await page.route('**/api/v1/scraper/start', route => {
    // Delay response by 10 seconds
    setTimeout(() => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ job_id: 'test-job', status: 'started' })
      });
    }, 10000);
  });
  
  // Set short timeout
  const response = await page.goto('http://localhost:8000/api/v1/scraper/start', {
    timeout: 5000
  }).catch(() => null);
  
  expect(response).toBeNull();
  
  // Verify timeout error handling
  await expect(page.locator('.timeout-error')).toBeVisible();
});
```

### 8. Accessibility Testing

#### Scenario 8.1: Keyboard Navigation
```javascript
test('application is keyboard accessible', async ({ page }) => {
  await page.goto('http://localhost:8000');
  
  // Test Tab navigation
  await page.keyboard.press('Tab');
  let focused = await page.locator(':focus');
  
  // Should focus on first interactive element
  expect(await focused.isVisible()).toBeTruthy();
  
  // Navigate through all interactive elements
  const interactiveElements = page.locator('a, button, input, select, textarea');
  const count = await interactiveElements.count();
  
  for (let i = 0; i < count; i++) {
    await page.keyboard.press('Tab');
    focused = await page.locator(':focus');
    expect(await focused.isVisible()).toBeTruthy();
  }
});
```

#### Scenario 8.2: Screen Reader Support
```javascript
test('application supports screen readers', async ({ page }) => {
  await page.goto('http://localhost:8000');
  
  // Check for proper semantic HTML
  await expect(page.locator('h1')).toBeVisible();
  await expect(page.locator('main')).toBeVisible();
  await expect(page.locator('nav')).toBeVisible();
  
  // Check for ARIA labels
  const links = page.locator('a[href]');
  const linkCount = await links.count();
  
  for (let i = 0; i < Math.min(linkCount, 5); i++) {
    const link = links.nth(i);
    const text = await link.textContent();
    expect(text.trim().length).toBeGreaterThan(0);
  }
  
  // Check for alt text on images
  const images = page.locator('img');
  const imageCount = await images.count();
  
  for (let i = 0; i < imageCount; i++) {
    const img = images.nth(i);
    const alt = await img.getAttribute('alt');
    expect(alt).toBeTruthy();
  }
});
```

## Performance Testing

### 9. Load Testing

#### Scenario 9.1: Concurrent Users
```javascript
test('application handles concurrent users', async ({ browser }) => {
  const contexts = [];
  const pages = [];
  
  // Create 10 concurrent users
  for (let i = 0; i < 10; i++) {
    const context = await browser.newContext();
    const page = await context.newPage();
    contexts.push(context);
    pages.push(page);
  }
  
  // All users access the application simultaneously
  const startTime = Date.now();
  
  await Promise.all(pages.map(async (page, index) => {
    await page.goto('http://localhost:8000');
    await expect(page.locator('h1')).toContainText('MWA Core API');
    
    // Each user makes API calls
    const response = await page.evaluate(async () => {
      const resp = await fetch('/api/v1/config');
      return resp.ok();
    });
    
    expect(response).toBeTruthy();
  }));
  
  const endTime = Date.now();
  const totalTime = endTime - startTime;
  
  // Should complete within reasonable time
  expect(totalTime).toBeLessThan(5000);
  
  // Clean up
  for (const context of contexts) {
    await context.close();
  }
});
```

#### Scenario 9.2: Large Dataset Handling
```javascript
test('application handles large datasets efficiently', async ({ page, request }) => {
  // Request large number of listings
  const response = await request.get('http://localhost:8000/api/v1/listings?limit=1000');
  expect(response.ok()).toBeTruthy();
  
  const startTime = Date.now();
  const listings = await response.json();
  const endTime = Date.now();
  
  // Should respond quickly even with large dataset
  expect(endTime - startTime).toBeLessThan(2000);
  expect(listings.listings.length).toBeGreaterThan(0);
  
  // Verify pagination works
  const paginatedResponse = await request.get('http://localhost:8000/api/v1/listings?page=1&limit=50');
  expect(paginatedResponse.ok()).toBeTruthy();
  
  const paginatedListings = await paginatedResponse.json();
  expect(paginatedListings.listings.length).toBeLessThanOrEqual(50);
});
```

## Mobile & Responsive Testing

### 10. Mobile Experience

#### Scenario 10.1: Mobile Viewport
```javascript
test('application works on mobile devices', async ({ page }) => {
  // Set mobile viewport
  await page.setViewportSize({ width: 375, height: 667 });
  await page.goto('http://localhost:8000');
  
  // Check mobile layout
  await expect(page.locator('h1')).toBeVisible();
  
  // Test touch interactions
  const docsLink = page.locator('a[href="/docs"]');
  await docsLink.tap();
  await expect(page).toHaveURL('/docs');
  
  // Verify responsive design
  await page.setViewportSize({ width: 768, height: 1024 });
  await expect(page.locator('.container')).toBeVisible();
});
```

#### Scenario 10.2: Touch Gestures
```javascript
test('touch gestures work correctly', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 667 });
  await page.goto('http://localhost:8000');
  
  // Test swipe navigation (if implemented)
  await page.touchscreen.tap(100, 100);
  
  // Test pinch zoom (should be disabled for usability)
  await page.touchscreen.pinch(100, 100, 200, 200);
  
  // Verify content remains readable
  await expect(page.locator('h1')).toBeVisible();
});
```

## Security Testing

### 11. Input Validation

#### Scenario 11.1: XSS Prevention
```javascript
test('application prevents XSS attacks', async ({ page, request }) => {
  const maliciousInput = '<script>alert("XSS")</script>';
  
  // Try to inject script through various endpoints
  const endpoints = [
    '/api/v1/contacts',
    '/api/v1/listings',
    '/api/v1/config'
  ];
  
  for (const endpoint of endpoints) {
    const response = await request.post(`http://localhost:8000${endpoint}`, {
      data: {
        title: maliciousInput,
        description: maliciousInput,
        name: maliciousInput
      }
    });
    
    // Should either reject or sanitize input
    if (response.status() === 200) {
      const data = await response.json();
      // Verify script tags are removed/escaped
      expect(JSON.stringify(data)).not.toContain('<script>');
    } else {
      expect(response.status()).toBeGreaterThanOrEqual(400);
    }
  }
});
```

#### Scenario 11.2: SQL Injection Prevention
```javascript
test('application prevents SQL injection', async ({ page, request }) => {
  const sqlInjection = "'; DROP TABLE listings; --";
  
  // Try SQL injection through search parameters
  const response = await request.get(`http://localhost:8000/api/v1/listings?search=${encodeURIComponent(sqlInjection)}`);
  
  // Should handle gracefully without database errors
  expect(response.ok()).toBeTruthy();
  
  const listings = await response.json();
  expect(listings).toHaveProperty('listings');
  
  // Verify database integrity
  const healthResponse = await request.get('http://localhost:8000/health');
  expect(healthResponse.ok()).toBeTruthy();
});
```

## Test Execution Plan

### Phase 1: Core Functionality (Priority: High)
1. Landing page navigation
2. API discovery
3. Configuration management
4. Basic listing operations
5. Health checks

### Phase 2: Advanced Features (Priority: Medium)
1. Scraper control
2. Contact management
3. Error handling
4. Performance testing
5. Mobile responsiveness

### Phase 3: Edge Cases & Security (Priority: Low)
1. Accessibility testing
2. Security vulnerabilities
3. Load testing
4. Timeout handling
5. Network error recovery

### Success Metrics
- All critical user workflows complete successfully
- Error scenarios handled gracefully with user-friendly messages
- Performance meets targets (< 2s response time)
- Accessibility standards met (WCAG 2.1 AA)
- No security vulnerabilities detected
- Mobile experience is fully functional

### Automation Strategy
- Run core functionality tests on every commit
- Execute full test suite before releases
- Performance tests run weekly
- Security scans run monthly
- Accessibility tests run with each feature update