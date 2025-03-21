/**
 * UI Module
 * Handles UI updates, modals, toasts, and other visual elements
 */

// --- Modal Management ---

/**
 * Show a modal by ID
 * @param {string} modalId ID of the modal to show
 * @param {Object} data Optional data to pass to the modal
 */
export function showModal(modalId, data = {}) {
    console.log(`Showing modal: ${modalId}`);
    const modal = document.getElementById(modalId);
    if (!modal) {
        console.error(`Modal not found: ${modalId}`);
        return;
    }
    
    // Handle any pre-show modal actions
    if (modalId === 'login-modal') {
        // Pre-fill username if provided
        if (data.username) {
            const usernameField = document.getElementById('username');
            if (usernameField) usernameField.value = data.username;
        }
        
        // Clear any previous error messages
        const errorElement = document.getElementById('login-error');
        if (errorElement) {
            errorElement.textContent = '';
            errorElement.classList.add('hidden');
        }
    } else if (modalId === 'register-modal') {
        // Clear any previous error messages
        const errorElement = document.getElementById('register-error');
        if (errorElement) {
            errorElement.textContent = '';
            errorElement.classList.add('hidden');
        }
    } else if (modalId === 'profile-modal') {
        // Update profile display before showing
        updateProfileDisplay();
    }
    
    // Show the modal
    modal.classList.add('active');
    
    // Focus the first input if any
    setTimeout(() => {
        const firstInput = modal.querySelector('input:not([type="hidden"])');
        if (firstInput) firstInput.focus();
    }, 100);
}

/**
 * Hide a modal by ID
 * @param {string} modalId ID of the modal to hide
 */
export function hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}

/**
 * Hide all modals
 */
export function hideAllModals() {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.classList.remove('active');
    });
}

// --- Form Error Display ---

/**
 * Show an error message in a form
 * @param {HTMLElement} element Error display element
 * @param {string} message Error message to display
 */
export function showFormError(element, message) {
    if (!element) {
        console.error('Error element not found');
        return;
    }
    
    element.textContent = message;
    element.classList.remove('hidden');
    
    // Focus on the element
    element.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * Clear an error message in a form
 * @param {HTMLElement} element Error display element
 */
export function clearFormError(element) {
    if (element) {
        element.textContent = '';
        element.classList.add('hidden');
    }
}

// --- Toast Notifications ---

/**
 * Show a toast notification
 * @param {string} message Message to display
 * @param {string} type Toast type: success, error, info
 */
export function showToast(message, type = 'info') {
    // Create toast element
    const toast = document.createElement('div');
    
    // Add appropriate styling based on type
    toast.className = `glass p-4 rounded-lg flex items-center space-x-2 mb-2 transform transition-all duration-300 ${
        type === 'success' ? 'border-green-500/50 text-green-400' :
        type === 'error' ? 'border-red-500/50 text-red-400' :
        'border-primary/50 text-primary'
    } toast`;
    
    // Select icon based on type
    const icon = type === 'success' ? 
        '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>' :
        type === 'error' ?
        '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>' :
        '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>';
    
    // Populate toast content
    toast.innerHTML = `
        <div class="flex-shrink-0">${icon}</div>
        <p class="text-sm font-medium">${message}</p>
    `;
    
    // Add to toast container
    const container = document.getElementById('toast-container');
    if (container) {
        container.appendChild(toast);
        
        // Remove after delay with fade animation
        setTimeout(() => {
            toast.classList.add('translate-x-full', 'opacity-0');
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    } else {
        console.error('Toast container not found');
    }
}

// --- Loading Indicators ---

/**
 * Show or hide the global page loader
 * @param {boolean} show Whether to show the loader
 */
export function showPageLoader(show) {
    document.body.style.cursor = show ? 'wait' : 'default';
    
    // TODO: Add a proper loading spinner in the future
}

// --- Progress Bar ---

let progressInterval = null;
let currentProgress = 0;

/**
 * Show the progress bar
 */
export function showProgressBar() {
    const container = document.getElementById('progress-container');
    if (container) {
        container.classList.remove('hidden');
        startProgress();
    } else {
        console.error('Progress container not found');
    }
}

/**
 * Hide the progress bar
 */
export function hideProgressBar() {
    const container = document.getElementById('progress-container');
    if (container) {
        container.classList.add('hidden');
        stopProgress();
    }
}

/**
 * Start progress animation
 */
function startProgress() {
    currentProgress = 0;
    progressInterval = setInterval(() => {
        if (currentProgress < 100) {
            // Decrease increment as we get closer to 100%
            const increment = currentProgress < 30 ? 1 : 
                             currentProgress < 70 ? 0.7 : 0.3;
            
            currentProgress = Math.min(100, currentProgress + increment);
            updateProgress(currentProgress);
        }
    }, 500);
}

/**
 * Stop progress animation
 */
function stopProgress() {
    clearInterval(progressInterval);
    currentProgress = 0;
    updateProgress(0);
}

/**
 * Update progress bar display
 * @param {number} progress Progress value (0-100)
 */
function updateProgress(progress) {
    const bar = document.getElementById('progress-bar');
    const percentage = document.getElementById('progress-percentage');
    const status = document.getElementById('progress-status');
    
    if (bar && percentage && status) {
        bar.style.width = `${progress}%`;
        bar.setAttribute('aria-valuenow', Math.round(progress));
        percentage.textContent = `${Math.round(progress)}%`;
        
        // Update status text based on progress
        if (progress < 25) status.textContent = 'Prozess wird gestartet...';
        else if (progress < 50) status.textContent = 'Daten werden verarbeitet...';
        else if (progress < 75) status.textContent = 'Formular wird ausgefüllt...';
        else if (progress < 100) status.textContent = 'Abschluss wird vorbereitet...';
        else status.textContent = 'Prozess abgeschlossen!';
    }
}

// --- UI State Updates ---

/**
 * Check login state and update UI accordingly
 */
export function checkLoginStateAndUpdateUI() {
    const token = localStorage.getItem('accessToken');
    const userId = localStorage.getItem('userId');
    
    console.log('Checking login state:', !!token && !!userId);
    
    if (token && userId) {
        // User is logged in
        updateUIForLoggedInUser();
    } else {
        // User is logged out
        updateUIForLoggedOutUser();
    }
}

/**
 * Update UI for a logged in user
 */
export function updateUIForLoggedInUser() {
    console.log('Updating UI for logged in user');
    // Hide/show relevant navigation buttons
    const loginButton = document.getElementById('loginButton');
    const registerButton = document.getElementById('registerButton');
    const logoutButton = document.getElementById('logoutButton');
    const profileButton = document.getElementById('profileButton');
    
    if (loginButton) loginButton.classList.add('hidden');
    if (registerButton) registerButton.classList.add('hidden');
    if (logoutButton) logoutButton.classList.remove('hidden');
    if (profileButton) profileButton.classList.remove('hidden');
    
    // Add a brief animation to the profile button
    if (profileButton) {
        profileButton.classList.add('pulse-animation');
        setTimeout(() => {
            profileButton.classList.remove('pulse-animation');
        }, 2000);
    }
}

/**
 * Update UI for a logged out user
 */
export function updateUIForLoggedOutUser() {
    console.log('Updating UI for logged out user');
    // Show/hide relevant navigation buttons
    const loginButton = document.getElementById('loginButton');
    const registerButton = document.getElementById('registerButton');
    const logoutButton = document.getElementById('logoutButton');
    const profileButton = document.getElementById('profileButton');
    
    if (loginButton) loginButton.classList.remove('hidden');
    if (registerButton) registerButton.classList.remove('hidden');
    if (logoutButton) logoutButton.classList.add('hidden');
    if (profileButton) profileButton.classList.add('hidden');
    
    // Hide user data containers
    const incidentsContainer = document.getElementById('incidents-container');
    const activitiesContainer = document.getElementById('activities-container');
    
    if (incidentsContainer) incidentsContainer.classList.add('hidden');
    if (activitiesContainer) activitiesContainer.classList.add('hidden');
}

/**
 * Update profile display in the profile modal
 */
export function updateProfileDisplay() {
    const userData = window.authState.userData;
    if (!userData) {
        console.error('Cannot update profile: No user data');
        return;
    }
    
    // Show full name
    const profileFullname = document.getElementById('profile-fullname');
    if (profileFullname) {
        profileFullname.textContent = `${userData.vorname} ${userData.nachname}`;
    }
    
    // Show username
    const profileUsername = document.getElementById('profile-username');
    if (profileUsername) {
        profileUsername.textContent = `@${userData.username}`;
    }
    
    // Fill form fields
    const fields = {
        'profile-nachname': userData.nachname || '',
        'profile-vorname': userData.vorname || '',
        'profile-geburtsdatum': userData.geburtsdatum || '',
        'profile-geburtsort': userData.geburtsort || '',
        'profile-geburtsland': userData.geburtsland || '',
        'profile-telefonnr': userData.telefonnr || '',
        'profile-email': userData.email || '',
        'profile-firma': userData.firma || '',
        'profile-ort': userData.ort || '',
        'profile-strasse': userData.strasse || '',
        'profile-hausnummer': userData.hausnummer || ''
    };
    
    Object.entries(fields).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) element.value = value;
    });
}

export default {
    showModal,
    hideModal,
    hideAllModals,
    showFormError,
    clearFormError,
    showToast,
    showPageLoader,
    showProgressBar,
    hideProgressBar,
    checkLoginStateAndUpdateUI,
    updateUIForLoggedInUser,
    updateUIForLoggedOutUser,
    updateProfileDisplay
};