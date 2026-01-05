/**
 * Live Language Switching - Changes language without page refresh
 */
(function() {
    'use strict';
    
    // Store current language
    let currentLanguage = 'en';
    
    // Get all translation keys and values for current page
    function getPageTranslations() {
        const translations = {};
        const elements = document.querySelectorAll('[data-i18n-key]');
        elements.forEach(el => {
            const key = el.getAttribute('data-i18n-key');
            if (key) {
                translations[key] = {
                    element: el,
                    originalText: el.textContent.trim()
                };
            }
        });
        return translations;
    }
    
    // Load translations from server
    async function loadTranslations(language) {
        try {
            const response = await fetch(`/api/i18n/strings?language=${language}`);
            const data = await response.json();
            if (data.success) {
                return data.strings;
            }
        } catch (error) {
            console.error('Error loading translations:', error);
        }
        return {};
    }
    
    // Update page with new translations
    async function updatePageLanguage(language) {
        // Update session via AJAX
        try {
            const response = await fetch('/language/change', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ language: language })
            });
            
            if (response.ok) {
                // Reload translations
                const translations = await loadTranslations(language);
                
                // Update all elements with data-i18n-key
                document.querySelectorAll('[data-i18n-key]').forEach(el => {
                    const key = el.getAttribute('data-i18n-key');
                    if (translations[key]) {
                        el.textContent = translations[key];
                    }
                });
                
                // Update current language
                currentLanguage = language;
                
                // Show success message
                showLanguageChangeMessage(language);
            }
        } catch (error) {
            console.error('Error changing language:', error);
            // Fallback: reload page
            window.location.reload();
        }
    }
    
    // Show language change message
    function showLanguageChangeMessage(language) {
        const langNames = {
            'en': 'English',
            'hi': 'Hindi',
            'kn': 'Kannada',
            'ta': 'Tamil',
            'mr': 'Marathi',
            'bn': 'Bengali'
        };
        
        // Create or update toast notification
        let toast = document.getElementById('language-change-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'language-change-toast';
            toast.className = 'toast position-fixed top-0 end-0 p-3';
            toast.style.zIndex = '9999';
            document.body.appendChild(toast);
        }
        
        toast.innerHTML = `
            <div class="toast-header bg-success text-white">
                <strong class="me-auto">Language Changed</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                Language changed to ${langNames[language] || language}
            </div>
        `;
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    }
    
    // Initialize on page load
    document.addEventListener('DOMContentLoaded', function() {
        // Get current language from page
        if (window.currentLanguage) {
            currentLanguage = window.currentLanguage;
        }
        
        // Handle language selector change
        const languageSelect = document.getElementById('language-select');
        if (languageSelect) {
            languageSelect.addEventListener('change', function() {
                const newLanguage = this.value;
                if (newLanguage !== currentLanguage) {
                    updatePageLanguage(newLanguage);
                }
            });
        }
        
        // Add data-i18n-key to elements that need translation
        // This is done server-side, but we can also do it client-side
        document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, span, a, button, label, th, td').forEach(el => {
            if (el.textContent && el.textContent.trim().length > 0) {
                // Check if it's not already translated
                if (!el.textContent.includes('{{') && !el.textContent.includes('get_localized_string')) {
                    // We'll mark these for potential client-side translation
                    // But server-side is preferred
                }
            }
        });
    });
    
    // Export function for manual language change
    window.changeLanguageLive = function(language) {
        updatePageLanguage(language);
    };
    
})();

