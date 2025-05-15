/**
 * User Locations Module
 * Handles user-specific crime scene locations
 */

import { api } from './api.js';
import { showToast } from './ui.js';

let userLocations = [];

/**
 * Load all user locations
 */
export async function loadUserLocations() {
    try {
        userLocations = await api.getUserLocations();
        renderUserLocations();
        return userLocations;
    } catch (error) {
        console.error('Error loading user locations:', error);
        return [];
    }
}

/**
 * Render user locations in the profile modal
 */
export function renderUserLocations() {
    const container = document.getElementById('user-locations-list');
    if (!container) return;
    
    if (userLocations.length === 0) {
        container.innerHTML = `
            <div class="text-center text-gray-400 py-4">
                Keine Standorte definiert
            </div>
        `;
        return;
    }
    
    container.innerHTML = userLocations.map(location => `
        <div class="glass p-4 rounded-lg mb-3 flex justify-between items-center">
            <div>
                <h4 class="font-semibold text-white">${location.name}</h4>
                <p class="text-sm text-gray-300">
                    ${location.strasse} ${location.hausnummer}, ${location.ort}
                </p>
                ${location.zusatz_info ? `<p class="text-xs text-gray-400">${location.zusatz_info}</p>` : ''}
            </div>
            <div class="flex space-x-2">
                <button class="creative-btn px-3 py-1 text-sm" 
                        data-action="edit-user-location" 
                        data-location-id="${location.id}">
                    Bearbeiten
                </button>
                <button class="creative-btn px-3 py-1 text-sm bg-red-500/20" 
                        data-action="delete-user-location" 
                        data-location-id="${location.id}">
                    Löschen
                </button>
            </div>
        </div>
    `).join('');
}

/**
 * Show location form for create/edit
 */
// ... Imports bleiben wie gehabt ...

export function showLocationForm(locationData = null) {
    console.log('showLocationForm called with data:', locationData);
    
    // Erst prüfen ob das Profil-Modal aktiv ist
    const profileModal = document.getElementById('profile-modal');
    if (!profileModal || !profileModal.classList.contains('active')) {
        console.error('Profile modal must be open before showing location form');
        return;
    }
    
    // Container und Liste finden
    const container = document.getElementById('user-location-form-container');
    const list = document.getElementById('user-locations-list');
    
    if (!container || !list) {
        console.error('Required elements not found');
        return;
    }
    
    // Container sichtbar machen
    container.classList.remove('hidden');
    list.classList.add('hidden');
    
    // Prüfen ob das Form-Element existiert, wenn nicht - dynamisch erstellen
    let form = document.getElementById('user-location-form');
    
    if (!form) {
        console.log('Form not found, creating it dynamically');
        
        // Erstelle das Form-Element
        form = document.createElement('form');
        form.id = 'user-location-form';
        form.className = 'space-y-4';
        
        // Verschiebe alle Kinder des Containers in das Form-Element
        while (container.firstChild) {
            form.appendChild(container.firstChild);
        }
        
        // Füge das Form dem Container hinzu
        container.appendChild(form);
    }
    
    // Event-Handler für das Formular setzen
    form.onsubmit = async function(event) {
        event.preventDefault();
        console.log('Form submitted');
        
        // Sammle die Formulardaten
        const locationData = {
            id: form.querySelector('#location-id').value,
            name: form.querySelector('#location-name').value,
            bundesland: form.querySelector('#location-bundesland').value,
            ort: form.querySelector('#location-ort').value,
            strasse: form.querySelector('#location-strasse').value,
            hausnummer: form.querySelector('#location-hausnummer').value,
            zusatz_info: form.querySelector('#location-zusatz').value
        };
        
        console.log('Collected location data:', locationData);
        
        try {
            await saveUserLocation(locationData);
        } catch (error) {
            console.error('Error in form submission:', error);
            showToast('Fehler beim Speichern des Standorts', 'error');
        }
    };
    
    // Form-Daten setzen
    setTimeout(() => {
        if (locationData) {
            // Bearbeiten
            console.log('Filling form with existing data');
            form.querySelector('#location-id').value = locationData.id || '';
            form.querySelector('#location-name').value = locationData.name || '';
            form.querySelector('#location-bundesland').value = locationData.bundesland || '';
            form.querySelector('#location-ort').value = locationData.ort || '';
            form.querySelector('#location-strasse').value = locationData.strasse || '';
            form.querySelector('#location-hausnummer').value = locationData.hausnummer || '';
            form.querySelector('#location-zusatz').value = locationData.zusatz_info || '';
        } else {
            // Neu
            console.log('Resetting form for new location');
            form.reset();
            form.querySelector('#location-id').value = '';
        }
        
        // Focus auf das erste Input-Feld setzen
        const firstInput = form.querySelector('#location-name');
        if (firstInput) firstInput.focus();
    }, 100);
}

export function hideLocationForm() {
    console.log('hideLocationForm called');
    
    const container = document.getElementById('user-location-form-container');
    const list = document.getElementById('user-locations-list');
    
    if (container) container.classList.add('hidden');
    if (list) list.classList.remove('hidden');
}

export async function saveUserLocation(locationData) {
    try {
        console.log('saveUserLocation called with data:', locationData);
        
        // ID überprüfen
        const locationId = locationData.id;
        
        // Prepare data for API
        const apiData = {
            name: locationData.name,
            bundesland: locationData.bundesland,
            ort: locationData.ort,
            strasse: locationData.strasse,
            hausnummer: locationData.hausnummer,
            zusatz_info: locationData.zusatz_info || null,
            staat: 'Deutschland'
        };
        
        console.log('Prepared API data:', apiData);
        
        let result;
        
        if (locationId && locationId !== '') {
            // Update existing location
            console.log('Updating location with ID:', locationId);
            result = await api.updateUserLocation(locationId, apiData);
        } else {
            // Create new location
            console.log('Creating new location');
            result = await api.createUserLocation(apiData);
        }
        
        console.log('API result:', result);
        
        showToast('Standort erfolgreich gespeichert', 'success');
        await loadUserLocations();
        hideLocationForm();
        return result;
    } catch (error) {
        console.error('Error saving location:', error);
        
        // Detailliertere Fehlermeldung
        let errorMessage = 'Fehler beim Speichern des Standorts';
        if (error.message) {
            errorMessage += ': ' + error.message;
        }
        
        showToast(errorMessage, 'error');
        throw error;
    }
}

/**
 * Delete user location
 */
export async function deleteUserLocation(locationId) {
    try {
        await api.deleteUserLocation(locationId);
        showToast('Standort erfolgreich gelöscht', 'success');
        await loadUserLocations();
    } catch (error) {
        console.error('Error deleting location:', error);
        showToast('Fehler beim Löschen des Standorts', 'error');
    }
}

/**
 * Render user locations in the incident creation modal
 */
export function renderUserLocationsDropdown() {
    const container = document.getElementById('user-locations-dropdown');
    if (!container) return;
    
    if (userLocations.length === 0) {
        container.innerHTML = `
            <option value="">Keine eigenen Standorte definiert</option>
        `;
        return;
    }
    
    container.innerHTML = `
        <option value="">-- Standort auswählen --</option>
        ${userLocations.map(location => `
            <option value="${location.id}" 
                    data-location-data='${JSON.stringify(location)}'>
                ${location.name} - ${location.ort}
            </option>
        `).join('')}
    `;
}

export default {
    loadUserLocations,
    renderUserLocations,
    showLocationForm,
    hideLocationForm,
    saveUserLocation,
    deleteUserLocation,
    renderUserLocationsDropdown
};