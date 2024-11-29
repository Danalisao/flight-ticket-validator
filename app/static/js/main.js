document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const fileUpload = document.getElementById('file-upload');
    const fileName = document.getElementById('file-name');
    const validateBtn = document.getElementById('validate-btn');
    const resultsModal = document.getElementById('results-modal');
    const closeModalBtn = document.getElementById('close-modal');
    const validationStatus = document.getElementById('validation-status');
    const ticketDetails = document.getElementById('ticket-details');

    // File upload handling
    fileUpload.addEventListener('change', function(e) {
        const file = e.target.files[0];
        fileName.textContent = file ? file.name : 'No file selected';
    });

    // Drag and drop handling
    const dropZone = document.querySelector('label[for="file-upload"]');
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });

    function highlight(e) {
        dropZone.classList.add('border-blue-500', 'bg-blue-50');
    }

    function unhighlight(e) {
        dropZone.classList.remove('border-blue-500', 'bg-blue-50');
    }

    dropZone.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const file = dt.files[0];
        fileUpload.files = dt.files;
        fileName.textContent = file.name;
    }

    // Validation button handling
    validateBtn.addEventListener('click', async function() {
        const file = fileUpload.files[0];
        if (!file) {
            showError('Please select a file first');
            return;
        }

        // Check file type
        if (!file.type.match(/^image\/.+|application\/pdf$/)) {
            showError('Only images and PDF files are supported');
            return;
        }

        const formData = new FormData();
        formData.append('ticket_image', file);

        // Get checkbox values
        const useAmadeus = document.getElementById('amadeus-check').checked;
        const clearCache = document.getElementById('cache-clear').checked;

        try {
            // Clear cache if requested
            if (clearCache) {
                await fetch('/api/clear-cache', {
                    method: 'POST'
                });
            }

            // Show loading state
            validateBtn.disabled = true;
            validateBtn.innerHTML = '<span class="inline-block animate-spin mr-2">↻</span> Validating...';

            // Send validation request
            const response = await fetch('/api/validate', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            // Display results
            showResults(result);
        } catch (error) {
            showError('An error occurred during validation');
            console.error('Error:', error);
        } finally {
            // Reset button state
            validateBtn.disabled = false;
            validateBtn.textContent = 'Validate Ticket';
        }
    });

    // Modal handling
    closeModalBtn.addEventListener('click', function() {
        resultsModal.classList.add('hidden');
    });

    function showResults(result) {
        // Update validation status
        validationStatus.innerHTML = result.is_valid
            ? '<div class="bg-green-100 text-green-800 p-4 rounded-lg">✓ Ticket is valid</div>'
            : '<div class="bg-red-100 text-red-800 p-4 rounded-lg">✗ Ticket validation failed</div>';

        // Update ticket details
        let detailsHTML = '';
        if (result.extracted_info) {
            detailsHTML += '<h3 class="font-semibold mb-2">Extracted Information:</h3>';
            for (const [key, value] of Object.entries(result.extracted_info)) {
                detailsHTML += `<div class="mb-1"><span class="font-medium">${key}:</span> ${value}</div>`;
            }
        }
        if (result.errors && result.errors.length > 0) {
            detailsHTML += '<h3 class="font-semibold mt-4 mb-2 text-red-600">Errors:</h3>';
            detailsHTML += '<ul class="list-disc list-inside">';
            result.errors.forEach(error => {
                detailsHTML += `<li class="text-red-600">${error}</li>`;
            });
            detailsHTML += '</ul>';
        }
        ticketDetails.innerHTML = detailsHTML;

        // Show modal
        resultsModal.classList.remove('hidden');
        resultsModal.classList.add('flex');
    }

    function showError(message) {
        validationStatus.innerHTML = `<div class="bg-red-100 text-red-800 p-4 rounded-lg">${message}</div>`;
        ticketDetails.innerHTML = '';
        resultsModal.classList.remove('hidden');
        resultsModal.classList.add('flex');
    }
});
