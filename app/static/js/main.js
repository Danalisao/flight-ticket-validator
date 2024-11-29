document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('file-upload');
    const fileName = document.getElementById('file-name');
    const validateButton = document.getElementById('validate-button');
    const results = document.getElementById('results');
    const loading = document.getElementById('loading');
    const validationResults = document.getElementById('validationResults');
    const errorMessages = document.getElementById('errorMessages');

    // Mise à jour du nom de fichier
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            fileName.textContent = file.name;
        } else {
            fileName.textContent = 'Aucun fichier choisi';
        }
    });

    // Validation du billet
    validateButton.addEventListener('click', function() {
        const file = fileInput.files[0];
        if (!file) {
            showError('Veuillez sélectionner un fichier');
            return;
        }
        
        // Check file type
        const validTypes = ['image/jpeg', 'image/png', 'application/pdf'];
        if (!validTypes.includes(file.type)) {
            showError('Format de fichier non supporté. Utilisez JPEG, PNG ou PDF');
            return;
        }

        // Check file size (10MB max)
        if (file.size > 10 * 1024 * 1024) {
            showError('Le fichier est trop volumineux (maximum 10MB)');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('use_amadeus', document.getElementById('useAmadeus').checked);

        const clearCache = document.getElementById('clearCacheBeforeValidation').checked;
        
        const processValidation = () => {
            showLoading();

            fetch('/api/validate', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                hideLoading();
                displayResults(data);
            })
            .catch(error => {
                hideLoading();
                showError('Une erreur est survenue lors de la validation');
                console.error('Error:', error);
            });
        };

        if (clearCache) {
            fetch('/api/clear-cache', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    processValidation();
                } else {
                    throw new Error(data.message);
                }
            })
            .catch(error => {
                showError('Erreur lors du vidage du cache');
                console.error('Error:', error);
            });
        } else {
            processValidation();
        }
    });

    function showLoading() {
        results.classList.remove('hidden');
        loading.classList.remove('hidden');
        validationResults.classList.add('hidden');
    }

    function hideLoading() {
        loading.classList.add('hidden');
        validationResults.classList.remove('hidden');
    }

    function displayResults(data) {
        // Update status banner
        const statusBanner = document.getElementById('statusBanner');
        if (data.is_valid) {
            statusBanner.className = 'rounded-md bg-green-50 p-4';
            statusBanner.innerHTML = `
                <div class="flex">
                    <div class="ml-3">
                        <p class="text-sm font-medium text-green-800">Billet valide</p>
                    </div>
                </div>
            `;
        } else {
            statusBanner.className = 'rounded-md bg-yellow-50 p-4';
            statusBanner.innerHTML = `
                <div class="flex">
                    <div class="ml-3">
                        <p class="text-sm font-medium text-yellow-800">Billet invalide</p>
                    </div>
                </div>
            `;
        }

        // Update flight details
        const info = data.extracted_info || {};
        document.getElementById('passengerName').textContent = info.passenger_name || 'Non trouvé';
        document.getElementById('flightNumber').textContent = info.flight_number || 'Non trouvé';
        document.getElementById('departureDate').textContent = info.departure_date || 'Non trouvé';
        document.getElementById('departure').textContent = formatLocation(info.departure);
        document.getElementById('arrival').textContent = formatLocation(info.arrival);
        document.getElementById('ticketNumber').textContent = info.ticket_number || 'Non trouvé';

        // Display errors if any
        const errorList = document.getElementById('errorList');
        errorList.innerHTML = '';
        
        if (data.errors && data.errors.length > 0) {
            errorMessages.classList.remove('hidden');
            data.errors.forEach(error => {
                const li = document.createElement('li');
                li.textContent = error;
                errorList.appendChild(li);
            });
        } else {
            errorMessages.classList.add('hidden');
        }
    }

    function formatLocation(location) {
        if (!location) return 'Non trouvé';
        const parts = [];
        if (location.city) parts.push(location.city);
        if (location.country) parts.push(location.country);
        if (location.airport_code) parts.push(`(${location.airport_code})`);
        return parts.length > 0 ? parts.join(' ') : 'Non trouvé';
    }

    function showError(message) {
        results.classList.remove('hidden');
        loading.classList.add('hidden');
        validationResults.classList.remove('hidden');
        
        const statusBanner = document.getElementById('statusBanner');
        statusBanner.className = 'rounded-md bg-red-50 p-4';
        statusBanner.innerHTML = `
            <div class="flex">
                <div class="ml-3">
                    <p class="text-sm font-medium text-red-800">${message}</p>
                </div>
            </div>
        `;
    }
});
