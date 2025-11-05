from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import json
import logging
from typing import Dict, Optional

# Importações dos módulos do projeto
from collectors.peoplesoft_collector import PeopleSoftCollector
from collectors.google_collector import GoogleCollector
from processors.data_processors import DataProcessor
from storage.local_storage import LocalStorage

logger = logging.getLogger(__name__)

# Instância global para acesso por outros módulos
_orchestrator_instance = None

def get_orchestrator_instance():
    """Retorna instância global do orquestrador"""
    return _orchestrator_instance

class StatusTracker:
    """Rastreia status atual de todos os sistemas"""
    
    def __init__(self):
        self.status = {}
        self.last_update = {}
    
    def update(self, system_name: str, data: Dict):
        """Atualiza status de um sistema"""
        self.status[system_name] = data
        self.last_update[system_name] = datetime.now()
        logger.debug(f"Status atualizado: {system_name}")
    
    def get_system(self, system_name: str) -> Dict:
        """Retorna status de um sistema"""
        return self.status.get(system_name, {})
    
    def get_all(self) -> Dict:
        """Retorna status de todos os sistemas"""
        return self.status

class DashboardOrchestrator:
    """Orquestrador principal do dashboard"""
    
    def __init__(self, config_path="config/systems_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.scheduler = None
        self.collectors = {}
        self.running_systems = set()  # Rastreia sistemas ativos
        self.processor = DataProcessor()
        self.storage = LocalStorage()
        self.status_tracker = StatusTracker()
        self.socketio = None  # Será definido externamente
        
        logger.info("📋 Orquestrador criado")
    
    def _load_config(self) -> Dict:
        """Carrega configuração dos sistemas"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def set_socketio(self, socketio):
        """Define instância do SocketIO para broadcasts"""
        self.socketio = socketio
        logger.info("✓ SocketIO configurado no orquestrador")
    
    def initialize_collectors(self):
        """Inicializa coletores para cada sistema habilitado"""
        logger.info("🔧 Inicializando coletores...")
        
        # Mapa de coletores disponíveis
        collector_map = {
            'peoplesoft': PeopleSoftCollector,
            'google': GoogleCollector,
            # Adicione outros coletores aqui conforme implementar
            # 'oracle_fusion': OracleFusionCollector,
            # 'bonita': BonitaCollector,
            # 'n8n': N8nCollector
        }
        
        for system_name, system_config in self.config.items():
            if not system_config.get('enabled', False):
                logger.info(f"⏭ Sistema {system_name} desabilitado, pulando...")
                continue
            
            collector_class = collector_map.get(system_name)
            
            if collector_class:
                try:
                    self.collectors[system_name] = collector_class(system_config)
                    logger.info(f"✓ Coletor {system_name} inicializado")
                except Exception as e:
                    logger.error(f"❌ Erro ao inicializar {system_name}: {e}")
            else:
                logger.warning(f"⚠ Coletor {system_name} não implementado")
        
        logger.info(f"✓ {len(self.collectors)} coletores inicializados")
    
    def schedule_jobs(self):
        """Agenda jobs de coleta para cada sistema"""
        logger.info("📅 Agendando jobs de coleta...")
        
        # Configurar scheduler
        self.scheduler = BackgroundScheduler(
            timezone='America/Sao_Paulo',
            job_defaults={
                'coalesce': True,
                'max_instances': 1,
                'misfire_grace_time': 60
            }
        )
        
        for system_name, collector in self.collectors.items():
            interval = self.config[system_name].get('collection_interval', 300)
            
            self.scheduler.add_job(
                func=self._collect_system_data,
                trigger=IntervalTrigger(seconds=interval),
                args=[system_name, collector],
                id=f"collect_{system_name}",
                name=f"Coleta {system_name}",
                replace_existing=True,
                next_run_time=datetime.now()  # Executar imediatamente
            )
            
            self.running_systems.add(system_name)  # Marcar como rodando
            logger.info(f"✓ Job agendado: {system_name} a cada {interval}s")
        
        # Job de limpeza diária
        self.scheduler.add_job(
            func=self.storage.cleanup_old_data,
            trigger='cron',
            hour=2,
            minute=0,
            id='cleanup',
            name='Limpeza diária'
        )
        
        logger.info("✓ Jobs agendados")
    
    def _collect_system_data(self, system_name: str, collector):
        """Executa coleta de dados de um sistema"""
        try:
            logger.info(f"🔄 Coletando: {system_name}")
            
            # Coletar dados brutos
            raw_data = collector.collect()
            
            # Processar e padronizar
            processed_data = self.processor.standardize(raw_data, system_name)
            
            # Salvar no storage local
            self.storage.save_metrics(system_name, processed_data)
            
            # Atualizar status tracker
            self.status_tracker.update(system_name, processed_data)
            
            # Notificar frontend via WebSocket
            if self.socketio:
                self._broadcast_update(system_name, processed_data)
            
            logger.info(f"✓ Coleta concluída: {system_name}")
            
        except Exception as e:
            logger.error(f"❌ Erro na coleta de {system_name}: {e}")
            
            # Marcar erro no status
            error_data = {
                'system': system_name,
                'status': 'error',
                'error_message': str(e),
                'timestamp': datetime.now().isoformat()
            }
            self.status_tracker.update(system_name, error_data)
    
    def _broadcast_update(self, system_name: str, data: Dict):
        """Envia atualização para todos os clientes via WebSocket"""
        try:
            from backend.websocket_handlers import broadcast_update
            broadcast_update(self.socketio, system_name, data)
        except Exception as e:
            logger.error(f"Erro ao fazer broadcast: {e}")
    
    def start(self):
        """Inicia o orquestrador"""
        global _orchestrator_instance
        _orchestrator_instance = self
        
        logger.info("="*60)
        logger.info("🚀 INICIANDO ORQUESTRADOR")
        logger.info("="*60)
        
        self.initialize_collectors()
        self.schedule_jobs()
        self.scheduler.start()
        
        logger.info("✓ Orquestrador ativo!")
        self._list_jobs()
    
    def _list_jobs(self):
        """Lista todos os jobs agendados"""
        jobs = self.scheduler.get_jobs()
        logger.info(f"\n📋 Jobs agendados ({len(jobs)}):")
        for job in jobs:
            logger.info(f"  • {job.name} | próxima execução: {job.next_run_time}")
    
    def start_system(self, system_name: str) -> bool:
        """Inicia coleta de um sistema específico"""
        try:
            if system_name in self.running_systems:
                logger.warning(f"⚠ Sistema {system_name} já está rodando")
                return False
            
            if system_name not in self.config:
                logger.error(f"❌ Sistema {system_name} não encontrado no config")
                return False
            
            # Criar collector se não existir
            if system_name not in self.collectors:
                collector_map = {
                    'peoplesoft': PeopleSoftCollector,
                    'google': GoogleCollector,
                }
                
                collector_class = collector_map.get(system_name)
                if not collector_class:
                    logger.error(f"❌ Collector {system_name} não implementado")
                    return False
                
                self.collectors[system_name] = collector_class(self.config[system_name])
                logger.info(f"✓ Collector {system_name} criado")
            
            # Agendar job
            collector = self.collectors[system_name]
            interval = self.config[system_name].get('collection_interval', 300)
            
            self.scheduler.add_job(
                func=self._collect_system_data,
                trigger=IntervalTrigger(seconds=interval),
                args=[system_name, collector],
                id=f"collect_{system_name}",
                name=f"Coleta {system_name}",
                replace_existing=True,
                next_run_time=datetime.now()  # Executar imediatamente
            )
            
            self.running_systems.add(system_name)
            logger.info(f"✅ Sistema {system_name} iniciado (intervalo: {interval}s)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar sistema {system_name}: {e}")
            return False
    
    def stop_system(self, system_name: str) -> bool:
        """Para coleta de um sistema específico"""
        try:
            if system_name not in self.running_systems:
                logger.warning(f"⚠ Sistema {system_name} não está rodando")
                return False
            
            # Remover job
            job_id = f"collect_{system_name}"
            try:
                self.scheduler.remove_job(job_id)
                logger.info(f"✓ Job {job_id} removido")
            except Exception as e:
                logger.warning(f"⚠ Erro ao remover job: {e}")
            
            self.running_systems.remove(system_name)
            logger.info(f"⏹️  Sistema {system_name} parado")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao parar sistema {system_name}: {e}")
            return False
    
    def stop(self):
        """Para o orquestrador"""
        logger.info("🛑 Parando orquestrador...")
        if self.scheduler:
            self.scheduler.shutdown(wait=True)
        logger.info("✓ Orquestrador parado")
