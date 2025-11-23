// Security patch for svelte-market-intelligence build file
// Fixes incomplete string escaping and double escaping vulnerabilities

/**
 * Fixed version of the Ze function - handles URL decoding properly
 * Original: function Ze(n){return n.split("%25").map(decodeURI).join("%25")}
 * Problem: Incomplete string escaping - doesn't handle edge cases properly
 */
function Ze_fixed(n) {
    // Use proper URL decoding with error handling
    try {
        // First, properly decode any encoded characters
        let decoded = decodeURIComponent(n);
        // Then re-encode to ensure consistency
        return encodeURIComponent(decoded);
    } catch (error) {
        // If decoding fails, return safely escaped version
        return SecurityUtils.escapeHtml(n);
    }
}

/**
 * Fixed version of the et function - prevents double escaping
 * Original: function et(n){for(const o in n)n[o]=decodeURIComponent(n[o]);return n}
 * Problem: Double escaping - applies decodeURIComponent without checking if already decoded
 */
function et_fixed(n) {
    const result = {};
    for (const o in n) {
        if (n.hasOwnProperty(o)) {
            try {
                // Only decode if it appears to be encoded
                const value = n[o];
                if (typeof value === 'string' && /%[0-9A-Fa-f]{2}/.test(value)) {
                    result[o] = decodeURIComponent(value);
                } else {
                    result[o] = value; // Leave as-is if not encoded
                }
            } catch (error) {
                // If decoding fails, use original value with HTML escaping for safety
                result[o] = SecurityUtils.escapeHtml(n[o]);
            }
        }
    }
    return result;
}

/**
 * Comprehensive URL parameter parsing with security
 */
function parseUrlParamsSecure(url) {
    const params = {};
    try {
        const urlObj = new URL(url, window.location.origin);
        for (const [key, value] of urlObj.searchParams.entries()) {
            // Sanitize both key and value
            const safeKey = SecurityUtils.escapeHtml(key);
            const safeValue = SecurityUtils.escapeHtml(value);
            params[safeKey] = safeValue;
        }
    } catch (error) {
        console.error('Error parsing URL parameters:', error);
    }
    return params;
}

/**
 * Safe pathname extraction with encoding validation
 */
function extractPathnameSecure(url) {
    try {
        const urlObj = new URL(url, window.location.origin);
        // Validate and sanitize the pathname
        let pathname = urlObj.pathname;
        
        // Remove any potentially dangerous characters
        pathname = pathname.replace(/[<>"']/g, '');
        
        // Ensure proper encoding
        return encodeURIComponent(decodeURIComponent(pathname));
    } catch (error) {
        console.error('Error extracting pathname:', error);
        return '';
    }
}

// Export for use in patching
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        Ze_fixed,
        et_fixed,
        parseUrlParamsSecure,
        extractPathnameSecure
    };
}

// Apply patch if running in browser context
if (typeof window !== 'undefined') {
    // Replace the vulnerable functions if they exist
    if (typeof window.Ze === 'function') {
        window.Ze = Ze_fixed;
    }
    
    if (typeof window.et === 'function') {
        window.et = et_fixed;
    }
    
    console.log('Svelte Market Intelligence security patch applied');
}