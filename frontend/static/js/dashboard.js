/**
 * Controlador principal do dashboard
 */

class Dashboard {
    constructor() {
        this.wsClient = null;
        this.carousel = null;
        this.systems = [];
        this.systemData = {};
    }
    
    async init() {
        console.log('🚀 Inicializando dashboard...');
        
        // Carregar configurações
        await this.loadConfig();
        
        // Inicializar WebSocket
        this.initWebSocket();
        
        // Inicializar carrossel
        this.initCarousel();
        
        // Carregar dados iniciais
        await this.loadInitialData();
        
        // Iniciar atualização de timestamp
        this.startTimestampUpdate();
        
        // Configurar atalhos de teclado
        this.setupKeyboardShortcuts();
        
        console.log('✓ Dashboard inicializado');
    }
    
    async loadConfig() {
        try {
            const response = await fetch('/api/config/display');
            const config = await response.json();
            this.config = config;
            
            const systemsResponse = await fetch('/api/systems');
            const systems = await systemsResponse.json();
            this.systems = Object.keys(systems);
            
            console.log('✓ Configuração carregada:', this.systems);
        } catch (error) {
            console.error('Erro ao carregar configuração:', error);
        }
    }
    
    initWebSocket() {
        this.wsClient = new WebSocketClient();
        
        this.wsClient.on('connected', (data) => {
            this.updateConnectionStatus(true);
            // Inscrever em todos os sistemas
            this.wsClient.subscribe(this.systems);
        });
        
        this.wsClient.on('disconnected', () => {
            this.updateConnectionStatus(false);
        });
        
        this.wsClient.on('update', (data) => {
            this.handleDataUpdate(data);
        });
        
        this.wsClient.on('error', (error) => {
            console.error('Erro WebSocket:', error);
        });
        
        this.wsClient.connect();
    }
    
    initCarousel() {
        const carouselConfig = this.config?.carousel || {};
        
        this.carousel = new CarouselController('carousel', {
            autoRotate: carouselConfig.auto_rotate,
            rotationInterval: carouselConfig.rotation_interval * 1000,
            transitionDuration: carouselConfig.transition_duration * 1000,
            displayOrder: carouselConfig.display_order
        });
        
        // Criar slides para cada sistema
        this.createSlides();
        
        // Inicializar carrossel
        this.carousel.init();
    }
    
    createSlides() {
        const container = document.getElementById('carousel');
        if (!container) return;
        
        this.systems.forEach((system, index) => {
            const slide = document.createElement('div');
            slide.className = 'slide' + (index === 0 ? ' active' : '');
            slide.id = `slide-${system}`;
            slide.innerHTML = '<div class="loading">Carregando...</div>';
            container.appendChild(slide);
        });
    }
    
    async loadInitialData() {
        console.log('📊 Carregando dados iniciais...');
        
        for (const system of this.systems) {
            try {
                const response = await fetch(`/api/status/${system}`);
                const data = await response.json();
                
                this.systemData[system] = data;
                this.carousel.updateSlideContent(system, data);
                
            } catch (error) {
                console.error(`Erro ao carregar dados de ${system}:`, error);
            }
        }
    }
    
    handleDataUpdate(data) {
        const system = data.system;
        const newData = data.data;
        
        console.log(`📈 Dados atualizados: ${system}`);
        
        this.systemData[system] = newData;
        this.carousel.updateSlideContent(system, newData);
    }
    
    updateConnectionStatus(connected) {
        const statusEl = document.getElementById('connectionStatus');
        if (!statusEl) return;
        
        if (connected) {
            statusEl.textContent = '🟢 Conectado';
            statusEl.className = 'connection-status connected';
        } else {
            statusEl.textContent = '🔴 Desconectado';
            statusEl.className = 'connection-status disconnected';
        }
    }
    
    startTimestampUpdate() {
        const updateTimestamp = () => {
            const timestampEl = document.getElementById('timestamp');
            if (timestampEl) {
                const now = new Date();
                timestampEl.textContent = now.toLocaleString('pt-BR', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                });
            }
        };
        
        updateTimestamp();
        setInterval(updateTimestamp, 1000);
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            switch(e.key) {
                case 'ArrowRight':
                    this.carousel.next();
                    break;
                case 'ArrowLeft':
                    this.carousel.previous();
                    break;
                case ' ':
                    this.carousel.toggle();
                    e.preventDefault();
                    break;
                case 'f':
                case 'F':
                    this.toggleFullscreen();
                    break;
            }
        });
    }
    
    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
        } else {
            document.exitFullscreen();
        }
    }
}

// Inicializar quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    const dashboard = new Dashboard();
    dashboard.init();
});
