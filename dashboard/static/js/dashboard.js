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
const API_BASE_URL = '/api';

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
        const response = await fetch(`${API_BASE_URL}/contacts/stats`);
        if (!response.ok) throw new Error('Failed to fetch stats');
        
        const stats = await response.json();
        
        // Update statistics cards
        document.getElementById('total-contacts').textContent = stats.total_contacts;
        document.getElementById('approved-contacts').textContent = stats.contacts_by_status.approved || 0;
        document.getElementById('pending-contacts').textContent = stats.contacts_by_status.pending || 0;
        document.getElementById('rejected-contacts').textContent = stats.contacts_by_status.rejected || 0;
        
        // Update top sources
        const topSourcesList = document.getElementById('top-sources-list');
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
        
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
        showAlert('Failed to load dashboard statistics', 'danger');
    }
}

async function loadRecentContacts() {
    try {
        const response = await fetch(`${API_BASE_URL}/contacts?limit=10&offset=0`);
        if (!response.ok) throw new Error('Failed to fetch recent contacts');
        
        const contacts = await response.json();
        
        const recentContactsBody = document.getElementById('recent-contacts-body');
        if (recentContactsBody) {
            recentContactsBody.innerHTML = contacts.map(contact => `
                <tr>
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
                    <td>
                        <button class="btn btn-sm btn-outline-primary" onclick="viewContactDetails(${contact.id})">
                            <i class="fas fa-eye"></i> View
                        </button>
                    </td>
                </tr>
            `).join('');
        }
        
    } catch (error) {
        console.error('Error loading recent contacts:', error);
        showAlert('Failed to load recent contacts', 'danger');
    }
}

async function loadTopSources() {
    try {
        const response = await fetch(`${API_BASE_URL}/contacts/stats`);
        if (!response.ok) throw new Error('Failed to fetch stats');
        
        const stats = await response.json();
        
        const topSourcesList = document.getElementById('top-sources-list');
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
        
        // Update showing info
        const showingStart = (page - 1) * limit + 1;
        const showingEnd = showingStart + contacts.length - 1;
        
        document.getElementById('showing-start').textContent = showingStart;
        document.getElementById('showing-end').textContent = showingEnd;
        
        // Update total count
        const totalResponse = await fetch(`${API_BASE_URL}/contacts/stats`);
        if (totalResponse.ok) {
            const stats = await totalResponse.json();
            document.getElementById('total-contacts').textContent = stats.total_contacts;
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
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                status: 'approved',
                notes: 'Approved via dashboard'
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
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                status: 'rejected',
                notes: 'Rejected via dashboard'
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
        const response = await fetch(`${API_BASE_URL}/contacts/bulk-update`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                contact_ids: contactIds,
                status: action === 'approve' ? 'approved' : 'rejected',
                notes: notes || `Bulk ${action} via dashboard`
            })
        });
        
        if (!response.ok) throw new Error('Failed to perform bulk action');
        
        const result = await response.json();
        
        showAlert(`Successfully ${action}d ${result.updated_count} contacts`, 'success');
        
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
});