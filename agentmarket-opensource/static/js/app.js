/**
 * AgentMarket Client-side JavaScript
 * Minimal JS - Alpine.js handles most interactivity
 */

// ==========================================================================
// Dark Mode Toggle
// ==========================================================================

/**
 * Initialize dark mode based on user preference or system setting
 */
function initDarkMode() {
    const stored = localStorage.getItem('darkMode');
    if (stored === 'true' || (stored === null && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
}

/**
 * Toggle dark mode on/off and persist to localStorage
 */
function toggleDarkMode() {
    const isDark = document.documentElement.classList.toggle('dark');
    localStorage.setItem('darkMode', isDark);
}

// Initialize on load
initDarkMode();

// Listen for system preference changes
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    if (localStorage.getItem('darkMode') === null) {
        document.documentElement.classList.toggle('dark', e.matches);
    }
});

// ==========================================================================
// HTMX Event Listeners
// ==========================================================================

// Global loading indicator
document.body.addEventListener('htmx:beforeRequest', function (evt) {
    const loader = document.getElementById('global-loader');
    if (loader) {
        loader.style.opacity = '1';
    }
});

document.body.addEventListener('htmx:afterRequest', function (evt) {
    const loader = document.getElementById('global-loader');
    if (loader) {
        loader.style.opacity = '0';
    }
});

// Add fade-in animation after HTMX swaps content
document.body.addEventListener('htmx:afterSwap', function (evt) {
    const target = evt.detail.target;
    if (target) {
        target.classList.add('fade-in');
        // Remove the class after animation completes
        setTimeout(() => {
            target.classList.remove('fade-in');
        }, 300);
    }
});

// Handle HTMX errors gracefully
document.body.addEventListener('htmx:responseError', function (evt) {
    console.error('HTMX request error:', evt.detail);
    showToast('请求失败，请稍后重试', 'error');
});

document.body.addEventListener('htmx:sendError', function (evt) {
    console.error('HTMX send error:', evt.detail);
    showToast('网络连接失败', 'error');
});

// Handle 401/403 redirects
document.body.addEventListener('htmx:beforeOnLoad', function (evt) {
    const xhr = evt.detail.xhr;
    if (xhr.status === 401) {
        evt.preventDefault();
        showToast('请先登录', 'error');
        setTimeout(() => {
            window.location.href = '/login';
        }, 1500);
    } else if (xhr.status === 403) {
        evt.preventDefault();
        showToast('没有权限执行此操作', 'error');
    }
});

// ==========================================================================
// Toast Notification System
// ==========================================================================

/**
 * Show a toast notification
 * @param {string} message - The message to display
 * @param {string} type - 'success', 'error', 'warning', or 'info'
 * @param {number} duration - Duration in milliseconds (default: 3000)
 */
function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const icons = {
        success: '<svg class="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
        error: '<svg class="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
        warning: '<svg class="w-5 h-5 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>',
        info: '<svg class="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>'
    };

    const bgColors = {
        success: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800',
        error: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800',
        warning: 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800',
        info: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800'
    };

    const toast = document.createElement('div');
    toast.className = `toast flex items-center gap-3 px-4 py-3 rounded-xl border shadow-lg ${bgColors[type] || bgColors.info} max-w-sm`;
    toast.innerHTML = `
        ${icons[type] || icons.info}
        <p class="text-sm text-gray-800 dark:text-gray-200 flex-1">${message}</p>
        <button onclick="dismissToast(this.parentElement)" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 shrink-0">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
        </button>
    `;

    container.appendChild(toast);

    // Auto-dismiss
    setTimeout(() => {
        dismissToast(toast);
    }, duration);
}

/**
 * Dismiss a toast notification with animation
 * @param {HTMLElement} toast - The toast element to dismiss
 */
function dismissToast(toast) {
    if (!toast || !toast.parentElement) return;
    toast.classList.add('toast-exit');
    setTimeout(() => {
        if (toast.parentElement) {
            toast.parentElement.removeChild(toast);
        }
    }, 200);
}

// ==========================================================================
// Copy to Clipboard Utility
// ==========================================================================

/**
 * Copy text to clipboard and show a toast notification
 * @param {string} text - The text to copy
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('已复制到剪贴板', 'success');
    }).catch(() => {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.left = '-9999px';
        document.body.appendChild(textarea);
        textarea.select();
        try {
            document.execCommand('copy');
            showToast('已复制到剪贴板', 'success');
        } catch (err) {
            showToast('复制失败', 'error');
        }
        document.body.removeChild(textarea);
    });
}

// ==========================================================================
// Search Bar Keyboard Navigation
// ==========================================================================

document.addEventListener('keydown', function (e) {
    // Ctrl+K or Cmd+K to focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('input[name="q"]');
        if (searchInput) {
            searchInput.focus();
        }
    }
});

// ==========================================================================
// Mobile Menu Toggle (backup for Alpine.js)
// ==========================================================================

document.addEventListener('DOMContentLoaded', function () {
    // Close mobile menu on escape key
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            // Close any open dropdowns/menus
            document.querySelectorAll('[x-data]').forEach(el => {
                if (el.__x && el.__x.$data) {
                    if ('mobileMenuOpen' in el.__x.$data) {
                        el.__x.$data.mobileMenuOpen = false;
                    }
                    if ('userMenuOpen' in el.__x.$data) {
                        el.__x.$data.userMenuOpen = false;
                    }
                }
            });
        }
    });
});

// ==========================================================================
// Smooth Image Loading
// ==========================================================================

document.addEventListener('DOMContentLoaded', function () {
    const images = document.querySelectorAll('img[loading="lazy"]');
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.classList.add('loaded');
                    imageObserver.unobserve(img);
                }
            });
        });
        images.forEach(img => imageObserver.observe(img));
    }
});

// ==========================================================================
// HTMX Configuration
// ==========================================================================

// Set default HTMX config
document.body.addEventListener('htmx:configRequest', function (evt) {
    // Add CSRF token if available
    const csrfToken = document.querySelector('meta[name="csrf-token"]');
    if (csrfToken) {
        evt.detail.headers['X-CSRF-Token'] = csrfToken.getAttribute('content');
    }
    // Ensure credentials are sent
    evt.detail.credentials = 'include';
});

// Handle HTMX redirects
document.body.addEventListener('htmx:afterRequest', function (evt) {
    const xhr = evt.detail.xhr;
    const redirect = xhr.getResponseHeader('HX-Redirect');
    if (redirect) {
        window.location.href = redirect;
    }
    // Handle HX-Trigger events
    const trigger = xhr.getResponseHeader('HX-Trigger');
    if (trigger) {
        try {
            const events = JSON.parse(trigger);
            if (events.showToast) {
                showToast(events.showToast.message, events.showToast.type);
            }
        } catch (e) {
            // Single event name
        }
    }
});
