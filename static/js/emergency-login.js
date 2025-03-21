/**
 * Emergency Login Module
 * Provides fallback login functionality when the main login system fails
 */

/**
 * Initialize emergency login functionality
 */
export function initEmergencyLogin() {
    console.log('Emergency login system initialized');
    
    // Listen for special key combination (Ctrl+Alt+E)
    document.addEventListener('keydown', function(event) {
        if (event.ctrlKey && event.altKey && event.key === 'e') {
            showEmergencyLoginModal();
        }
    });
}

/**
 * Show emergency login modal
 */
function showEmergencyLoginModal() {
    console.log('Showing emergency login modal');
    
    // Create modal if it doesn't exist
    let modal = document.getElementById('emergency-login-modal');
    if (!modal) {
        modal = createEmergencyLoginModal();
        document.body.appendChild(modal);
    }
    
    // Show modal
    modal.style.display = 'flex';
}

/**
 * Create emergency login modal element
 */
function createEmergencyLoginModal() {
    const modal = document.createElement('div');
    modal.id = 'emergency-login-modal';
    modal.style.position = 'fixed';
    modal.style.top = '0';
    modal.style.left = '0';
    modal.style.width = '100%';
    modal.style.height = '100%';
    modal.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
    modal.style.display = 'flex';
    modal.style.alignItems = 'center';
    modal.style.justifyContent = 'center';
    modal.style.zIndex = '9999';
    
    const modalContent = document.createElement('div');
    modalContent.style.backgroundColor = '#0F1C21';
    modalContent.style.borderRadius = '8px';
    modalContent.style.padding = '20px';
    modalContent.style.width = '90%';
    modalContent.style.maxWidth = '400px';
    modalContent.style.border = '1px solid #00C389';
    modalContent.style.boxShadow = '0 0 20px rgba(0, 195, 137, 0.5)';
    
    modalContent.innerHTML = `
        <h2 style="color: #00C389; margin-bottom: 20px; font-size: 18px;">Notfall-Anmeldung</h2>
        <form id="emergency-login-form">
            <div style="margin-bottom: 15px;">
                <label for="emergency-username" style="display: block; margin-bottom: 5px; color: white;">Benutzername</label>
                <input type="text" id="emergency-username" style="width: 100%; padding: 8px; background: black; color: white; border: 1px solid #444; border-radius: 4px;">
            </div>
            <div style="margin-bottom: 15px;">
                <label for="emergency-password" style="display: block; margin-bottom: 5px; color: white;">Passwort</label>
                <input type="password" id="emergency-password" style="width: 100%; padding: 8px; background: black; color: white; border: 1px solid #444; border-radius: 4px;">
            </div>
            <div style="display: flex; justify-content: space-between;">
                <button type="button" id="emergency-cancel" style="padding: 8px 15px; background: transparent; color: white; border: 1px solid #666; border-radius: 20px; cursor: pointer;">Abbrechen</button>
                <button type="submit" style="padding: 8px 15px; background: #00C389; color: black; border: none; border-radius: 20px; cursor: pointer;">Anmelden</button>
            </div>
        </form>
        <div id="emergency-error" style="color: #ff6b6b; margin-top: 15px; font-size: 14px; display: none;"></div>
    `;
    
    modal.appendChild(modalContent);
    
    // Add event listeners
    setTimeout(() => {
        const form = document.getElementById('emergency-login-form');
        const cancelButton = document.getElementById('emergency-cancel');
        
        if (form) {
            form.addEventListener('submit', handleEmergencyLogin);
        }
        
        if (cancelButton) {
            cancelButton.addEventListener('click', () => {
                modal.style.display = 'none';
            });
        }
    }, 0);
    
    return modal;
}

/**
 * Handle emergency login submission
 */
async function handleEmergencyLogin(event) {
    event.preventDefault();
    
    const usernameInput = document.getElementById('emergency-username');
    const passwordInput = document.getElementById('emergency-password');
    const errorElement = document.getElementById('emergency-error');
    
    if (!usernameInput || !passwordInput || !errorElement) {
        return;
    }
    
    const username = usernameInput.value.trim();
    const password = passwordInput.value;
    
    // Client-side validation
    if (!username || !password) {
        errorElement.textContent = 'Bitte Benutzername und Passwort eingeben';
        errorElement.style.display = 'block';
        return;
    }
    
    try {
        // Create form data
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);
        
        // Send login request
        const response = await fetch('/token', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Store token and user ID
            localStorage.setItem('accessToken', data.access_token);
            localStorage.setItem('userId', data.user_id);
            
            // Update global state if available
            if (window.authState) {
                window.authState.accessToken = data.access_token;
                window.authState.userId = data.user_id;
                window.authState.isLoggedIn = true;
            }
            
            // Hide modal
            const modal = document.getElementById('emergency-login-modal');
            if (modal) {
                modal.style.display = 'none';
            }
            
            // Reload page to refresh state
            window.location.reload();
        } else {
            const errorData = await response.json();
            errorElement.textContent = errorData.detail || 'Ungültige Anmeldedaten';
            errorElement.style.display = 'block';
        }
    } catch (error) {
        console.error('Emergency login error:', error);
        errorElement.textContent = 'Ein Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.';
        errorElement.style.display = 'block';
    }
}

export default {
    initEmergencyLogin
};