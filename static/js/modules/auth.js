/**
 * Authentication Module
 * Handles login, logout, session management, and user state
 */

import { api } from './api.js';
import { showToast, updateUIForLoggedInUser, updateUIForLoggedOutUser, showModal, hideModal } from './ui.js';

// Local reference to global auth state
const authState = window.authState;

/**
 * Initialize authentication state from localStorage
 * @returns {Promise<boolean>} True if successfully authenticated
 */
export async function initAuth() {
    const savedToken = localStorage.getItem('accessToken');
    const savedUserId = localStorage.getItem('userId');
    
    if (!savedToken || !savedUserId) {
        console.log("No saved token or user ID found");
        updateUIForLoggedOutUser();
        return false;
    }
    
    try {
        // Validate token with the server
        const isValid = await validateToken(savedToken);
        
        if (isValid) {
            authState.accessToken = savedToken;
            authState.userId = savedUserId;
            authState.isLoggedIn = true;
            
            // Load user data
            await loadUserProfile();
            
            // Update UI
            updateUIForLoggedInUser();
            
            return true;
        } else {
            // Token invalid, clear storage
            handleLogout(false); // Silent logout
            return false;
        }
    } catch (error) {
        console.error('Error initializing auth:', error);
        handleLogout(false); // Silent logout
        return false;
    }
}

/**
 * Validates a token with the server
 * @param {string} token JWT token to validate
 * @returns {Promise<boolean>} True if token is valid
 */
export async function validateToken(token) {
    if (!token) {
        console.log('No token provided for validation');
        return false;
    }
    
    try {
        // Use the auth status endpoint to validate token
        const response = await fetch('/api/auth-status', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        // Wenn 401, dann ist der Token ungültig
        if (response.status === 401) {
            console.log('Token is invalid (401)');
            return false;
        }
        
        return response.ok;
    } catch (error) {
        console.error('Token validation error:', error);
        return false;
    }
}

/**
 * Load user profile data from server
 * @returns {Promise<Object>} User profile data
 */
export async function loadUserProfile() {
    if (!authState.isLoggedIn) {
        throw new Error('Cannot load profile: Not logged in');
    }
    
    try {
        const userData = await api.getUserProfile();
        authState.userData = userData;
        return userData;
    } catch (error) {
        console.error('Error loading user profile:', error);
        throw error;
    }
}

/**
 * Handle login button click
 */
export function handleLoginButton() {
    if (authState.isLoggedIn) {
        showToast('Sie sind bereits eingeloggt!', 'info');
        return;
    }
    
    // Show login modal by dispatching a custom event
    document.dispatchEvent(new CustomEvent('showModal', { detail: { modalId: 'login-modal' } }));
}

/**
 * Process login with username and password
 * @param {string} username User's username
 * @param {string} password User's password
 * @returns {Promise<boolean>} True if login successful
 */
export async function processLogin(username, password) {
    try {
        const data = await api.login(username, password);
        
        // Store token and user ID
        authState.accessToken = data.access_token;
        authState.userId = data.user_id;
        authState.isLoggedIn = true;
        
        // Save to localStorage
        localStorage.setItem('accessToken', data.access_token);
        localStorage.setItem('userId', data.user_id);
        
        // Load user data
        await loadUserProfile();
        
        // Update UI
        updateUIForLoggedInUser();
        
        // Show success message
        showToast(`Willkommen ${authState.userData.vorname}! Erfolgreich eingeloggt.`, 'success');
        
        return true;
    } catch (error) {
        console.error('Login error:', error);
        return false;
    }
}

/**
 * Handle logout
 * @param {boolean} showMessage Whether to show logout message
 */
export function handleLogout(showMessage = true) {
    // Clear auth state
    authState.isLoggedIn = false;
    authState.userData = null;
    authState.userId = null;
    authState.accessToken = null;
    
    // Remove from localStorage
    localStorage.removeItem('accessToken');
    localStorage.removeItem('userId');
    
    // Update UI
    updateUIForLoggedOutUser();
    
    // Show message if needed
    if (showMessage) {
        showToast('Erfolgreich abgemeldet!', 'success');
    }
}

/**
 * Handle register button click
 */
export function handleRegisterButton() {
    // Show register modal by dispatching a custom event
    document.dispatchEvent(new CustomEvent('showModal', { detail: { modalId: 'register-modal' } }));
}

/**
 * Process user registration
 * @param {Object} userData User registration data
 * @returns {Promise<boolean>} True if registration successful
 */
export async function processRegistration(userData) {
    try {
        const response = await fetch('/users/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(userData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Registrierung fehlgeschlagen');
        }
        
        // Show success message
        showToast('Registrierung erfolgreich! Sie können sich jetzt anmelden.', 'success');
        
        // Show login modal after short delay
        setTimeout(() => {
            hideModal('register-modal');
            showModal('login-modal', { username: userData.username });
        }, 1000);
        
        return true;
    } catch (error) {
        console.error('Registration error:', error);
        throw error; // Propagate for form handler
    }
}

export default {
    initAuth,
    validateToken,
    loadUserProfile,
    handleLoginButton,
    processLogin,
    handleLogout,
    handleRegisterButton,
    processRegistration
};