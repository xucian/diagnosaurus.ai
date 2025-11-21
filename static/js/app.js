// Diagnosaurus.ai Frontend Logic

let currentSessionId = null;
let pollInterval = null;

// DOM Elements
const symptomForm = document.getElementById('symptom-form');
const inputSection = document.getElementById('input-section');
const loadingSection = document.getElementById('loading-section');
const resultsSection = document.getElementById('results-section');
const loadingStatus = document.getElementById('loading-status');
const loadingMessage = document.getElementById('loading-message');
const progressFill = document.getElementById('progress-fill');

// Form submission
symptomForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const symptoms = document.getElementById('symptoms').value;
    const age = document.getElementById('age').value;
    const sex = document.getElementById('sex').value;

    if (symptoms.length < 10) {
        alert('Please provide a more detailed description of your symptoms.');
        return;
    }

    // Build request
    const requestData = {
        symptoms: symptoms,
        patient_age: age ? parseInt(age) : null,
        patient_sex: sex || null,
        documents: [],
    };

    // Handle file uploads (simplified - would need base64 encoding)
    const files = document.getElementById('documents').files;
    if (files.length > 0) {
        // TODO: Implement file encoding
        console.log('File uploads not yet implemented');
    }

    // Submit analysis
    try {
        showLoading();

        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData),
        });

        const data = await response.json();

        if (response.ok) {
            currentSessionId = data.session_id;
            startPolling();
        } else {
            alert('Error: ' + data.error);
            showInput();
        }
    } catch (error) {
        console.error('Submission error:', error);
        alert('Failed to submit analysis. Please try again.');
        showInput();
    }
});

// Show/hide sections
function showLoading() {
    inputSection.classList.add('hidden');
    loadingSection.classList.remove('hidden');
    resultsSection.classList.add('hidden');
}

function showResults() {
    inputSection.classList.add('hidden');
    loadingSection.classList.add('hidden');
    resultsSection.classList.remove('hidden');
}

function showInput() {
    inputSection.classList.remove('hidden');
    loadingSection.classList.add('hidden');
    resultsSection.classList.add('hidden');
}

// Polling for status updates
function startPolling() {
    pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/status/${currentSessionId}`);
            const data = await response.json();

            updateLoadingStatus(data);

            if (data.status === 'completed') {
                stopPolling();
                displayResults(data.result);
            } else if (data.status === 'failed') {
                stopPolling();
                alert('Analysis failed: ' + data.error);
                showInput();
            }
        } catch (error) {
            console.error('Polling error:', error);
        }
    }, 2000); // Poll every 2 seconds
}

function stopPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
}

function updateLoadingStatus(data) {
    const statusMessages = {
        'initializing': 'Initializing analysis...',
        'sanitizing': 'Sanitizing medical data...',
        'researching': 'Agent 1: Identifying potential conditions...',
        'deep_research': 'Agents researching conditions in detail...',
        'debating': 'Virtual forum: Cross-validating findings...',
        'analyzing': 'Analyzing condition probabilities...',
        'finding_clinics': 'Finding nearby healthcare providers...',
        'completed': 'Analysis complete!',
    };

    loadingStatus.textContent = statusMessages[data.status] || 'Processing...';
    progressFill.style.width = `${data.progress}%`;

    // Agent status messages
    if (data.status === 'deep_research') {
        loadingMessage.textContent = `Researching ${Math.ceil(data.progress / 10)} potential conditions...`;
    }
}

// Display results
function displayResults(result) {
    showResults();

    // Warning message
    if (result.warning_message) {
        const warningEl = document.getElementById('warning-message');
        warningEl.textContent = result.warning_message;
        warningEl.classList.remove('hidden');
    }

    // Conditions
    displayConditions(result.conditions);

    // Clinics
    displayClinics(result.clinics);
}

function displayConditions(conditions) {
    const bubblesGroup = document.getElementById('condition-bubbles');
    const legend = document.getElementById('condition-legend');

    bubblesGroup.innerHTML = '';
    legend.innerHTML = '';

    conditions.forEach((condition, index) => {
        // Create bubble on body diagram
        const bubble = createConditionBubble(condition, index);
        bubblesGroup.appendChild(bubble);

        // Create legend item
        const legendItem = createConditionLegend(condition);
        legend.appendChild(legendItem);
    });
}

function createConditionBubble(condition, index) {
    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    g.classList.add('condition-bubble');

    const x = condition.position.x;
    const y = condition.position.y;
    const size = 20 + (condition.probability * 40); // Size based on probability

    // Color based on confidence
    const color = getConfidenceColor(condition.confidence);

    // Circle
    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('cx', x);
    circle.setAttribute('cy', y);
    circle.setAttribute('r', size);
    circle.setAttribute('fill', color);
    circle.setAttribute('opacity', '0.85');
    circle.classList.add('condition-circle');

    // Percentage text
    const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    text.setAttribute('x', x);
    text.setAttribute('y', y + 6);
    text.classList.add('condition-percent');
    text.textContent = `${Math.round(condition.probability * 100)}%`;

    g.appendChild(circle);
    g.appendChild(text);

    // Tooltip on hover
    g.addEventListener('mouseenter', () => {
        showTooltip(condition, x, y);
    });

    return g;
}

function createConditionLegend(condition) {
    const div = document.createElement('div');
    div.classList.add('condition-item');
    div.style.borderColor = getConfidenceColor(condition.confidence);

    const probability = Math.round(condition.probability * 100);
    const confidence = Math.round(condition.confidence * 100);

    div.innerHTML = `
        <div class="condition-header">
            <div class="condition-name">${condition.name}</div>
            <div class="condition-scores">
                <span class="score">Probability: ${probability}%</span>
                <span class="score">Confidence: ${confidence}%</span>
                <span class="urgency-badge urgency-${condition.urgency}">${condition.urgency}</span>
            </div>
        </div>
        <div class="condition-evidence">${condition.evidence_summary}</div>
        ${condition.recommended_tests.length > 0 ? `
            <div style="margin-top: 10px; font-size: 0.9rem; color: #6b7280;">
                <strong>Recommended tests:</strong> ${condition.recommended_tests.join(', ')}
            </div>
        ` : ''}
    `;

    return div;
}

function displayClinics(clinics) {
    const clinicResults = document.getElementById('clinic-results');
    clinicResults.innerHTML = '';

    if (clinics.length === 0) {
        clinicResults.innerHTML = '<p>No clinics found in your area.</p>';
        return;
    }

    clinics.forEach(clinic => {
        const card = createClinicCard(clinic);
        clinicResults.appendChild(card);
    });
}

function createClinicCard(clinic) {
    const div = document.createElement('div');
    div.classList.add('clinic-card');

    const stars = '⭐'.repeat(Math.round(clinic.rating));

    div.innerHTML = `
        <div class="clinic-header">
            <div>
                <div class="clinic-name">${clinic.name}</div>
                <div class="clinic-doctor">
                    <span class="blurred" data-type="name">${clinic.doctor_name}</span>
                    <span class="click-to-reveal" onclick="revealInfo(this, 'name')">Click to reveal</span>
                </div>
                <div class="clinic-specialty">${clinic.specialty}</div>
            </div>
            <div class="clinic-rating">
                <span class="stars">${stars}</span>
                <span>${clinic.rating.toFixed(1)} (${clinic.review_count} reviews)</span>
            </div>
        </div>
        <div class="clinic-info">
            <div class="clinic-info-item">
                📍 ${clinic.address} (${clinic.distance_km.toFixed(1)} km away)
            </div>
            <div class="clinic-info-item">
                📞
                <span class="blurred" data-type="phone">${clinic.phone}</span>
                <span class="click-to-reveal" onclick="revealInfo(this, 'phone')">Click to reveal</span>
            </div>
            ${clinic.website ? `
                <div class="clinic-info-item">
                    🌐 <a href="${clinic.website}" target="_blank">Website</a>
                </div>
            ` : ''}
            ${clinic.next_available ? `
                <div class="clinic-info-item">
                    📅 Next available: ${clinic.next_available}
                </div>
            ` : ''}
        </div>
    `;

    return div;
}

// Reveal blurred info
function revealInfo(button, type) {
    const parent = button.parentElement;
    const blurred = parent.querySelector('.blurred');
    blurred.classList.remove('blurred');
    button.remove();
}

// Color helpers
function getConfidenceColor(confidence) {
    if (confidence >= 0.75) {
        return '#10b981'; // Green
    } else if (confidence >= 0.50) {
        return '#f59e0b'; // Yellow
    } else {
        return '#ef4444'; // Red
    }
}

// Tooltip (simplified)
function showTooltip(condition, x, y) {
    // Could implement a more sophisticated tooltip
    console.log('Tooltip:', condition);
}

// Reset form
function resetForm() {
    symptomForm.reset();
    showInput();
    currentSessionId = null;
}
