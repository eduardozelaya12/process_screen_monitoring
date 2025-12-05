from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import json
import logging
import os
from threading import Lock
from typing import Dict, Optional
from copy import deepcopy

# Importações dos módulos do projeto
from collectors.peoplesoft_collector import PeopleSoftCollector
from collectors.google_collector import GoogleCollector
from collectors.database_collector import DatabaseCollector
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
        self.config_lock = Lock()
        self.config_mtime = self._get_config_mtime()
        
        logger.info("📋 Orquestrador criado")
    
    def _load_config(self) -> Dict:
        """Carrega configuração dos sistemas"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _write_config(self, config_data: Dict):
        """Escreve configuração no disco de forma atômica"""
        temp_path = f"{self.config_path}.tmp"
        with open(temp_path, 'w', encoding='utf-8') as temp_file:
            json.dump(config_data, temp_file, ensure_ascii=False, indent=2)
        os.replace(temp_path, self.config_path)

    @staticmethod
    def _deep_merge_dicts(base: Dict, updates: Dict) -> Dict:
        """Mescla recursivamente dicionários sem modificar o original"""
        if not updates:
            return deepcopy(base)

        merged = deepcopy(base)

        for key, value in updates.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = DashboardOrchestrator._deep_merge_dicts(merged[key], value)
            else:
                merged[key] = value

        return merged

    def _get_config_mtime(self) -> Optional[float]:
        """Retorna timestamp de modificação do arquivo de configuração"""
        try:
            return os.path.getmtime(self.config_path)
        except OSError:
            logger.warning("⚠️ Não foi possível obter data de modificação do config")
            return None

    def _reload_config_if_needed(self):
        """Recarrega configuração se arquivo foi alterado"""
        try:
            current_mtime = os.path.getmtime(self.config_path)
        except OSError:
            return

        if self.config_mtime is not None and current_mtime <= self.config_mtime:
            return

        with self.config_lock:
            latest_mtime = self._get_config_mtime()
            if latest_mtime is None:
                return
            if self.config_mtime is not None and latest_mtime <= self.config_mtime:
                return

            logger.info("📝 Alteração detectada em systems_config.json — recarregando...")
            self.config = self._load_config()
            self.config_mtime = latest_mtime
            self._apply_runtime_config()

    def _apply_runtime_config(self):
        """Aplica novas configurações aos coletores já em execução"""
        for system_name, collector in self.collectors.items():
            system_config = self.config.get(system_name)
            if not system_config:
                continue

            if hasattr(collector, 'update_config'):
                collector.update_config(system_config)
            else:
                collector.config = system_config

            # Atualizar intervalo do job se necessário
            if not self.scheduler:
                continue

            interval = system_config.get('collection_interval', 300)
            job_id = f"collect_{system_name}"
            try:
                job = self.scheduler.get_job(job_id)
                if not job:
                    continue

                trigger = job.trigger
                current_seconds = None
                if isinstance(trigger, IntervalTrigger):
                    current_seconds = trigger.interval.total_seconds()

                if current_seconds is None or int(current_seconds) == int(interval):
                    continue

                self.scheduler.reschedule_job(job_id, trigger=IntervalTrigger(seconds=interval))
                logger.info(f"⏱️ Intervalo do job {system_name} atualizado para {interval}s")
            except Exception as e:
                logger.warning(f"⚠️ Falha ao atualizar intervalo de {system_name}: {e}")
    
    def set_socketio(self, socketio):
        """Define instância do SocketIO para broadcasts"""
        self.socketio = socketio
        logger.info("✓ SocketIO configurado no orquestrador")
    
    def get_system_config(self, system_name: str) -> Optional[Dict]:
        """Retorna configuração atual de um sistema específico"""
        with self.config_lock:
            config = self.config.get(system_name)
            return deepcopy(config) if config else None

    def get_all_configs(self) -> Dict:
        """Retorna snapshot das configurações de todos os sistemas"""
        with self.config_lock:
            return deepcopy(self.config)

    def _broadcast_config_update(self, system_name: str, config: Dict):
        """Emite atualização de configuração para clientes WebSocket"""
        if not self.socketio:
            return
        try:
            self.socketio.emit('config_update', {
                'system': system_name,
                'config': config
            })
        except Exception as e:
            logger.warning(f"⚠️ Falha ao emitir config_update: {e}")

    def update_system_config(self, system_name: str, updates: Dict) -> Dict:
        """
        Atualiza configuração de um sistema, persistindo no disco
        e aplicando mudanças em tempo de execução.
        """
        if not isinstance(updates, dict) or not updates:
            raise ValueError("Atualizações inválidas ou vazias")

        old_config = None
        new_enabled_state = None
        enable_changed = False

        with self.config_lock:
            config_data = self._load_config()

            if system_name not in config_data:
                raise KeyError(f"Sistema {system_name} não encontrado")

            old_config = deepcopy(config_data.get(system_name, {}))

            merged_config = self._deep_merge_dicts(config_data[system_name], updates)
            config_data[system_name] = merged_config

            self._write_config(config_data)

            # Atualizar estado interno e aplicar runtime config
            self.config = config_data
            self.config_mtime = self._get_config_mtime()
            self._apply_runtime_config()

            new_enabled_state = merged_config.get('enabled', False)
            enable_changed = old_config.get('enabled', False) != new_enabled_state

            logger.info(f"📝 Configuração de {system_name} atualizada em runtime")

        # Fora do lock para evitar deadlock com operações do scheduler
        if enable_changed and self.scheduler:
            try:
                if new_enabled_state:
                    logger.info(f"▶️  Sistema {system_name} habilitado via config - iniciando...")
                    start_success = self.start_system(system_name)
                    if not start_success:
                        logger.warning(f"⚠️ Falha ao iniciar sistema {system_name} após habilitar")
                else:
                    logger.info(f"⏹️  Sistema {system_name} desabilitado via config - parando...")
                    stop_success = self.stop_system(system_name)
                    if not stop_success:
                        logger.warning(f"⚠️ Falha ao parar sistema {system_name} após desabilitar")
            except Exception as e:
                logger.error(f"❌ Erro ao ajustar execução de {system_name}: {e}")

        merged_copy = deepcopy(merged_config)
        self._broadcast_config_update(system_name, merged_copy)
        return merged_copy

    def initialize_collectors(self):
        """Inicializa coletores para cada sistema habilitado"""
        logger.info("🔧 Inicializando coletores...")
        
        # Mapa de coletores por tipo de sistema
        type_collector_map = {
            'selenium': {
                'peoplesoft': PeopleSoftCollector,
                'google': GoogleCollector,
            },
            'database': {
                'sqlserver': DatabaseCollector,
                'postgresql': DatabaseCollector,
            },
            'api': {
                # Adicione coletores de API aqui
            }
        }
        
        # Mapa de coletores por nome (compatibilidade com versões antigas)
        name_collector_map = {
            'peoplesoft': PeopleSoftCollector,
            'google': GoogleCollector,
        }
        
        for system_name, system_config in self.config.items():
            if not system_config.get('enabled', False):
                logger.info(f"⏭ Sistema {system_name} desabilitado, pulando...")
                continue
            
            # Tentar encontrar collector pelo tipo primeiro
            system_type = system_config.get('type', '').lower()
            collector_class = None
            
            if system_type == 'database':
                # Para database, usar DatabaseCollector
                collector_class = DatabaseCollector
            elif system_type in type_collector_map:
                # Tentar encontrar pelo nome dentro do tipo
                type_map = type_collector_map[system_type]
                collector_class = type_map.get(system_name)
            
            # Fallback: tentar pelo nome (compatibilidade)
            if not collector_class:
                collector_class = name_collector_map.get(system_name)
            
            if collector_class:
                try:
                    self.collectors[system_name] = collector_class(system_config)
                    logger.info(f"✓ Coletor {system_name} inicializado (tipo: {system_type})")
                except Exception as e:
                    logger.error(f"❌ Erro ao inicializar {system_name}: {e}")
            else:
                logger.warning(f"⚠ Coletor {system_name} não implementado (tipo: {system_type})")
        
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
            self._reload_config_if_needed()

            system_config = self.config.get(system_name, {})
            if not system_config.get('enabled', True):
                logger.info(f"🚫 Sistema {system_name} desabilitado via config – pulando coleta atual")
                return

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
                system_config = self.config[system_name]
                system_type = system_config.get('type', '').lower()
                
                # Mapa de coletores por tipo
                type_collector_map = {
                    'database': DatabaseCollector,
                }
                
                # Mapa de coletores por nome (compatibilidade)
                name_collector_map = {
                    'peoplesoft': PeopleSoftCollector,
                    'google': GoogleCollector,
                }
                
                collector_class = None
                if system_type == 'database':
                    collector_class = DatabaseCollector
                else:
                    collector_class = name_collector_map.get(system_name)
                
                if not collector_class:
                    logger.error(f"❌ Collector {system_name} não implementado (tipo: {system_type})")
                    return False
                
                self.collectors[system_name] = collector_class(system_config)
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
