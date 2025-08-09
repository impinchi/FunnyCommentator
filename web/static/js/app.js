// FunnyCommentator Web Interface JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize auto-save functionality
    initializeAutoSave();
    
    // Initialize status updates
    initializeStatusUpdates();
});

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize form validation
 */
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
}

/**
 * Initialize auto-save functionality for forms
 */
function initializeAutoSave() {
    const autoSaveForms = document.querySelectorAll('[data-auto-save]');
    
    autoSaveForms.forEach(function(form) {
        const inputs = form.querySelectorAll('input, select, textarea');
        
        inputs.forEach(function(input) {
            input.addEventListener('change', function() {
                saveFormData(form);
            });
        });
        
        // Load saved data on page load
        loadFormData(form);
    });
}

/**
 * Save form data to localStorage
 */
function saveFormData(form) {
    const formId = form.id || 'default-form';
    const formData = new FormData(form);
    const data = {};
    
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    
    localStorage.setItem(`funnycommentator_${formId}`, JSON.stringify(data));
}

/**
 * Load form data from localStorage
 */
function loadFormData(form) {
    const formId = form.id || 'default-form';
    const savedData = localStorage.getItem(`funnycommentator_${formId}`);
    
    if (savedData) {
        try {
            const data = JSON.parse(savedData);
            
            Object.keys(data).forEach(function(key) {
                const element = form.querySelector(`[name="${key}"]`);
                if (element) {
                    if (element.type === 'checkbox') {
                        element.checked = data[key] === 'on';
                    } else {
                        element.value = data[key];
                    }
                }
            });
        } catch (e) {
            console.warn('Failed to load saved form data:', e);
        }
    }
}

/**
 * Clear saved form data
 */
function clearSavedFormData(formId) {
    localStorage.removeItem(`funnycommentator_${formId}`);
}

/**
 * Initialize status updates
 */
function initializeStatusUpdates() {
    const statusElements = document.querySelectorAll('[data-status-update]');
    
    if (statusElements.length > 0) {
        // Update status every 30 seconds
        setInterval(updateSystemStatus, 30000);
    }
}

/**
 * Update system status
 */
function updateSystemStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Status update failed:', data.error);
                return;
            }
            
            // Update status elements
            updateStatusElements(data);
        })
        .catch(error => {
            console.error('Error updating status:', error);
        });
}

/**
 * Update status elements on the page
 */
function updateStatusElements(statusData) {
    const statusElements = document.querySelectorAll('[data-status-update]');
    
    statusElements.forEach(function(element) {
        const statusType = element.getAttribute('data-status-update');
        
        switch (statusType) {
            case 'last-updated':
                element.textContent = statusData.last_updated;
                break;
            case 'servers-count':
                element.textContent = statusData.servers_count;
                break;
            case 'clusters-count':
                element.textContent = statusData.clusters_count;
                break;
            case 'discord-status':
                updateDiscordStatus(element, statusData.discord_configured);
                break;
        }
    });
}

/**
 * Update Discord status indicator
 */
function updateDiscordStatus(element, isConfigured) {
    const badge = element.querySelector('.badge');
    if (badge) {
        badge.className = isConfigured ? 'badge bg-success' : 'badge bg-warning';
        badge.textContent = isConfigured ? 'Configured' : 'Not Configured';
    }
}

/**
 * Show loading spinner on buttons
 */
function showButtonLoading(button, loadingText = 'Loading...') {
    button.disabled = true;
    button.innerHTML = `
        <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
        ${loadingText}
    `;
}

/**
 * Hide loading spinner on buttons
 */
function hideButtonLoading(button, originalText) {
    button.disabled = false;
    button.innerHTML = originalText;
}

/**
 * Show confirmation dialog
 */
function showConfirmDialog(title, message, onConfirm, onCancel = null) {
    const confirmed = confirm(`${title}\n\n${message}`);
    if (confirmed && onConfirm) {
        onConfirm();
    } else if (!confirmed && onCancel) {
        onCancel();
    }
    return confirmed;
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toastId = 'toast_' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <i class="bi bi-${getToastIcon(type)} text-${type} me-2"></i>
                <strong class="me-auto">FunnyCommentator</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    // Initialize and show toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
    
    // Remove toast element after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}

/**
 * Get appropriate icon for toast type
 */
function getToastIcon(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-triangle',
        'warning': 'exclamation-circle',
        'info': 'info-circle'
    };
    return icons[type] || icons['info'];
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(function() {
            showToast('Copied to clipboard!', 'success');
        }).catch(function(err) {
            console.error('Failed to copy: ', err);
            showToast('Failed to copy to clipboard', 'error');
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            showToast('Copied to clipboard!', 'success');
        } catch (err) {
            console.error('Fallback copy failed: ', err);
            showToast('Failed to copy to clipboard', 'error');
        }
        document.body.removeChild(textArea);
    }
}

/**
 * Format file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Format date/time
 */
function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

/**
 * Debounce function to limit function calls
 */
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

/**
 * Throttle function to limit function calls
 */
function throttle(func, limit) {
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
}

// Export functions for global use
window.FunnyCommentator = {
    showButtonLoading,
    hideButtonLoading,
    showConfirmDialog,
    showToast,
    copyToClipboard,
    formatFileSize,
    formatDateTime,
    debounce,
    throttle,
    updateSystemStatus,
    clearSavedFormData
};
