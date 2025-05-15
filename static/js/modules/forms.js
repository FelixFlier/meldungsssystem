// 1. ALLE Imports am Anfang (nur einmal!)
import { api } from './api.js';
import { showToast, showFormError, clearFormError, hideModal, showModal } from './ui.js';
import { processLogin } from './auth.js';
import { submitIncident } from './incidents.js';
import { parseEmailFile } from './email-parser.js';
import { 
    loadUserLocations, 
    showLocationForm, 
    hideLocationForm, 
    saveUserLocation, 
    deleteUserLocation, 
    renderUserLocationsDropdown 
} from './user-locations.js';

// 2. Variablen
let csrfToken = '';
let emailFile = null;
let extractedData = null;


/**
 * Fetch CSRF token from the server
 * @returns {Promise<string>} CSRF token
 */
export async function fetchCsrfToken() {
    try {
        const response = await api.fetchCsrfToken();
        csrfToken = response.csrf_token;
        console.log('CSRF token fetched');
        
        // Set CSRF token in all forms
        document.querySelectorAll('input[name="csrf_token"]').forEach(input => {
            input.value = csrfToken;
        });
        
        return csrfToken;
    } catch (error) {
        console.error('Error fetching CSRF token:', error);
        showToast('Fehler beim Laden der Seite. Bitte aktualisieren Sie die Seite.', 'error');
        return '';
    }
}

/**
 * Set up all form event handlers
 */
// ... Imports bleiben wie gehabt ...

export function setupFormHandlers() {
    console.log('Setting up form handlers');
    
    // Login form
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLoginSubmit);
        console.log('Login form handler set up');
    }
    
    // Register form
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegisterSubmit);
        console.log('Register form handler set up');
    }
    
    // Datetime form (incident creation)
    const datetimeForm = document.getElementById('datetime-form');
    if (datetimeForm) {
        datetimeForm.addEventListener('submit', handleDatetimeSubmit);
        console.log('Datetime form handler set up');
    }
    
    // Profile form
    const profileForm = document.getElementById('profile-form');
    if (profileForm) {
        profileForm.addEventListener('submit', handleProfileSubmit);
        console.log('Profile form handler set up');
    }
    
    // Setup user location handlers when profile modal is ready
    document.addEventListener('profileModalReady', function(event) {
        console.log('Profile modal ready event received');
        setupUserLocationHandlers();
    });
}

// Verbesserte setupUserLocationHandlers Funktion
function setupUserLocationHandlers() {
    console.log('Setting up user location handlers');
    
    // Direkt die Event-Handler setzen ohne Verzögerung
    const addLocationBtn = document.getElementById('add-location-btn');
    const cancelLocationBtn = document.getElementById('cancel-location-btn');
    const userLocationForm = document.getElementById('user-location-form');
    
    console.log('Element check:', {
        addBtn: !!addLocationBtn,
        cancelBtn: !!cancelLocationBtn,
        form: !!userLocationForm
    });
    
    if (addLocationBtn) {
        console.log('Found add location button');
        
        // Entferne alte Event-Listener
        const newAddBtn = addLocationBtn.cloneNode(true);
        addLocationBtn.parentNode.replaceChild(newAddBtn, addLocationBtn);
        
        newAddBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Add location button clicked');
            if (window.modules && window.modules.userLocations) {
                window.modules.userLocations.showLocationForm();
            }
        });
    }
    
    if (cancelLocationBtn) {
        console.log('Found cancel location button');
        
        // Entferne alte Event-Listener
        const newCancelBtn = cancelLocationBtn.cloneNode(true);
        cancelLocationBtn.parentNode.replaceChild(newCancelBtn, cancelLocationBtn);
        
        newCancelBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Cancel location button clicked');
            if (window.modules && window.modules.userLocations) {
                window.modules.userLocations.hideLocationForm();
            }
        });
    }
    
    if (userLocationForm) {
        console.log('Found user location form - setting up submit handler');
        
        // Entferne alte Event-Listener
        const newForm = userLocationForm.cloneNode(true);
        userLocationForm.parentNode.replaceChild(newForm, userLocationForm);
        
        newForm.addEventListener('submit', handleUserLocationSubmit);
    } else {
        console.log('User location form not found - will be initialized when shown');
    }
}

// Handler für User Location Form Submit
async function handleUserLocationSubmit(event) {
    event.preventDefault();
    console.log('User location form submitted');
    
    const form = event.target;
    const formData = new FormData(form);
    
    // Convert FormData to object
    const locationData = {};
    for (let [key, value] of formData.entries()) {
        locationData[key] = value;
    }
    
    console.log('Form data:', locationData);
    
    try {
        if (window.modules && window.modules.userLocations) {
            await window.modules.userLocations.saveUserLocation(locationData);
        }
    } catch (error) {
        console.error('Error saving location:', error);
        showToast('Fehler beim Speichern des Standorts', 'error');
    }
}
/**
 * Handle user location selection
 */
function handleUserLocationSelect(event) {
    const select = event.target;
    const selectedOption = select.options[select.selectedIndex];
    const preview = document.getElementById('user-location-preview');
    const previewContent = document.getElementById('location-preview-content');
    
    if (select.value && selectedOption.dataset.locationData) {
        const location = JSON.parse(selectedOption.dataset.locationData);
        
        previewContent.innerHTML = `
            <p><strong>${location.name}</strong></p>
            <p>${location.strasse} ${location.hausnummer}</p>
            <p>${location.ort}, ${location.bundesland}</p>
            ${location.zusatz_info ? `<p class="text-sm">${location.zusatz_info}</p>` : ''}
        `;
        
        preview.classList.remove('hidden');
    } else {
        preview.classList.add('hidden');
    }
}

/**
 * Handle login form submission
 * @param {Event} event Form submit event
 */
async function handleLoginSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const errorElement = document.getElementById('login-error');
    
    // Clear previous errors
    clearFormError(errorElement);
    
    const username = form.querySelector('#username').value.trim();
    const password = form.querySelector('#password').value;
    
    // Basic validation
    if (!username || !password) {
        showFormError(errorElement, 'Bitte geben Sie Benutzername und Passwort ein.');
        return;
    }
    
    try {
        // Process login
        const success = await processLogin(username, password);
        
        if (success) {
            hideModal('login-modal');
            form.reset();
        } else {
            showFormError(errorElement, 'Anmeldung fehlgeschlagen. Ungültige Anmeldedaten.');
        }
    } catch (error) {
        console.error('Login error:', error);
        showFormError(errorElement, 'Ein Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.');
    }
}

/**
 * Handle register form submission
 * @param {Event} event Form submit event
 */
async function handleRegisterSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const errorElement = document.getElementById('register-error');
    
    // Clear previous errors
    clearFormError(errorElement);
    
    // Sammle alle Formulardaten
    const userData = {
        username: form.querySelector('#register-username').value.trim(),
        password: form.querySelector('#register-password').value,
        nachname: form.querySelector('#register-nachname').value.trim(),
        vorname: form.querySelector('#register-vorname').value.trim(),
        geburtsdatum: form.querySelector('#register-geburtsdatum').value,
        geburtsort: form.querySelector('#register-geburtsort').value.trim(),
        geburtsland: form.querySelector('#register-geburtsland').value.trim(),
        telefonnr: form.querySelector('#register-telefonnr').value.trim(),
        email: form.querySelector('#register-email').value.trim(),
        firma: form.querySelector('#register-firma').value.trim() || null,
        ort: form.querySelector('#register-ort').value.trim(),
        strasse: form.querySelector('#register-strasse').value.trim(),
        hausnummer: form.querySelector('#register-hausnummer').value.trim()
    };
    
    // Validierung
    if (!userData.username || !userData.password || !userData.nachname || !userData.vorname) {
        showFormError(errorElement, 'Bitte füllen Sie alle erforderlichen Felder aus.');
        return;
    }
    
    try {
        // Process registration
        const response = await fetch('/users/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(userData)
        });
        
        const responseData = await response.json();
        
        if (response.ok) {
            showToast('Registrierung erfolgreich! Sie können sich jetzt anmelden.', 'success');
            hideModal('register-modal');
            form.reset();
            
            // Zeige Login-Modal nach kurzer Verzögerung
            setTimeout(() => {
                showModal('login-modal', { username: userData.username });
            }, 1000);
        } else {
            // Detaillierte Fehlermeldung anzeigen
            const errorMsg = responseData.detail || 'Registrierung fehlgeschlagen. Bitte versuchen Sie einen anderen Benutzernamen.';
            showFormError(errorElement, errorMsg);
        }
    } catch (error) {
        console.error('Registration error:', error);
        showFormError(errorElement, 'Ein Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.');
    }
}

/**
 * Handle datetime form submission (for incident creation)
 * @param {Event} event Form submit event
 */
async function handleDatetimeSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const errorElement = document.getElementById('datetime-error');
    
    clearFormError(errorElement);
    
    const incidentType = form.querySelector('#incident-type').value;
    const incidentDate = form.querySelector('#incident-date').value;
    const incidentTime = form.querySelector('#incident-time').value;
    
    // Nur noch Benutzer-Standort
    const userLocationId = form.querySelector('#user-locations-dropdown').value;
    
    // Validierung
    if (!incidentDate || !incidentTime) {
        showFormError(errorElement, 'Bitte geben Sie Datum und Uhrzeit ein.');
        return;
    }
    
    try {
        await submitIncident({
            type: incidentType,
            date: incidentDate,
            time: incidentTime,
            userLocationId: userLocationId ? parseInt(userLocationId) : null,
            emailData: extractedData ? JSON.stringify(extractedData) : null
        });
        
        hideModal('datetime-modal');
        form.reset();
        
        // Zurücksetzen der globalen Variablen
        emailFile = null;
        extractedData = null;
        
        // Verstecken des Extraktions-Bereichs
        const extractedDataPreview = document.getElementById('extracted-data-preview');
        if (extractedDataPreview) {
            extractedDataPreview.classList.add('hidden');
        }
        
        // Verstecken des Datei-Info-Bereichs
        const fileInfo = document.getElementById('file-info');
        if (fileInfo) {
            fileInfo.classList.add('hidden');
        }
    } catch (error) {
        console.error('Incident submit error:', error);
        showFormError(errorElement, error.message || 'Ein Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.');
    }
}

/**
 * Handle profile form submission
 * @param {Event} event Form submit event
 */
async function handleProfileSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const errorElement = document.getElementById('profile-error');
    
    // Clear previous errors
    clearFormError(errorElement);
    
    // Sammle alle Formulardaten
    const userData = {
        nachname: form.querySelector('#profile-nachname').value.trim(),
        vorname: form.querySelector('#profile-vorname').value.trim(),
        geburtsdatum: form.querySelector('#profile-geburtsdatum').value,
        geburtsort: form.querySelector('#profile-geburtsort').value.trim(),
        geburtsland: form.querySelector('#profile-geburtsland').value.trim(),
        telefonnr: form.querySelector('#profile-telefonnr').value.trim(),
        email: form.querySelector('#profile-email').value.trim(),
        firma: form.querySelector('#profile-firma').value.trim() || null,
        ort: form.querySelector('#profile-ort').value.trim(),
        strasse: form.querySelector('#profile-strasse').value.trim(),
        hausnummer: form.querySelector('#profile-hausnummer').value.trim()
    };
    
    try {
        const response = await fetch('/users/me/', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
            },
            body: JSON.stringify(userData)
        });
        
        if (response.ok) {
            const updatedData = await response.json();
            
            // Update authState
            window.authState.userData = updatedData;
            
            showToast('Profil erfolgreich aktualisiert!', 'success');
            hideModal('profile-modal');
        } else {
            const errorData = await response.json();
            showFormError(errorElement, errorData.detail || 'Aktualisierung fehlgeschlagen.');
        }
    } catch (error) {
        console.error('Profile update error:', error);
        showFormError(errorElement, 'Ein Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.');
    }
}

/**
 * Initialize drag and drop area for email uploads
 */
export function initializeUploadArea() {
    const dropZone = document.getElementById('drop-zone');
    const fileUpload = document.getElementById('email-upload');
    
    if (!dropZone || !fileUpload) {
        console.warn('Upload area elements not found');
        return;
    }
    
    console.log('Setting up upload area for emails');
    
    // File input change event
    fileUpload.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            handleEmailFile(e.target.files[0]);
        }
    });
    
    // Drag events for visual feedback
    dropZone.addEventListener('dragenter', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.classList.add('border-primary');
    });
    
    dropZone.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
    });
    
    dropZone.addEventListener('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.classList.remove('border-primary');
    });
    
    // Drop event to handle file
    dropZone.addEventListener('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.classList.remove('border-primary');
        
        if (e.dataTransfer.files.length > 0) {
            handleEmailFile(e.dataTransfer.files[0]);
        }
    });
}

/**
 * Handle uploaded email file
 * @param {File} file - The uploaded email file
 */
async function handleEmailFile(file) {
    console.log('Handling email file:', file.name);
    
    // Überprüfe, ob die Datei ein unterstütztes Format hat
    const fileExt = file.name.split('.').pop().toLowerCase();
    const supportedFormats = ['eml', 'msg', 'html', 'txt'];
    
    if (!supportedFormats.includes(fileExt)) {
        showToast('Bitte wählen Sie eine unterstützte E-Mail-Datei (.eml, .msg, .html, .txt)', 'error');
        return;
    }
    
    emailFile = file;
    
    // Aktualisiere UI
    const fileInfo = document.getElementById('file-info');
    const fileName = document.getElementById('file-name');
    const fileSize = document.getElementById('file-size');
    
    if (fileInfo && fileName && fileSize) {
        fileName.textContent = file.name;
        fileSize.textContent = formatFileSize(file.size);
        fileInfo.classList.remove('hidden');
    }
    
    // Zeige Ladeindikator
    showToast('E-Mail wird analysiert...', 'info');
    
    try {
        // Parse email file
        const result = await parseEmailFile(file);
        
        if (result.success) {
            // Speichere extrahierte Daten
            extractedData = result;
            
            // Aktualisiere UI mit extrahierten Daten
            updateExtractedDataPreview(result);
            
            showToast('E-Mail erfolgreich analysiert', 'success');
        } else {
            showToast('Fehler beim Analysieren der E-Mail: ' + result.error, 'error');
        }
    } catch (error) {
        console.error('Error handling email file:', error);
        showToast('Fehler beim Verarbeiten der E-Mail-Datei', 'error');
    }
}

/**
 * Update the extracted data preview
 * @param {Object} data - The extracted data
 */
function updateExtractedDataPreview(data) {
    const previewContainer = document.getElementById('extracted-data-preview');
    if (!previewContainer) return;
    
    const dateElement = document.getElementById('extracted-date');
    const timeElement = document.getElementById('extracted-time');
    const locationElement = document.getElementById('extracted-location');
    const locationConfidenceElement = document.getElementById('location-confidence');
    const locationIdInput = document.getElementById('location-id');
    const extractionErrorElement = document.getElementById('extraction-error');
    
    // "Übernehmen" Buttons
    const useDateButton = document.getElementById('use-extracted-date');
    const useTimeButton = document.getElementById('use-extracted-time');
    
    // Verstecke den Fehlertext standardmäßig
    if (extractionErrorElement) {
        extractionErrorElement.classList.add('hidden');
    }
    
    // Datum anzeigen
    if (dateElement) {
        if (data.date) {
            dateElement.textContent = formatDate(data.date);
            
            // Auch im Formular setzen, wenn vorhanden
            const incidentDateInput = document.getElementById('incident-date');
            if (incidentDateInput) {
                incidentDateInput.value = data.date;
                
                // Datenübernahme-Button ausblenden, da bereits übernommen
                if (useDateButton) {
                    useDateButton.classList.add('hidden');
                }
            } else if (useDateButton) {
                // Button anzeigen, wenn das Datum nicht automatisch übernommen wurde
                useDateButton.classList.remove('hidden');
            }
        } else {
            dateElement.textContent = 'Nicht erkannt';
            if (extractionErrorElement) {
                extractionErrorElement.classList.remove('hidden');
            }
        }
    }
    
    // Zeit anzeigen
    if (timeElement) {
        if (data.time) {
            timeElement.textContent = data.time;
            
            // Auch im Formular setzen, wenn vorhanden
            const incidentTimeInput = document.getElementById('incident-time');
            if (incidentTimeInput) {
                incidentTimeInput.value = data.time;
                
                // Zeitübernahme-Button ausblenden, da bereits übernommen
                if (useTimeButton) {
                    useTimeButton.classList.add('hidden');
                }
            } else if (useTimeButton) {
                // Button anzeigen, wenn die Zeit nicht automatisch übernommen wurde
                useTimeButton.classList.remove('hidden');
            }
        } else {
            timeElement.textContent = 'Nicht erkannt';
            if (extractionErrorElement) {
                extractionErrorElement.classList.remove('hidden');
            }
        }
    }
    
    // Standort anzeigen
    if (locationElement) {
        if (data.location) {
            locationElement.textContent = data.location;
            
            // Konfidenzwert anzeigen
            if (locationConfidenceElement) {
                const confidencePercentage = Math.round(data.confidence * 100);
                locationConfidenceElement.textContent = `(${confidencePercentage}% Übereinstimmung)`;
                
                // Farbcodierung basierend auf Konfidenz
                if (data.confidence > 0.8) {
                    locationConfidenceElement.classList.add('text-green-400');
                } else if (data.confidence > 0.5) {
                    locationConfidenceElement.classList.add('text-yellow-400');
                } else {
                    locationConfidenceElement.classList.add('text-red-400');
                }
            }
            
            // Standort-ID speichern
            if (locationIdInput && data.locationId) {
                locationIdInput.value = data.locationId;
            }
        } else {
            locationElement.textContent = 'Nicht erkannt';
            if (extractionErrorElement) {
                extractionErrorElement.classList.remove('hidden');
            }
        }
    }
    
    // Vorschaubereich anzeigen
    previewContainer.classList.remove('hidden');
}

/**
 * Format a date for display
 * @param {string} dateStr - Date string in YYYY-MM-DD format
 * @returns {string} Formatted date string in DD.MM.YYYY format
 */
function formatDate(dateStr) {
    if (!dateStr) return '';
    
    try {
        const parts = dateStr.split('-');
        if (parts.length === 3) {
            return `${parts[2]}.${parts[1]}.${parts[0]}`;
        }
        return dateStr;
    } catch (e) {
        return dateStr;
    }
}

/**
 * Remove the selected email file
 */
export function removeEmailFile() {
    emailFile = null;
    extractedData = null;
    
    // Update UI
    const fileInfo = document.getElementById('file-info');
    if (fileInfo) {
        fileInfo.classList.add('hidden');
    }
    
    // Hide extracted data preview
    const extractedDataPreview = document.getElementById('extracted-data-preview');
    if (extractedDataPreview) {
        extractedDataPreview.classList.add('hidden');
    }
    
    // Reset location ID
    const locationIdInput = document.getElementById('location-id');
    if (locationIdInput) {
        locationIdInput.value = '';
    }
    
    // Clear file input
    const fileUpload = document.getElementById('email-upload');
    if (fileUpload) {
        fileUpload.value = '';
    }
    
    showToast('Datei entfernt', 'info');
}

/**
 * Format file size for display
 * @param {number} bytes File size in bytes
 * @returns {string} Formatted file size
 */
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' Bytes';
    else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    else return (bytes / 1048576).toFixed(1) + ' MB';
}
// 4. Export statement am Ende
export default {
    fetchCsrfToken,
    setupFormHandlers,
    initializeUploadArea,
    removeEmailFile
};