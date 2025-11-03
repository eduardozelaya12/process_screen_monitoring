from flask import render_template, jsonify, request, send_from_directory
from storage.local_storage import LocalStorage
import logging
import json
import os

logger = logging.getLogger(__name__)

# Instância global de storage
storage = LocalStorage()

def register_routes(app):
    """Registra todas as rotas REST da aplicação"""
    
    @app.route('/')
    def index():
        """Página principal do dashboard"""
        return render_template('dashboard.html')
    
    @app.route('/tv')
    def tv_display():
        """Versão otimizada para TV"""
        return render_template('tv_display.html')
    
    @app.route('/storage/<path:filename>')
    def serve_storage(filename):
        """Serve qualquer arquivo dentro de storage/ de forma read-only"""
        safe_root = os.path.abspath('storage')
        return send_from_directory(safe_root, filename)
    
    @app.route('/api/health')
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'service': 'process-monitor-dashboard',
            'version': '1.0.0'
        })
    
    @app.route('/api/systems')
    def get_systems():
        """Lista todos os sistemas configurados"""
        try:
            with open('config/systems_config.json', 'r') as f:
                systems = json.load(f)
            
            # Retornar apenas sistemas habilitados
            enabled_systems = {
                name: {
                    'name': config['name'],
                    'type': config['type'],
                    'enabled': config['enabled']
                }
                for name, config in systems.items()
                if config.get('enabled', False)
            }
            
            return jsonify(enabled_systems)
        except Exception as e:
            logger.error(f"Erro ao buscar sistemas: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/status')
    def get_all_status():
        """Obtém status de todos os sistemas"""
        try:
            # Importar do orquestrador (será implementado)
            from orchestrator.orchestrator import get_orchestrator_instance
            
            orchestrator = get_orchestrator_instance()
            if not orchestrator:
                return jsonify({'error': 'Orquestrador não iniciado'}), 503
            
            status = orchestrator.status_tracker.get_all()
            return jsonify(status)
            
        except Exception as e:
            logger.error(f"Erro ao buscar status: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/status/<system_name>')
    def get_system_status(system_name):
        """Obtém status de um sistema específico"""
        try:
            from orchestrator.orchestrator import get_orchestrator_instance
            
            orchestrator = get_orchestrator_instance()
            if not orchestrator:
                return jsonify({'error': 'Orquestrador não iniciado'}), 503
            
            status = orchestrator.status_tracker.get_system(system_name)
            
            if not status:
                return jsonify({'error': 'Sistema não encontrado'}), 404
            
            return jsonify(status)
            
        except Exception as e:
            logger.error(f"Erro ao buscar status do sistema: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/history/<system_name>')
    def get_system_history(system_name):
        """Obtém histórico de um sistema"""
        try:
            hours = request.args.get('hours', default=24, type=int)
            
            metrics = storage.get_metrics_range(system_name, hours)
            
            return jsonify({
                'system': system_name,
                'period_hours': hours,
                'data': metrics
            })
            
        except Exception as e:
            logger.error(f"Erro ao buscar histórico: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/config/display')
    def get_display_config():
        """Retorna configuração de display"""
        try:
            with open('config/display_config.json', 'r') as f:
                config = json.load(f)
            return jsonify(config)
        except Exception as e:
            logger.error(f"Erro ao buscar config de display: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/screenshot/<system_name>')
    def get_latest_screenshot(system_name):
        """Retorna caminho do último screenshot"""
        try:
            # Buscar último screenshot do sistema
            screenshot_dir = f"storage/screenshots/{system_name}"
            
            if not os.path.exists(screenshot_dir):
                return jsonify({'error': 'Nenhum screenshot encontrado'}), 404
            
            files = [f for f in os.listdir(screenshot_dir) if f.endswith('.png')]
            if not files:
                return jsonify({'error': 'Nenhum screenshot encontrado'}), 404
            
            latest = sorted(files, reverse=True)[0]
            
            return jsonify({
                'system': system_name,
                'filename': latest,
                # Passa a servir do diretório storage via rota dedicada
                'path': f"/storage/screenshots/{system_name}/{latest}"
            })
            
        except Exception as e:
            logger.error(f"Erro ao buscar screenshot: {e}")
            return jsonify({'error': str(e)}), 500
    
    logger.info("✓ Rotas registradas")
