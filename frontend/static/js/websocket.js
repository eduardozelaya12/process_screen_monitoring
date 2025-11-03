/**
 * Cliente WebSocket para comunicação em tempo real
 */

class WebSocketClient {
    constructor(serverUrl = 'http://localhost:5000') {
        this.serverUrl = serverUrl;
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 3000;
        this.eventHandlers = {};
    }
    
    connect() {
        console.log('🔌 Conectando ao servidor WebSocket...');
        
        this.socket = io(this.serverUrl, {
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionDelay: this.reconnectDelay,
            reconnectionAttempts: this.maxReconnectAttempts
        });
        
        this._setupEventListeners();
    }
    
    _setupEventListeners() {
        this.socket.on('connect', () => {
            console.log('✓ Conectado ao servidor WebSocket');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this._triggerHandler('connected', { connected: true });
        });
        
        this.socket.on('disconnect', () => {
            console.log('❌ Desconectado do servidor WebSocket');
            this.isConnected = false;
            this._triggerHandler('disconnected', { connected: false });
        });
        
        this.socket.on('connect_error', (error) => {
            console.error('Erro de conexão:', error);
            this.reconnectAttempts++;
            this._triggerHandler('error', { error: error.message });
        });
        
        this.socket.on('update', (data) => {
            console.log('📥 Dados recebidos:', data);
            this._triggerHandler('update', data);
        });
        
        this.socket.on('system_update', (data) => {
            console.log('📥 Atualização de sistema:', data);
            this._triggerHandler('system_update', data);
        });
        
        this.socket.on('error', (data) => {
            console.error('Erro do servidor:', data);
            this._triggerHandler('error', data);
        });
        
        this.socket.on('pong', () => {
            console.log('🏓 Pong recebido');
        });
    }
    
    on(event, handler) {
        if (!this.eventHandlers[event]) {
            this.eventHandlers[event] = [];
        }
        this.eventHandlers[event].push(handler);
    }
    
    _triggerHandler(event, data) {
        if (this.eventHandlers[event]) {
            this.eventHandlers[event].forEach(handler => handler(data));
        }
    }
    
    requestUpdate(systemName) {
        if (this.isConnected) {
            this.socket.emit('request_update', { system: systemName });
        }
    }
    
    subscribe(systems) {
        if (this.isConnected) {
            this.socket.emit('subscribe', { systems: systems });
        }
    }
    
    unsubscribe(systems) {
        if (this.isConnected) {
            this.socket.emit('unsubscribe', { systems: systems });
        }
    }
    
    ping() {
        if (this.isConnected) {
            this.socket.emit('ping');
        }
    }
    
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
        }
    }
}
