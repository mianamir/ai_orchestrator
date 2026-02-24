/**
 * Travel Companion App - Frontend JavaScript
 * Handles user interactions and API communication
 */

// API Base URL - Update this to match your backend URL
const API_BASE_URL = 'http://localhost:8000';

// DOM Elements
const locationForm = document.getElementById('locationForm');
const imageForm = document.getElementById('imageForm');
const imageInput = document.getElementById('imageInput');
const imagePreview = document.getElementById('imagePreview');
const previewImg = document.getElementById('previewImg');
const loadingSpinner = document.getElementById('loadingSpinner');
const resultsSection = document.getElementById('resultsSection');
const resultsContainer = document.getElementById('resultsContainer');
const weatherModal = new bootstrap.Modal(document.getElementById('weatherModal'));
const weatherContent = document.getElementById('weatherContent');

// Preference checkboxes
const preferenceCheckboxes = document.querySelectorAll('.preference-check');
const imagePreferenceCheckboxes = document.querySelectorAll('.image-preference-check');

/**
 * Limit preference selection to maximum 3
 */
function limitPreferences(checkboxes) {
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const checkedCount = Array.from(checkboxes).filter(cb => cb.checked).length;
            
            if (checkedCount > 3) {
                this.checked = false;
                showToast('Maximum 3 preferences allowed', 'warning');
            }
        });
    });
}

// Apply preference limits
limitPreferences(preferenceCheckboxes);
limitPreferences(imagePreferenceCheckboxes);

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    // Create a simple alert-style notification
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.style.zIndex = '9999';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 3000);
}

/**
 * Get selected preferences from checkboxes
 */
function getSelectedPreferences(checkboxes) {
    return Array.from(checkboxes)
        .filter(cb => cb.checked)
        .map(cb => cb.value);
}

/**
 * Handle image preview
 */
imageInput.addEventListener('change', function(e) {
    const file = e.target.files[0];
    
    if (file) {
        const reader = new FileReader();
        
        reader.onload = function(event) {
            previewImg.src = event.target.result;
            imagePreview.classList.remove('d-none');
        };
        
        reader.readAsDataURL(file);
    } else {
        imagePreview.classList.add('d-none');
    }
});

/**
 * Show loading state
 */
function showLoading() {
    loadingSpinner.classList.remove('d-none');
    resultsSection.classList.add('d-none');
}

/**
 * Hide loading state
 */
function hideLoading() {
    loadingSpinner.classList.add('d-none');
}

/**
 * Display travel suggestions
 */
function displaySuggestions(destinations) {
    resultsContainer.innerHTML = '';
    
    destinations.forEach((destination, index) => {
        const card = createDestinationCard(destination, index);
        resultsContainer.appendChild(card);
    });
    
    resultsSection.classList.remove('d-none');
    
    // Smooth scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Create a destination card element
 */
function createDestinationCard(destination, index) {
    const col = document.createElement('div');
    col.className = 'col-md-6 col-lg-4';
    
    // Determine budget badge color
    let badgeClass = 'bg-success';
    if (destination.budget_level === 'Moderate') {
        badgeClass = 'bg-warning text-dark';
    } else if (destination.budget_level === 'Luxury') {
        badgeClass = 'bg-danger';
    }
    
    // Create attractions list
    const attractionsList = destination.attractions
        .map(attraction => `<li>${attraction}</li>`)
        .join('');
    
    col.innerHTML = `
        <div class="card destination-card shadow-sm h-100">
            <div class="card-body">
                <h5 class="card-title">
                    <i class="bi bi-geo-alt-fill"></i> ${destination.name}
                </h5>
                <span class="badge ${badgeClass} mb-3">${destination.budget_level}</span>
                
                <p class="card-text">${destination.description}</p>
                
                <div class="mb-3">
                    <strong><i class="bi bi-calendar-event"></i> Best Time:</strong>
                    <p class="mb-0">${destination.best_time}</p>
                </div>
                
                <div class="mb-3">
                    <strong><i class="bi bi-star-fill"></i> Top Attractions:</strong>
                    <ul class="attractions-list mt-2">
                        ${attractionsList}
                    </ul>
                </div>
                
                <button class="btn btn-outline-primary weather-btn" 
                        onclick="getWeather('${destination.name}')">
                    <i class="bi bi-cloud-sun"></i> Check Weather
                </button>
            </div>
        </div>
    `;
    
    return col;
}

/**
 * Display weather information in modal
 */
function displayWeather(data, destination) {
    const weatherData = data.weather_data;
    const description = data.description;
    
    let weatherHTML = `<div class="weather-info">`;
    
    if (weatherData) {
        // Display structured weather data
        weatherHTML += `
            <h5 class="text-center mb-3">
                <i class="bi bi-geo-alt-fill"></i> ${weatherData.location}
            </h5>
            <div class="temperature-display">
                ${weatherData.temperature}°${weatherData.unit === 'celsius' ? 'C' : 'F'}
            </div>
            <p class="text-center lead">${weatherData.condition}</p>
            <hr>
            <div class="weather-detail">
                <strong><i class="bi bi-droplet-fill"></i> Humidity:</strong>
                <span>${weatherData.humidity}</span>
            </div>
            <div class="weather-detail">
                <strong><i class="bi bi-wind"></i> Wind Speed:</strong>
                <span>${weatherData.wind_speed}</span>
            </div>
        `;
    }
    
    // Add AI description
    if (description) {
        weatherHTML += `
            <hr>
            <div class="mt-3">
                <strong><i class="bi bi-chat-left-text"></i> AI Insight:</strong>
                <p class="mt-2">${description}</p>
            </div>
        `;
    }
    
    weatherHTML += `</div>`;
    
    weatherContent.innerHTML = weatherHTML;
}



/**
 * Initialize app
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Travel Companion App initialized');
    console.log('API Base URL:', API_BASE_URL);
});

/**
 * Integration Task 1:
 * Handle location form submission
 */

locationForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    
	const location = document.getElementById('locationInput').value.trim();
    const preferences = getSelectedPreferences(preferenceCheckboxes);

    if (!location) {
       showToast('Please enter a location', 'warning');
       return;
    }
    
    showLoading();

    try {

        const response = await fetch(`${API_BASE_URL}/api/suggest-by-location`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    location: location,
                    preferences: preferences
                })
        });
                
        if (!response.ok) {
            throw new Error('Failed to fetch suggestions');
        }
                
        const data = await response.json();
        hideLoading();
        displaySuggestions(data.destinations);
    } catch (error) {
        hideLoading();
        console.error('Error:', error);
        showToast('Error fetching travel suggestions. Please try again.', 'danger');
    }
})


/**
 * Integration Task 2:
 * Handle image form submission
 */

imageForm.addEventListener('submit', async function(e) {

    e.preventDefault();
    
    const file = imageInput.files[0];
    const preferences = getSelectedPreferences(imagePreferenceCheckboxes);
        
    if (!file) {
        showToast('Please select an image', 'warning');
        return;
    }

    showLoading();

    try {

        const formData = new FormData();
        formData.append('file', file);
                
        // Add preferences as a comma-separated string
        if (preferences.length > 0) {
            formData.append('preferences', preferences.join(','));
        }

        const response = await fetch(`${API_BASE_URL}/api/suggest-by-image`, {
                method: 'POST',
                body: formData
        });

        if (!response.ok) {
                throw new Error('Failed to process image');
        }
                
        const data = await response.json();
        hideLoading();
        displaySuggestions(data.destinations);

    } catch (error) {

        hideLoading();
        console.error('Error:', error);
        showToast('Error processing image. Please try again.', 'danger');
    }

})


/**
 * Integration Task 3: Implement getWeather()
 * Get weather information for a destination
 * This function is called from the onclick attribute in the HTML
 */

async function getWeather(destination) {

    // Show modal with loading state
    weatherContent.innerHTML = `
        <div class="text-center">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Fetching weather information...</p>
        </div>
    `;
    weatherModal.show();

    try {

        const response = await fetch(`${API_BASE_URL}/api/weather`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                destination: destination
            })
        });

        if (!response.ok) {
            throw new Error('Failed to fetch weather');
        }

        const data = await response.json();
        displayWeather(data, destination);

    } catch (error) {
            console.error('Error:', error);
            weatherContent.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle"></i>
                    Error fetching weather information. Please try again.
                </div>
            `;
    }

}

