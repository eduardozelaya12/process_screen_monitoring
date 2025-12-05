import logging
from typing import Dict, Optional, List
from datetime import datetime
import pyodbc
import psycopg2
from psycopg2 import pool

from collectors.base_collector import BaseCollector

logger = logging.getLogger(__name__)


class DatabaseCollector(BaseCollector):
    """Coletor para bancos de dados (SQL Server e PostgreSQL)"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        
        self.db_type = config.get('database_connection', {}).get('db_type', 'sqlserver').lower()
        self.server = config.get('database_connection', {}).get('server')
        self.database = config.get('database_connection', {}).get('database')
        self.username = config.get('database_connection', {}).get('username')
        self.password = config.get('database_connection', {}).get('password')
        self.query = config.get('database_connection', {}).get('query')
        self.port = config.get('database_connection', {}).get('port')
        self.connection = None
        self.connection_pool = None
        
        # Portas padrão
        if not self.port:
            if self.db_type == 'postgresql':
                self.port = 5432
            elif self.db_type == 'sqlserver':
                self.port = 1433
        
        logger.info(f"🗄️ DatabaseCollector inicializado: {self.system_name} ({self.db_type})")
    
    def update_config(self, config: Dict):
        """Atualiza configuração do coletor de banco de dados em runtime"""
        super().update_config(config)
        
        db_conn = config.get('database_connection', {})
        self.db_type = db_conn.get('db_type', self.db_type).lower()
        self.server = db_conn.get('server')
        self.database = db_conn.get('database')
        self.username = db_conn.get('username')
        self.password = db_conn.get('password')
        self.query = db_conn.get('query')
        self.port = db_conn.get('port')
        
        if not self.port:
            if self.db_type == 'postgresql':
                self.port = 5432
            elif self.db_type == 'sqlserver':
                self.port = 1433
        
        # Fechar conexões antigas
        self._close_connection()
        
        logger.info("♻️ Configuração do DatabaseCollector atualizada")
    
    def _get_sqlserver_connection_string(self) -> str:
        """Gera string de conexão para SQL Server"""
        if not all([self.server, self.database, self.username, self.password]):
            raise ValueError("Server, database, username e password são obrigatórios para SQL Server")
        
        # String de conexão ODBC para SQL Server
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={self.server},{self.port};"
            f"DATABASE={self.database};"
            f"UID={self.username};"
            f"PWD={self.password};"
            f"TrustServerCertificate=yes;"
        )
        return conn_str
    
    def _get_postgresql_connection_string(self) -> Dict:
        """Retorna parâmetros de conexão para PostgreSQL"""
        if not all([self.server, self.database, self.username, self.password]):
            raise ValueError("Server, database, username e password são obrigatórios para PostgreSQL")
        
        return {
            'host': self.server,
            'port': self.port,
            'database': self.database,
            'user': self.username,
            'password': self.password
        }
    
    def _connect_sqlserver(self) -> pyodbc.Connection:
        """Conecta ao SQL Server"""
        try:
            conn_str = self._get_sqlserver_connection_string()
            connection = pyodbc.connect(conn_str, timeout=10)
            logger.info(f"✓ Conectado ao SQL Server: {self.server}/{self.database}")
            return connection
        except pyodbc.Error as e:
            logger.error(f"❌ Erro ao conectar SQL Server: {e}")
            raise
    
    def _connect_postgresql(self) -> psycopg2.extensions.connection:
        """Conecta ao PostgreSQL"""
        try:
            conn_params = self._get_postgresql_connection_string()
            connection = psycopg2.connect(**conn_params, connect_timeout=10)
            logger.info(f"✓ Conectado ao PostgreSQL: {self.server}/{self.database}")
            return connection
        except psycopg2.Error as e:
            logger.error(f"❌ Erro ao conectar PostgreSQL: {e}")
            raise
    
    def _get_connection(self):
        """Obtém conexão com o banco de dados"""
        if self.connection:
            try:
                # Testa se a conexão ainda está viva
                if self.db_type == 'sqlserver':
                    cursor = self.connection.cursor()
                    cursor.execute("SELECT 1")
                    cursor.close()
                elif self.db_type == 'postgresql':
                    cursor = self.connection.cursor()
                    cursor.execute("SELECT 1")
                    cursor.close()
                return self.connection
            except Exception:
                # Conexão morta, fecha e reconecta
                self._close_connection()
        
        # Cria nova conexão
        if self.db_type == 'sqlserver':
            self.connection = self._connect_sqlserver()
        elif self.db_type == 'postgresql':
            self.connection = self._connect_postgresql()
        else:
            raise ValueError(f"Tipo de banco de dados não suportado: {self.db_type}")
        
        return self.connection
    
    def _close_connection(self):
        """Fecha conexão com o banco de dados"""
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass
            finally:
                self.connection = None
    
    def test_connection(self) -> bool:
        """Testa conexão com o banco de dados"""
        try:
            conn = self._get_connection()
            if conn:
                self._close_connection()
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Teste de conexão falhou: {e}")
            return False
    
    def _execute_query_sqlserver(self, query: str) -> List[Dict]:
        """Executa query no SQL Server e retorna resultados"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(query)
            
            # Obter nomes das colunas
            columns = [column[0] for column in cursor.description]
            
            # Obter resultados
            rows = cursor.fetchall()
            
            # Converter para lista de dicionários
            results = []
            for row in rows:
                row_dict = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    # Converter tipos não serializáveis
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    elif hasattr(value, '__dict__'):
                        value = str(value)
                    row_dict[col] = value
                results.append(row_dict)
            
            return results
        finally:
            cursor.close()
    
    def _execute_query_postgresql(self, query: str) -> List[Dict]:
        """Executa query no PostgreSQL e retorna resultados"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(query)
            
            # Obter nomes das colunas
            columns = [desc[0] for desc in cursor.description]
            
            # Obter resultados
            rows = cursor.fetchall()
            
            # Converter para lista de dicionários
            results = []
            for row in rows:
                row_dict = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    # Converter tipos não serializáveis
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    elif hasattr(value, '__dict__'):
                        value = str(value)
                    row_dict[col] = value
                results.append(row_dict)
            
            return results
        finally:
            cursor.close()
    
    def collect(self) -> Dict:
        """Coleta dados do banco de dados executando a query configurada"""
        try:
            logger.info(f"📊 Coletando dados do banco: {self.system_name}")
            
            if not self.query:
                return self._mark_error("Query não configurada")
            
            # Executar query baseado no tipo de banco
            if self.db_type == 'sqlserver':
                results = self._execute_query_sqlserver(self.query)
            elif self.db_type == 'postgresql':
                results = self._execute_query_postgresql(self.query)
            else:
                return self._mark_error(f"Tipo de banco de dados não suportado: {self.db_type}")
            
            data = {
                'query': self.query,
                'db_type': self.db_type,
                'server': self.server,
                'database': self.database,
                'results': results,
                'row_count': len(results),
                'status': 'success'
            }
            
            logger.info(f"✓ Query executada com sucesso: {len(results)} linhas retornadas")
            
            return self._mark_success(data)
            
        except Exception as e:
            logger.exception(f"❌ Erro na coleta: {e}")
            return self._mark_error(str(e))
        finally:
            # Não fechar conexão aqui para reutilização
            pass
    
    def cleanup(self):
        """Limpa recursos"""
        self._close_connection()
        if self.connection_pool:
            try:
                self.connection_pool.closeall()
            except Exception:
                pass
            self.connection_pool = None






