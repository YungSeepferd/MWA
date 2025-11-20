/**
 * MAFA Contact Review Dashboard JavaScript
 * 
 * This file contains the client-side functionality for the contact review dashboard.
 */

// Global variables
let currentPage = 1;
let pageSize = 50;
let selectedContacts = new Set();
let currentFilters = {};

// API base URL
const API_BASE_URL = '/api/v1';

// Utility functions
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('de-DE', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function getStatusBadgeClass(status) {
    switch (status) {
        case 'approved':
            return 'bg-success';
        case 'rejected':
            return 'bg-danger';
        case 'pending':
            return 'bg-warning';
        default:
            return 'bg-secondary';
    }
}

function getConfidenceBadgeClass(confidence) {
    switch (confidence) {
        case 'high':
            return 'bg-success';
        case 'medium':
            return 'bg-warning';
        case 'low':
            return 'bg-danger';
        default:
            return 'bg-secondary';
    }
}

function getMethodIcon(method) {
    switch (method) {
        case 'email':
            return 'fas fa-envelope';
        case 'phone':
            return 'fas fa-phone';
        case 'form':
            return 'fas fa-file-alt';
        default:
            return 'fas fa-question';
    }
}

function showAlert(message, type = 'info') {
    const alertContainer = document.createElement('div');
    alertContainer.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    alertContainer.style.zIndex = '9999';
    alertContainer.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertContainer);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertContainer.parentNode) {
            alertContainer.parentNode.removeChild(alertContainer);
        }
    }, 5000);
}

function updateLastUpdated() {
    const lastUpdatedElement = document.getElementById('last-updated');
    if (lastUpdatedElement) {
        lastUpdatedElement.textContent = new Date().toLocaleString('de-DE');
    }
}

// Dashboard functions
async function loadDashboardStats() {
    try {
        // Use system endpoint for dashboard stats
        const response = await fetch(`${API_BASE_URL}/system/dashboard/stats`);
        if (!response.ok) throw new Error('Failed to fetch stats');
        
        const stats = await response.json();
        
        // Update dashboard cards
        const elements = {
            'total-contacts': stats.total_contacts,
            'active-searches': stats.active_searches,
            'new-contacts': stats.new_contacts_today,
            'pending-review': stats.contacts_by_status.pending || 0,
            'success-rate': `${stats.success_rate}%`
        };
        
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
        
        // Update contact statistics
        const contactCounts = {
            'total-contacts-count': stats.total_contacts,
            'approved-contacts-count': stats.contacts_by_status.approved || 0,
            'pending-contacts-count': stats.contacts_by_status.pending || 0,
            'rejected-contacts-count': stats.contacts_by_status.rejected || 0
        };
        
        Object.entries(contactCounts).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
        
        // Update top sources
        const topSourcesList = document.getElementById('top-sources');
        if (topSourcesList) {
            topSourcesList.innerHTML = stats.top_sources.slice(0, 5).map(source => `
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <span class="text-truncate" style="max-width: 200px;" title="${source.source}">
                        ${source.source}
                    </span>
                    <span class="badge bg-primary">${source.count}</span>
                </div>
            `).join('');
        }
        
        // Update system status indicators
        updateSystemStatusIndicators(stats);
        
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
        showAlert('Failed to load dashboard statistics', 'danger');
    }
}

async function loadRecentContacts() {
    try {
        const response = await fetch(`${API_BASE_URL}/contacts?limit=10&offset=0`);
        if (!response.ok) throw new Error('Failed to fetch recent contacts');
        
        const result = await response.json();
        const contacts = result.contacts || result; // Handle both formats
        
        // Update activity feed
        const activityFeed = document.getElementById('activity-feed');
        if (activityFeed) {
            activityFeed.innerHTML = contacts.slice(0, 5).map(contact => `
                <div class="activity-item d-flex align-items-center mb-3">
                    <div class="activity-icon bg-primary text-white rounded-circle d-flex align-items-center justify-content-center me-3" style="width: 40px; height: 40px;">
                        <i class="fas fa-${getMethodIcon(contact.type || contact.method)}"></i>
                    </div>
                    <div class="activity-content flex-grow-1">
                        <div class="activity-title fw-bold">${contact.type || contact.method} Contact Found</div>
                        <div class="activity-description text-muted">${contact.value || contact.contact_info || 'Contact extracted from listing'}</div>
                        <div class="activity-meta text-muted small">${formatDate(contact.created_at)} • ${contact.source || 'Unknown source'}</div>
                    </div>
                    <div class="activity-actions">
                        <button class="btn btn-sm btn-outline-primary" onclick="viewContactDetails(${contact.id})">
                            <i class="fas fa-eye"></i>
                        </button>
                    </div>
                </div>
            `).join('');
        }
        
    } catch (error) {
        console.error('Error loading recent contacts:', error);
        // Don't show error for activity feed, just log it
    }
}

async function loadTopSources() {
    try {
        const response = await fetch(`${API_BASE_URL}/system/dashboard/stats`);
        if (!response.ok) throw new Error('Failed to fetch stats');
        
        const stats = await response.json();
        
        // Update both top-sources and sources-list elements
        const updateSourcesList = (elementId) => {
            const element = document.getElementById(elementId);
            if (element) {
                element.innerHTML = stats.top_sources.slice(0, 5).map(source => `
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <span class="text-truncate" style="max-width: 200px;" title="${source.source}">
                            ${source.source}
                        </span>
                        <span class="badge bg-primary">${source.count}</span>
                    </div>
                `).join('');
            }
        };
        
        updateSourcesList('top-sources');
        updateSourcesList('sources-list');
        
    } catch (error) {
        console.error('Error loading top sources:', error);
    }
}

// Contacts page functions
async function loadContacts(page = 1, limit = pageSize) {
    try {
        currentPage = page;
        
        // Build query parameters
        const params = new URLSearchParams({
            limit: limit,
            offset: (page - 1) * limit
        });
        
        // Add filters
        Object.keys(currentFilters).forEach(key => {
            if (currentFilters[key]) {
                params.append(key, currentFilters[key]);
            }
        });
        
        const response = await fetch(`${API_BASE_URL}/contacts?${params}`);
        if (!response.ok) throw new Error('Failed to fetch contacts');
        
        const contacts = await response.json();
        
        // Update contacts table
        const contactsBody = document.getElementById('contacts-body');
        if (contactsBody) {
            contactsBody.innerHTML = contacts.map(contact => `
                <tr>
                    <td>
                        <input type="checkbox" class="contact-checkbox" value="${contact.id}" 
                               onchange="toggleContactSelection(${contact.id})">
                    </td>
                    <td>${contact.id}</td>
                    <td>
                        <span class="text-truncate" style="max-width: 200px;" title="${contact.source}">
                            ${contact.source}
                        </span>
                    </td>
                    <td>
                        <i class="${getMethodIcon(contact.method)}"></i>
                        ${contact.method}
                    </td>
                    <td>
                        <span class="text-truncate" style="max-width: 200px;" title="${contact.value}">
                            ${contact.value}
                        </span>
                    </td>
                    <td>
                        <span class="badge ${getConfidenceBadgeClass(contact.confidence)}">
                            ${contact.confidence}
                        </span>
                    </td>
                    <td>
                        <span class="badge ${getStatusBadgeClass(contact.status)}">
                            ${contact.status}
                        </span>
                    </td>
                    <td>${formatDate(contact.created_at)}</td>
                    <td>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-primary" onclick="viewContactDetails(${contact.id})">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn btn-outline-success" onclick="approveContact(${contact.id})">
                                <i class="fas fa-check"></i>
                            </button>
                            <button class="btn btn-outline-danger" onclick="rejectContact(${contact.id})">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `).join('');
        }
        
        // Update pagination
        updatePagination(contacts.length, page, limit);
        
        // Update total count
        try {
            const totalResponse = await fetch(`${API_BASE_URL}/system/dashboard/stats`);
            if (totalResponse.ok) {
                const stats = await totalResponse.json();
                const totalElement = document.getElementById('total-contacts-count');
                if (totalElement) {
                    totalElement.textContent = stats.total_contacts;
                }
            }
        } catch (e) {
            console.warn('Could not update total count:', e);
        }
        
    } catch (error) {
        console.error('Error loading contacts:', error);
        showAlert('Failed to load contacts', 'danger');
    }
}

function updatePagination(itemCount, currentPage, pageSize) {
    const pagination = document.getElementById('pagination');
    if (!pagination) return;
    
    // Simple pagination - show previous, current, next
    pagination.innerHTML = `
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="loadContacts(${currentPage - 1}); return false;">
                <i class="fas fa-chevron-left"></i> Previous
            </a>
        </li>
        <li class="page-item active">
            <span class="page-link">${currentPage}</span>
        </li>
        <li class="page-item ${itemCount < pageSize ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="loadContacts(${currentPage + 1}); return false;">
                Next <i class="fas fa-chevron-right"></i>
            </a>
        </li>
    `;
}

// Contact detail functions
async function viewContactDetails(contactId) {
    try {
        const response = await fetch(`${API_BASE_URL}/contacts/${contactId}`);
        if (!response.ok) throw new Error('Failed to fetch contact details');
        
        const contact = await response.json();
        
        // Populate modal
        const modalBody = document.getElementById('contact-detail-body');
        if (modalBody) {
            modalBody.innerHTML = `
                <div class="row">
                    <div class="col-md-6">
                        <h6>Contact Information</h6>
                        <table class="table table-sm">
                            <tr><td><strong>ID:</strong></td><td>${contact.id}</td></tr>
                            <tr><td><strong>Method:</strong></td><td>
                                <i class="${getMethodIcon(contact.method)}"></i> ${contact.method}
                            </td></tr>
                            <tr><td><strong>Value:</strong></td><td>${contact.value}</td></tr>
                            <tr><td><strong>Confidence:</strong></td><td>
                                <span class="badge ${getConfidenceBadgeClass(contact.confidence)}">
                                    ${contact.confidence}
                                </span>
                            </td></tr>
                            <tr><td><strong>Status:</strong></td><td>
                                <span class="badge ${getStatusBadgeClass(contact.status)}">
                                    ${contact.status}
                                </span>
                            </td></tr>
                        </table>
                    </div>
                    <div class="col-md-6">
                        <h6>Metadata</h6>
                        <table class="table table-sm">
                            <tr><td><strong>Source:</strong></td><td>${contact.source}</td></tr>
                            <tr><td><strong>Created:</strong></td><td>${formatDate(contact.created_at)}</td></tr>
                            <tr><td><strong>Updated:</strong></td><td>${formatDate(contact.updated_at)}</td></tr>
                        </table>
                    </div>
                </div>
                ${contact.context ? `
                <div class="row mt-3">
                    <div class="col-12">
                        <h6>Context</h6>
                        <pre class="bg-light p-3 rounded"><code>${JSON.stringify(contact.context, null, 2)}</code></pre>
                    </div>
                </div>
                ` : ''}
                ${contact.raw_data ? `
                <div class="row mt-3">
                    <div class="col-12">
                        <h6>Raw Data</h6>
                        <pre class="bg-light p-3 rounded"><code>${JSON.stringify(contact.raw_data, null, 2)}</code></pre>
                    </div>
                </div>
                ` : ''}
            `;
        }
        
        // Store current contact ID for actions
        window.currentContactId = contactId;
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('contact-detail-modal'));
        modal.show();
        
    } catch (error) {
        console.error('Error loading contact details:', error);
        showAlert('Failed to load contact details', 'danger');
    }
}

// Contact actions
async function approveContact(contactId = null) {
    const id = contactId || window.currentContactId;
    if (!id) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/contacts/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                status: 'approved'
            })
        });
        
        if (!response.ok) throw new Error('Failed to approve contact');
        
        showAlert('Contact approved successfully', 'success');
        
        // Refresh data
        if (contactId) {
            loadContacts(currentPage);
        } else {
            // Close modal and refresh
            const modal = bootstrap.Modal.getInstance(document.getElementById('contact-detail-modal'));
            modal.hide();
            loadContacts(currentPage);
        }
        
    } catch (error) {
        console.error('Error approving contact:', error);
        showAlert('Failed to approve contact', 'danger');
    }
}

async function rejectContact(contactId = null) {
    const id = contactId || window.currentContactId;
    if (!id) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/contacts/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                status: 'rejected'
            })
        });
        
        if (!response.ok) throw new Error('Failed to reject contact');
        
        showAlert('Contact rejected successfully', 'success');
        
        // Refresh data
        if (contactId) {
            loadContacts(currentPage);
        } else {
            // Close modal and refresh
            const modal = bootstrap.Modal.getInstance(document.getElementById('contact-detail-modal'));
            modal.hide();
            loadContacts(currentPage);
        }
        
    } catch (error) {
        console.error('Error rejecting contact:', error);
        showAlert('Failed to reject contact', 'danger');
    }
}

// Bulk actions
function toggleSelectAll() {
    const selectAllCheckbox = document.getElementById('select-all');
    const contactCheckboxes = document.querySelectorAll('.contact-checkbox');
    
    contactCheckboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
        const contactId = parseInt(checkbox.value);
        if (selectAllCheckbox.checked) {
            selectedContacts.add(contactId);
        } else {
            selectedContacts.delete(contactId);
        }
    });
}

function toggleContactSelection(contactId) {
    if (selectedContacts.has(contactId)) {
        selectedContacts.delete(contactId);
    } else {
        selectedContacts.add(contactId);
    }
}

function bulkApproveSelected() {
    if (selectedContacts.size === 0) {
        showAlert('No contacts selected', 'warning');
        return;
    }
    
    const contactIds = Array.from(selectedContacts);
    showBulkActionModal('approve', contactIds);
}

function bulkRejectSelected() {
    if (selectedContacts.size === 0) {
        showAlert('No contacts selected', 'warning');
        return;
    }
    
    const contactIds = Array.from(selectedContacts);
    showBulkActionModal('reject', contactIds);
}

function showBulkActionModal(action, contactIds) {
    const modal = new bootstrap.Modal(document.getElementById('bulk-action-modal'));
    const message = document.getElementById('bulk-action-message');
    
    const actionText = action === 'approve' ? 'approve' : 'reject';
    message.textContent = `Are you sure you want to ${actionText} ${contactIds.length} selected contact(s)?`;
    
    window.bulkActionData = {
        action: action,
        contactIds: contactIds
    };
    
    modal.show();
}

async function confirmBulkAction() {
    if (!window.bulkActionData) return;
    
    const { action, contactIds } = window.bulkActionData;
    const notes = document.getElementById('bulk-action-notes').value;
    
    try {
        // Since bulk-update endpoint doesn't exist, process contacts individually
        let successCount = 0;
        const updatePromises = contactIds.map(async (contactId) => {
            try {
                const response = await fetch(`${API_BASE_URL}/contacts/${contactId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        status: action === 'approve' ? 'approved' : 'rejected'
                    })
                });
                
                if (response.ok) {
                    successCount++;
                    return true;
                }
                return false;
            } catch (error) {
                console.error(`Error updating contact ${contactId}:`, error);
                return false;
            }
        });
        
        await Promise.all(updatePromises);
        
        showAlert(`Successfully ${action}d ${successCount} contacts`, 'success');
        
        // Close modal and refresh
        const modal = bootstrap.Modal.getInstance(document.getElementById('bulk-action-modal'));
        modal.hide();
        
        // Clear selection
        selectedContacts.clear();
        
        // Refresh contacts
        loadContacts(currentPage);
        
    } catch (error) {
        console.error('Error performing bulk action:', error);
        showAlert('Failed to perform bulk action', 'danger');
    }
}

// Filter functions
function applyFilters() {
    currentFilters = {
        method: document.getElementById('filter-method').value,
        confidence: document.getElementById('filter-confidence').value,
        status: document.getElementById('filter-status').value,
        source: document.getElementById('filter-source').value
    };
    
    // Remove empty filters
    Object.keys(currentFilters).forEach(key => {
        if (!currentFilters[key]) {
            delete currentFilters[key];
        }
    });
    
    loadContacts(1);
}

function clearFilters() {
    document.getElementById('filter-method').value = '';
    document.getElementById('filter-confidence').value = '';
    document.getElementById('filter-status').value = '';
    document.getElementById('filter-source').value = '';
    
    currentFilters = {};
    loadContacts(1);
}

// Export functions
async function exportContacts() {
    try {
        const params = new URLSearchParams();
        if (currentFilters.status) {
            params.append('status', currentFilters.status);
        }
        params.append('format', 'csv');
        
        const response = await fetch(`${API_BASE_URL}/contacts/export?${params}`);
        if (!response.ok) throw new Error('Failed to export contacts');
        
        const result = await response.json();
        
        // Create download link
        const blob = new Blob([result.csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `contacts_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showAlert('Contacts exported successfully', 'success');
        
    } catch (error) {
        console.error('Error exporting contacts:', error);
        showAlert('Failed to export contacts', 'danger');
    }
}

// Quick action functions
function bulkApprove() {
    // Approve all pending contacts
    if (confirm('Are you sure you want to approve all pending contacts?')) {
        // This would need a special endpoint to approve all pending
        showAlert('Bulk approve all pending contacts - feature coming soon', 'info');
    }
}

function bulkReview() {
    // Mark all pending contacts for review
    if (confirm('Are you sure you want to mark all pending contacts for review?')) {
        // This would need a special endpoint to mark all for review
        showAlert('Bulk review all pending contacts - feature coming soon', 'info');
    }
}

function refreshStats() {
    loadDashboardStats();
    loadTopSources();
    updateLastUpdated();
    showAlert('Statistics refreshed', 'success');
}

function refreshContacts() {
    loadContacts(currentPage);
    updateLastUpdated();
    showAlert('Contacts refreshed', 'success');
}

// System status indicator updates
function updateSystemStatusIndicators(stats) {
    // Update connection status
    const connectionElement = document.getElementById('connection-status');
    if (connectionElement) {
        connectionElement.className = 'fas fa-circle text-success';
        const connectionText = document.getElementById('connection-text');
        if (connectionText) {
            connectionText.textContent = 'Online';
        }
    }
    
    // Update system status indicators if they exist
    const statusIndicators = [
        { id: 'scraper-status', status: 'Active', class: 'text-success' },
        { id: 'discovery-status', status: 'Running', class: 'text-success' },
        { id: 'notification-status', status: 'Connected', class: 'text-success' },
        { id: 'database-status', status: 'Synced', class: 'text-success' }
    ];
    
    statusIndicators.forEach(({ id, status, class: statusClass }) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = status;
            element.className = `status-text ${statusClass}`;
        }
    });
}

// Dashboard refresh functions
function refreshDashboard() {
    loadDashboardStats();
    loadRecentContacts();
    loadTopSources();
    updateLastUpdated();
    showAlert('Dashboard refreshed successfully', 'success');
}

function showQuickSetup() {
    window.location.href = '/dashboard/setup/welcome';
}

// Quick action functions for dashboard
function startNewSearch() {
    window.location.href = '/dashboard/search';
}

function reviewContacts() {
    window.location.href = '/dashboard/contacts';
}

function exportData() {
    showAlert('Export functionality coming soon', 'info');
}

function openSettings() {
    window.location.href = '/api/v1/config';
}

function viewAllActivity() {
    window.location.href = '/dashboard/contacts';
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Set up event listeners
    const filterInputs = ['filter-method', 'filter-confidence', 'filter-status', 'filter-source'];
    filterInputs.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('change', applyFilters);
        }
    });
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Load initial data
    if (document.body.classList.contains('dashboard-page')) {
        loadDashboardStats();
        loadRecentContacts();
        loadTopSources();
    }
});