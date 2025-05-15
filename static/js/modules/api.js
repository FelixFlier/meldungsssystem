/**
 * API Client Module - Updated for Location Support
 * Centralized service for all API communication
 */

// Base configuration
const API_BASE_URL = '';  // Base URL is empty for same-origin requests

// Default headers for JSON requests
const defaultHeaders = {
  'Content-Type': 'application/json',
};

/**
 * Get authentication headers if a token is available
 * @returns {Object} Authentication headers or empty object
 */
const getAuthHeader = () => {
  const token = localStorage.getItem('accessToken');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
};

/**
 * Parse API response based on content type
 * @param {Response} response Fetch response object
 * @returns {Promise<Object|string>} Parsed response data
 */
const parseResponse = async (response) => {
  // Try to parse as JSON first
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    try {
      return await response.json();
    } catch (error) {
      console.error('Error parsing JSON response:', error);
      return await response.text();
    }
  }
  return await response.text();
};

/**
 * Generic request function with error handling
 * @param {string} url API endpoint
 * @param {Object} options Fetch options
 * @returns {Promise<Object|string>} Response data
 */
const request = async (url, options = {}) => {
  try {
    const response = await fetch(`${API_BASE_URL}${url}`, options);
    
    if (!response.ok) {
      const errorData = await parseResponse(response);
      throw new Error(
        typeof errorData === 'object' && errorData.detail 
          ? errorData.detail 
          : typeof errorData === 'string' 
            ? errorData 
            : `Error ${response.status}: ${response.statusText}`
      );
    }
    
    return parseResponse(response);
  } catch (error) {
    console.error(`API Error [${url}]:`, error);
    throw error;
  }
};

/**
 * API client with all available endpoints
 */
export const api = {
  // --- Auth endpoints ---
  
  /**
   * Fetch a CSRF token for form submission
   * @returns {Promise<Object>} CSRF token object
   */
  fetchCsrfToken: async () => {
    return request('/csrf-token');
  },
  
  /**
   * Login with username and password
   * @param {string} username User's username
   * @param {string} password User's password 
   * @returns {Promise<Object>} Authentication token and user ID
   */
  login: async (username, password) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    return request('/token', {
      method: 'POST',
      body: formData,
    });
  },
  
  // --- User endpoints ---
  
  /**
   * Create a new user account
   * @param {Object} userData User registration data
   * @returns {Promise<Object>} Created user data
   */
  registerUser: async (userData) => {
    return request('/users/', {
      method: 'POST',
      headers: {
        ...defaultHeaders,
      },
      body: JSON.stringify(userData),
    });
  },
  
  /**
   * Get current user's profile
   * @returns {Promise<Object>} User profile data
   */
  getUserProfile: async () => {
    return request('/users/me/', {
      headers: {
        ...defaultHeaders,
        ...getAuthHeader(),
      }
    });
  },
  
  /**
   * Update current user's profile
   * @param {Object} userData Updated user data
   * @returns {Promise<Object>} Updated user profile
   */
  updateUserProfile: async (userData) => {
    return request('/users/me/', {
      method: 'PUT',
      headers: {
        ...defaultHeaders,
        ...getAuthHeader(),
      },
      body: JSON.stringify(userData),
    });
  },
  
  /**
   * Get simplified user profile for UI
   * @returns {Promise<Object>} Basic user profile
   */
  getBasicProfile: async () => {
    return request('/basic-profile', {
      headers: getAuthHeader(),
    });
  },
  
  /**
   * Check if authentication is valid
   * @returns {Promise<Object>} Auth status
   */
  checkAuthStatus: async () => {
    return request('/api/auth-status', {
      headers: getAuthHeader(),
    });
  },
  
  // --- Location endpoints ---
  
  /**
   * Get all locations from the police database
   * @returns {Promise<Array>} List of locations
   */
  getLocations: async () => {
    return request('/api/locations', {
      headers: {
        ...defaultHeaders,
        ...getAuthHeader()
      },
    });
  },
  
  /**
   * Get location by ID
   * @param {number} id Location ID
   * @returns {Promise<Object>} Location details
   */
  getLocationById: async (id) => {
    return request(`/api/locations/${id}`, {
      headers: {
        ...defaultHeaders,
        ...getAuthHeader()
      },
    });
  },
  
  // --- Incident endpoints ---
  
  /**
   * Get all incidents for current user
   * @returns {Promise<Array>} List of incidents
   */
  getIncidents: async () => {
    return request('/incidents/', {
      headers: {
        ...defaultHeaders,
        ...getAuthHeader()
      },
    });
  },
  
  /**
   * Get incident details by ID
   * @param {number} id Incident ID
   * @returns {Promise<Object>} Incident details
   */
  getIncidentDetails: async (id) => {
    return request(`/incidents/${id}`, {
      headers: {
        ...defaultHeaders,
        ...getAuthHeader()
      },
    });
  },
  
  /**
   * Create a new incident
   * @param {Object} incidentData Incident data
   * @returns {Promise<Object>} Created incident
   */
  createIncident: async (incidentData) => {
    return request('/incidents/', {
      method: 'POST',
      headers: {
        ...defaultHeaders,
        ...getAuthHeader(),
      },
      body: JSON.stringify(incidentData),
    });
  },
  
  /**
   * Update incident status
   * @param {number} id Incident ID
   * @param {Object} updateData Update data
   * @returns {Promise<Object>} Updated incident
   */
  updateIncident: async (id, updateData) => {
    return request(`/incidents/${id}`, {
      method: 'PATCH',
      headers: {
        ...defaultHeaders,
        ...getAuthHeader(),
      },
      body: JSON.stringify(updateData),
    });
  },
  

  // Fügen Sie diese Funktionen zum API-Objekt hinzu:

// --- User Location endpoints ---

/**
 * Get all user locations
 * @returns {Promise<Array>} List of user locations
 */
getUserLocations: async () => {
  return request('/api/user-locations', {
      headers: {
          ...defaultHeaders,
          ...getAuthHeader()
      },
  });
},

/**
* Get specific user location
* @param {number} id Location ID
* @returns {Promise<Object>} Location details
*/
getUserLocationById: async (id) => {
  return request(`/api/user-locations/${id}`, {
      headers: {
          ...defaultHeaders,
          ...getAuthHeader()
      },
  });
},

/**
* Create a new user location
* @param {Object} locationData Location data
* @returns {Promise<Object>} Created location
*/
createUserLocation: async (locationData) => {
  return request('/api/user-locations', {
      method: 'POST',
      headers: {
          ...defaultHeaders,
          ...getAuthHeader(),
      },
      body: JSON.stringify(locationData),
  });
},

/**
* Update user location
* @param {number} id Location ID
* @param {Object} locationData Updated location data
* @returns {Promise<Object>} Updated location
*/
updateUserLocation: async (id, locationData) => {
  return request(`/api/user-locations/${id}`, {
      method: 'PUT',
      headers: {
          ...defaultHeaders,
          ...getAuthHeader(),
      },
      body: JSON.stringify(locationData),
  });
},

/**
* Delete user location
* @param {number} id Location ID
* @returns {Promise<Object>} Deletion confirmation
*/
deleteUserLocation: async (id) => {
  return request(`/api/user-locations/${id}`, {
      method: 'DELETE',
      headers: {
          ...defaultHeaders,
          ...getAuthHeader(),
      },
  });
},

  // --- Activities endpoints ---
  
  /**
   * Get user activities/audit logs
   * @returns {Promise<Array>} List of activities
   */
  getActivities: async () => {
    return request('/api/activities', {
      headers: {
        ...defaultHeaders,
        ...getAuthHeader()
      },
    });
  },
};

export default api;