from abc import ABC, abstractmethod
from typing import Dict
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseCollector(ABC):
    """Classe abstrata base para todos os coletores"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.system_name = config.get('name', 'Unknown')
        self.system_type = config.get('type', 'unknown')
        self.last_collection = None
        self.last_error = None
        self.is_healthy = True
        
        logger.info(f"✓ Coletor {self.system_name} inicializado")

    def update_config(self, config: Dict):
        """Atualiza configuração base do coletor em tempo de execução"""
        self.config = config
        old_system_name = self.system_name
        self.system_name = config.get('name', self.system_name)
        self.system_type = config.get('type', self.system_type)

        if old_system_name != self.system_name:
            logger.info(f"🔄 Coletor renomeado: {old_system_name} ➜ {self.system_name}")
    
    @abstractmethod
    def collect(self) -> Dict:
        """Método principal de coleta de dados"""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Testa conexão com o sistema"""
        pass
    
    def _mark_success(self, data: Dict) -> Dict:
        """Marca coleta como sucesso"""
        self.last_collection = datetime.now()
        self.last_error = None
        self.is_healthy = True
        
        return {
            'status': 'success',
            'system': self.system_name,
            'data': data,
            'timestamp': self.last_collection
        }
    
    def _mark_error(self, error: str) -> Dict:
        """Marca coleta como erro"""
        self.last_error = error
        self.is_healthy = False
        
        logger.error(f"❌ Erro em {self.system_name}: {error}")
        
        return {
            'status': 'error',
            'system': self.system_name,
            'error': error,
            'timestamp': datetime.now()
        }
