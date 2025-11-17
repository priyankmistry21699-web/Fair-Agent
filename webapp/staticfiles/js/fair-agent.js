/**
 * FAIR-Agent JavaScript Utilities
 * Core functionality for the FAIR-Agent web application
 */

// Global configuration
const FAIR_CONFIG = {
    apiBaseUrl: '/api',
    wsBaseUrl: (window.location.protocol === 'https:' ? 'wss:' : 'ws:') + '//' + window.location.host + '/ws',
    refreshInterval: 30000, // 30 seconds
    chartUpdateInterval: 5000, // 5 seconds
    maxRetries: 3,
    retryDelay: 1000
};

// Global state
const FAIR_STATE = {
    websockets: new Map(),
    charts: new Map(),
    intervals: new Map(),
    cache: new Map(),
    isOnline: navigator.onLine
};

/**
 * Utility Functions
 */
const FairUtils = {
    /**
     * Get CSRF token for AJAX requests
     */
    getCsrfToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    },

    /**
     * Format numbers with proper suffixes
     */
    formatNumber(num) {
        if (num === null || num === undefined) return '0';
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    },

    /**
     * Format percentage with specified decimal places
     */
    formatPercentage(value, decimals = 1) {
        if (value === null || value === undefined) return '0%';
        return (parseFloat(value) || 0).toFixed(decimals) + '%';
    },

    /**
     * Format timestamp to human-readable format
     */
    formatTimestamp(timestamp) {
        if (!timestamp) return 'N/A';
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        if (diff < 60000) { // Less than 1 minute
            return 'Just now';
        } else if (diff < 3600000) { // Less than 1 hour
            const minutes = Math.floor(diff / 60000);
            return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
        } else if (diff < 86400000) { // Less than 1 day
            const hours = Math.floor(diff / 3600000);
            return `${hours} hour${hours > 1 ? 's' : ''} ago`;
        } else {
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
        }
    },

    /**
     * Format duration in seconds to human-readable format
     */
    formatDuration(seconds) {
        if (!seconds || seconds < 0) return '0s';
        
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (days > 0) return `${days}d ${hours}h`;
        if (hours > 0) return `${hours}h ${minutes}m`;
        if (minutes > 0) return `${minutes}m ${secs}s`;
        return `${secs}s`;
    },

    /**
     * Debounce function to limit API calls
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Throttle function to limit execution frequency
     */
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    /**
     * Generate unique ID
     */
    generateId() {
        return 'fair_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    },

    /**
     * Validate email format
     */
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },

    /**
     * Sanitize HTML to prevent XSS
     */
    sanitizeHtml(str) {
        const temp = document.createElement('div');
        temp.textContent = str;
        return temp.innerHTML;
    },

    /**
     * Copy text to clipboard
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            try {
                document.execCommand('copy');
                return true;
            } catch (fallbackErr) {
                return false;
            } finally {
                document.body.removeChild(textArea);
            }
        }
    }
};

/**
 * API Service
 */
const FairAPI = {
    /**
     * Make HTTP request with error handling and retries
     */
    async request(url, options = {}) {
        const config = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': FairUtils.getCsrfToken()
            },
            ...options
        };

        let retries = 0;
        while (retries < FAIR_CONFIG.maxRetries) {
            try {
                const response = await fetch(FAIR_CONFIG.apiBaseUrl + url, config);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                return data;
            } catch (error) {
                retries++;
                if (retries >= FAIR_CONFIG.maxRetries) {
                    throw error;
                }
                await new Promise(resolve => setTimeout(resolve, FAIR_CONFIG.retryDelay * retries));
            }
        }
    },

    /**
     * GET request
     */
    async get(url, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const fullUrl = queryString ? `${url}?${queryString}` : url;
        return this.request(fullUrl);
    },

    /**
     * POST request
     */
    async post(url, data = {}) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    /**
     * PUT request
     */
    async put(url, data = {}) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    /**
     * DELETE request
     */
    async delete(url) {
        return this.request(url, {
            method: 'DELETE'
        });
    }
};

/**
 * WebSocket Manager
 */
const FairWebSocket = {
    /**
     * Create WebSocket connection
     */
    connect(endpoint, handlers = {}) {
        const wsUrl = `${FAIR_CONFIG.wsBaseUrl}${endpoint}`;
        const ws = new WebSocket(wsUrl);
        
        ws.onopen = (event) => {
            console.log(`WebSocket connected: ${endpoint}`);
            if (handlers.onOpen) handlers.onOpen(event);
        };
        
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (handlers.onMessage) handlers.onMessage(data);
            } catch (error) {
                console.error('WebSocket message parsing error:', error);
            }
        };
        
        ws.onclose = (event) => {
            console.log(`WebSocket closed: ${endpoint}`);
            if (handlers.onClose) handlers.onClose(event);
            
            // Auto-reconnect after delay
            if (!event.wasClean) {
                setTimeout(() => {
                    this.connect(endpoint, handlers);
                }, 3000);
            }
        };
        
        ws.onerror = (error) => {
            console.error(`WebSocket error: ${endpoint}`, error);
            if (handlers.onError) handlers.onError(error);
        };
        
        FAIR_STATE.websockets.set(endpoint, ws);
        return ws;
    },

    /**
     * Send message through WebSocket
     */
    send(endpoint, data) {
        const ws = FAIR_STATE.websockets.get(endpoint);
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify(data));
            return true;
        }
        return false;
    },

    /**
     * Close WebSocket connection
     */
    close(endpoint) {
        const ws = FAIR_STATE.websockets.get(endpoint);
        if (ws) {
            ws.close();
            FAIR_STATE.websockets.delete(endpoint);
        }
    }
};

/**
 * UI Components
 */
const FairUI = {
    /**
     * Show toast notification
     */
    showToast(message, type = 'info', duration = 5000) {
        const toastId = FairUtils.generateId();
        const toastHtml = `
            <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">${FairUtils.sanitizeHtml(message)}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        // Create toast container if it doesn't exist
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'position-fixed top-0 end-0 p-3';
            container.style.zIndex = '1050';
            document.body.appendChild(container);
        }
        
        container.insertAdjacentHTML('beforeend', toastHtml);
        
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, { delay: duration });
        toast.show();
        
        // Remove toast element after it's hidden
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
        
        return toastId;
    },

    /**
     * Show loading state on element
     */
    showLoading(element, text = 'Loading...') {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        
        if (!element) return;
        
        const originalContent = element.innerHTML;
        element.dataset.originalContent = originalContent;
        
        const spinner = '<span class="loading-spinner me-2"></span>';
        element.innerHTML = spinner + text;
        element.disabled = true;
    },

    /**
     * Hide loading state
     */
    hideLoading(element) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        
        if (!element) return;
        
        const originalContent = element.dataset.originalContent;
        if (originalContent) {
            element.innerHTML = originalContent;
            delete element.dataset.originalContent;
        }
        element.disabled = false;
    },

    /**
     * Show modal dialog
     */
    showModal(title, content, actions = []) {
        const modalId = FairUtils.generateId();
        const modalHtml = `
            <div class="modal fade" id="${modalId}" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${FairUtils.sanitizeHtml(title)}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            ${content}
                        </div>
                        <div class="modal-footer">
                            ${actions.map(action => `
                                <button type="button" class="btn ${action.class || 'btn-secondary'}" 
                                        onclick="${action.onclick || ''}" 
                                        data-bs-dismiss="${action.dismiss || 'modal'}">
                                    ${FairUtils.sanitizeHtml(action.text)}
                                </button>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        const modalElement = document.getElementById(modalId);
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
        
        // Remove modal element after it's hidden
        modalElement.addEventListener('hidden.bs.modal', () => {
            modalElement.remove();
        });
        
        return modalId;
    },

    /**
     * Update progress bar
     */
    updateProgress(elementId, percentage) {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.width = Math.min(Math.max(percentage, 0), 100) + '%';
            element.setAttribute('aria-valuenow', percentage);
        }
    },

    /**
     * Animate counter
     */
    animateCounter(elementId, targetValue, duration = 1000) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        const startValue = parseInt(element.textContent) || 0;
        const difference = targetValue - startValue;
        const increment = difference / (duration / 16); // 60fps
        
        let currentValue = startValue;
        const timer = setInterval(() => {
            currentValue += increment;
            if ((increment > 0 && currentValue >= targetValue) || 
                (increment < 0 && currentValue <= targetValue)) {
                currentValue = targetValue;
                clearInterval(timer);
            }
            element.textContent = Math.round(currentValue);
        }, 16);
    }
};

/**
 * Chart Utilities
 */
const FairCharts = {
    /**
     * Default chart configuration
     */
    defaultConfig: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true,
                position: 'top'
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: {
                    color: 'rgba(0, 0, 0, 0.1)'
                }
            },
            x: {
                grid: {
                    color: 'rgba(0, 0, 0, 0.1)'
                }
            }
        }
    },

    /**
     * Create line chart
     */
    createLineChart(canvasId, data, options = {}) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        const config = {
            type: 'line',
            data: data,
            options: { ...this.defaultConfig, ...options }
        };
        
        const chart = new Chart(ctx, config);
        FAIR_STATE.charts.set(canvasId, chart);
        return chart;
    },

    /**
     * Create bar chart
     */
    createBarChart(canvasId, data, options = {}) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        const config = {
            type: 'bar',
            data: data,
            options: { ...this.defaultConfig, ...options }
        };
        
        const chart = new Chart(ctx, config);
        FAIR_STATE.charts.set(canvasId, chart);
        return chart;
    },

    /**
     * Create doughnut chart
     */
    createDoughnutChart(canvasId, data, options = {}) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        const config = {
            type: 'doughnut',
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: true,
                ...options
            }
        };
        
        const chart = new Chart(ctx, config);
        FAIR_STATE.charts.set(canvasId, chart);
        return chart;
    },

    /**
     * Update chart data
     */
    updateChart(canvasId, newData) {
        const chart = FAIR_STATE.charts.get(canvasId);
        if (chart) {
            chart.data = newData;
            chart.update();
        }
    },

    /**
     * Destroy chart
     */
    destroyChart(canvasId) {
        const chart = FAIR_STATE.charts.get(canvasId);
        if (chart) {
            chart.destroy();
            FAIR_STATE.charts.delete(canvasId);
        }
    }
};

/**
 * Cache Manager
 */
const FairCache = {
    /**
     * Set cache item with expiration
     */
    set(key, value, expirationMinutes = 5) {
        const expirationTime = new Date().getTime() + (expirationMinutes * 60000);
        const cacheItem = {
            value: value,
            expiration: expirationTime
        };
        FAIR_STATE.cache.set(key, cacheItem);
    },

    /**
     * Get cache item
     */
    get(key) {
        const cacheItem = FAIR_STATE.cache.get(key);
        if (!cacheItem) return null;
        
        if (new Date().getTime() > cacheItem.expiration) {
            FAIR_STATE.cache.delete(key);
            return null;
        }
        
        return cacheItem.value;
    },

    /**
     * Clear cache
     */
    clear() {
        FAIR_STATE.cache.clear();
    },

    /**
     * Remove expired items
     */
    cleanup() {
        const now = new Date().getTime();
        for (const [key, item] of FAIR_STATE.cache.entries()) {
            if (now > item.expiration) {
                FAIR_STATE.cache.delete(key);
            }
        }
    }
};

/**
 * Event Handlers
 */
const FairEvents = {
    /**
     * Initialize global event listeners
     */
    init() {
        // Online/offline status
        window.addEventListener('online', () => {
            FAIR_STATE.isOnline = true;
            FairUI.showToast('Connection restored', 'success');
        });
        
        window.addEventListener('offline', () => {
            FAIR_STATE.isOnline = false;
            FairUI.showToast('Connection lost', 'warning');
        });
        
        // Page visibility change
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                // Pause non-critical updates when page is hidden
                this.pauseUpdates();
            } else {
                // Resume updates when page becomes visible
                this.resumeUpdates();
            }
        });
        
        // Before page unload
        window.addEventListener('beforeunload', () => {
            // Close WebSocket connections
            for (const [endpoint, ws] of FAIR_STATE.websockets.entries()) {
                ws.close();
            }
            
            // Clear intervals
            for (const [id, interval] of FAIR_STATE.intervals.entries()) {
                clearInterval(interval);
            }
        });
        
        // Cache cleanup interval
        setInterval(() => {
            FairCache.cleanup();
        }, 60000); // Every minute
    },

    /**
     * Pause updates when page is hidden
     */
    pauseUpdates() {
        for (const [id, interval] of FAIR_STATE.intervals.entries()) {
            clearInterval(interval);
        }
        FAIR_STATE.intervals.clear();
    },

    /**
     * Resume updates when page becomes visible
     */
    resumeUpdates() {
        // Trigger immediate refresh
        if (typeof refreshDashboard === 'function') {
            refreshDashboard();
        }
    }
};

/**
 * Initialize FAIR-Agent utilities
 */
document.addEventListener('DOMContentLoaded', function() {
    FairEvents.init();
    
    // Global AJAX setup
    const csrfToken = FairUtils.getCsrfToken();
    if (window.$ && $.ajaxSetup) {
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                if (!settings.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrfToken);
                }
            }
        });
    }
    
    console.log('FAIR-Agent utilities initialized');
});

// Export for use in other scripts
window.FairUtils = FairUtils;
window.FairAPI = FairAPI;
window.FairWebSocket = FairWebSocket;
window.FairUI = FairUI;
window.FairCharts = FairCharts;
window.FairCache = FairCache;
window.FAIR_CONFIG = FAIR_CONFIG;
window.FAIR_STATE = FAIR_STATE;