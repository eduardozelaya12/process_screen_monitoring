/**
 * Controlador de carrossel com rotação automática
 */

class CarouselController {
    constructor(containerId, config = {}) {
        this.container = document.getElementById(containerId);
        this.slides = [];
        this.currentIndex = 0;
        this.isPlaying = true;
        this.interval = null;
        
        // Configurações
        this.config = {
            autoRotate: config.autoRotate !== false,
            rotationInterval: config.rotationInterval || 15000, // 15s padrão
            transitionDuration: config.transitionDuration || 1000, // 1s padrão
            displayOrder: config.displayOrder || []
        };
    }
    
    init() {
        console.log('🎠 Inicializando carrossel...');
        
        if (!this.container) {
            console.error('Container do carrossel não encontrado');
            return;
        }
        
        this.slides = Array.from(this.container.querySelectorAll('.slide'));
        
        if (this.slides.length === 0) {
            console.warn('Nenhum slide encontrado');
            return;
        }
        
        // Mostrar primeiro slide
        this.showSlide(0);
        
        // Iniciar rotação automática
        if (this.config.autoRotate) {
            this.start();
        }
        
        console.log(`✓ Carrossel inicializado com ${this.slides.length} slides`);
    }
    
    showSlide(index) {
        // Esconder slide atual
        if (this.slides[this.currentIndex]) {
            this.slides[this.currentIndex].classList.remove('active');
        }
        
        // Normalizar índice
        this.currentIndex = index % this.slides.length;
        
        // Mostrar novo slide
        if (this.slides[this.currentIndex]) {
            this.slides[this.currentIndex].classList.add('active');
        }
        
        console.log(`Mostrando slide ${this.currentIndex + 1}/${this.slides.length}`);
    }
    
    next() {
        this.showSlide(this.currentIndex + 1);
    }
    
    previous() {
        this.showSlide(this.currentIndex - 1);
    }
    
    goTo(index) {
        this.showSlide(index);
    }
    
    start() {
        if (this.interval) {
            clearInterval(this.interval);
        }
        
        this.isPlaying = true;
        
        // Usar duração customizada se configurada
        const duration = this.config.displayOrder[this.currentIndex]?.duration || 
                        (this.config.rotationInterval / 1000);
        
        this.interval = setInterval(() => {
            this.next();
        }, duration * 1000);
        
        console.log('▶ Carrossel iniciado');
    }
    
    stop() {
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
        
        this.isPlaying = false;
        console.log('⏸ Carrossel pausado');
    }
    
    toggle() {
        if (this.isPlaying) {
            this.stop();
        } else {
            this.start();
        }
    }
    
    updateSlideContent(systemName, data) {
        const slide = this.container.querySelector(`#slide-${systemName}`);
        if (slide) {
            const content = this._generateSlideHTML(systemName, data);
            slide.innerHTML = content;
            console.log(`✓ Slide ${systemName} atualizado`);
        }
    }
    
    _generateSlideHTML(systemName, data) {
        const systemNames = {
            'peoplesoft': 'PeopleSoft',
            'oracle_fusion': 'Oracle Fusion',
            'bonita': 'Bonita BPM',
            'n8n': 'N8n Workflows'
        };
        
        return `
            <h2 class="system-title">${systemNames[systemName] || systemName}</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Total de Processos</div>
                    <div class="metric-value">${data.total_processes || 0}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Em Execução</div>
                    <div class="metric-value success">${data.running || 0}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Com Erro</div>
                    <div class="metric-value error">${data.failed || 0}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Taxa de Sucesso</div>
                    <div class="metric-value ${data.success_rate >= 95 ? 'success' : 'warning'}">
                        ${data.success_rate || 0}%
                    </div>
                </div>
            </div>
            ${this._generateErrorTable(data.critical_errors || [])}
        `;
    }
    
    _generateErrorTable(errors) {
        if (!errors || errors.length === 0) {
            return `
                <div class="no-errors">
                    <span class="icon">✓</span>
                    <p>Nenhum erro crítico</p>
                </div>
            `;
        }
        
        const rows = errors.slice(0, 10).map(error => `
            <tr>
                <td>${error.name || 'N/A'}</td>
                <td><span class="status-badge error">Erro</span></td>
                <td>${error.message || 'Sem detalhes'}</td>
                <td>${error.timestamp || 'N/A'}</td>
            </tr>
        `).join('');
        
        return `
            <div class="process-table">
                <table>
                    <thead>
                        <tr>
                            <th>Processo</th>
                            <th>Status</th>
                            <th>Mensagem</th>
                            <th>Horário</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rows}
                    </tbody>
                </table>
            </div>
        `;
    }
}
