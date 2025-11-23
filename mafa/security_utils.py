"""
Security Utilities for XSS Prevention
This module provides comprehensive security utilities to prevent XSS vulnerabilities
across the entire MWA codebase.
"""

import re
import html
from typing import Union, Dict, Any, List

class SecurityUtils:
    """Security utilities for preventing XSS and other injection attacks."""
    
    # Dangerous patterns that should be sanitized
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',  # JavaScript protocol
        r'on\w+\s*=',   # Event handlers like onclick=
        r'vbscript:',   # VBScript protocol
        r'data:text/html',  # Data URL with HTML
        r'<iframe[^>]*>.*?</iframe>',  # Iframe tags
        r'eval\s*\(',   # Eval function calls
        r'expression\s*\(',  # CSS expressions
        r'url\s*\(',    # CSS url() with javascript
    ]
    
    @staticmethod
    def escape_html(text: Union[str, int, float]) -> str:
        """
        Escape HTML special characters to prevent XSS attacks.
        
        Args:
            text: Input text to escape
            
        Returns:
            Escaped HTML-safe text
        """
        if text is None:
            return ''
        
        if not isinstance(text, str):
            text = str(text)
        
        return html.escape(text)
    
    @staticmethod
    def sanitize_html(text: str, allowed_tags: List[str] = None) -> str:
        """
        Sanitize HTML by removing dangerous patterns while preserving safe content.
        
        Args:
            text: HTML text to sanitize
            allowed_tags: List of allowed HTML tags (default: basic formatting tags)
            
        Returns:
            Sanitized HTML text
        """
        if not text:
            return ''
        
        if allowed_tags is None:
            allowed_tags = ['b', 'i', 'u', 'strong', 'em', 'br', 'p', 'div', 'span']
        
        # First escape all HTML
        safe_text = SecurityUtils.escape_html(text)
        
        # Remove dangerous patterns
        for pattern in SecurityUtils.DANGEROUS_PATTERNS:
            safe_text = re.sub(pattern, '', safe_text, flags=re.IGNORECASE | re.DOTALL)
        
        return safe_text
    
    @staticmethod
    def sanitize_url(url: str) -> str:
        """
        Sanitize URL to prevent JavaScript injection.
        
        Args:
            url: URL to sanitize
            
        Returns:
            Sanitized URL
        """
        if not url:
            return ''
        
        # Remove dangerous protocols
        dangerous_protocols = ['javascript:', 'vbscript:', 'data:']
        for protocol in dangerous_protocols:
            if url.lower().startswith(protocol):
                return '#'
        
        # Ensure URL starts with safe protocol or relative path
        if not (url.startswith('/') or 
                url.startswith('#') or 
                url.startswith('?') or
                url.lower().startswith('http://') or
                url.lower().startswith('https://') or
                url.lower().startswith('mailto:') or
                url.lower().startswith('tel:')):
            return '#'
        
        return SecurityUtils.escape_html(url)
    
    @staticmethod
    def sanitize_json(data: Any) -> Any:
        """
        Recursively sanitize JSON data to prevent XSS.
        
        Args:
            data: JSON data to sanitize
            
        Returns:
            Sanitized JSON data
        """
        if isinstance(data, str):
            return SecurityUtils.escape_html(data)
        elif isinstance(data, dict):
            return {SecurityUtils.sanitize_json(k): SecurityUtils.sanitize_json(v) 
                   for k, v in data.items()}
        elif isinstance(data, list):
            return [SecurityUtils.sanitize_json(item) for item in data]
        else:
            return data
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email address format and prevent injection.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if email is valid and safe
        """
        if not email:
            return False
        
        # Basic email format validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False
        
        # Check for dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '(', ')', ';', '&']
        if any(char in email for char in dangerous_chars):
            return False
        
        return True
    
    @staticmethod
    def sanitize_form_data(form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize form data to prevent XSS and injection attacks.
        
        Args:
            form_data: Form data dictionary to sanitize
            
        Returns:
            Sanitized form data
        """
        sanitized = {}
        
        for key, value in form_data.items():
            if isinstance(value, str):
                sanitized[key] = SecurityUtils.escape_html(value)
            elif isinstance(value, (int, float)):
                sanitized[key] = value
            elif isinstance(value, dict):
                sanitized[key] = SecurityUtils.sanitize_json(value)
            elif isinstance(value, list):
                sanitized[key] = [SecurityUtils.sanitize_json(item) for item in value]
            else:
                sanitized[key] = SecurityUtils.escape_html(str(value))
        
        return sanitized
    
    @staticmethod
    def create_safe_html_template(template: str, **kwargs) -> str:
        """
        Create safe HTML by escaping all template variables.
        
        Args:
            template: HTML template string
            **kwargs: Template variables
            
        Returns:
            Safe HTML with escaped variables
        """
        # Escape all template variables
        safe_kwargs = {k: SecurityUtils.escape_html(v) for k, v in kwargs.items()}
        
        # Format template with safe variables
        return template.format(**safe_kwargs)


# JavaScript security utilities for frontend
JS_SECURITY_UTILS = """
/**
 * JavaScript Security Utilities for XSS Prevention
 */

class SecurityUtils {
    /**
     * Escape HTML special characters to prevent XSS attacks
     */
    static escapeHtml(text) {
        if (typeof text !== 'string') {
            return text;
        }
        
        const map = {
            '&': '&',
            '<': '<',
            '>': '>',
            '"': '"',
            "'": '&#x27;',
            '/': '&#x2F;'
        };
        
        return text.replace(/[&<>"'/]/g, (char) => map[char]);
    }

    /**
     * Sanitize URL to prevent JavaScript injection
     */
    static sanitizeUrl(url) {
        if (!url) return '#';
        
        const dangerousProtocols = ['javascript:', 'vbscript:', 'data:'];
        for (const protocol of dangerousProtocols) {
            if (url.toLowerCase().startsWith(protocol)) {
                return '#';
            }
        }
        
        // Allow safe protocols and relative paths
        const safePattern = /^(https?:|mailto:|tel:|\/|#|\?)/i;
        if (!safePattern.test(url)) {
            return '#';
        }
        
        return this.escapeHtml(url);
    }

    /**
     * Sanitize form data recursively
     */
    static sanitizeFormData(formData) {
        if (typeof formData !== 'object' || formData === null) {
            return this.escapeHtml(String(formData));
        }
        
        if (Array.isArray(formData)) {
            return formData.map(item => this.sanitizeFormData(item));
        }
        
        const sanitized = {};
        for (const [key, value] of Object.entries(formData)) {
            sanitized[key] = this.sanitizeFormData(value);
        }
        return sanitized;
    }

    /**
     * Validate email address format
     */
    static validateEmail(email) {
        if (!email) return false;
        
        const emailRegex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
        if (!emailRegex.test(email)) {
            return false;
        }
        
        const dangerousChars = ['<', '>', '"', "'", '(', ')', ';', '&'];
        return !dangerousChars.some(char => email.includes(char));
    }

    /**
     * Safe innerHTML replacement using textContent when possible
     */
    static safeSetInnerHTML(element, html) {
        if (!element || !html) return;
        
        // For simple text content, use textContent to avoid XSS
        if (!html.includes('<') && !html.includes('>')) {
            element.textContent = html;
            return;
        }
        
        // For HTML content, sanitize first
        const sanitizedHtml = this.escapeHtml(html);
        element.innerHTML = sanitizedHtml;
    }
}

// Make available globally
window.SecurityUtils = SecurityUtils;
"""


def generate_js_security_utils() -> str:
    """
    Generate JavaScript security utilities for frontend use.
    
    Returns:
        JavaScript code for security utilities
    """
    return JS_SECURITY_UTILS


# Example usage
if __name__ == "__main__":
    # Test HTML escaping
    test_text = '<script>alert("XSS")</script>Hello World'
    escaped = SecurityUtils.escape_html(test_text)
    print(f"Escaped: {escaped}")
    
    # Test URL sanitization
    test_url = 'javascript:alert("XSS")'
    sanitized_url = SecurityUtils.sanitize_url(test_url)
    print(f"Sanitized URL: {sanitized_url}")
    
    # Test form data sanitization
    test_form_data = {
        'name': '<script>alert("XSS")</script>John',
        'email': 'john@example.com',
        'message': 'Hello <b>World</b>'
    }
    sanitized_form = SecurityUtils.sanitize_form_data(test_form_data)
    print(f"Sanitized form: {sanitized_form}")