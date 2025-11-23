/**
 * JavaScript Security Utilities for XSS Prevention
 * This file provides comprehensive security utilities to prevent XSS vulnerabilities
 * across the entire MWA dashboard frontend.
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
        
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
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

    /**
     * Create safe HTML template with escaped variables
     */
    static createSafeTemplate(template, variables) {
        const escapedVars = {};
        for (const [key, value] of Object.entries(variables)) {
            escapedVars[key] = this.escapeHtml(String(value));
        }
        
        // Replace template variables with escaped values
        let safeHtml = template;
        for (const [key, value] of Object.entries(escapedVars)) {
            const pattern = new RegExp(`\\$\\{${key}\\}`, 'g');
            safeHtml = safeHtml.replace(pattern, value);
        }
        
        return safeHtml;
    }

    /**
     * Sanitize user input for display in HTML attributes
     */
    static sanitizeAttribute(value) {
        return this.escapeHtml(String(value)).replace(/"/g, '"');
    }

    /**
     * Sanitize user input for display in JavaScript contexts
     */
    static sanitizeForJs(value) {
        return String(value)
            .replace(/\\/g, '\\\\')
            .replace(/'/g, "\\'")
            .replace(/"/g, '\\"')
            .replace(/\n/g, '\\n')
            .replace(/\r/g, '\\r')
            .replace(/\t/g, '\\t');
    }

    /**
     * Validate and sanitize numeric input
     */
    static sanitizeNumber(value, min = -Infinity, max = Infinity, defaultValue = 0) {
        const num = Number(value);
        if (isNaN(num)) return defaultValue;
        return Math.max(min, Math.min(max, num));
    }

    /**
     * Validate and sanitize string input with length limits
     */
    static sanitizeString(value, maxLength = 255, defaultValue = '') {
        if (typeof value !== 'string') value = String(value);
        value = value.trim();
        
        if (value.length > maxLength) {
            value = value.substring(0, maxLength);
        }
        
        return this.escapeHtml(value) || defaultValue;
    }
}

// DOM security utilities
class DomSecurity {
    /**
     * Safely set element content with XSS protection
     */
    static setSafeContent(element, content) {
        if (!element) return;
        
        if (typeof content === 'string') {
            SecurityUtils.safeSetInnerHTML(element, content);
        } else if (typeof content === 'number') {
            element.textContent = content.toString();
        } else {
            element.textContent = String(content);
        }
    }

    /**
     * Safely set element attribute with XSS protection
     */
    static setSafeAttribute(element, attribute, value) {
        if (!element) return;
        
        const sanitizedValue = SecurityUtils.sanitizeAttribute(value);
        element.setAttribute(attribute, sanitizedValue);
    }

    /**
     * Safely create HTML element from template
     */
    static createSafeElement(tagName, attributes = {}, content = '') {
        const element = document.createElement(tagName);
        
        // Set attributes safely
        for (const [attr, value] of Object.entries(attributes)) {
            this.setSafeAttribute(element, attr, value);
        }
        
        // Set content safely
        if (content) {
            this.setSafeContent(element, content);
        }
        
        return element;
    }

    /**
     * Safely append HTML content to element
     */
    static appendSafeHtml(parent, html) {
        if (!parent || !html) return;
        
        const sanitizedHtml = SecurityUtils.escapeHtml(html);
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = sanitizedHtml;
        
        while (tempDiv.firstChild) {
            parent.appendChild(tempDiv.firstChild);
        }
    }
}

// Form security utilities
class FormSecurity {
    /**
     * Sanitize all form inputs before submission
     */
    static sanitizeForm(formElement) {
        if (!formElement) return {};
        
        const formData = new FormData(formElement);
        const sanitizedData = {};
        
        for (const [key, value] of formData.entries()) {
            sanitizedData[key] = SecurityUtils.sanitizeString(value);
        }
        
        return sanitizedData;
    }

    /**
     * Validate and sanitize form data with custom rules
     */
    static validateForm(formElement, rules = {}) {
        const formData = this.sanitizeForm(formElement);
        const errors = {};
        
        for (const [field, rule] of Object.entries(rules)) {
            const value = formData[field];
            
            if (rule.required && (!value || value.trim() === '')) {
                errors[field] = rule.requiredMessage || `${field} is required`;
                continue;
            }
            
            if (value && rule.pattern && !rule.pattern.test(value)) {
                errors[field] = rule.patternMessage || `${field} format is invalid`;
                continue;
            }
            
            if (value && rule.minLength && value.length < rule.minLength) {
                errors[field] = rule.minLengthMessage || `${field} must be at least ${rule.minLength} characters`;
                continue;
            }
            
            if (value && rule.maxLength && value.length > rule.maxLength) {
                errors[field] = rule.maxLengthMessage || `${field} must be at most ${rule.maxLength} characters`;
                continue;
            }
            
            if (value && rule.type === 'email' && !SecurityUtils.validateEmail(value)) {
                errors[field] = rule.emailMessage || 'Invalid email address';
                continue;
            }
            
            if (value && rule.type === 'number') {
                const num = Number(value);
                if (isNaN(num)) {
                    errors[field] = rule.numberMessage || 'Invalid number';
                } else if (rule.min !== undefined && num < rule.min) {
                    errors[field] = rule.minMessage || `Value must be at least ${rule.min}`;
                } else if (rule.max !== undefined && num > rule.max) {
                    errors[field] = rule.maxMessage || `Value must be at most ${rule.max}`;
                }
            }
        }
        
        return { isValid: Object.keys(errors).length === 0, errors, data: formData };
    }
}

// Make utilities available globally
window.SecurityUtils = SecurityUtils;
window.DomSecurity = DomSecurity;
window.FormSecurity = FormSecurity;

// Auto-initialize security for existing DOM elements
document.addEventListener('DOMContentLoaded', function() {
    // Add security attributes to all forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.setAttribute('data-security-scanned', 'true');
    });
    
    console.log('Security utilities initialized');
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        SecurityUtils,
        DomSecurity,
        FormSecurity
    };
}