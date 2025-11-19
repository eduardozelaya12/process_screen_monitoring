(() => {
    const systemSelect = document.getElementById('systemSelect');
    const form = document.getElementById('configForm');
    const messageBox = document.getElementById('message');
    const submitButton = document.getElementById('submitButton');
    const resetButton = document.getElementById('resetButton');
    const filtersSection = document.getElementById('filtersSection');
    const credentialsSection = document.getElementById('credentialsSection');

    const collectionIntervalInput = document.getElementById('collectionInterval');
    const timeoutInput = document.getElementById('timeout');
    const retryAttemptsInput = document.getElementById('retryAttempts');
    const baseUrlInput = document.getElementById('baseUrl');
    const processMonitorUrlInput = document.getElementById('processMonitorUrl');
    const enabledCheckbox = document.getElementById('enabled');
    const headlessCheckbox = document.getElementById('headless');
    const credentialUsernameInput = document.getElementById('credentialUsername');
    const credentialPasswordInput = document.getElementById('credentialPassword');

    const filterInputs = filtersSection.querySelectorAll('[data-filter-key]');
    const timeFilterInputs = filtersSection.querySelectorAll('[data-time-key]');

    let configs = {};
    let currentSystem = null;

    async function init() {
        await loadConfigs();
        systemSelect.addEventListener('change', handleSystemChange);
        form.addEventListener('submit', handleSubmit);
        resetButton.addEventListener('click', resetForm);
    }

    async function loadConfigs() {
        try {
            const response = await fetch('/api/config/systems', { cache: 'no-store' });
            if (!response.ok) {
                throw new Error('Não foi possível carregar as configurações');
            }

            configs = await response.json();
            renderSystemOptions();
        } catch (error) {
            showMessage(error.message, 'error');
        }
    }

    function renderSystemOptions() {
        systemSelect.innerHTML = '<option value="">Selecione um sistema</option>';
        Object.keys(configs).forEach(systemKey => {
            const option = document.createElement('option');
            option.value = systemKey;
            option.textContent = configs[systemKey].name || systemKey;
            systemSelect.appendChild(option);
        });
    }

    function handleSystemChange() {
        hideMessage();
        currentSystem = systemSelect.value;

        if (!currentSystem) {
            form.classList.add('hidden');
            return;
        }

        const config = configs[currentSystem];
        form.classList.remove('hidden');

        populateForm(config);
    }

    function populateForm(config) {
        const filters = config.filters || null;
        const credentials = config.credentials || {};

        collectionIntervalInput.value = config.collection_interval ?? '';
        timeoutInput.value = config.timeout ?? '';
        retryAttemptsInput.value = config.retry_attempts ?? '';
        baseUrlInput.value = config.base_url ?? '';
        processMonitorUrlInput.value = config.process_monitor_url ?? '';
        enabledCheckbox.checked = Boolean(config.enabled);
        headlessCheckbox.checked = Boolean(config.headless);

        credentialUsernameInput.value = credentials.username ?? '';
        credentialPasswordInput.value = credentials.password ?? '';
        credentialsSection.classList.toggle('hidden', !credentials || Object.keys(credentials).length === 0);

        if (filters) {
            filtersSection.classList.remove('hidden');

            filterInputs.forEach(input => {
                const key = input.dataset.filterKey;
                const value = filters[key];
                input.value = value === null || value === undefined ? '' : value;
            });

            const timeFilter = filters.time_filter || {};
            timeFilterInputs.forEach(input => {
                const key = input.dataset.timeKey;
                const value = timeFilter[key];
                input.value = value === null || value === undefined ? '' : value;
            });
        } else {
            filtersSection.classList.add('hidden');
            filterInputs.forEach(input => { input.value = ''; });
            timeFilterInputs.forEach(input => { input.value = ''; });
        }
    }

    function collectPayload() {
        if (!currentSystem) {
            throw new Error('Nenhum sistema selecionado');
        }

        const collectionInterval = Number(collectionIntervalInput.value);
        if (!collectionInterval || Number.isNaN(collectionInterval) || collectionInterval <= 0) {
            throw new Error('Informe um intervalo de coleta válido (maior que zero).');
        }

        const payload = {
            enabled: enabledCheckbox.checked,
            headless: headlessCheckbox.checked,
            collection_interval: collectionInterval
        };

        if (timeoutInput.value.trim() !== '') {
            payload.timeout = Number(timeoutInput.value);
        } else if (Object.prototype.hasOwnProperty.call(configs[currentSystem], 'timeout')) {
            payload.timeout = null;
        }

        if (retryAttemptsInput.value.trim() !== '') {
            payload.retry_attempts = Number(retryAttemptsInput.value);
        } else if (Object.prototype.hasOwnProperty.call(configs[currentSystem], 'retry_attempts')) {
            payload.retry_attempts = null;
        }

        payload.base_url = sanitizeTextValue(baseUrlInput);
        payload.process_monitor_url = sanitizeTextValue(processMonitorUrlInput);

        if (!credentialsSection.classList.contains('hidden')) {
            payload.credentials = {
                username: sanitizeTextValue(credentialUsernameInput),
                password: credentialPasswordInput.value || null
            };
        }

        const sourceFilters = configs[currentSystem].filters
            ? JSON.parse(JSON.stringify(configs[currentSystem].filters))
            : {};

        if (!filtersSection.classList.contains('hidden')) {
            filterInputs.forEach(input => {
                const key = input.dataset.filterKey;
                const value = input.value.trim();
                sourceFilters[key] = value === '' ? null : value;
            });

            if (!sourceFilters.time_filter) {
                sourceFilters.time_filter = {};
            }

            timeFilterInputs.forEach(input => {
                const key = input.dataset.timeKey;
                const value = input.value.trim();
                sourceFilters.time_filter[key] = value === '' ? null : value;
            });

            const timeValues = Object.values(sourceFilters.time_filter);
            const allTimeEmpty = timeValues.every(v => v === null || v === '' || v === undefined);
            if (allTimeEmpty) {
                delete sourceFilters.time_filter;
            }

            payload.filters = sourceFilters;
        }

        return payload;
    }

    function sanitizeTextValue(input) {
        const value = typeof input === 'string' ? input : input.value;
        if (value === undefined || value === null) {
            return null;
        }
        const trimmed = value.trim();
        return trimmed === '' ? null : trimmed;
    }

    async function handleSubmit(event) {
        event.preventDefault();
        hideMessage();

        try {
            const payload = collectPayload();

            submitButton.disabled = true;
            submitButton.textContent = 'Salvando...';

            const response = await fetch(`/api/config/systems/${currentSystem}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errorBody = await response.json().catch(() => ({}));
                throw new Error(errorBody.error || 'Falha ao salvar alterações');
            }

            const result = await response.json();
            configs[currentSystem] = result.config;
            populateForm(result.config);
            showMessage('Configurações atualizadas com sucesso!', 'success');
        } catch (error) {
            showMessage(error.message, 'error');
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = 'Salvar alterações';
        }
    }

    function resetForm() {
        hideMessage();
        if (!currentSystem) {
            return;
        }
        populateForm(configs[currentSystem]);
    }

    function showMessage(text, type) {
        if (!messageBox) return;
        messageBox.textContent = text;
        messageBox.className = `message ${type}`;
        messageBox.style.display = 'block';
    }

    function hideMessage() {
        if (!messageBox) return;
        messageBox.style.display = 'none';
        messageBox.textContent = '';
        messageBox.className = 'message';
    }

    document.addEventListener('DOMContentLoaded', init);
})();

