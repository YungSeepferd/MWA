/**
 * Setup Wizard JavaScript Module
 * Handles setup wizard functionality, real-time updates, and API integration
 */

class SetupWizard {
    constructor() {
        this.currentStep = 1;
        this.totalSteps = 4;
        this.configuration = {};
        this.websocket = null;
        this.isValidating = false;
        this.init();
    }

    init() {
        this.setupWebSocket();
        this.bindEvents();
        this.loadCurrentConfiguration();
    }

    setupWebSocket() {
        // Initialize WebSocket connection for real-time updates
        if (typeof initializeWebSocket === 'function') {
            this.websocket = initializeWebSocket();
            
            // Listen for setup wizard specific messages
            if (this.websocket) {
                this.websocket.addEventListener('setup_wizard_update', (event) => {
                    this.handleRealtimeUpdate(event.data);
                });
            }
        }
    }

    bindEvents() {
        // Form validation events
        document.querySelectorAll('input, select').forEach(element => {
            element.addEventListener('change', () => this.validateStep());
            element.addEventListener('input', () => this.autoSaveStep());
        });

        // Navigation events
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft' && this.currentStep > 1) {
                this.prevStep();
            } else if (e.key === 'ArrowRight' && this.currentStep < this.totalSteps) {
                this.nextStep();
            }
        });
    }

    updateProgressBar() {
        const percentage = (this.currentStep / this.totalSteps) * 100;
        const progressBar = document.getElementById('progressBar');
        if (progressBar) {
            progressBar.style.width = percentage + '%';
            progressBar.textContent = Math.round(percentage) + '%';
        }

        // Emit progress update via WebSocket
        if (this.websocket) {
            this.websocket.broadcastSetupWizardProgress({
                step: this.currentStep,
                progress: percentage,
                completed: false
            });
        }
    }

    showStep(stepNumber) {
        // Hide all steps
        document.querySelectorAll('.setup-step').forEach(step => {
            step.classList.remove('active');
        });
        
        // Show target step
        const targetStep = document.getElementById(stepNumber === 'success' ? 'successStep' : `step${stepNumber}`);
        if (targetStep) {
            targetStep.classList.add('active');
            targetStep.scrollIntoView({ behavior: 'smooth' });
            
            if (stepNumber === 4) {
                this.updateConfigurationReview();
            }
        }

        // Update progress
        this.updateProgressBar();
    }

    nextStep() {
        if (this.currentStep < this.totalSteps && this.validateStep()) {
            this.saveStep();
            this.currentStep++;
            this.showStep(this.currentStep);
        }
    }

    prevStep() {
        if (this.currentStep > 1) {
            this.currentStep--;
            this.showStep(this.currentStep);
        }
    }

    validateStep() {
        if (this.isValidating) return true;
        
        this.isValidating = true;
        let isValid = true;
        const currentForm = document.getElementById(`step${this.currentStep}`).querySelector('form');

        if (currentForm) {
            // Remove previous validation messages
            currentForm.querySelectorAll('.invalid-feedback').forEach(el => el.remove());
            currentForm.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));

            // Validate required fields
            const requiredFields = currentForm.querySelectorAll('[required]');
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    this.showFieldError(field, 'This field is required');
                    isValid = false;
                }
            });

            // Step-specific validation
            if (this.currentStep === 1) {
                isValid = this.validateSearchStep() && isValid;
            } else if (this.currentStep === 2) {
                isValid = this.validateNotificationStep() && isValid;
            } else if (this.currentStep === 3) {
                isValid = this.validateProvidersStep() && isValid;
            }
        }

        this.isValidating = false;
        return isValid;
    }

    validateSearchStep() {
        let isValid = true;
        const minRent = document.getElementById('minRent').value;
        const maxRent = document.getElementById('maxRent').value;

        if (minRent && maxRent && parseInt(minRent) >= parseInt(maxRent)) {
            this.showFieldError(document.getElementById('maxRent'), 'Max rent must be greater than min rent');
            isValid = false;
        }

        const minSize = document.getElementById('minSize').value;
        if (minSize && parseInt(minSize) < 10) {
            this.showFieldError(document.getElementById('minSize'), 'Minimum size should be at least 10m²');
            isValid = false;
        }

        return isValid;
    }

    validateNotificationStep() {
        const emailEnabled = document.getElementById('emailNotifications').checked;
        const emailAddress = document.getElementById('emailAddress').value;

        if (emailEnabled && !emailAddress) {
            this.showFieldError(document.getElementById('emailAddress'), 'Email address is required when email notifications are enabled');
            return false;
        }

        if (emailAddress && !this.isValidEmail(emailAddress)) {
            this.showFieldError(document.getElementById('emailAddress'), 'Please enter a valid email address');
            return false;
        }

        return true;
    }

    validateProvidersStep() {
        const immoscout = document.getElementById('immoscoutEnabled').checked;
        const wgGesucht = document.getElementById('wgGesuchtEnabled').checked;

        if (!immoscout && !wgGesucht) {
            this.showFieldError(document.getElementById('wgGesuchtEnabled'), 'Please select at least one platform');
            return false;
        }

        return true;
    }

    showFieldError(field, message) {
        field.classList.add('is-invalid');
        const feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        feedback.textContent = message;
        field.parentNode.appendChild(feedback);
    }

    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    autoSaveStep() {
        // Debounced auto-save
        clearTimeout(this.autoSaveTimeout);
        this.autoSaveTimeout = setTimeout(() => {
            this.saveStep();
        }, 1000);
    }

    async saveStep() {
        try {
            const formData = this.collectFormData();
            localStorage.setItem(`setupStep${this.currentStep}`, JSON.stringify(formData));
            
            // Optional: Send to API for real-time validation
            await this.validateConfigurationRealTime(formData);
        } catch (error) {
            console.error('Failed to save step:', error);
        }
    }

    collectFormData() {
        const forms = document.querySelectorAll('.setup-step.active form');
        const formData = {};

        forms.forEach(form => {
            const formElements = form.elements;
            for (let i = 0; i < formElements.length; i++) {
                const element = formElements[i];
                if (element.name) {
                    if (element.type === 'checkbox') {
                        formData[element.name] = element.checked;
                    } else {
                        formData[element.name] = element.value;
                    }
                }
            }
        });

        return formData;
    }

    async validateConfigurationRealTime(formData) {
        try {
            const response = await fetch('/api/v1/config/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ config_data: formData })
            });

            const result = await response.json();
            this.showValidationResult(result);
        } catch (error) {
            console.error('Real-time validation failed:', error);
        }
    }

    showValidationResult(result) {
        // Show validation feedback
        const validationEl = document.getElementById('validationFeedback') || this.createValidationElement();
        
        if (result.is_valid) {
            validationEl.innerHTML = '<div class="alert alert-success"><i class="fas fa-check me-2"></i>Configuration looks good!</div>';
        } else {
            const issuesHtml = result.issues.map(issue => `<li>${issue}</li>`).join('');
            validationEl.innerHTML = `
                <div class="alert alert-warning">
                    <h6><i class="fas fa-exclamation-triangle me-2"></i>Configuration Issues</h6>
                    <ul class="mb-0">${issuesHtml}</ul>
                </div>
            `;
        }
    }

    createValidationElement() {
        const el = document.createElement('div');
        el.id = 'validationFeedback';
        el.className = 'mt-3';
        document.querySelector('.setup-step.active .card-body').appendChild(el);
        return el;
    }

    async updateConfigurationReview() {
        const reviewElement = document.getElementById('configurationReview');
        if (!reviewElement) return;

        const searchForm = document.getElementById('searchForm');
        const notificationForm = document.getElementById('notificationForm');
        const providersForm = document.getElementById('providersForm');

        this.configuration = {
            search: this.getFormData(searchForm),
            notifications: this.getFormData(notificationForm),
            providers: this.getFormData(providersForm)
        };

        reviewElement.innerHTML = this.generateReviewHTML();
    }

    getFormData(form) {
        const data = {};
        const elements = form.elements;
        for (let i = 0; i < elements.length; i++) {
            const element = elements[i];
            if (element.name) {
                if (element.type === 'checkbox') {
                    data[element.name] = element.checked;
                } else {
                    data[element.name] = element.value || 'Any';
                }
            }
        }
        return data;
    }

    generateReviewHTML() {
        const search = this.configuration.search;
        const notifications = this.configuration.notifications;
        const providers = this.configuration.providers;

        // Sanitize all user input to prevent XSS
        const minRent = this.escapeHtml(search.minRent || 'Any');
        const maxRent = this.escapeHtml(search.maxRent || 'Any');
        const minSize = this.escapeHtml(search.minSize || 'Any');
        const location = this.escapeHtml(search.location || 'Any area');
        const emailAddress = this.escapeHtml(notifications.emailAddress || 'Not provided');

        return `
            <div class="row">
                <div class="col-md-6 mb-4">
                    <h5><i class="fas fa-search me-2"></i>Search Preferences</h5>
                    <ul class="list-unstyled">
                        <li><strong>Rent Range:</strong> €${minRent} - €${maxRent}</li>
                        <li><strong>Min Size:</strong> ${minSize}m²</li>
                        <li><strong>Location:</strong> ${location}</li>
                    </ul>
                </div>
                <div class="col-md-6 mb-4">
                    <h5><i class="fas fa-bell me-2"></i>Notifications</h5>
                    <ul class="list-unstyled">
                        <li><strong>Email:</strong> ${notifications.emailNotifications ? 'Enabled' : 'Disabled'}</li>
                        ${notifications.emailNotifications ? `<li><strong>Address:</strong> ${emailAddress}</li>` : ''}
                        <li><strong>Discord:</strong> ${notifications.discordNotifications ? 'Enabled' : 'Disabled'}</li>
                        <li><strong>Telegram:</strong> ${notifications.telegramNotifications ? 'Enabled' : 'Disabled'}</li>
                    </ul>
                </div>
            </div>
            <div class="row">
                <div class="col-12">
                    <h5><i class="fas fa-globe me-2"></i>Platforms</h5>
                    <ul class="list-unstyled">
                        <li><strong>ImmoScout24:</strong> ${providers.immoscoutEnabled ? 'Enabled' : 'Disabled'}</li>
                        <li><strong>WG-Gesucht:</strong> ${providers.wgGesuchtEnabled ? 'Enabled' : 'Disabled'}</li>
                    </ul>
                </div>
            </div>
        `;
    }

    async completeSetup() {
        const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
        loadingModal.show();

        try {
            const configResponse = await this.saveConfiguration();
            if (configResponse.success) {
                this.currentStep = 'success';
                this.showStep('success');
                this.updateProgressBar();
                
                // Clear local storage
                for (let i = 1; i <= this.totalSteps; i++) {
                    localStorage.removeItem(`setupStep${i}`);
                }

                // Emit completion event
                if (this.websocket) {
                    this.websocket.broadcastSetupWizardProgress({
                        step: 'completed',
                        progress: 100,
                        completed: true
                    });
                }

                // Show success notification
                this.showNotification('Setup completed successfully!', 'success');
            } else {
                throw new Error(configResponse.error || 'Failed to save configuration');
            }
        } catch (error) {
            console.error('Setup completion error:', error);
            this.showNotification('Error saving configuration: ' + error.message, 'error');
        } finally {
            loadingModal.hide();
        }
    }

    async saveConfiguration() {
        try {
            // Save search configuration
            const searchUpdates = {
                search_criteria: {
                    rent_range: {
                        min: parseInt(this.configuration.search.minRent) || 0,
                        max: parseInt(this.configuration.search.maxRent) || 5000
                    },
                    size_min: parseInt(this.configuration.search.minSize) || 0,
                    preferred_areas: this.configuration.search.location && this.configuration.search.location !== 'Any area' ? [this.configuration.search.location] : []
                }
            };

            const searchResponse = await this.updateConfigSection('search', searchUpdates);
            if (!searchResponse.ok) {
                throw new Error('Failed to save search configuration');
            }

            // Save notification configuration
            const notificationUpdates = {
                email: {
                    enabled: this.configuration.notifications.emailNotifications,
                    address: this.configuration.notifications.emailAddress
                },
                discord: {
                    enabled: this.configuration.notifications.discordNotifications
                },
                telegram: {
                    enabled: this.configuration.notifications.telegramNotifications
                }
            };

            const notificationResponse = await this.updateConfigSection('notification', notificationUpdates);
            if (!notificationResponse.ok) {
                throw new Error('Failed to save notification configuration');
            }

            // Save provider configuration
            const providerUpdates = {
                immoscout24: {
                    enabled: this.configuration.providers.immoscoutEnabled
                },
                wg_gesucht: {
                    enabled: this.configuration.providers.wgGesuchtEnabled
                }
            };

            const providerResponse = await this.updateConfigSection('providers', providerUpdates);
            if (!providerResponse.ok) {
                throw new Error('Failed to save provider configuration');
            }

            return { success: true };
        } catch (error) {
            console.error('Configuration save error:', error);
            return { success: false, error: error.message };
        }
    }

    async updateConfigSection(section, updates) {
        return await fetch('/api/v1/config/', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                section: section,
                updates: updates
            })
        });
    }

    async loadCurrentConfiguration() {
        try {
            const response = await fetch('/api/v1/config/');
            if (response.ok) {
                const data = await response.json();
                this.populateFormWithConfig(data.config);
            }
        } catch (error) {
            console.error('Failed to load configuration:', error);
        }

        // Load from localStorage as backup
        this.loadFromLocalStorage();
    }

    populateFormWithConfig(config) {
        try {
            if (config.search?.search_criteria) {
                const criteria = config.search.search_criteria;
                if (criteria.rent_range?.min) document.getElementById('minRent').value = criteria.rent_range.min;
                if (criteria.rent_range?.max) document.getElementById('maxRent').value = criteria.rent_range.max;
                if (criteria.size_min) document.getElementById('minSize').value = criteria.size_min;
                if (criteria.preferred_areas?.length > 0) document.getElementById('location').value = criteria.preferred_areas[0];
            }

            if (config.notification?.email) {
                document.getElementById('emailNotifications').checked = config.notification.email.enabled;
                document.getElementById('emailAddress').value = config.notification.email.address || '';
            }

            if (config.providers) {
                document.getElementById('immoscoutEnabled').checked = config.providers.immoscout24?.enabled || false;
                document.getElementById('wgGesuchtEnabled').checked = config.providers.wg_gesucht?.enabled || false;
            }
        } catch (error) {
            console.error('Error populating form:', error);
        }
    }

    loadFromLocalStorage() {
        for (let i = 1; i <= this.totalSteps; i++) {
            const savedData = localStorage.getItem(`setupStep${i}`);
            if (savedData) {
                try {
                    const data = JSON.parse(savedData);
                    this.populateFormFields(data);
                } catch (error) {
                    console.error('Error loading saved data for step', i, error);
                }
            }
        }
    }

    populateFormFields(data) {
        Object.keys(data).forEach(fieldName => {
            const field = document.querySelector(`[name="${fieldName}"]`);
            if (field) {
                if (field.type === 'checkbox') {
                    field.checked = data[fieldName];
                } else {
                    field.value = data[fieldName];
                }
            }
        });
    }

    handleRealtimeUpdate(data) {
        // Handle real-time setup wizard updates
        if (data.step !== undefined) {
            // Update progress if needed
            this.updateProgressBar();
        }
    }

    showNotification(message, type = 'info') {
        const alertClass = type === 'success' ? 'alert-success' : type === 'error' ? 'alert-danger' : 'alert-info';
        const icon = type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle';
        
        // Sanitize message to prevent XSS
        const sanitizedMessage = this.escapeHtml(message);
        
        const notification = document.createElement('div');
        notification.className = `alert ${alertClass} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            <i class="fas ${icon} me-2"></i>${sanitizedMessage}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
    /**
     * Escape HTML special characters to prevent XSS attacks
     */
    escapeHtml(text) {
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
}

// Global functions for compatibility
function nextStep() {
    if (window.setupWizard) {
        window.setupWizard.nextStep();
    }
}

function prevStep() {
    if (window.setupWizard) {
        window.setupWizard.prevStep();
    }
}

function goBack() {
    window.location.href = '/dashboard/setup/welcome';
}

async function completeSetup() {
    if (window.setupWizard) {
        await window.setupWizard.completeSetup();
    }
}

function goToDashboard() {
    window.location.href = '/dashboard';
}

function startSearch() {
    window.location.href = '/dashboard/search';
}

// Initialize setup wizard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.setupWizard = new SetupWizard();
});