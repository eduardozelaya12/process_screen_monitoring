from typing import Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DataProcessor:
    """Processa e padroniza dados de diferentes sistemas"""
    
    def __init__(self):
        self.processors = {
            'peoplesoft': self._process_peoplesoft,
            'oracle_fusion': self._process_oracle,
            'bonita': self._process_bonita,
            'n8n': self._process_n8n
        }
    
    def standardize(self, raw_data: Dict, system_name: str) -> Dict:
        """
        Padroniza dados de qualquer sistema para formato unificado
        
        Args:
            raw_data: Dados brutos do coletor
            system_name: Nome do sistema (peoplesoft, oracle_fusion, etc)
            
        Returns:
            Dict padronizado
        """
        try:
            # Obter processador específico
            processor = self.processors.get(
                system_name.lower(),
                self._process_generic
            )
            
            # Processar dados
            processed = processor(raw_data)
            
            # Adicionar metadados
            processed['system'] = system_name
            processed['processed_at'] = datetime.now().isoformat()
            
            logger.info(f"✓ Dados de {system_name} processados")
            
            return processed
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar {system_name}: {e}")
            return self._get_error_response(system_name, str(e))
    
    def _process_peoplesoft(self, data: Dict) -> Dict:
        """Processa dados do PeopleSoft"""
        if data.get('status') == 'error':
            return self._get_error_response('PeopleSoft', data.get('error'))
        
        metrics = data['data'].get('metrics', {})
        
        return {
            'total_processes': metrics.get('total_processes', 0),
            'running': metrics.get('running', 0),
            'failed': metrics.get('failed', 0),
            'success': metrics.get('success', 0),
            'success_rate': self._calculate_success_rate(
                metrics.get('success', 0),
                metrics.get('total_processes', 1)
            ),
            'critical_errors': metrics.get('critical_errors', []),
            'screenshot_path': data['data'].get('screenshot_path'),
            'status': 'healthy' if metrics.get('failed', 0) == 0 else 'warning',
            'timestamp': data.get('timestamp', datetime.now()).isoformat()
        }
    
    def _process_oracle(self, data: Dict) -> Dict:
        """Processa dados do Oracle Fusion"""
        if data.get('status') == 'error':
            return self._get_error_response('Oracle Fusion', data.get('error'))
        
        # Adaptar estrutura da API Oracle para formato padrão
        items = data['data'].get('items', [])
        
        failed = [item for item in items if item.get('status') == 'FAILED']
        running = [item for item in items if item.get('status') == 'RUNNING']
        success = [item for item in items if item.get('status') == 'SUCCESS']
        
        return {
            'total_processes': len(items),
            'running': len(running),
            'failed': len(failed),
            'success': len(success),
            'success_rate': self._calculate_success_rate(len(success), len(items)),
            'critical_errors': [
                {
                    'name': item.get('processName'),
                    'message': item.get('errorMessage'),
                    'timestamp': item.get('endTime')
                }
                for item in failed[:10]  # Limitar a 10
            ],
            'status': 'healthy' if len(failed) == 0 else 'critical',
            'timestamp': datetime.now().isoformat()
        }
    
    def _process_bonita(self, data: Dict) -> Dict:
        """Processa dados do Bonita"""
        if data.get('status') == 'error':
            return self._get_error_response('Bonita', data.get('error'))
        
        cases = data['data'].get('cases', [])
        
        return {
            'total_processes': len(cases),
            'running': len([c for c in cases if c.get('state') == 'started']),
            'failed': len([c for c in cases if c.get('state') == 'error']),
            'success': len([c for c in cases if c.get('state') == 'completed']),
            'success_rate': self._calculate_success_rate(
                len([c for c in cases if c.get('state') == 'completed']),
                len(cases)
            ),
            'critical_errors': [],
            'status': 'healthy',
            'timestamp': datetime.now().isoformat()
        }
    
    def _process_n8n(self, data: Dict) -> Dict:
        """Processa dados do N8n"""
        if data.get('status') == 'error':
            return self._get_error_response('N8n', data.get('error'))
        
        executions = data['data'].get('executions', [])
        
        failed = [e for e in executions if e.get('finished') == False]
        success = [e for e in executions if e.get('finished') == True]
        running = [e for e in executions if e.get('status') == 'running']
        
        return {
            'total_processes': len(executions),
            'running': len(running),
            'failed': len(failed),
            'success': len(success),
            'success_rate': self._calculate_success_rate(len(success), len(executions)),
            'critical_errors': [
                {
                    'name': e.get('workflowName'),
                    'message': e.get('errorMessage', 'Erro desconhecido'),
                    'timestamp': e.get('stopTime')
                }
                for e in failed[:10]
            ],
            'status': 'critical' if len(failed) > 5 else 'healthy',
            'timestamp': datetime.now().isoformat()
        }
    
    def _process_generic(self, data: Dict) -> Dict:
        """Processamento genérico para sistemas não mapeados"""
        return {
            'total_processes': 0,
            'running': 0,
            'failed': 0,
            'success': 0,
            'success_rate': 0.0,
            'critical_errors': [],
            'status': 'unknown',
            'timestamp': datetime.now().isoformat(),
            'raw_data': data
        }
    
    def _calculate_success_rate(self, success: int, total: int) -> float:
        """Calcula taxa de sucesso em porcentagem"""
        if total == 0:
            return 100.0
        return round((success / total) * 100, 2)
    
    def _get_error_response(self, system: str, error: str) -> Dict:
        """Retorna resposta padronizada de erro"""
        return {
            'total_processes': 0,
            'running': 0,
            'failed': 0,
            'success': 0,
            'success_rate': 0.0,
            'critical_errors': [],
            'status': 'error',
            'error_message': error,
            'timestamp': datetime.now().isoformat()
        }
