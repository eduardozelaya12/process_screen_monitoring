(() => {
    const systemSelect = document.getElementById('systemSelect');
    const form = document.getElementById('configForm');
    const messageBox = document.getElementById('message');
    const submitButton = document.getElementById('submitButton');
    const resetButton = document.getElementById('resetButton');
    const filtersSection = document.getElementById('filtersSection');
    const credentialsSection = document.getElementById('credentialsSection');
    const databaseSection = document.getElementById('databaseSection');

    const collectionIntervalInput = document.getElementById('collectionInterval');
    const timeoutInput = document.getElementById('timeout');
    const retryAttemptsInput = document.getElementById('retryAttempts');
    const baseUrlInput = document.getElementById('baseUrl');
    const processMonitorUrlInput = document.getElementById('processMonitorUrl');
    const enabledCheckbox = document.getElementById('enabled');
    const headlessCheckbox = document.getElementById('headless');
    const credentialUsernameInput = document.getElementById('credentialUsername');
    const credentialPasswordInput = document.getElementById('credentialPassword');

    // Database connection fields
    const databaseTypeSelect = document.getElementById('databaseType');
    const databaseServerInput = document.getElementById('databaseServer');
    const databaseNameSelect = document.getElementById('databaseName');
    const databaseUsernameInput = document.getElementById('databaseUsername');
    const databasePasswordInput = document.getElementById('databasePassword');
    const databasePortInput = document.getElementById('databasePort');
    const databaseQueryTextarea = document.getElementById('databaseQuery');
    const listDatabasesButton = document.getElementById('listDatabasesButton');
    const testConnectionButton = document.getElementById('testConnectionButton');
    const connectionStatusSpan = document.getElementById('connectionStatus');
    const addDatabaseButton = document.getElementById('addDatabaseButton');
    const deleteDatabaseButton = document.getElementById('deleteDatabaseButton');

    const filterInputs = filtersSection.querySelectorAll('[data-filter-key]');
    const timeFilterInputs = filtersSection.querySelectorAll('[data-time-key]');

    let configs = {};
    let currentSystem = null;

    async function init() {
        await loadConfigs();
        systemSelect.addEventListener('change', handleSystemChange);
        form.addEventListener('submit', handleSubmit);
        resetButton.addEventListener('click', resetForm);

        // Database connection handlers
        if (listDatabasesButton) {
            listDatabasesButton.addEventListener('click', handleListDatabases);
        }
        if (testConnectionButton) {
            testConnectionButton.addEventListener('click', handleTestConnection);
        }
        if (addDatabaseButton) {
            addDatabaseButton.addEventListener('click', handleAddDatabaseSystem);
        }
        if (deleteDatabaseButton) {
            deleteDatabaseButton.addEventListener('click', handleDeleteDatabaseSystem);
        }
        if (databaseTypeSelect) {
            databaseTypeSelect.addEventListener('change', handleDatabaseTypeChange);
        }
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

    function computeDisplayName(systemKey, cfg, overrideDbType) {
        const systemType = (cfg.type || '').toLowerCase();
        let displayName = cfg.name || systemKey;

        if (systemType === 'database') {
            const dbType = overrideDbType || (cfg.database_connection || {}).db_type || '';
            let dbLabel = '';
            switch (dbType.toLowerCase()) {
                case 'sqlserver':
                    dbLabel = 'SQL Server';
                    break;
                case 'postgresql':
                    dbLabel = 'PostgreSQL';
                    break;
                default:
                    dbLabel = dbType ? dbType.charAt(0).toUpperCase() + dbType.slice(1) : 'Database';
            }

            if (dbLabel) {
                // Remove qualquer trecho entre parênteses, ex: "Banco de Dados (Exemplo) #1" -> "Banco de Dados #1"
                const parenStart = displayName.lastIndexOf('(');
                const parenEnd = displayName.lastIndexOf(')');
                if (parenStart !== -1 && parenEnd !== -1 && parenEnd > parenStart) {
                    displayName = (displayName.slice(0, parenStart) + displayName.slice(parenEnd + 1)).trim();
                }
                displayName = `${displayName} (${dbLabel})`;
            }
        }

        return displayName;
    }

    function renderSystemOptions() {
        systemSelect.innerHTML = '<option value="">Selecione um sistema</option>';
        Object.keys(configs).forEach(systemKey => {
            const option = document.createElement('option');
            option.value = systemKey;
            const cfg = configs[systemKey];
            option.textContent = computeDisplayName(systemKey, cfg);
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
        const databaseConnection = config.database_connection || {};
        const systemType = (config.type || '').toLowerCase();

        collectionIntervalInput.value = config.collection_interval ?? '';
        timeoutInput.value = config.timeout ?? '';
        retryAttemptsInput.value = config.retry_attempts ?? '';
        baseUrlInput.value = config.base_url ?? '';
        processMonitorUrlInput.value = config.process_monitor_url ?? '';
        enabledCheckbox.checked = Boolean(config.enabled);
        headlessCheckbox.checked = Boolean(config.headless);

        // Credentials section
        credentialUsernameInput.value = credentials.username ?? '';
        credentialPasswordInput.value = credentials.password ?? '';
        credentialsSection.classList.toggle('hidden', !credentials || Object.keys(credentials).length === 0 || systemType === 'database');

        // Database connection section
        if (systemType === 'database') {
            databaseSection.classList.remove('hidden');
            databaseTypeSelect.value = databaseConnection.db_type || 'sqlserver';
            databaseServerInput.value = databaseConnection.server || '';
            databaseUsernameInput.value = databaseConnection.username || '';
            databasePasswordInput.value = databaseConnection.password || '';
            databasePortInput.value = databaseConnection.port || '';
            databaseQueryTextarea.value = databaseConnection.query || '';

            // Preencher select de databases
            databaseNameSelect.innerHTML = '<option value="">Selecione uma database</option>';
            if (databaseConnection.database) {
                const option = document.createElement('option');
                option.value = databaseConnection.database;
                option.textContent = databaseConnection.database;
                option.selected = true;
                databaseNameSelect.appendChild(option);
            }

            connectionStatusSpan.textContent = '';
        } else {
            databaseSection.classList.add('hidden');
            databaseTypeSelect.value = 'sqlserver';
            databaseServerInput.value = '';
            databaseNameSelect.innerHTML = '<option value="">Selecione uma database</option>';
            databaseUsernameInput.value = '';
            databasePasswordInput.value = '';
            databasePortInput.value = '';
            databaseQueryTextarea.value = '';
            connectionStatusSpan.textContent = '';
        }

        // Botão de remover DB: só aparece para clones (chave com _db)
        if (deleteDatabaseButton) {
            const isDatabaseClone = systemType === 'database' && currentSystem && currentSystem.includes('_db');
            deleteDatabaseButton.style.display = isDatabaseClone ? 'inline-flex' : 'none';
        }

        // Filters section
        if (filters && systemType !== 'bonita') {
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

        // Bonita section
        const bonitaSection = document.getElementById('bonitaFiltersSection');
        if (bonitaSection) {
            if (systemType === 'bonita') {
                bonitaSection.classList.remove('hidden');
                // Esconder campos de URL para Bonita
                baseUrlInput.closest('label').classList.add('hidden');
                processMonitorUrlInput.closest('label').classList.add('hidden');
            } else {
                bonitaSection.classList.add('hidden');
                // Restaurar campos de URL
                baseUrlInput.closest('label').classList.remove('hidden');
                processMonitorUrlInput.closest('label').classList.remove('hidden');
            }
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

        // Database connection
        if (!databaseSection.classList.contains('hidden')) {
            const dbType = databaseTypeSelect.value;
            const dbServer = sanitizeTextValue(databaseServerInput);
            const dbName = databaseNameSelect.value || '';
            const dbUsername = sanitizeTextValue(databaseUsernameInput);
            const dbPassword = databasePasswordInput.value || null;
            const dbPort = sanitizeTextValue(databasePortInput);
            const dbQuery = sanitizeTextValue(databaseQueryTextarea);

            if (!dbServer || !dbName || !dbUsername || !dbPassword) {
                throw new Error('Server, Database, Username e Password são obrigatórios para conexão com banco de dados');
            }

            payload.database_connection = {
                db_type: dbType,
                server: dbServer,
                database: dbName,
                username: dbUsername,
                password: dbPassword
            };

            if (dbPort) {
                payload.database_connection.port = Number(dbPort);
            }

            if (dbQuery) {
                payload.database_connection.query = dbQuery;
            }
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

    async function handleListDatabases() {
        const server = sanitizeTextValue(databaseServerInput);
        const username = sanitizeTextValue(databaseUsernameInput);
        const password = databasePasswordInput.value;
        const port = sanitizeTextValue(databasePortInput);
        const dbType = databaseTypeSelect.value;

        if (!server || !username || !password) {
            showMessage('Preencha Server, Username e Password para buscar databases', 'error');
            return;
        }

        if (dbType !== 'sqlserver') {
            showMessage('A listagem de databases está disponível apenas para SQL Server', 'error');
            return;
        }

        listDatabasesButton.disabled = true;
        listDatabasesButton.textContent = 'Buscando...';
        connectionStatusSpan.textContent = '';

        try {
            const response = await fetch('/api/database/list-databases', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    db_type: dbType,
                    server: server,
                    username: username,
                    password: password,
                    port: port || null
                })
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Erro ao buscar databases');
            }

            // Preencher select com databases
            databaseNameSelect.innerHTML = '<option value="">Selecione uma database</option>';
            result.databases.forEach(dbName => {
                const option = document.createElement('option');
                option.value = dbName;
                option.textContent = dbName;
                databaseNameSelect.appendChild(option);
            });

            showMessage(`${result.databases.length} database(s) encontrada(s)`, 'success');
            connectionStatusSpan.textContent = '';
        } catch (error) {
            showMessage(error.message, 'error');
            connectionStatusSpan.textContent = '';
        } finally {
            listDatabasesButton.disabled = false;
            listDatabasesButton.textContent = 'Buscar Databases';
        }
    }

    async function handleTestConnection() {
        const dbType = databaseTypeSelect.value;
        const server = sanitizeTextValue(databaseServerInput);
        const database = databaseNameSelect.value || '';
        const username = sanitizeTextValue(databaseUsernameInput);
        const password = databasePasswordInput.value;
        const port = sanitizeTextValue(databasePortInput);

        if (!server || !database || !username || !password) {
            showMessage('Preencha todos os campos obrigatórios para testar a conexão', 'error');
            return;
        }

        if (dbType !== 'sqlserver') {
            showMessage('O teste de conexão está disponível apenas para SQL Server', 'error');
            return;
        }

        testConnectionButton.disabled = true;
        testConnectionButton.textContent = 'Testando...';
        connectionStatusSpan.textContent = '';

        try {
            const response = await fetch('/api/database/test-connection', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    db_type: dbType,
                    server: server,
                    database: database,
                    username: username,
                    password: password,
                    port: port || null
                })
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Erro ao testar conexão');
            }

            connectionStatusSpan.textContent = '✓ Conexão bem-sucedida!';
            connectionStatusSpan.style.color = '#6ee7b7';
            showMessage('Conexão testada com sucesso!', 'success');
        } catch (error) {
            connectionStatusSpan.textContent = '✗ Erro na conexão';
            connectionStatusSpan.style.color = '#fca5a5';
            showMessage(error.message, 'error');
        } finally {
            testConnectionButton.disabled = false;
            testConnectionButton.textContent = 'Testar Conexão';
        }
    }

    async function handleAddDatabaseSystem() {
        hideMessage();

        if (!currentSystem) {
            showMessage('Selecione um sistema de banco de dados antes de adicionar mais DBs', 'error');
            return;
        }

        const config = configs[currentSystem];
        if (!config || (config.type || '').toLowerCase() !== 'database') {
            showMessage('Apenas sistemas do tipo Banco de Dados podem ser clonados', 'error');
            return;
        }

        try {
            addDatabaseButton.disabled = true;
            addDatabaseButton.textContent = 'Clonando...';

            const response = await fetch(`/api/config/systems/${currentSystem}/clone-database`, {
                method: 'POST'
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Erro ao adicionar novo banco de dados');
            }

            const newKey = result.system;
            const newConfig = result.config;

            // Atualiza cache local e opções do select
            configs[newKey] = newConfig;
            renderSystemOptions();

            // Seleciona automaticamente o novo sistema clonado
            systemSelect.value = newKey;
            currentSystem = newKey;
            populateForm(newConfig);

            showMessage('Novo banco de dados criado. Ajuste as credenciais e query e salve as alterações.', 'success');
        } catch (error) {
            showMessage(error.message, 'error');
        } finally {
            addDatabaseButton.disabled = false;
            addDatabaseButton.textContent = 'Adicionar mais DBs';
        }
    }

    async function handleDeleteDatabaseSystem() {
        hideMessage();

        if (!currentSystem) {
            showMessage('Nenhum sistema selecionado', 'error');
            return;
        }

        const config = configs[currentSystem];
        const systemType = (config?.type || '').toLowerCase();

        if (systemType !== 'database' || !currentSystem.includes('_db')) {
            showMessage('Apenas DBs adicionais podem ser removidos. O primeiro DB não pode ser excluído.', 'error');
            return;
        }

        const confirmed = window.confirm('Tem certeza que deseja remover este banco de dados? Esta ação não pode ser desfeita.');
        if (!confirmed) {
            return;
        }

        try {
            deleteDatabaseButton.disabled = true;

            const response = await fetch(`/api/config/systems/${currentSystem}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Erro ao remover banco de dados');
            }

            // Remover do cache e atualizar select
            delete configs[currentSystem];

            // Tentar voltar para o DB raiz da família
            const rootKey = currentSystem.split('_db')[0];
            renderSystemOptions();

            if (configs[rootKey]) {
                systemSelect.value = rootKey;
                currentSystem = rootKey;
                populateForm(configs[rootKey]);
            } else {
                systemSelect.value = '';
                currentSystem = null;
                form.classList.add('hidden');
            }

            showMessage('Banco de dados removido com sucesso.', 'success');
        } catch (error) {
            showMessage(error.message, 'error');
        } finally {
            deleteDatabaseButton.disabled = false;
        }
    }

    function handleDatabaseTypeChange() {
        // Atualiza o texto do sistema no combo quando o tipo de banco muda
        if (!currentSystem) return;
        const cfg = configs[currentSystem];
        if (!cfg) return;

        const systemType = (cfg.type || '').toLowerCase();
        if (systemType !== 'database') return;

        const option = systemSelect.querySelector(`option[value="${currentSystem}"]`);
        if (!option) return;

        const newDbType = databaseTypeSelect.value;
        option.textContent = computeDisplayName(currentSystem, cfg, newDbType);
    }

    document.addEventListener('DOMContentLoaded', init);
})();

