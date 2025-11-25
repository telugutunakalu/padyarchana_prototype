// Padyarchana Application JavaScript

// Alpine.js will be loaded via CDN, but here are custom utilities

// Search functionality
async function searchPoems(query) {
    try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Search error:', error);
        return [];
    }
}

// Autocomplete functionality
let autocompleteTimer;
async function handleAutocomplete(input, callback) {
    clearTimeout(autocompleteTimer);

    autocompleteTimer = setTimeout(async () => {
        if (input.length < 2) {
            callback([]);
            return;
        }

        try {
            const response = await fetch(`/api/search/autocomplete?q=${encodeURIComponent(input)}`);
            const data = await response.json();
            callback(data);
        } catch (error) {
            console.error('Autocomplete error:', error);
            callback([]);
        }
    }, 300);
}

// Dictionary lookup
async function lookupWord(word) {
    try {
        const response = await fetch(`/api/dictionary/${encodeURIComponent(word)}`);
        if (response.ok) {
            return await response.json();
        }
        return null;
    } catch (error) {
        console.error('Dictionary lookup error:', error);
        return null;
    }
}

// Show word definition modal
function showWordDefinition(word, definition) {
    // This will be implemented with Alpine.js in templates
    console.log('Word:', word, 'Definition:', definition);
}

// Utility: Format Telugu text
function formatTeluguText(text) {
    // Add any Telugu-specific formatting here
    return text;
}

// Utility: Debounce function
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

// Export functions for use in templates
window.padyarchana = {
    searchPoems,
    handleAutocomplete,
    lookupWord,
    showWordDefinition,
    formatTeluguText,
    debounce
};
