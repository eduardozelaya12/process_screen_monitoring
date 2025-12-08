#!/usr/bin/env python3
"""
Process Monitor Dashboard - Ponto de entrada principal
"""

import sys
import signal
import os
import logging
import io
from threading import Thread
import time

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configurar logging
# Força UTF-8 no console do Windows para evitar UnicodeEncodeError com emojis
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass
utf8_stream = None
try:
    utf8_stream = io.TextIOWrapper(getattr(sys.stdout, 'buffer', sys.stdout), encoding='utf-8', errors='replace')
except Exception:
    utf8_stream = sys.stdout

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('storage/logs/dashboard.log', encoding='utf-8'),
        logging.StreamHandler(stream=utf8_stream)
    ]
)

logger = logging.getLogger(__name__)

# Importações do projeto
from orchestrator.orchestrator import DashboardOrchestrator
from backend.app import app, socketio

# Instâncias globais
orchestrator = None
web_thread = None

def start_orchestrator():
    """Inicia orquestrador em thread separada"""
    global orchestrator
    
    try:
        orchestrator = DashboardOrchestrator()
        orchestrator.set_socketio(socketio)
        orchestrator.start()
        
        # Manter thread viva
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Erro no orquestrador: {e}")

def start_web_server():
    """Inicia servidor web Flask"""
    logger.info("🌐 Iniciando servidor web...")
    
    try:
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=False,
            use_reloader=False,
            log_output=False,
            allow_unsafe_werkzeug=True
        )
    except Exception as e:
        logger.error(f"Erro no servidor web: {e}")

def signal_handler(sig, frame):
    """Handler para shutdown gracioso"""
    logger.info("\n\n🛑 Recebido sinal de interrupção...")
    
    if orchestrator:
        orchestrator.stop()
    
    logger.info("👋 Encerrando aplicação...")
    sys.exit(0)

def check_requirements():
    """Verifica se estrutura de diretórios existe"""
    required_dirs = [
        'config',
        'config/credentials',
        'storage',
        'storage/screenshots',
        'storage/logs'
    ]
    
    for dir_path in required_dirs:
        os.makedirs(dir_path, exist_ok=True)
    
    logger.info("✓ Estrutura de diretórios verificada")

def main():
    """Função principal"""
    # Registrar handlers de sinais
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Banner
    logger.info("\n" + "="*60)
    logger.info("    PROCESS MONITOR DASHBOARD")
    logger.info("    Versão 1.0.0")
    logger.info("="*60 + "\n")
    
    # Verificar requisitos
    check_requirements()
    
    # Iniciar orquestrador em thread separada
    logger.info("🔧 Iniciando componentes...")
    orch_thread = Thread(target=start_orchestrator, daemon=True, name="Orchestrator")
    orch_thread.start()
    
    # Aguardar inicialização
    time.sleep(3)
    
    # Iniciar servidor web (thread principal)
    logger.info("\n" + "="*60)
    logger.info("✓ Dashboard disponível em: http://localhost:5000")
    logger.info("✓ Versão TV disponível em: http://localhost:5000/tv")
    logger.info("="*60 + "\n")
    
    start_web_server()

if __name__ == "__main__":
    main()
