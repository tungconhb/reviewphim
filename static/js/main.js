// ReviewChill - Video Review Platform JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize smooth scrolling
    initializeSmoothScrolling();
    
    // Initialize lazy loading
    initializeLazyLoading();
    
    // Initialize keyboard shortcuts
    initializeKeyboardShortcuts();
    
    // Initialize theme system
    initializeTheme();
    
    // Initialize analytics
    initializeAnalytics();
}

// Tooltip initialization
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Smooth scrolling for internal links
function initializeSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Lazy loading for images
function initializeLazyLoading() {
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }
}

// Keyboard shortcuts
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl + K: Focus search
        if (e.ctrlKey && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('input[name="q"]');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // Escape: Close modals
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal.show');
            if (openModal) {
                const modal = bootstrap.Modal.getInstance(openModal);
                if (modal) {
                    modal.hide();
                }
            }
        }
        
        // Arrow keys: Navigate reviews
        if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
            navigateReviews(e.key === 'ArrowRight');
        }
    });
}

// Theme system
function initializeTheme() {
    // Check for saved theme or default to dark
    const savedTheme = localStorage.getItem('reviewchill-theme') || 'dark';
    applyTheme(savedTheme);
    
    // Theme toggle if exists
    const themeToggle = document.querySelector('#theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('reviewchill-theme', theme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    applyTheme(newTheme);
}

// Analytics and tracking
function initializeAnalytics() {
    // Track page views
    trackPageView();
    
    // Track video plays
    trackVideoInteractions();
    
    // Track search queries
    trackSearchQueries();
}

function trackPageView() {
    // Simple page view tracking
    const pageData = {
        url: window.location.href,
        title: document.title,
        timestamp: new Date().toISOString()
    };
    
    // Store in localStorage for demo purposes
    const views = JSON.parse(localStorage.getItem('reviewchill-pageviews') || '[]');
    views.push(pageData);
    
    // Keep only last 50 views
    if (views.length > 50) {
        views.splice(0, views.length - 50);
    }
    
    localStorage.setItem('reviewchill-pageviews', JSON.stringify(views));
}

function trackVideoInteractions() {
    // Track video thumbnail clicks
    document.querySelectorAll('.review-card').forEach(card => {
        card.addEventListener('click', function() {
            const videoTitle = this.querySelector('.review-title')?.textContent;
            const movieTitle = this.querySelector('.movie-title')?.textContent;
            
            trackEvent('video_click', {
                video_title: videoTitle,
                movie_title: movieTitle
            });
        });
    });
    
    // Track external link clicks
    document.querySelectorAll('a[target="_blank"]').forEach(link => {
        link.addEventListener('click', function() {
            const href = this.href;
            const text = this.textContent;
            
            trackEvent('external_link_click', {
                url: href,
                text: text
            });
        });
    });
}

function trackSearchQueries() {
    const searchForms = document.querySelectorAll('form[action*="search"]');
    searchForms.forEach(form => {
        form.addEventListener('submit', function() {
            const query = this.querySelector('input[name="q"]')?.value;
            if (query) {
                trackEvent('search', { query: query });
            }
        });
    });
}

function trackEvent(eventName, data) {
    const event = {
        name: eventName,
        data: data,
        timestamp: new Date().toISOString(),
        url: window.location.href
    };
    
    // Store events in localStorage for demo purposes
    const events = JSON.parse(localStorage.getItem('reviewchill-events') || '[]');
    events.push(event);
    
    // Keep only last 100 events
    if (events.length > 100) {
        events.splice(0, events.length - 100);
    }
    
    localStorage.setItem('reviewchill-events', JSON.stringify(events));
}

// Navigation helpers
function navigateReviews(forward) {
    const currentReview = document.querySelector('.review-card.active');
    const allReviews = document.querySelectorAll('.review-card');
    
    if (allReviews.length === 0) return;
    
    let nextIndex = 0;
    
    if (currentReview) {
        const currentIndex = Array.from(allReviews).indexOf(currentReview);
        nextIndex = forward ? 
            (currentIndex + 1) % allReviews.length : 
            (currentIndex - 1 + allReviews.length) % allReviews.length;
        
        currentReview.classList.remove('active');
    }
    
    const nextReview = allReviews[nextIndex];
    nextReview.classList.add('active');
    nextReview.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// Video utilities
function extractVideoId(url) {
    // YouTube
    const youtubeRegex = /(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)/;
    const youtubeMatch = url.match(youtubeRegex);
    if (youtubeMatch) {
        return { platform: 'youtube', id: youtubeMatch[1] };
    }
    
    // Facebook (basic detection)
    if (url.includes('facebook.com')) {
        return { platform: 'facebook', id: url.split('/').pop() };
    }
    
    return null;
}

function generateThumbnailUrl(platform, videoId) {
    switch (platform) {
        case 'youtube':
            return `https://img.youtube.com/vi/${videoId}/maxresdefault.jpg`;
        case 'facebook':
            return '/static/images/facebook-placeholder.png';
        default:
            return '/static/images/video-placeholder.png';
    }
}

// Form utilities
function validateVideoUrl(url) {
    return url.includes('youtube.com/watch') || 
           url.includes('youtu.be/') || 
           url.includes('facebook.com');
}

function showToast(message, type = 'success') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <i class="fas fa-${type === 'success' ? 'check' : 'exclamation-triangle'} me-2"></i>
            ${message}
        </div>
    `;
    
    // Add to page
    document.body.appendChild(toast);
    
    // Show toast
    setTimeout(() => toast.classList.add('show'), 100);
    
    // Hide and remove toast
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Search functionality
function highlightSearchTerm(text, term) {
    if (!term) return text;
    
    const regex = new RegExp(`(${term})`, 'gi');
    return text.replace(regex, '<mark class="bg-warning text-dark">$1</mark>');
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

// Auto-save functionality for forms
function initializeAutoSave() {
    const forms = document.querySelectorAll('form[data-autosave]');
    
    forms.forEach(form => {
        const formId = form.id || form.action;
        const inputs = form.querySelectorAll('input, textarea, select');
        
        // Load saved data
        const savedData = JSON.parse(localStorage.getItem(`autosave-${formId}`) || '{}');
        inputs.forEach(input => {
            if (savedData[input.name]) {
                input.value = savedData[input.name];
            }
        });
        
        // Save on input
        const debouncedSave = debounce(() => {
            const formData = {};
            inputs.forEach(input => {
                formData[input.name] = input.value;
            });
            localStorage.setItem(`autosave-${formId}`, JSON.stringify(formData));
        }, 1000);
        
        inputs.forEach(input => {
            input.addEventListener('input', debouncedSave);
        });
        
        // Clear on submit
        form.addEventListener('submit', () => {
            localStorage.removeItem(`autosave-${formId}`);
        });
    });
}

// Performance monitoring
function monitorPerformance() {
    if ('performance' in window) {
        window.addEventListener('load', () => {
            setTimeout(() => {
                const perfData = performance.getEntriesByType('navigation')[0];
                const loadTime = perfData.loadEventEnd - perfData.loadEventStart;
                
                trackEvent('page_load_time', {
                    load_time: loadTime,
                    page: window.location.pathname
                });
            }, 0);
        });
    }
}

// Error handling
window.addEventListener('error', function(e) {
    trackEvent('javascript_error', {
        message: e.message,
        filename: e.filename,
        lineno: e.lineno,
        colno: e.colno
    });
});

// Social sharing
function shareToSocial(platform, url, title) {
    const encodedUrl = encodeURIComponent(url);
    const encodedTitle = encodeURIComponent(title);
    
    let shareUrl = '';
    
    switch (platform) {
        case 'facebook':
            shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`;
            break;
        case 'twitter':
            shareUrl = `https://twitter.com/intent/tweet?url=${encodedUrl}&text=${encodedTitle}`;
            break;
        case 'linkedin':
            shareUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${encodedUrl}`;
            break;
    }
    
    if (shareUrl) {
        window.open(shareUrl, '_blank', 'width=600,height=400');
        trackEvent('social_share', { platform, url, title });
    }
}

// Copy to clipboard
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showToast('Đã sao chép vào clipboard!');
        return true;
    } catch (err) {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        
        try {
            document.execCommand('copy');
            showToast('Đã sao chép vào clipboard!');
            return true;
        } catch (err) {
            showToast('Không thể sao chép!', 'error');
            return false;
        } finally {
            document.body.removeChild(textArea);
        }
    }
}

// Initialize additional features when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeAutoSave();
    monitorPerformance();
});

// Export functions for global use
window.ReviewChill = {
    showToast,
    copyToClipboard,
    shareToSocial,
    validateVideoUrl,
    extractVideoId,
    generateThumbnailUrl,
    trackEvent
};