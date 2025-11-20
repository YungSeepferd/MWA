/**
 * Search Management JavaScript
 * Interactive search configuration and management functionality
 */

class SearchManagement {
    constructor() {
        this.currentSearchConfig = {};
        this.editorMode = 'visual';
        this.munichDistricts = [
            { id: 1, name: 'Altstadt-Lehel', code: '01' },
            { id: 2, name: 'Ludwigsvorstadt-Isarvorstadt', code: '02' },
            { id: 3, name: 'Maxvorstadt', code: '03' },
            { id: 4, name: 'Schwabing-West', code: '04' },
            { id: 5, name: 'Au-Haidhausen', code: '05' },
            { id: 6, name: 'Schwabing-Freimann', code: '06' },
            { id: 7, name: 'Neuhausen-Nymphenburg', code: '07' },
            { id: 8, name: 'Moosach', code: '08' },
            { id: 9, name: 'Milbertshofen-Am Hart', code: '09' },
            { id: 10, name: 'Schwanthalerhöhe', code: '10' },
            { id: 11, name: 'Laim', code: '11' },
            { id: 12, name: 'Thalkirchen-Obersendling-Forstenried', code: '12' },
            { id: 13, name: 'Hadern', code: '13' },
            { id: 14, name: 'Pasing-Obermenzing', code: '14' },
            { id: 15, name: 'Aubing-Lochhausen-Langwied', code: '15' },
            { id: 16, name: 'Ramersdorf-Perlach', code: '16' },
            { id: 17, name: 'Trudering-Riem', code: '17' },
            { id: 18, name: 'Berg am Laim', code: '18' },
            { id: 19, name: 'Bogenhausen', code: '19' },
            { id: 20, name: 'Untergiesing-Harlaching', code: '20' },
            { id: 21, name: 'Thalkirchen-Obersendling-Forstenried-Fürstenried', code: '21' },
            { id: 22, name: 'Laim', code: '22' },
            { id: 23, name: 'Lohhof', code: '23' },
            { id: 24, name: 'Taufkirchen', code: '24' },
            { id: 25, name: 'Unterhaching', code: '25' }
        ];
        this.selectedDistricts = new Set();
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.renderDistricts();
        this.loadSearchConfigurations();
        this.updatePriceDisplay();
        this.loadSearchStatistics();
    }

    setupEventListeners() {
        // Price range controls
        const minPriceInput = document.getElementById('min-price');
        const maxPriceInput = document.getElementById('max-price');
        const priceSlider = document.getElementById('price-range-slider');
        
        if (minPriceInput) minPriceInput.addEventListener('input', () => this.updatePriceDisplay());
        if (maxPriceInput) maxPriceInput.addEventListener('input', () => this.updatePriceDisplay());
        if (priceSlider) priceSlider.addEventListener('input', () => this.updatePriceDisplay());

        // Schedule options
        document.querySelectorAll('input[name="schedule"]').forEach(radio => {
            radio.addEventListener('change', (e) => this.handleScheduleChange(e));
        });

        // Custom interval
        const customInterval = document.getElementById('custom-interval');
        if (customInterval) {
            customInterval.addEventListener('input', () => this.updateScheduleDisplay());
        }

        // Room selection
        document.querySelectorAll('input[name="rooms"]').forEach(radio => {
            radio.addEventListener('change', (e) => this.updateRoomDisplay(e));
        });

        // Move-in date
        const moveInDate = document.getElementById('move-in-date');
        if (moveInDate) {
            moveInDate.addEventListener('change', () => this.updateMoveInDateDisplay());
        }
    }

    renderDistricts() {
        const districtGrid = document.getElementById('district-grid');
        if (!districtGrid) return;

        districtGrid.innerHTML = this.munichDistricts.map(district => `
            <div class="district-card" data-district-id="${district.id}">
                <div class="district-code">${district.code}</div>
                <div class="district-name">${district.name}</div>
            </div>
        `).join('');

        // Add click event listeners to district cards
        districtGrid.addEventListener('click', (e) => {
            const districtCard = e.target.closest('.district-card');
            if (districtCard) {
                const districtId = parseInt(districtCard.dataset.districtId);
                this.toggleDistrict(districtId, districtCard);
            }
        });
    }

    toggleDistrict(districtId, districtCard) {
        if (this.selectedDistricts.has(districtId)) {
            this.selectedDistricts.delete(districtId);
            districtCard.classList.remove('selected');
        } else {
            this.selectedDistricts.add(districtId);
            districtCard.classList.add('selected');
        }
        this.updateSelectedDistrictsDisplay();
    }

    updateSelectedDistrictsDisplay() {
        const selectedDistrictsElement = document.getElementById('selected-districts');
        if (!selectedDistrictsElement) return;

        if (this.selectedDistricts.size === 0) {
            selectedDistrictsElement.innerHTML = '<small class="text-muted">No districts selected</small>';
        } else {
            const selectedNames = Array.from(this.selectedDistricts).map(id => {
                const district = this.munichDistricts.find(d => d.id === id);
                return district ? district.name : '';
            });
            selectedDistrictsElement.innerHTML = `
                <small class="text-success">
                    ${selectedNames.join(', ')} (${this.selectedDistricts.size} selected)
                </small>
            `;
        }
    }

    updatePriceDisplay() {
        const minPrice = parseInt(document.getElementById('min-price')?.value || 0);
        const maxPrice = parseInt(document.getElementById('max-price')?.value || 0);
        const priceSlider = document.getElementById('price-range-slider');
        const priceDisplay = document.getElementById('price-display');

        if (priceDisplay) {
            priceDisplay.textContent = `€${minPrice.toLocaleString()} - €${maxPrice.toLocaleString()}`;
        }

        // Update slider based on input values
        if (priceSlider && maxPrice > 0) {
            priceSlider.max = Math.max(maxPrice, 1000);
            priceSlider.value = maxPrice;
        }
    }

    updateRoomDisplay(event) {
        const selectedRoom = event.target.value;
        console.log('Room selected:', selectedRoom);
        // Additional room-specific logic can be added here
    }

    updateMoveInDateDisplay() {
        const moveInDate = document.getElementById('move-in-date').value;
        if (moveInDate) {
            const date = new Date(moveInDate);
            const options = { month: 'long', year: 'numeric' };
            console.log('Move-in date set:', date.toLocaleDateString('de-DE', options));
        }
    }

    handleScheduleChange(event) {
        const selectedSchedule = event.target.value;
        const customSchedule = document.getElementById('custom-schedule');
        
        if (customSchedule) {
            customSchedule.style.display = selectedSchedule === 'custom' ? 'block' : 'none';
        }
        
        this.updateScheduleDisplay();
    }

    updateScheduleDisplay() {
        const selectedSchedule = document.querySelector('input[name="schedule"]:checked')?.value;
        console.log('Schedule updated:', selectedSchedule);
    }

    async loadSearchConfigurations() {
        try {
            const response = await fetch('/api/v1/search/configurations');
            if (!response.ok) throw new Error('Failed to load search configurations');
            
            const configurations = await response.json();
            this.renderSearchConfigurations(configurations);
            
        } catch (error) {
            console.error('Error loading search configurations:', error);
            this.renderDefaultConfigurations();
        }
    }

    renderSearchConfigurations(configurations) {
        const grid = document.getElementById('active-searches-grid');
        if (!grid) return;

        if (configurations.length === 0) {
            grid.innerHTML = `
                <div class="no-searches-state">
                    <i class="fas fa-search fa-3x text-muted mb-3"></i>
                    <h5>No Active Searches</h5>
                    <p class="text-muted">Create your first search to start finding apartments</p>
                    <button class="btn btn-primary" onclick="createNewSearch()">Create Search</button>
                </div>
            `;
            return;
        }

        grid.innerHTML = configurations.map(config => `
            <div class="search-card ${config.status}">
                <div class="search-card-header">
                    <h6>${config.name}</h6>
                    <span class="badge bg-${this.getStatusBadgeColor(config.status)}">${config.status}</span>
                </div>
                <div class="search-card-body">
                    <div class="search-criteria">
                        <small><strong>Price:</strong> €${config.min_price} - €${config.max_price}</small>
                        <small><strong>Rooms:</strong> ${config.min_rooms}+</small>
                        <small><strong>Districts:</strong> ${config.districts?.length || 0} selected</small>
                    </div>
                    <div class="search-stats">
                        <small><strong>Last Run:</strong> ${this.formatRelativeTime(config.last_run)}</small>
                        <small><strong>Results:</strong> ${config.results_count || 0}</small>
                    </div>
                </div>
                <div class="search-card-actions">
                    <button class="btn btn-sm btn-outline-primary" onclick="editSearch(${config.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-success" onclick="toggleSearch(${config.id})">
                        <i class="fas fa-${config.status === 'running' ? 'pause' : 'play'}"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteSearch(${config.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }

    renderDefaultConfigurations() {
        const grid = document.getElementById('active-searches-grid');
        if (grid) {
            grid.innerHTML = `
                <div class="no-searches-state">
                    <i class="fas fa-search fa-3x text-muted mb-3"></i>
                    <h5>No Search Configurations</h5>
                    <p class="text-muted">Configure your first search to get started</p>
                    <button class="btn btn-primary" onclick="createNewSearch()">Get Started</button>
                </div>
            `;
        }
    }

    async loadSearchStatistics() {
        try {
            const response = await fetch('/api/v1/search/statistics');
            if (!response.ok) throw new Error('Failed to load search statistics');
            
            const stats = await response.json();
            this.updateStatisticsDisplay(stats);
            
        } catch (error) {
            console.error('Error loading search statistics:', error);
            this.setDefaultStatistics();
        }
    }

    updateStatisticsDisplay(stats) {
        const updates = [
            { id: 'total-searches', value: stats.total_searches || 0 },
            { id: 'running-searches', value: stats.running_searches || 0 },
            { id: 'results-today', value: stats.results_today || 0 },
            { id: 'success-rate', value: `${stats.success_rate || 0}%` }
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
            { id: 'total-searches', value: 0 },
            { id: 'running-searches', value: 0 },
            { id: 'results-today', value: 0 },
            { id: 'success-rate', value: '0%' }
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

    getStatusBadgeColor(status) {
        const colors = {
            'running': 'success',
            'paused': 'warning',
            'completed': 'info',
            'error': 'danger',
            'idle': 'secondary'
        };
        return colors[status] || 'secondary';
    }

    formatRelativeTime(timestamp) {
        if (!timestamp) return 'Never';
        
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

    switchEditorMode(mode) {
        this.editorMode = mode;
        
        // Update button states
        document.querySelectorAll('.btn-group .btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[onclick="switchEditorMode('${mode}')"]`).classList.add('active');
        
        // Show/hide editor modes
        document.querySelectorAll('.editor-mode').forEach(editor => {
            editor.classList.remove('active');
        });
        document.getElementById(`${mode}-editor`).classList.add('active');
    }

    getCurrentConfiguration() {
        const config = {
            name: document.getElementById('search-name')?.value || 'New Search',
            min_price: parseInt(document.getElementById('min-price')?.value || 0),
            max_price: parseInt(document.getElementById('max-price')?.value || 0),
            min_rooms: document.querySelector('input[name="rooms"]:checked')?.value || 1,
            districts: Array.from(this.selectedDistricts),
            move_in_date: document.getElementById('move-in-date')?.value,
            amenities: this.getSelectedAmenities(),
            providers: this.getSelectedProviders(),
            schedule: this.getSelectedSchedule()
        };

        if (this.editorMode === 'advanced') {
            config.advanced_query = document.getElementById('advanced-query')?.value;
        }

        return config;
    }

    getSelectedAmenities() {
        const amenities = [];
        document.querySelectorAll('#amenities-grid input[type="checkbox"]:checked').forEach(checkbox => {
            amenities.push(checkbox.id.replace('amenity-', ''));
        });
        return amenities;
    }

    getSelectedProviders() {
        const providers = [];
        document.querySelectorAll('.provider-list input[type="checkbox"]:checked').forEach(checkbox => {
            providers.push(checkbox.id.replace('provider-', ''));
        });
        return providers;
    }

    getSelectedSchedule() {
        const selectedSchedule = document.querySelector('input[name="schedule"]:checked')?.value;
        const schedule = { type: selectedSchedule };
        
        if (selectedSchedule === 'custom') {
            schedule.interval = parseInt(document.getElementById('custom-interval')?.value || 60);
        }
        
        return schedule;
    }

    async previewSearch() {
        const config = this.getCurrentConfiguration();
        
        try {
            const response = await fetch('/api/v1/search/preview', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
            
            if (!response.ok) throw new Error('Failed to preview search');
            
            const preview = await response.json();
            this.showSearchPreview(preview);
            
        } catch (error) {
            console.error('Error previewing search:', error);
            this.showNotification('Failed to preview search', 'error');
        }
    }

    showSearchPreview(preview) {
        const modalBody = document.getElementById('preview-results');
        if (!modalBody) return;

        modalBody.innerHTML = `
            <div class="preview-summary">
                <h6>Search Configuration</h6>
                <p><strong>Estimated Results:</strong> ${preview.estimated_results || 0} listings</p>
                <p><strong>Search Time:</strong> ~${preview.estimated_time || 0} seconds</p>
                <p><strong>Providers:</strong> ${preview.providers?.join(', ') || 'None'}</p>
            </div>
            ${preview.sample_results ? `
                <div class="preview-listings">
                    <h6>Sample Results</h6>
                    ${preview.sample_results.map(listing => `
                        <div class="preview-listing">
                            <h6>${listing.title}</h6>
                            <p>${listing.location} • €${listing.price} • ${listing.rooms} rooms</p>
                        </div>
                    `).join('')}
                </div>
            ` : ''}
        `;

        const modal = new bootstrap.Modal(document.getElementById('search-preview-modal'));
        modal.show();
    }

    async saveSearch() {
        const config = this.getCurrentConfiguration();
        
        try {
            const response = await fetch('/api/v1/search/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
            
            if (!response.ok) throw new Error('Failed to save search');
            
            const savedSearch = await response.json();
            this.showNotification('Search saved successfully', 'success');
            this.loadSearchConfigurations();
            
        } catch (error) {
            console.error('Error saving search:', error);
            this.showNotification('Failed to save search', 'error');
        }
    }

    async startSearch() {
        // First preview the search
        await this.previewSearch();
        
        // Store the configuration for when user confirms
        this.pendingSearchConfig = this.getCurrentConfiguration();
    }

    async confirmAndStartSearch() {
        if (!this.pendingSearchConfig) return;
        
        try {
            const response = await fetch('/api/v1/search/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.pendingSearchConfig)
            });
            
            if (!response.ok) throw new Error('Failed to start search');
            
            const result = await response.json();
            this.showNotification('Search started successfully', 'success');
            this.loadSearchConfigurations();
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('search-preview-modal'));
            modal.hide();
            
        } catch (error) {
            console.error('Error starting search:', error);
            this.showNotification('Failed to start search', 'error');
        }
    }

    showNotification(message, type = 'info') {
        const container = document.querySelector('.toast-container') || document.body;
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
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
}

// Global functions for HTML onclick handlers
function createNewSearch() {
    window.location.href = '/dashboard/search/new';
}

function importSearch() {
    // Implementation for importing search configurations
    console.log('Import search functionality');
}

function switchEditorMode(mode) {
    if (window.searchManagement) {
        window.searchManagement.switchEditorMode(mode);
    }
}

function previewSearch() {
    if (window.searchManagement) {
        window.searchManagement.previewSearch();
    }
}

function saveSearch() {
    if (window.searchManagement) {
        window.searchManagement.saveSearch();
    }
}

function startSearch() {
    if (window.searchManagement) {
        window.searchManagement.startSearch();
    }
}

function confirmAndStartSearch() {
    if (window.searchManagement) {
        window.searchManagement.confirmAndStartSearch();
    }
}

function editSearch(searchId) {
    window.location.href = `/dashboard/search/edit/${searchId}`;
}

function toggleSearch(searchId) {
    // Implementation for toggling search status
    console.log('Toggle search:', searchId);
}

function deleteSearch(searchId) {
    if (confirm('Are you sure you want to delete this search?')) {
        // Implementation for deleting search
        console.log('Delete search:', searchId);
    }
}

// Initialize search management when DOM is loaded
let searchManagement;

document.addEventListener('DOMContentLoaded', function() {
    searchManagement = new SearchManagement();
    window.searchManagement = searchManagement;
});