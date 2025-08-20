// Image Definitions Web UI JavaScript

// Global state
let currentModal = null;
let productGroups = [];
let products = [];
let variants = [];

// API base URL
const API_BASE = '/api';

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    loadDashboard();
    loadProductGroups();
    loadProducts();
    loadVariants();
    loadArtifacts();
    
    // Set up event listeners for filters
    document.getElementById('artifact-type-filter').addEventListener('change', loadArtifacts);
    document.getElementById('artifact-status-filter').addEventListener('change', loadArtifacts);
    document.getElementById('artifact-region-filter').addEventListener('input', debounce(loadArtifacts, 500));
});

// Utility functions
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastBody = document.getElementById('toast-body');
    const toastBootstrap = new bootstrap.Toast(toast);
    
    toastBody.textContent = message;
    toast.className = `toast ${type === 'error' ? 'border-danger' : 'border-primary'}`;
    toastBootstrap.show();
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatBytes(bytes) {
    if (!bytes) return 'N/A';
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 B';
    const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Navigation
function showSection(sectionId) {
    // Update nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Show section
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById(sectionId).classList.add('active');
}

// API calls
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        showToast(error.message, 'error');
        throw error;
    }
}

// Dashboard
async function loadDashboard() {
    try {
        // Load artifact stats
        const stats = await apiCall('/artifacts/stats/summary');
        
        // Display stats cards
        const statsContainer = document.getElementById('stats-cards');
        statsContainer.innerHTML = `
            <div class="col-md-3">
                <div class="stats-card">
                    <h3>${Object.values(stats.by_status).reduce((a, b) => a + b, 0)}</h3>
                    <p>Total Artifacts</p>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stats-card">
                    <h3>${stats.by_status.completed || 0}</h3>
                    <p>Completed</p>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stats-card">
                    <h3>${stats.by_status.building || 0}</h3>
                    <p>Building</p>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stats-card">
                    <h3>${formatBytes(stats.total_size_bytes)}</h3>
                    <p>Total Size</p>
                </div>
            </div>
        `;
        
        // Load recent artifacts for activity
        const recentArtifacts = await apiCall('/artifacts?limit=10');
        const activityContainer = document.getElementById('recent-activity');
        
        if (recentArtifacts.length === 0) {
            activityContainer.innerHTML = '<p class="text-muted">No recent activity</p>';
        } else {
            activityContainer.innerHTML = recentArtifacts.map(artifact => `
                <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
                    <div>
                        <strong>${artifact.name}</strong>
                        <span class="badge badge-status badge-${artifact.status} ms-2">${artifact.status}</span>
                        <br>
                        <small class="text-muted">${artifact.artifact_type.replace('_', ' ').toUpperCase()}</small>
                    </div>
                    <small class="text-muted">${formatDate(artifact.created_at)}</small>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Failed to load dashboard:', error);
        document.getElementById('recent-activity').innerHTML = '<p class="text-danger">Failed to load recent activity</p>';
    }
}

// Product Groups
async function loadProductGroups() {
    try {
        productGroups = await apiCall('/product-groups');
        const tbody = document.querySelector('#product-groups-table tbody');
        
        if (productGroups.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No product groups found</td></tr>';
            return;
        }
        
        tbody.innerHTML = productGroups.map(group => `
            <tr>
                <td><strong>${group.name}</strong></td>
                <td>${group.description || '<span class="text-muted">No description</span>'}</td>
                <td>${formatDate(group.created_at)}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary btn-action" onclick="editItem('product-group', ${group.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger btn-action" onclick="deleteItem('product-group', ${group.id}, '${group.name}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Failed to load product groups:', error);
    }
}

// Products
async function loadProducts() {
    try {
        products = await apiCall('/products');
        const tbody = document.querySelector('#products-table tbody');
        
        if (products.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No products found</td></tr>';
            return;
        }
        
        tbody.innerHTML = products.map(product => {
            const group = productGroups.find(g => g.id === product.product_group_id);
            return `
                <tr>
                    <td><strong>${product.name}</strong></td>
                    <td>${product.version || '<span class="text-muted">No version</span>'}</td>
                    <td>${group ? group.name : 'Unknown'}</td>
                    <td>${formatDate(product.created_at)}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary btn-action" onclick="editItem('product', ${product.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger btn-action" onclick="deleteItem('product', ${product.id}, '${product.name}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        console.error('Failed to load products:', error);
    }
}

// Variants
async function loadVariants() {
    try {
        variants = await apiCall('/variants');
        const tbody = document.querySelector('#variants-table tbody');
        
        if (variants.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No variants found</td></tr>';
            return;
        }
        
        tbody.innerHTML = variants.map(variant => {
            const product = products.find(p => p.id === variant.product_id);
            return `
                <tr>
                    <td><strong>${variant.name}</strong></td>
                    <td>${variant.architecture || '<span class="text-muted">Any</span>'}</td>
                    <td>${product ? product.name : 'Unknown'}</td>
                    <td>${formatDate(variant.created_at)}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary btn-action" onclick="editItem('variant', ${variant.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger btn-action" onclick="deleteItem('variant', ${variant.id}, '${variant.name}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        console.error('Failed to load variants:', error);
    }
}

// Artifacts
async function loadArtifacts() {
    try {
        const typeFilter = document.getElementById('artifact-type-filter').value;
        const statusFilter = document.getElementById('artifact-status-filter').value;
        const regionFilter = document.getElementById('artifact-region-filter').value;
        
        let query = '/artifacts?';
        if (typeFilter) query += `artifact_type=${typeFilter}&`;
        if (statusFilter) query += `status=${statusFilter}&`;
        if (regionFilter) query += `region=${encodeURIComponent(regionFilter)}&`;
        
        const artifacts = await apiCall(query);
        const tbody = document.querySelector('#artifacts-table tbody');
        
        if (artifacts.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No artifacts found</td></tr>';
            return;
        }
        
        tbody.innerHTML = artifacts.map(artifact => {
            const variant = variants.find(v => v.id === artifact.variant_id);
            return `
                <tr>
                    <td><strong>${artifact.name}</strong></td>
                    <td><span class="badge bg-secondary">${artifact.artifact_type.replace('_', ' ')}</span></td>
                    <td><span class="badge badge-status badge-${artifact.status}">${artifact.status}</span></td>
                    <td>${artifact.region || '<span class="text-muted">N/A</span>'}</td>
                    <td>${formatBytes(artifact.size_bytes)}</td>
                    <td>${formatDate(artifact.created_at)}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary btn-action" onclick="editItem('artifact', ${artifact.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger btn-action" onclick="deleteItem('artifact', ${artifact.id}, '${artifact.name}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        console.error('Failed to load artifacts:', error);
    }
}

// Modal operations
function showCreateModal(type) {
    currentModal = { type, action: 'create', id: null };
    const modal = document.getElementById('createModal');
    const modalTitle = modal.querySelector('.modal-title');
    const modalBody = document.getElementById('modal-body');
    
    modalTitle.textContent = `Create ${type.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}`;
    
    let formHtml = '';
    
    switch (type) {
        case 'product-group':
            formHtml = `
                <div class="mb-3">
                    <label class="form-label">Name *</label>
                    <input type="text" class="form-control" id="form-name" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Description</label>
                    <textarea class="form-control" id="form-description" rows="3"></textarea>
                </div>
            `;
            break;
        case 'product':
            formHtml = `
                <div class="mb-3">
                    <label class="form-label">Name *</label>
                    <input type="text" class="form-control" id="form-name" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Version</label>
                    <input type="text" class="form-control" id="form-version">
                </div>
                <div class="mb-3">
                    <label class="form-label">Product Group *</label>
                    <select class="form-select" id="form-product-group-id" required>
                        <option value="">Select a product group</option>
                        ${productGroups.map(group => `<option value="${group.id}">${group.name}</option>`).join('')}
                    </select>
                </div>
                <div class="mb-3">
                    <label class="form-label">Description</label>
                    <textarea class="form-control" id="form-description" rows="3"></textarea>
                </div>
            `;
            break;
        case 'variant':
            formHtml = `
                <div class="mb-3">
                    <label class="form-label">Name *</label>
                    <input type="text" class="form-control" id="form-name" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Architecture</label>
                    <select class="form-select" id="form-architecture">
                        <option value="">Any</option>
                        <option value="x86_64">x86_64</option>
                        <option value="aarch64">aarch64</option>
                        <option value="ppc64le">ppc64le</option>
                        <option value="s390x">s390x</option>
                    </select>
                </div>
                <div class="mb-3">
                    <label class="form-label">Product *</label>
                    <select class="form-select" id="form-product-id" required>
                        <option value="">Select a product</option>
                        ${products.map(product => `<option value="${product.id}">${product.name}</option>`).join('')}
                    </select>
                </div>
                <div class="mb-3">
                    <label class="form-label">Description</label>
                    <textarea class="form-control" id="form-description" rows="3"></textarea>
                </div>
            `;
            break;
        case 'artifact':
            formHtml = `
                <div class="mb-3">
                    <label class="form-label">Name *</label>
                    <input type="text" class="form-control" id="form-name" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Type *</label>
                    <select class="form-select" id="form-artifact-type" required>
                        <option value="">Select type</option>
                        <option value="base_image">Base Image</option>
                        <option value="cloud_image">Cloud Image</option>
                        <option value="region_copy">Region Copy</option>
                        <option value="account_share">Account Share</option>
                    </select>
                </div>
                <div class="mb-3">
                    <label class="form-label">Variant *</label>
                    <select class="form-select" id="form-variant-id" required>
                        <option value="">Select a variant</option>
                        ${variants.map(variant => `<option value="${variant.id}">${variant.name}</option>`).join('')}
                    </select>
                </div>
                <div class="mb-3">
                    <label class="form-label">Region</label>
                    <input type="text" class="form-control" id="form-region">
                </div>
                <div class="mb-3">
                    <label class="form-label">Location</label>
                    <input type="text" class="form-control" id="form-location" placeholder="URL or path">
                </div>
            `;
            break;
    }
    
    modalBody.innerHTML = formHtml;
    const modalBootstrap = new bootstrap.Modal(modal);
    modalBootstrap.show();
}

async function submitForm() {
    if (!currentModal) return;
    
    const { type, action, id } = currentModal;
    let data = {};
    
    // Collect form data
    const formElements = document.querySelectorAll('#modal-body input, #modal-body select, #modal-body textarea');
    formElements.forEach(element => {
        const key = element.id.replace('form-', '').replace(/-/g, '_');
        let value = element.value.trim();
        
        // Convert string numbers to integers for ID fields
        if (key.includes('_id') && value) {
            value = parseInt(value);
        }
        
        if (value !== '') {
            data[key] = value;
        }
    });
    
    try {
        let endpoint = '';
        let method = 'POST';
        
        switch (type) {
            case 'product-group':
                endpoint = '/product-groups';
                break;
            case 'product':
                endpoint = '/products';
                break;
            case 'variant':
                endpoint = '/variants';
                break;
            case 'artifact':
                endpoint = '/artifacts';
                break;
        }
        
        if (action === 'edit') {
            endpoint += `/${id}`;
            method = 'PATCH';
        }
        
        await apiCall(endpoint, {
            method,
            body: JSON.stringify(data)
        });
        
        showToast(`${type.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())} ${action === 'create' ? 'created' : 'updated'} successfully!`);
        
        // Close modal and reload data
        const modal = bootstrap.Modal.getInstance(document.getElementById('createModal'));
        modal.hide();
        
        // Reload relevant data
        switch (type) {
            case 'product-group':
                await loadProductGroups();
                break;
            case 'product':
                await loadProducts();
                break;
            case 'variant':
                await loadVariants();
                break;
            case 'artifact':
                await loadArtifacts();
                break;
        }
        
        // Also reload dashboard if artifacts were modified
        if (type === 'artifact') {
            await loadDashboard();
        }
        
    } catch (error) {
        // Error already shown by apiCall
        console.error('Form submission failed:', error);
    }
}

async function deleteItem(type, id, name) {
    if (!confirm(`Are you sure you want to delete "${name}"? This action cannot be undone.`)) {
        return;
    }
    
    try {
        let endpoint = '';
        switch (type) {
            case 'product-group':
                endpoint = `/product-groups/${id}`;
                break;
            case 'product':
                endpoint = `/products/${id}`;
                break;
            case 'variant':
                endpoint = `/variants/${id}`;
                break;
            case 'artifact':
                endpoint = `/artifacts/${id}`;
                break;
        }
        
        await apiCall(endpoint, { method: 'DELETE' });
        
        showToast(`${type.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())} deleted successfully!`);
        
        // Reload relevant data
        switch (type) {
            case 'product-group':
                await loadProductGroups();
                await loadProducts(); // Products depend on groups
                await loadVariants(); // Variants depend on products
                break;
            case 'product':
                await loadProducts();
                await loadVariants(); // Variants depend on products
                break;
            case 'variant':
                await loadVariants();
                await loadArtifacts(); // Artifacts depend on variants
                break;
            case 'artifact':
                await loadArtifacts();
                await loadDashboard(); // Dashboard shows artifact stats
                break;
        }
        
    } catch (error) {
        console.error('Delete failed:', error);
    }
}
