import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

def datetime_handler(obj):
    """Converte datetime para string ISO format"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

class LocalStorage:
    """Armazenamento local usando SQLite"""
    
    def __init__(self, db_path="storage/dashboard.db"):
        self.db_path = db_path
        self._init_database()
    
    @contextmanager
    def _get_connection(self):
        """Context manager para conexão com banco"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Retorna dicts
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_database(self):
        """Inicializa tabelas do banco"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabela de métricas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    system_name TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    total_processes INTEGER,
                    running INTEGER,
                    failed INTEGER,
                    success INTEGER,
                    success_rate REAL,
                    status TEXT,
                    data JSON
                )
            """)
            
            # Tabela de screenshots
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS screenshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    system_name TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER
                )
            """)
            
            # Tabela de eventos/erros
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    system_name TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    message TEXT,
                    severity TEXT,
                    timestamp DATETIME NOT NULL
                )
            """)

            # Índices (SQLite exige CREATE INDEX separado)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_system_timestamp
                ON metrics (system_name, timestamp DESC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_screenshots_system_timestamp
                ON screenshots (system_name, timestamp DESC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_system_timestamp
                ON events (system_name, timestamp DESC)
            """)
            
            logger.info("✓ Banco de dados inicializado")
    
    def save_metrics(self, system_name: str, metrics: Dict) -> int:
        """Salva métricas no banco"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO metrics 
                    (system_name, timestamp, total_processes, running, failed, 
                     success, success_rate, status, data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    system_name,
                    datetime.now(),
                    metrics.get('total_processes', 0),
                    metrics.get('running', 0),
                    metrics.get('failed', 0),
                    metrics.get('success', 0),
                    metrics.get('success_rate', 0.0),
                    metrics.get('status', 'unknown'),
                    json.dumps(metrics, default=datetime_handler)
                ))
                
                return cursor.lastrowid
                
        except Exception as e:
            logger.error(f"Erro ao salvar métricas: {e}")
            return -1
    
    def get_latest_metrics(self, system_name: str, limit: int = 10) -> List[Dict]:
        """Obtém métricas mais recentes"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM metrics
                    WHERE system_name = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (system_name, limit))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Erro ao buscar métricas: {e}")
            return []
    
    def get_metrics_range(self, system_name: str, hours: int = 24) -> List[Dict]:
        """Obtém métricas de um período"""
        try:
            cutoff = datetime.now() - timedelta(hours=hours)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM metrics
                    WHERE system_name = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                """, (system_name, cutoff))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Erro ao buscar intervalo: {e}")
            return []
    
    def cleanup_old_data(self, days: int = 90) -> int:
        """Remove dados antigos"""
        try:
            cutoff = datetime.now() - timedelta(days=days)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM metrics WHERE timestamp < ?", (cutoff,))
                metrics_deleted = cursor.rowcount
                
                cursor.execute("DELETE FROM events WHERE timestamp < ?", (cutoff,))
                events_deleted = cursor.rowcount
                
                logger.info(f"✓ Limpeza: {metrics_deleted} métricas, {events_deleted} eventos removidos")
                
                return metrics_deleted + events_deleted
                
        except Exception as e:
            logger.error(f"Erro na limpeza: {e}")
            return 0
