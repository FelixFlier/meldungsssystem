/**
 * Main JavaScript for Meldungssystem
 * Application entry point that initializes and coordinates all modules
 */

// Global modules container
const modules = {};

// Global auth state for app-wide access
window.authState = {
    isLoggedIn: false,
    userId: null,
    accessToken: null,
    userData: null
};

/**
 * Helper function to safely load a module
 * @param {string} name Module name
 * @param {string} path Module path
 * @returns {Promise<boolean>} Success status
 */
async function loadModule(name, path) {
    try {
        const module = await import(path);
        modules[name] = module.default || module;
        console.log(`Module ${name} loaded successfully`);
        return true;
    } catch (error) {
        console.error(`Failed to load module ${name} from ${path}:`, error);
        
        // Try fallback to direct function definitions for critical functionality
        if (name === 'animations') {
            // Include critical createStarField directly as fallback
            modules.animations = {
                createStarField: function() {
                    console.log("Using fallback star field implementation");
                    const container = document.getElementById('stars-container');
                    if (!container) {
                        console.warn('Stars container not found!');
                        return;
                    }
                    
                    // Force container styling
                    container.style.position = 'fixed';
                    container.style.top = '0';
                    container.style.left = '0';
                    container.style.width = '100%';
                    container.style.height = '100%';
                    container.style.overflow = 'hidden';
                    container.style.pointerEvents = 'none';
                    container.style.zIndex = '1';
                    
                    // Clear container
                    container.innerHTML = '';
                    
                    // Create stars
                    const numStars = 200;
                    for (let i = 0; i < numStars; i++) {
                        const star = document.createElement('div');
                        
                        // Star size with more variety
                        if (i % 25 === 0) {
                            star.className = 'star extra-large';
                        } else if (i % 15 === 0) {
                            star.className = 'star large';
                        } else if (i % 5 === 0) {
                            star.className = 'star medium';
                        } else {
                            star.className = 'star small';
                        }
                        
                        // Add animation classes
                        if (i % 2 === 0) {
                            star.classList.add('twinkle');
                        }
                        if (i % 3 === 0) {
                            star.classList.add('drift');
                        }
                        
                        // Explicitly set styles
                        star.style.position = 'absolute';
                        star.style.borderRadius = '50%';
                        star.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
                        
                        // Set star size
                        if (star.classList.contains('extra-large')) {
                            star.style.width = '3.5px';
                            star.style.height = '3.5px';
                            star.style.boxShadow = '0 0 8px 2px rgba(0, 195, 137, 0.6)';
                        } else if (star.classList.contains('large')) {
                            star.style.width = '2.5px';
                            star.style.height = '2.5px';
                            star.style.boxShadow = '0 0 5px 2px rgba(0, 195, 137, 0.5)';
                        } else if (star.classList.contains('medium')) {
                            star.style.width = '1.5px';
                            star.style.height = '1.5px';
                            star.style.boxShadow = '0 0 3px 1px rgba(0, 195, 137, 0.4)';
                        } else {
                            star.style.width = '1px';
                            star.style.height = '1px';
                            star.style.boxShadow = '0 0 2px 1px rgba(0, 195, 137, 0.3)';
                        }
                        
                        // Random position
                        const x = Math.random() * 100;
                        const y = Math.random() * 100;
                        star.style.left = `${x}%`;
                        star.style.top = `${y}%`;
                        
                        // Animation delay
                        star.style.animationDelay = `${Math.random() * 5}s`;
                        
                        container.appendChild(star);
                    }
                },
                initAnimations: function() {
                    this.createStarField();
                }
            };
            return true;
        }
        
        return false;
    }
}

/**
 * Wait for DOM to be fully loaded
 */
document.addEventListener('DOMContentLoaded', async function() {
    console.log('DOM loaded - Initialization begins');
    
    try {
        // Load all modules
        const moduleLoads = [
            loadModule('api', './modules/api.js'),
            loadModule('auth', './modules/auth.js'),
            loadModule('ui', './modules/ui.js'),
            loadModule('forms', './modules/forms.js'),
            loadModule('incidents', './modules/incidents.js'),
            loadModule('animations', './modules/animations.js')
        ];
        
        // Wait for all modules to load (or fail)
        await Promise.all(moduleLoads);
        
        // Initialize critical functionality
        if (modules.animations) {
            modules.animations.initAnimations();
        }
        
        // Fetch CSRF token
        if (modules.forms) {
            await modules.forms.fetchCsrfToken();
        }
        
        // Set up form handlers
        if (modules.forms) {
            modules.forms.setupFormHandlers();
            modules.forms.initializeUploadArea();
        }
        
        // First, force UI to match localStorage state (immediate visual feedback)
        if (modules.ui) {
            modules.ui.checkLoginStateAndUpdateUI();
        }
        
        // Check for existing login session
        if (modules.auth) {
            const isLoggedIn = await modules.auth.initAuth();
            console.log('Auth initialized, isLoggedIn:', isLoggedIn);
            
            // Explicitly force UI update based on login state
            if (isLoggedIn) {
                if (modules.ui) {
                    modules.ui.updateUIForLoggedInUser();
                }
                
                // If logged in, load user data
                if (modules.incidents) {
                    modules.incidents.loadUserIncidents();
                    modules.incidents.loadUserActivities();
                }
            } else if (modules.ui) {
                modules.ui.updateUIForLoggedOutUser();
            }
        }
        
        // Set up event listeners
        initializeEventListeners();
        
        console.log('Initialization completed successfully');
    } catch (error) {
        console.error('Initialization error:', error);
    }
});

/**
 * Initialize all event listeners
 */
function initializeEventListeners() {
    // Event delegation for clickable elements
    document.addEventListener('click', function(event) {
        // Find element with data-action attribute
        const actionElement = event.target.closest('[data-action]');
        if (!actionElement) return;
        
        // Prevent default for links
        if (actionElement.tagName === 'A' && actionElement.getAttribute('href') === '#') {
            event.preventDefault();
        }
        
        // Get the action
        const action = actionElement.dataset.action;
        
        // Handle actions
        switch (action) {
            case 'login':
                if (modules.auth) modules.auth.handleLoginButton();
                break;
            case 'logout':
                if (modules.auth) modules.auth.handleLogout();
                break;
            case 'register':
                if (modules.auth) modules.auth.handleRegisterButton();
                break;
            case 'show-profile':
                if (modules.ui) modules.ui.showModal('profile-modal');
                break;
            case 'agent-click':
                const agentType = actionElement.dataset.type;
                if (modules.incidents) modules.incidents.handleAgentClick(agentType);
                break;
            case 'close-modal':
                const targetModal = actionElement.dataset.target;
                if (modules.ui) modules.ui.hideModal(targetModal);
                break;
            case 'remove-file':
                if (modules.forms) modules.forms.removeExcelFile();
                break;
            case 'show-incident-details': 
                const incidentId = actionElement.dataset.incidentId;
                if (modules.incidents) modules.incidents.showIncidentDetails(incidentId);
                break;
            default:
                console.log(`Unknown action: ${action}`);
        }
    });
    
    // Custom event for showing modals
    document.addEventListener('showModal', function(event) {
        if (event.detail && event.detail.modalId && modules.ui) {
            modules.ui.showModal(event.detail.modalId, event.detail.data || {});
        }
    });
    
    // Escape key for modals
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modules.ui) {
            modules.ui.hideAllModals();
        }
    });
    
    // Global error handler
    window.addEventListener('error', function(event) {
        console.error('Global error:', event.error);
        if (!event.defaultPrevented && modules.ui) {
            modules.ui.showToast("Ein unerwarteter Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.", "error");
        }
    });
    
    // Handle unhandled promise rejections
    window.addEventListener('unhandledrejection', function(event) {
        console.error('Unhandled promise rejection:', event.reason);
        if (modules.ui) {
            modules.ui.showToast("Ein unerwarteter Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.", "error");
        }
    });
    
    // Register service worker
    registerServiceWorker();
}

/**
 * Register service worker
 */
function registerServiceWorker() {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => console.log('Service Worker registered: ', registration))
            .catch(error => console.error('Service Worker error:', error));
    }
}