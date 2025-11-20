/**
 * Enhanced Contact Management JavaScript
 * Handles contact review, validation, and management functionality
 */

class ContactManager {
    constructor() {
        this.currentView = 'cards';
        this.currentPage = 1;
        this.itemsPerPage = 20;
        this.contacts = [];
        this.filteredContacts = [];
        this.selectedContacts = new Set();
        this.currentFilters = {
            method: '',
            confidence: '',
            status: '',
            search: ''
        };
        this.currentSort = {
            field: 'created_at',
            order: 'desc'
        };
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadContacts();
        this.loadStatistics();
    }

    setupEventListeners() {
        // Filter controls
        document.getElementById('filter-method')?.addEventListener('change', () => this.applyFilters());
        document.getElementById('filter-confidence')?.addEventListener('change', () => this.applyFilters());
        document.getElementById('filter-status')?.addEventListener('change', () => this.applyFilters());
        document.getElementById('search-contacts')?.addEventListener('input', (e) => {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => this.applyFilters(), 300);
        });

        // Sort control
        document.getElementById('sort-by')?.addEventListener('change', () => this.sortContacts());

        // Select all checkbox
        document.getElementById('select-all-contacts')?.addEventListener('change', () => this.toggleSelectAll());

        // Contact card click events
        document.addEventListener('click', (e) => {
            const contactCard = e.target.closest('.contact-card');
            if (contactCard && !e.target.closest('.contact-actions')) {
                const contactId = contactCard.dataset.contactId;
                this.showContactDetail(contactId);
            }
        });

        // WebSocket integration for real-time updates
        this.setupRealTimeUpdates();
    }

    async loadContacts() {
        try {
            const response = await fetch('/api/v1/contacts/');
            if (!response.ok) throw new Error('Failed to load contacts');
            
            const data = await response.json();
            this.contacts = data.contacts || [];
            this.filteredContacts = [...this.contacts];
            
            this.renderContacts();
            this.updatePagination();
            
        } catch (error) {
            console.error('Error loading contacts:', error);
            this.showNotification('Failed to load contacts', 'error');
            this.renderEmptyState();
        }
    }

    async loadStatistics() {
        try {
            const response = await fetch('/api/v1/contacts/statistics/summary');
            if (!response.ok) throw new Error('Failed to load statistics');
            
            const stats = await response.json();
            this.updateStatisticsDisplay(stats);
            
        } catch (error) {
            console.error('Error loading statistics:', error);
            this.setDefaultStatistics();
        }
    }

    updateStatisticsDisplay(stats) {
        const updates = [
            { id: 'total-contacts-count', value: stats.total_contacts || 0 },
            { id: 'approved-contacts-count', value: stats.contacts_by_status?.valid || 0 },
            { id: 'pending-contacts-count', value: stats.contacts_by_status?.unvalidated || 0 },
            { id: 'rejected-contacts-count', value: stats.contacts_by_status?.invalid || 0 }
        ];

        updates.forEach(({ id, value }) => {
            const element = document.getElementById(id);
            if (element) {
                this.animateNumber(element, parseInt(element.textContent) || 0, value);
            }
        });
    }

    setDefaultStatistics() {
        const defaults = [
            { id: 'total-contacts-count', value: 0 },
            { id: 'approved-contacts-count', value: 0 },
            { id: 'pending-contacts-count', value: 0 },
            { id: 'rejected-contacts-count', value: 0 }
        ];

        defaults.forEach(({ id, value }) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        });
    }

    animateNumber(element, start, end) {
        const duration = 1000;
        const startTime = performance.now();
        
        const updateNumber = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const easeOutCubic = 1 - Math.pow(1 - progress, 3);
            const current = Math.round(start + (end - start) * easeOutCubic);
            
            element.textContent = current;
            
            if (progress < 1) {
                requestAnimationFrame(updateNumber);
            }
        };
        
        requestAnimationFrame(updateNumber);
    }

    applyFilters() {
        this.currentFilters = {
            method: document.getElementById('filter-method')?.value || '',
            confidence: document.getElementById('filter-confidence')?.value || '',
            status: document.getElementById('filter-status')?.value || '',
            search: document.getElementById('search-contacts')?.value || ''
        };

        this.filteredContacts = this.contacts.filter(contact => {
            // Method filter
            if (this.currentFilters.method && contact.type !== this.currentFilters.method) {
                return false;
            }

            // Status filter
            if (this.currentFilters.status && contact.status !== this.currentFilters.status) {
                return false;
            }

            // Confidence filter
            if (this.currentFilters.confidence) {
                const confidence = contact.confidence || 0;
                switch (this.currentFilters.confidence) {
                    case 'high':
                        if (confidence < 0.9) return false;
                        break;
                    case 'medium':
                        if (confidence < 0.7 || confidence >= 0.9) return false;
                        break;
                    case 'low':
                        if (confidence >= 0.7) return false;
                        break;
                }
            }

            // Search filter
            if (this.currentFilters.search) {
                const searchTerm = this.currentFilters.search.toLowerCase();
                const searchableText = `${contact.value} ${contact.source} ${contact.type}`.toLowerCase();
                if (!searchableText.includes(searchTerm)) {
                    return false;
                }
            }

            return true;
        });

        this.sortContacts();
        this.currentPage = 1;
        this.renderContacts();
        this.updatePagination();
    }

    sortContacts() {
        const sortField = document.getElementById('sort-by')?.value || 'created_at';
        this.currentSort.field = sortField;

        this.filteredContacts.sort((a, b) => {
            let aValue = a[sortField];
            let bValue = b[sortField];

            // Handle different data types
            if (sortField === 'confidence') {
                aValue = aValue || 0;
                bValue = bValue || 0;
            } else if (sortField === 'created_at' || sortField === 'updated_at') {
                aValue = new Date(aValue);
                bValue = new Date(bValue);
            } else {
                aValue = (aValue || '').toString().toLowerCase();
                bValue = (bValue || '').toString().toLowerCase();
            }

            // Sort order
            if (this.currentSort.order === 'desc') {
                return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
            } else {
                return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
            }
        });

        this.renderContacts();
    }

    renderContacts() {
        if (this.currentView === 'cards') {
            this.renderCardView();
        } else {
            this.renderTableView();
        }
    }

    renderCardView() {
        const grid = document.getElementById('contacts-grid');
        if (!grid) return;

        if (this.filteredContacts.length === 0) {
            grid.innerHTML = this.renderEmptyState();
            return;
        }

        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const pageContacts = this.filteredContacts.slice(startIndex, endIndex);

        grid.innerHTML = pageContacts.map(contact => this.renderContactCard(contact)).join('');
    }

    renderContactCard(contact) {
        const confidenceClass = this.getConfidenceClass(contact.confidence);
        const statusClass = this.getStatusClass(contact.status);
        const methodIcon = this.getMethodIcon(contact.type);

        return `
            <div class="contact-card" data-contact-id="${contact.id}">
                <div class="contact-card-header">
                    <div class="contact-method">
                        <i class="${methodIcon}"></i>
                        <span class="contact-type">${contact.type}</span>
                    </div>
                    <div class="contact-actions">
                        <button class="btn btn-sm btn-outline-primary" onclick="event.stopPropagation(); contactManager.approveContact(${contact.id})">
                            <i class="fas fa-check"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="event.stopPropagation(); contactManager.rejectContact(${contact.id})">
                            <i class="fas fa-times"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-info" onclick="event.stopPropagation(); contactManager.showContactDetail(${contact.id})">
                            <i class="fas fa-eye"></i>
                        </button>
                    </div>
                </div>
                <div class="contact-card-body">
                    <div class="contact-value">
                        <strong>${contact.value}</strong>
                    </div>
                    <div class="contact-meta">
                        <span class="confidence-badge ${confidenceClass}">
                            ${Math.round((contact.confidence || 0) * 100)}% confidence
                        </span>
                        <span class="status-badge ${statusClass}">${contact.status}</span>
                    </div>
                    <div class="contact-source">
                        <small>Source: ${contact.source}</small>
                    </div>
                </div>
                <div class="contact-card-footer">
                    <small class="text-muted">${this.formatRelativeTime(contact.created_at)}</small>
                </div>
            </div>
        `;
    }

    renderTableView() {
        const tbody = document.getElementById('contacts-table-body');
        if (!tbody) return;

        if (this.filteredContacts.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center py-4">
                        <i class="fas fa-address-book fa-3x text-muted mb-3"></i>
                        <h5>No contacts found</h5>
                        <p class="text-muted">Try adjusting your filters</p>
                    </td>
                </tr>
            `;
            return;
        }

        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const pageContacts = this.filteredContacts.slice(startIndex, endIndex);

        tbody.innerHTML = pageContacts.map(contact => this.renderTableRow(contact)).join('');
    }

    renderTableRow(contact) {
        const confidenceClass = this.getConfidenceClass(contact.confidence);
        const statusClass = this.getStatusClass(contact.status);
        const methodIcon = this.getMethodIcon(contact.type);

        return `
            <tr>
                <td>
                    <input type="checkbox" class="contact-checkbox" value="${contact.id}" 
                           onchange="contactManager.toggleContactSelection(${contact.id})">
                </td>
                <td>
                    <i class="${methodIcon}"></i> ${contact.type}
                </td>
                <td><strong>${contact.value}</strong></td>
                <td>
                    <span class="badge ${confidenceClass}">${Math.round((contact.confidence || 0) * 100)}%</span>
                </td>
                <td>
                    <span class="badge ${statusClass}">${contact.status}</span>
                </td>
                <td>${contact.source}</td>
                <td>${this.formatRelativeTime(contact.created_at)}</td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-success" onclick="contactManager.approveContact(${contact.id})">
                            <i class="fas fa-check"></i>
                        </button>
                        <button class="btn btn-outline-danger" onclick="contactManager.rejectContact(${contact.id})">
                            <i class="fas fa-times"></i>
                        </button>
                        <button class="btn btn-outline-primary" onclick="contactManager.showContactDetail(${contact.id})">
                            <i class="fas fa-eye"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }

    renderEmptyState() {
        return `
            <div class="empty-state text-center py-5">
                <i class="fas fa-address-book fa-4x text-muted mb-3"></i>
                <h4>No Contacts Found</h4>
                <p class="text-muted">No contacts match your current filters</p>
                <button class="btn btn-primary" onclick="contactManager.clearAllFilters()">
                    <i class="fas fa-filter"></i> Clear Filters
                </button>
            </div>
        `;
    }

    updatePagination() {
        const pagination = document.getElementById('contacts-pagination');
        if (!pagination) return;

        const totalPages = Math.ceil(this.filteredContacts.length / this.itemsPerPage);
        
        if (totalPages <= 1) {
            pagination.innerHTML = '';
            return;
        }

        let paginationHtml = '';

        // Previous button
        paginationHtml += `
            <li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="contactManager.goToPage(${this.currentPage - 1})">Previous</a>
            </li>
        `;

        // Page numbers
        const startPage = Math.max(1, this.currentPage - 2);
        const endPage = Math.min(totalPages, this.currentPage + 2);

        if (startPage > 1) {
            paginationHtml += `
                <li class="page-item">
                    <a class="page-link" href="#" onclick="contactManager.goToPage(1)">1</a>
                </li>
            `;
            if (startPage > 2) {
                paginationHtml += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            paginationHtml += `
                <li class="page-item ${i === this.currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="contactManager.goToPage(${i})">${i}</a>
                </li>
            `;
        }

        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                paginationHtml += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
            paginationHtml += `
                <li class="page-item">
                    <a class="page-link" href="#" onclick="contactManager.goToPage(${totalPages})">${totalPages}</a>
                </li>
            `;
        }

        // Next button
        paginationHtml += `
            <li class="page-item ${this.currentPage === totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="contactManager.goToPage(${this.currentPage + 1})">Next</a>
            </li>
        `;

        pagination.innerHTML = paginationHtml;
    }

    goToPage(page) {
        const totalPages = Math.ceil(this.filteredContacts.length / this.itemsPerPage);
        if (page >= 1 && page <= totalPages) {
            this.currentPage = page;
            this.renderContacts();
            this.updatePagination();
        }
    }

    switchView(view) {
        this.currentView = view;
        
        // Update button states
        document.querySelectorAll('.view-controls .btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.getElementById(`${view}-view-btn`)?.classList.add('active');
        
        // Show/hide views
        document.getElementById('cards-view').style.display = view === 'cards' ? 'block' : 'none';
        document.getElementById('table-view').style.display = view === 'table' ? 'block' : 'none';
        
        this.renderContacts();
    }

    async showContactDetail(contactId) {
        try {
            const response = await fetch(`/api/v1/contacts/${contactId}`);
            if (!response.ok) throw new Error('Failed to load contact details');
            
            const contact = await response.json();
            this.renderContactDetail(contact);
            
            const modal = new bootstrap.Modal(document.getElementById('contact-detail-modal'));
            modal.show();
            
        } catch (error) {
            console.error('Error loading contact details:', error);
            this.showNotification('Failed to load contact details', 'error');
        }
    }

    renderContactDetail(contact) {
        const modalBody = document.getElementById('contact-detail-body');
        if (!modalBody) return;

        const confidenceClass = this.getConfidenceClass(contact.confidence);
        const statusClass = this.getStatusClass(contact.status);

        modalBody.innerHTML = `
            <div class="contact-detail">
                <div class="row">
                    <div class="col-md-6">
                        <h6>Contact Information</h6>
                        <table class="table table-sm">
                            <tr>
                                <th>Type:</th>
                                <td><i class="${this.getMethodIcon(contact.type)}"></i> ${contact.type}</td>
                            </tr>
                            <tr>
                                <th>Value:</th>
                                <td><strong>${contact.value}</strong></td>
                            </tr>
                            <tr>
                                <th>Confidence:</th>
                                <td><span class="badge ${confidenceClass}">${Math.round((contact.confidence || 0) * 100)}%</span></td>
                            </tr>
                            <tr>
                                <th>Status:</th>
                                <td><span class="badge ${statusClass}">${contact.status}</span></td>
                            </tr>
                            <tr>
                                <th>Source:</th>
                                <td>${contact.source}</td>
                            </tr>
                        </table>
                    </div>
                    <div class="col-md-6">
                        <h6>Timestamps</h6>
                        <table class="table table-sm">
                            <tr>
                                <th>Created:</th>
                                <td>${new Date(contact.created_at).toLocaleString()}</td>
                            </tr>
                            <tr>
                                <th>Updated:</th>
                                <td>${new Date(contact.updated_at).toLocaleString()}</td>
                            </tr>
                            ${contact.validated_at ? `
                                <tr>
                                    <th>Validated:</th>
                                    <td>${new Date(contact.validated_at).toLocaleString()}</td>
                                </tr>
                            ` : ''}
                            ${contact.listing_id ? `
                                <tr>
                                    <th>Listing ID:</th>
                                    <td>${contact.listing_id}</td>
                                </tr>
                            ` : ''}
                        </table>
                    </div>
                </div>
                ${Object.keys(contact.validation_metadata || {}).length > 0 ? `
                    <div class="row mt-3">
                        <div class="col-12">
                            <h6>Validation Metadata</h6>
                            <pre class="bg-light p-3 rounded">${JSON.stringify(contact.validation_metadata, null, 2)}</pre>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;

        // Store current contact ID for modal actions
        modalBody.dataset.currentContactId = contact.id;
    }

    async approveContact(contactId) {
        try {
            const response = await fetch(`/api/v1/contacts/${contactId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: 'approved' })
            });
            
            if (!response.ok) throw new Error('Failed to approve contact');
            
            // Update local data
            const contactIndex = this.contacts.findIndex(c => c.id === contactId);
            if (contactIndex !== -1) {
                this.contacts[contactIndex].status = 'approved';
                this.contacts[contactIndex].updated_at = new Date().toISOString();
            }
            
            this.applyFilters();
            this.loadStatistics();
            this.showNotification('Contact approved successfully', 'success');
            
        } catch (error) {
            console.error('Error approving contact:', error);
            this.showNotification('Failed to approve contact', 'error');
        }
    }

    async rejectContact(contactId) {
        try {
            const response = await fetch(`/api/v1/contacts/${contactId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: 'rejected' })
            });
            
            if (!response.ok) throw new Error('Failed to reject contact');
            
            // Update local data
            const contactIndex = this.contacts.findIndex(c => c.id === contactId);
            if (contactIndex !== -1) {
                this.contacts[contactIndex].status = 'rejected';
                this.contacts[contactIndex].updated_at = new Date().toISOString();
            }
            
            this.applyFilters();
            this.loadStatistics();
            this.showNotification('Contact rejected', 'info');
            
        } catch (error) {
            console.error('Error rejecting contact:', error);
            this.showNotification('Failed to reject contact', 'error');
        }
    }

    toggleContactSelection(contactId) {
        if (this.selectedContacts.has(contactId)) {
            this.selectedContacts.delete(contactId);
        } else {
            this.selectedContacts.add(contactId);
        }
    }

    toggleSelectAll() {
        const selectAllCheckbox = document.getElementById('select-all-contacts');
        if (!selectAllCheckbox) return;

        if (selectAllCheckbox.checked) {
            // Select all visible contacts
            const startIndex = (this.currentPage - 1) * this.itemsPerPage;
            const endIndex = startIndex + this.itemsPerPage;
            const pageContacts = this.filteredContacts.slice(startIndex, endIndex);
            
            pageContacts.forEach(contact => this.selectedContacts.add(contact.id));
            
            // Check all checkboxes
            document.querySelectorAll('.contact-checkbox').forEach(checkbox => {
                checkbox.checked = true;
            });
        } else {
            // Deselect all
            this.selectedContacts.clear();
            
            // Uncheck all checkboxes
            document.querySelectorAll('.contact-checkbox').forEach(checkbox => {
                checkbox.checked = false;
            });
        }
    }

    async bulkApproveSelected() {
        if (this.selectedContacts.size === 0) {
            this.showNotification('No contacts selected', 'warning');
            return;
        }

        try {
            const approvePromises = Array.from(this.selectedContacts).map(contactId => 
                fetch(`/api/v1/contacts/${contactId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: 'approved' })
                })
            );

            await Promise.all(approvePromises);
            
            // Update local data
            this.selectedContacts.forEach(contactId => {
                const contactIndex = this.contacts.findIndex(c => c.id === contactId);
                if (contactIndex !== -1) {
                    this.contacts[contactIndex].status = 'approved';
                    this.contacts[contactIndex].updated_at = new Date().toISOString();
                }
            });
            
            this.selectedContacts.clear();
            this.applyFilters();
            this.loadStatistics();
            this.showNotification(`${this.selectedContacts.size} contacts approved`, 'success');
            
        } catch (error) {
            console.error('Error bulk approving contacts:', error);
            this.showNotification('Failed to approve contacts', 'error');
        }
    }

    clearAllFilters() {
        document.getElementById('filter-method').value = '';
        document.getElementById('filter-confidence').value = '';
        document.getElementById('filter-status').value = '';
        document.getElementById('search-contacts').value = '';
        
        this.applyFilters();
    }

    setupRealTimeUpdates() {
        // WebSocket integration for real-time contact updates
        if (window.websocketManager) {
            window.websocketManager.addEventListener('contact_update', (event) => {
                this.handleRealTimeUpdate(event.data);
            });
        }
    }

    handleRealTimeUpdate(data) {
        if (data.action === 'new_contact') {
            this.contacts.unshift(data.contact);
            this.applyFilters();
            this.loadStatistics();
        } else if (data.action === 'contact_updated') {
            const contactIndex = this.contacts.findIndex(c => c.id === data.contact.id);
            if (contactIndex !== -1) {
                this.contacts[contactIndex] = data.contact;
                this.applyFilters();
                this.loadStatistics();
            }
        }
    }

    showNotification(message, type = 'info') {
        const container = document.querySelector('.toast-container') || document.body;
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${this.getNotificationClass(type)} border-0`;
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        container.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        toast.addEventListener('hidden.bs.toast', () => toast.remove());
    }

    getNotificationClass(type) {
        const classes = {
            'success': 'success',
            'error': 'danger',
            'warning': 'warning',
            'info': 'info'
        };
        return classes[type] || 'info';
    }

    getConfidenceClass(confidence) {
        const conf = confidence || 0;
        if (conf >= 0.9) return 'bg-success';
        if (conf >= 0.7) return 'bg-warning';
        return 'bg-danger';
    }

    getStatusClass(status) {
        const classes = {
            'approved': 'bg-success',
            'pending': 'bg-warning',
            'rejected': 'bg-danger',
            'valid': 'bg-success',
            'invalid': 'bg-danger',
            'unvalidated': 'bg-secondary',
            'suspicious': 'bg-warning'
        };
        return classes[status] || 'bg-secondary';
    }

    getMethodIcon(method) {
        const icons = {
            'email': 'fas fa-envelope',
            'phone': 'fas fa-phone',
            'form': 'fas fa-form',
            'social_media': 'fas fa-share-alt',
            'other': 'fas fa-info'
        };
        return icons[method] || 'fas fa-info';
    }

    formatRelativeTime(timestamp) {
        if (!timestamp) return 'Unknown';
        
        const now = new Date();
        const time = new Date(timestamp);
        const diffMs = now - time;
        const diffMins = Math.floor(diffMs / 60000);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        
        const diffHours = Math.floor(diffMins / 60);
        if (diffHours < 24) return `${diffHours}h ago`;
        
        const diffDays = Math.floor(diffHours / 24);
        return `${diffDays}d ago`;
    }
}

// Global functions for HTML onclick handlers
function switchView(view) {
    if (window.contactManager) {
        window.contactManager.switchView(view);
    }
}

function sortContacts() {
    if (window.contactManager) {
        window.contactManager.sortContacts();
    }
}

function applyFilters() {
    if (window.contactManager) {
        window.contactManager.applyFilters();
    }
}

function clearAllFilters() {
    if (window.contactManager) {
        window.contactManager.clearAllFilters();
    }
}

function toggleSelectAll() {
    if (window.contactManager) {
        window.contactManager.toggleSelectAll();
    }
}

function exportContacts() {
    // Implementation for contact export
    console.log('Export contacts functionality');
}

function bulkApproveSelected() {
    if (window.contactManager) {
        window.contactManager.bulkApproveSelected();
    }
}

function approveContact(contactId) {
    if (window.contactManager) {
        window.contactManager.approveContact(contactId);
    }
}

function rejectContact(contactId) {
    if (window.contactManager) {
        window.contactManager.rejectContact(contactId);
    }
}

function showContactDetail(contactId) {
    if (window.contactManager) {
        window.contactManager.showContactDetail(contactId);
    }
}

function markForReview(contactId) {
    // Implementation for marking contact for review
    console.log('Mark for review:', contactId);
}

function validateEmail() {
    // Implementation for email validation
    console.log('Validate email functionality');
}

function validatePhone() {
    // Implementation for phone validation
    console.log('Validate phone functionality');
}

// Initialize contact manager when DOM is loaded
let contactManager;

document.addEventListener('DOMContentLoaded', function() {
    contactManager = new ContactManager();
    window.contactManager = contactManager;
});