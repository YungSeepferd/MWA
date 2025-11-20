# {API Endpoint Name}

<!--
Template: API Reference Template
Description: Standard template for MAFA API documentation
Usage: Copy this template and document your API endpoint
Last Updated: {Date}
-->

---
title: "{API Endpoint Name}"
description: "{Brief description of what this API endpoint does}"
category: "{developer-guide}"
type: "{api}"
audience: "{developer}"
version: "1.0.0"
last_updated: "{YYYY-MM-DD}"
authors:
  - name: "{Author Name}"
    email: "{author@example.com}"
tags:
  - "api"
  - "{endpoint-category}"
  - "developer"
review_status: "draft"
review_date: "{YYYY-MM-DD}"
base_url: "https://api.mafa.example.com/v1"
---

## Overview

{Provide a brief overview of what this API endpoint does and its purpose in the MAFA system. Include any important context about when to use this endpoint.}

## Base URL

```
{base_url}
```

## Authentication

{Describe authentication requirements for this endpoint}

This endpoint requires:
- {Authentication method 1} (e.g., API Key, Bearer Token, OAuth2)
- {Authentication method 2} (if applicable)

### Example Authentication

```bash
# Using curl with API key
curl -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     {base_url}{endpoint-path}

# Using Python requests
import requests

headers = {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
}
response = requests.get('{base_url}{endpoint-path}', headers=headers)
```

## Endpoint

### {HTTP Method} `{endpoint-path}`

{Detailed description of what this endpoint does}

#### Parameters

##### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `{param1}` | `{type}` | {Yes/No} | {Description of parameter 1} |
| `{param2}` | `{type}` | {Yes/No} | {Description of parameter 2} |

##### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `{query_param1}` | `{type}` | {Yes/No} | `{default_value}` | {Description} |
| `{query_param2}` | `{type}` | {Yes/No} | `{default_value}` | {Description} |

##### Request Body

{Describe the request body structure if applicable}

**Content-Type:** `application/json`

```json
{
  "{field1}": {
    "type": "{type}",
    "required": {true/false},
    "description": "{field description}",
    "example": "{example_value}"
  },
  "{field2}": {
    "type": "{type}",
    "required": {true/false},
    "description": "{field description}",
    "example": "{example_value}"
  }
}
```

#### Request Examples

##### Example Request

```bash
curl -X {HTTP_METHOD} "{base_url}{endpoint-path}" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "{field1}": "{value1}",
    "{field2}": "{value2}"
  }'
```

```python
import requests

url = "{base_url}{endpoint-path}"
headers = {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
}
data = {
    "{field1}": "{value1}",
    "{field2}": "{value2}"
}
response = requests.{method_lower}(url, headers=headers, json=data)
```

#### Response

##### Success Response

**Status Code:** `{200|201|204}`

**Content-Type:** `application/json`

```json
{
  "success": true,
  "data": {
    "{response_field1}": {
      "type": "{type}",
      "description": "{description}",
      "example": "{example_value}"
    },
    "{response_field2}": {
      "type": "{type}",
      "description": "{description}",
      "example": "{example_value}"
    }
  },
  "metadata": {
    "timestamp": "2025-11-19T23:04:06Z",
    "request_id": "req_123456789",
    "version": "1.0.0"
  }
}
```

##### Error Responses

**Status Code:** `{400|401|403|404|422|429|500}`

```json
{
  "success": false,
  "error": {
    "code": "{ERROR_CODE}",
    "message": "{Human readable error message}",
    "details": {
      "{detail_field}": "{detail_value}"
    }
  },
  "metadata": {
    "timestamp": "2025-11-19T23:04:06Z",
    "request_id": "req_123456789"
  }
}
```

###### Common Error Codes

| Error Code | Status | Description |
|------------|--------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `UNAUTHORIZED` | 401 | Invalid or missing authentication |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

#### Response Examples

##### Example Success Response

```json
{
  "success": true,
  "data": {
    "id": "res_123456789",
    "status": "completed",
    "result": {
      "processed_items": 42,
      "success_rate": 0.95,
      "execution_time_ms": 1234
    }
  },
  "metadata": {
    "timestamp": "2025-11-19T23:04:06Z",
    "request_id": "req_123456789",
    "version": "1.0.0"
  }
}
```

##### Example Error Response

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "field_errors": {
        "email": ["Invalid email format"],
        "password": ["Password must be at least 8 characters"]
      }
    }
  },
  "metadata": {
    "timestamp": "2025-11-19T23:04:06Z",
    "request_id": "req_123456789"
  }
}
```

## Rate Limiting

{Describe rate limiting if applicable}

- **Rate Limit:** {X} requests per {minute|hour|day}
- **Burst Limit:** {X} requests in a {timeframe}
- **Headers:** Rate limit information is provided in response headers:
  - `X-RateLimit-Limit`: Request limit
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Reset time (Unix timestamp)

## SDK Examples

### Python SDK

```python
from mafa import MAFAClient

client = MAFAClient(api_key="YOUR_API_KEY")

# Using the endpoint
try:
    result = client.{endpoint_method}(
        {param1}="{value1}",
        {param2}="{value2}"
    )
    print(f"Success: {result}")
except mafa.exceptions.APIError as e:
    print(f"API Error: {e.message}")
```

### JavaScript SDK

```javascript
import { MAFAClient } from '@mafa/sdk';

const client = new MAFAClient({
  apiKey: 'YOUR_API_KEY'
});

// Using the endpoint
try {
  const result = await client.{endpointMethod}({
    {param1}: '{value1}',
    {param2}: '{value2}'
  });
  console.log('Success:', result);
} catch (error) {
  console.error('API Error:', error.message);
}
```

### cURL Example

```bash
# Complete example with all parameters
curl -X {HTTP_METHOD} "{base_url}{endpoint-path}" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -G \
  --data-urlencode "query_param1=value1" \
  --data-urlencode "query_param2=value2" \
  -d '{
    "field1": "value1",
    "field2": {
      "nested": "value"
    }
  }'
```

## Webhooks

{If this endpoint supports webhooks, describe them here}

This endpoint can trigger webhooks when certain events occur:

### Events

- `{event_name_1}`: {Description of event 1}
- `{event_name_2}`: {Description of event 2}

### Webhook Payload

```json
{
  "event": "{event_name}",
  "data": {
    "{field1}": "{value1}",
    "{field2}": "{value2}"
  },
  "timestamp": "2025-11-19T23:04:06Z",
  "webhook_id": "wh_123456789"
}
```

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | {YYYY-MM-DD} | Initial API version |
| 0.9.0 | {YYYY-MM-DD} | Beta release |

## Related Endpoints

- [Related Endpoint 1](./endpoint-1.md) - {Description}
- [Related Endpoint 2](./endpoint-2.md) - {Description}
- [Related Endpoint 3](./endpoint-3.md) - {Description}

## Testing

### Sandbox Environment

For testing purposes, use the sandbox endpoint:

```
{base_url_sandbox}
```

Sandbox features:
- {Feature 1}
- {Feature 2}
- {Feature 3}

### Test Data

{Provide information about test data or mock responses}

## Support

- **API Documentation Issues:** [Report a docs issue](https://github.com/your-org/mafa-docs/issues)
- **API Support:** [api-support@mafa.example.com](mailto:api-support@mafa.example.com)
- **Status Page:** [status.mafa.example.com](https://status.mafa.example.com)

---

*This API reference is part of the MAFA documentation. For the most up-to-date information, visit our [documentation homepage](../README.md).*

<!--
Template Instructions:
1. Replace all {placeholder} text with actual endpoint information
2. Ensure all examples are tested and working
3. Update version numbers when making changes
4. Add webhook documentation if applicable
5. Include SDK examples for supported languages
6. Use consistent formatting and structure
-->