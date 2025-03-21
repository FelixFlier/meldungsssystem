/**
 * Forms Module
 * Handles form submissions, validation, and file uploads
 */

import { api } from './api.js';
import { showToast, showFormError, clearFormError, hideModal, showModal } from './ui.js';
import { processLogin } from './auth.js';
import { submitIncident } from './incidents.js';

// Global CSRF token
let csrfToken = '';

// Global file storage
let excelFile = null;

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
export function setupFormHandlers() {
    console.log('Setting up form handlers');
    
    // Login form
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLoginSubmit);
        console.log('Login form handler set up');
    } else {
        console.warn('Login form not found');
    }
    
    // Register form
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegisterSubmit);
        console.log('Register form handler set up');
    } else {
        console.warn('Register form not found');
    }
    
    // Datetime form (incident creation)
    const datetimeForm = document.getElementById('datetime-form');
    if (datetimeForm) {
        datetimeForm.addEventListener('submit', handleDatetimeSubmit);
        console.log('Datetime form handler set up');
    } else {
        console.warn('Datetime form not found');
    }
    
    // Profile form
    const profileForm = document.getElementById('profile-form');
    if (profileForm) {
        profileForm.addEventListener('submit', handleProfileSubmit);
        console.log('Profile form handler set up');
    } else {
        console.warn('Profile form not found');
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
    
    // Clear previous errors
    clearFormError(errorElement);
    
    const incidentType = form.querySelector('#incident-type').value;
    const incidentDate = form.querySelector('#incident-date').value;
    const incidentTime = form.querySelector('#incident-time').value;
    
    // Validierung
    if (!incidentDate || !incidentTime) {
        showFormError(errorElement, 'Bitte geben Sie Datum und Uhrzeit ein.');
        return;
    }
    
    // Hole Excel-Daten, falls vorhanden
    const excelData = localStorage.getItem('excel-data');
    localStorage.removeItem('excel-data'); // Entferne aus localStorage
    
    try {
        // Submit incident
        await submitIncident({
            type: incidentType,
            date: incidentDate,
            time: incidentTime,
            excelData: excelData
        });
        
        hideModal('datetime-modal');
        form.reset();
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
 * Initialize drag and drop area for Excel uploads
 */
export function initializeUploadArea() {
    const dropZone = document.getElementById('drop-zone');
    const fileUpload = document.getElementById('excel-upload');
    
    if (!dropZone || !fileUpload) {
        console.warn('Upload area elements not found');
        return;
    }
    
    console.log('Setting up upload area');
    
    // File input change event
    fileUpload.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            handleExcelFile(e.target.files[0]);
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
            handleExcelFile(e.dataTransfer.files[0]);
        }
    });
}

/**
 * Handle Excel file selection
 * @param {File} file The selected Excel file
 */
function handleExcelFile(file) {
    console.log('Handling Excel file:', file.name);
    
    // Check if file is Excel
    if (!file || (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls'))) {
        showToast('Bitte wählen Sie eine gültige Excel-Datei (.xlsx, .xls)', 'error');
        return;
    }
    
    excelFile = file;
    
    // Update UI
    const fileInfo = document.getElementById('file-info');
    const fileName = document.getElementById('file-name');
    const fileSize = document.getElementById('file-size');
    
    if (fileInfo && fileName && fileSize) {
        fileName.textContent = file.name;
        fileSize.textContent = formatFileSize(file.size);
        fileInfo.classList.remove('hidden');
    }
    
    // Parse file
    parseExcelFile(file);
}

/**
 * Parse Excel file and store data in localStorage
 * @param {File} file The Excel file to parse
 */
function parseExcelFile(file) {
    const reader = new FileReader();
    
    reader.onload = function(e) {
        try {
            const data = new Uint8Array(e.target.result);
            
            // Make sure XLSX is defined
            if (typeof XLSX === 'undefined') {
                console.error('XLSX library not found. Make sure the SheetJS library is loaded.');
                showToast('Excel-Verarbeitung nicht verfügbar. Bitte Administrator kontaktieren.', 'error');
                return;
            }
            
            const workbook = XLSX.read(data, { type: 'array' });
            
            // Get first sheet
            const sheetName = workbook.SheetNames[0];
            const sheet = workbook.Sheets[sheetName];
            
            // Convert to JSON
            const jsonData = XLSX.utils.sheet_to_json(sheet);
            
            // Store in localStorage for later use
            localStorage.setItem('excel-data', JSON.stringify(jsonData));
            
            showToast('Excel-Datei erfolgreich geladen', 'success');
        } catch (error) {
            console.error('Error parsing Excel file:', error);
            showToast('Fehler beim Lesen der Excel-Datei', 'error');
        }
    };
    
    reader.onerror = function() {
        showToast('Fehler beim Lesen der Datei', 'error');
    };
    
    reader.readAsArrayBuffer(file);
}

/**
 * Remove the selected Excel file
 */
export function removeExcelFile() {
    excelFile = null;
    localStorage.removeItem('excel-data');
    
    // Update UI
    const fileInfo = document.getElementById('file-info');
    if (fileInfo) {
        fileInfo.classList.add('hidden');
    }
    
    // Clear file input
    const fileUpload = document.getElementById('excel-upload');
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

export default {
    fetchCsrfToken,
    setupFormHandlers,
    initializeUploadArea,
    removeExcelFile
};