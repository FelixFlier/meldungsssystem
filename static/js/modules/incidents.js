/**
 * Incidents Module - Updated for Location Support
 * Handles incident creation, listing, and management
 */

import { api } from './api.js';
import { showToast, showModal, hideModal, showProgressBar, hideProgressBar } from './ui.js';

/**
 * Load user incidents from API
 * @returns {Promise<Array>} List of incidents
 */
export async function loadUserIncidents() {
    // Direkter Zugriff auf localStorage für den Token
    const token = localStorage.getItem('accessToken');
    if (!token) {
        console.warn('Cannot load incidents: No authentication token');
        return [];
    }
    
    try {
        // Explizite Verwendung der Fetch API mit Authorization-Header
        const response = await fetch('/incidents/', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`Error loading incidents: ${response.status} ${response.statusText}`);
        }
        
        const incidents = await response.json();
        displayIncidents(incidents);
        return incidents;
    } catch (error) {
        console.error('Error loading incidents:', error);
        showToast("Fehler beim Laden der Vorfälle", "error");
        return [];
    }
}

/**
 * Load user activities from API
 * @returns {Promise<Array>} List of activities
 */
export async function loadUserActivities() {
    // Direkter Zugriff auf localStorage für den Token
    const token = localStorage.getItem('accessToken');
    if (!token) {
        console.warn('Cannot load activities: No authentication token');
        return [];
    }
    
    try {
        // Explizite Verwendung der Fetch API mit Authorization-Header
        const response = await fetch('/api/activities', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`Error loading activities: ${response.status} ${response.statusText}`);
        }
        
        const activities = await response.json();
        displayActivities(activities);
        return activities;
    } catch (error) {
        console.error('Error loading activities:', error);
        showToast("Fehler beim Laden der Aktivitäten", "error");
        return [];
    }
}

/**
 * Display incidents in the UI
 * @param {Array} incidents List of incidents to display
 */
export function displayIncidents(incidents) {
    const tableBody = document.getElementById('incidents-table-body');
    const container = document.getElementById('incidents-container');
    
    if (!tableBody || !container) {
        console.warn('Incidents container or table body not found');
        return;
    }
    
    // Show container
    container.classList.remove('hidden');
    
    // Clear table
    tableBody.innerHTML = '';
    
    if (!incidents || incidents.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="7" class="py-4 px-4 text-center text-gray-400">Keine Vorfälle gefunden</td>
            </tr>
        `;
        return;
    }
    
    // Sort incidents - newest first
    incidents.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    
    // Add incidents
    incidents.forEach(incident => {
        const row = document.createElement('tr');
        row.className = 'border-b border-primary/10 hover:bg-surface/50';
        
        // Format date - explizit die lokale Zeitzone berücksichtigen
        const createdAt = new Date(incident.created_at);
        
        // Korrigiere Zeitverschiebung
        const localOffset = createdAt.getTimezoneOffset() * 60000; // Lokaler Offset in Millisekunden
        const localCreatedAt = new Date(createdAt.getTime() - localOffset);
        
        const formattedCreatedAt = localCreatedAt.toLocaleDateString('de-DE') + ' ' + 
                                  localCreatedAt.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
        
        // Determine status color
        const statusColor = getStatusClass(incident.status);
        const statusText = getStatusText(incident.status);
        
        // Location display
        const locationDisplay = incident.location ? incident.location : '-';
        
        row.innerHTML = `
            <td class="py-3 px-4">${incident.type === 'diebstahl' ? 'Diebstahl' : 'Sachbeschädigung'}</td>
            <td class="py-3 px-4">${locationDisplay}</td>
            <td class="py-3 px-4">${incident.incident_date}</td>
            <td class="py-3 px-4">${incident.incident_time}</td>
            <td class="py-3 px-4"><span class="${statusColor}">${statusText}</span></td>
            <td class="py-3 px-4">${formattedCreatedAt}</td>
            <td class="py-3 px-4">
                <button class="text-primary hover:text-secondary transition-colors" 
                        data-action="show-incident-details"
                        data-incident-id="${incident.id}"
                        aria-label="Details anzeigen">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                            d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                    </svg>
                </button>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
}

/**
 * Display activities in the UI
 * @param {Array} activities List of activities to display
 */
export function displayActivities(activities) {
    const tableBody = document.getElementById('activities-table-body');
    const container = document.getElementById('activities-container');
    
    if (!tableBody || !container) {
        console.warn('Activities container or table body not found');
        return;
    }
    
    // Show container
    container.classList.remove('hidden');
    
    // Clear table
    tableBody.innerHTML = '';
    
    if (!activities || activities.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="4" class="py-4 px-4 text-center text-gray-400">Keine Aktivitäten gefunden</td>
            </tr>
        `;
        return;
    }
    
    // Sort activities - newest first
    activities.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    // Add activities
    activities.forEach(activity => {
        const row = document.createElement('tr');
        row.className = 'border-b border-primary/10 hover:bg-surface/50';
        
        // Format date
        const timestamp = new Date(activity.timestamp);
        const formattedTimestamp = timestamp.toLocaleDateString('de-DE') + ' ' + 
                                  timestamp.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
        
        // Combine resource ID and type
        const resourceLabel = activity.resource_type + 
                            (activity.resource_id ? ` #${activity.resource_id}` : '');
        
        row.innerHTML = `
            <td class="py-3 px-4">${formattedTimestamp}</td>
            <td class="py-3 px-4">${formatActivityAction(activity.action)}</td>
            <td class="py-3 px-4">${resourceLabel}</td>
            <td class="py-3 px-4">${activity.details || '-'}</td>
        `;
        
        tableBody.appendChild(row);
    });
}

/**
 * Show incident details in modal
 * @param {number} incidentId ID of the incident to show
 */
export async function showIncidentDetails(incidentId) {
    const token = localStorage.getItem('accessToken');
    if (!token) {
        showToast('Bitte melden Sie sich an, um Details zu sehen.', 'error');
        return;
    }
    
    try {
        // Show loading state
        showProgressBar();
        
        // Load incident details
        const incident = await api.getIncidentDetails(incidentId);
        
        // Set data in modal
        const detailType = document.getElementById('detail-type');
        if (detailType) {
            detailType.textContent = incident.type === 'diebstahl' ? 'Diebstahl' : 'Sachbeschädigung';
        }
        
        // Status with color
        const statusEl = document.getElementById('detail-status');
        if (statusEl) {
            statusEl.textContent = getStatusText(incident.status);
            statusEl.className = getStatusClass(incident.status);
        }
        
        // Other fields
        const elements = {
            'detail-date': incident.incident_date,
            'detail-time': incident.incident_time,
            'detail-id': incident.id
        };
        
        // Add location if available
        if (document.getElementById('detail-location')) {
            document.getElementById('detail-location').textContent = incident.location || '-';
        }
        
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        });
        
        // Format creation date with timezone correction
        const createdDate = new Date(incident.created_at);
        
        // Korrigiere Zeitverschiebung für lokale Anzeige
        const localOffset = createdDate.getTimezoneOffset() * 60000; // Lokaler Offset in Millisekunden
        const localCreatedDate = new Date(createdDate.getTime() - localOffset);
        
        const createdEl = document.getElementById('detail-created');
        if (createdEl) {
            createdEl.textContent = `${localCreatedDate.toLocaleDateString('de-DE')} ${localCreatedDate.toLocaleTimeString('de-DE')}`;
        }
        
        // Agent log, if available
        const logContainer = document.getElementById('agent-log-container');
        const logElement = document.getElementById('agent-log');
        
        if (logContainer && logElement) {
            if (incident.agent_log) {
                logElement.textContent = incident.agent_log;
                logContainer.classList.remove('hidden');
            } else {
                logContainer.classList.add('hidden');
            }
        }
        
        // Hide loading state
        hideProgressBar();
        
        // Show modal
        showModal('incident-details-modal');
    } catch (error) {
        console.error('Error loading incident details:', error);
        showToast("Fehler beim Laden der Vorfalldetails", "error");
        hideProgressBar();
    }
}

/**
 * Handle agent type selection click
 * @param {string} type Type of incident (diebstahl, sachbeschaedigung)
 */
export function handleAgentClick(type) {
    if (!localStorage.getItem('accessToken')) {
        showToast('Bitte melden Sie sich zuerst an, um einen Vorfall zu melden.', 'info');
        showModal('login-modal');
        return;
    }
    
    // Set incident type and show datetime modal
    const incidentTypeInput = document.getElementById('incident-type');
    if (incidentTypeInput) {
        incidentTypeInput.value = type;
    }
    
    showModal('datetime-modal');
}

/**
 * Submit incident to API
 * @param {Object} incidentData Incident data
 * @returns {Promise<Object>} Created incident
 */
export async function submitIncident(incidentData) {
    if (!localStorage.getItem('accessToken')) {
        throw new Error('Sie sind nicht angemeldet');
    }
    
    hideModal('datetime-modal');
    showProgressBar();
    
    try {
        // Prepare API request data
        const apiData = {
            type: incidentData.type,
            incident_date: incidentData.date,
            incident_time: incidentData.time,
            location_id: incidentData.locationId, // Stellen Sie sicher, dass der Name identisch ist
            email_data: incidentData.emailData
        };
        
        console.log('Submitting incident data to API:', apiData);
        
        // Create incident
        const response = await fetch('/incidents/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
            },
            body: JSON.stringify(apiData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Fehler beim Erstellen des Vorfalls');
        }
        
        const result = await response.json();
        
        showToast("Vorgang wurde erfolgreich gestartet", "success");
        
        // Reload incidents after a short delay
        setTimeout(() => {
            loadUserIncidents();
        }, 1000);
        
        return result;
    } catch (error) {
        console.error('Error submitting incident:', error);
        showToast(error.message || "Ein Fehler ist aufgetreten", "error");
        throw error;
    } finally {
        hideProgressBar();
    }
}

/**
 * Get readable text for a status code
 * @param {string} status Status code
 * @returns {string} Readable status text
 */
export function getStatusText(status) {
    switch(status) {
        case 'pending': return 'In Bearbeitung';
        case 'processing': return 'Wird ausgeführt';
        case 'completed': return 'Abgeschlossen';
        case 'error': return 'Fehler';
        default: return 'Unbekannt';
    }
}

/**
 * Get CSS class for a status code
 * @param {string} status Status code
 * @returns {string} CSS class name
 */
export function getStatusClass(status) {
    switch(status) {
        case 'pending': return 'text-yellow-400';
        case 'processing': return 'text-blue-400';
        case 'completed': return 'text-green-400';
        case 'error': return 'text-red-400';
        default: return 'text-gray-400';
    }
}

/**
 * Format activity action for display
 * @param {string} action Activity action code
 * @returns {string} Readable action text
 */
export function formatActivityAction(action) {
    switch(action) {
        case 'login': return 'Anmeldung';
        case 'login_failed': return 'Fehlgeschlagene Anmeldung';
        case 'register': return 'Registrierung';
        case 'create': return 'Erstellt';
        case 'update': return 'Aktualisiert';
        case 'delete': return 'Gelöscht';
        default: return action;
    }
}

export default {
    loadUserIncidents,
    loadUserActivities,
    displayIncidents,
    displayActivities,
    showIncidentDetails,
    handleAgentClick,
    submitIncident,
    getStatusText,
    getStatusClass,
    formatActivityAction
};