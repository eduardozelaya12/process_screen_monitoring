from flask import render_template, jsonify, request, send_from_directory
from storage.local_storage import LocalStorage
import logging
import json
import os
from copy import deepcopy
import pyodbc

logger = logging.getLogger(__name__)

# Instância global de storage
storage = LocalStorage()

SYSTEMS_CONFIG_PATH = 'config/systems_config.json'
ALLOWED_SYSTEM_FIELDS = {
    'enabled',
    'collection_interval',
    'filters',
    'credentials',
    'database_connection',
    'base_url',
    'process_monitor_url',
    'headless',
    'retry_attempts',
    'timeout',
    'name',
    'type',
    'screenshot'
}


def _load_systems_config() -> dict:
    with open(SYSTEMS_CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def _write_systems_config(config_data: dict):
    temp_path = f"{SYSTEMS_CONFIG_PATH}.tmp"
    with open(temp_path, 'w', encoding='utf-8') as temp_file:
        json.dump(config_data, temp_file, ensure_ascii=False, indent=2)
    os.replace(temp_path, SYSTEMS_CONFIG_PATH)


def _normalize_filters(filters: dict) -> dict:
    normalized = {}
    for key, value in filters.items():
        if isinstance(value, dict):
            normalized[key] = _normalize_filters(value)
        elif isinstance(value, str):
            normalized[key] = value.strip() or None
        else:
            normalized[key] = value
    return normalized


def _deep_merge_dicts(base: dict, updates: dict) -> dict:
    merged = deepcopy(base)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged


def _sanitize_system_updates(payload: dict) -> dict:
    if not isinstance(payload, dict) or not payload:
        raise ValueError("Payload inválido ou vazio")

    sanitized = {}
    for key, value in payload.items():
        if key not in ALLOWED_SYSTEM_FIELDS:
            raise ValueError(f"Campo '{key}' não é permitido para atualização")

        if key == 'collection_interval':
            if isinstance(value, str) and value.isdigit():
                value = int(value)
            if not isinstance(value, int) or value <= 0:
                raise ValueError("collection_interval deve ser inteiro positivo")

        if key == 'enabled' and not isinstance(value, bool):
            raise ValueError("enabled deve ser booleano")

        if key in {'filters', 'credentials', 'database_connection', 'screenshot'} and value is not None and not isinstance(value, dict):
            raise ValueError(f"{key} deve ser um objeto")

        if key == 'filters' and isinstance(value, dict):
            value = _normalize_filters(value)

        if key == 'database_connection' and isinstance(value, dict):
            db_conn = {}
            
            # Validar db_type
            if 'db_type' in value:
                db_type = value['db_type']
                if db_type not in {'sqlserver', 'postgresql'}:
                    raise ValueError("database_connection.db_type deve ser 'sqlserver' ou 'postgresql'")
                db_conn['db_type'] = db_type
            
            # Validar campos obrigatórios
            required_fields = ['server', 'database', 'username', 'password']
            for field in required_fields:
                if field in value:
                    field_value = value[field]
                    if isinstance(field_value, str):
                        field_value = field_value.strip()
                    if not field_value:
                        raise ValueError(f"database_connection.{field} é obrigatório e não pode estar vazio")
                    db_conn[field] = field_value
            
            # Validar port (opcional)
            if 'port' in value:
                try:
                    port = int(value['port'])
                    if port <= 0 or port > 65535:
                        raise ValueError("database_connection.port deve estar entre 1 e 65535")
                    db_conn['port'] = port
                except (TypeError, ValueError):
                    raise ValueError("database_connection.port deve ser um número inteiro")
            
            # Validar query (opcional)
            if 'query' in value:
                query = value['query']
                if isinstance(query, str):
                    query = query.strip()
                if query:
                    db_conn['query'] = query
            
            value = db_conn

        if key == 'screenshot' and isinstance(value, dict):
            screenshot = {}

            if 'width' in value:
                try:
                    width = int(value['width'])
                    if width < 600:
                        raise ValueError("screenshot.width deve ser >= 600")
                    screenshot['width'] = width
                except (TypeError, ValueError):
                    raise ValueError("screenshot.width deve ser inteiro")

            if 'height' in value:
                try:
                    height = int(value['height'])
                    if height < 400:
                        raise ValueError("screenshot.height deve ser >= 400")
                    screenshot['height'] = height
                except (TypeError, ValueError):
                    raise ValueError("screenshot.height deve ser inteiro")

            if 'full_page' in value:
                full_page = value['full_page']
                if not isinstance(full_page, bool):
                    raise ValueError("screenshot.full_page deve ser booleano")
                screenshot['full_page'] = full_page

            value = screenshot

        sanitized[key] = value

    return sanitized


def _update_system_config(system_name: str, updates: dict) -> dict:
    """Atualiza configuração no disco, usando orquestrador se disponível."""
    try:
        from orchestrator.orchestrator import get_orchestrator_instance
        orchestrator = get_orchestrator_instance()
    except Exception:
        orchestrator = None

    if orchestrator:
        return orchestrator.update_system_config(system_name, updates)

    config_data = _load_systems_config()

    if system_name not in config_data:
        raise KeyError(f"Sistema {system_name} não encontrado")

    merged_config = _deep_merge_dicts(config_data[system_name], updates)
    config_data[system_name] = merged_config
    _write_systems_config(config_data)

    return merged_config


def _format_system_display_name(system_key: str, config: dict) -> str:
    """
    Gera um nome amigável para exibição.
    Para sistemas de banco de dados, adiciona o tipo do banco entre parênteses,
    por exemplo: "Banco de Dados (SQL Server)".
    """
    base_name = config.get('name') or system_key
    system_type = (config.get('type') or '').lower()

    if system_type == 'database':
        db_type = (config.get('database_connection', {}) or {}).get('db_type', '').lower()
        if db_type == 'sqlserver':
            db_label = 'SQL Server'
        elif db_type == 'postgresql':
            db_label = 'PostgreSQL'
        else:
            db_label = db_type.capitalize() if db_type else 'Database'

        # Remove qualquer trecho entre parênteses, ex: "Banco de Dados (Exemplo) #1" -> "Banco de Dados #1"
        if '(' in base_name and ')' in base_name:
            last_open = base_name.rfind('(')
            last_close = base_name.rfind(')')
            if last_close > last_open:
                base_name = (base_name[:last_open] + base_name[last_close + 1:]).strip()

        return f"{base_name} ({db_label})"

    return base_name

def register_routes(app):
    """Registra todas as rotas REST da aplicação"""
    
    @app.route('/api/config/systems/<system_name>/clone-database', methods=['POST'])
    def clone_database_system(system_name):
        """Clona um sistema do tipo database criando um novo sistema para outro DB/query"""
        try:
            configs = _load_systems_config()
            if system_name not in configs:
                return jsonify({'error': 'Sistema não encontrado'}), 404

            base_config = configs[system_name]
            if base_config.get('type') != 'database':
                return jsonify({'error': 'Apenas sistemas do tipo database podem ser clonados'}), 400

            # Descobrir a chave raiz (sem sufixos _dbN)
            root_key = system_name.split('_db')[0]
            if root_key not in configs:
                root_key = system_name

            root_config = configs[root_key]

            # Encontrar próximo índice disponível baseado em todas as chaves da família root_key
            family_prefix = f"{root_key}_db"
            indices = []
            for key in configs.keys():
                if key.startswith(family_prefix):
                    suffix = key[len(family_prefix):]
                    try:
                        indices.append(int(suffix))
                    except ValueError:
                        continue

            next_index = 1 if not indices else max(indices) + 1

            new_key = f"{family_prefix}{next_index}"
            new_config = deepcopy(base_config)

            # Nome base sempre vindo da raiz, sem empilhar #1 #1
            base_name = root_config.get('name', root_key)
            # Remove qualquer sufixo " #N" existente do nome base
            if ' #' in base_name:
                base_name = base_name.split(' #')[0]
            # Remove qualquer trecho entre parênteses, como "(Exemplo)"
            if '(' in base_name and ')' in base_name:
                last_open = base_name.rfind('(')
                last_close = base_name.rfind(')')
                if last_close > last_open:
                    base_name = (base_name[:last_open] + base_name[last_close + 1:]).strip()
            new_config['name'] = f"{base_name} #{next_index}"

            # Ao clonar, deixa desabilitado por padrão até o usuário ajustar
            new_config['enabled'] = False

            configs[new_key] = new_config
            _write_systems_config(configs)

            return jsonify({
                'status': 'success',
                'system': new_key,
                'config': new_config
            }), 201
        except Exception as e:
            logger.error(f"Erro ao clonar sistema de banco de dados: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/')
    def index():
        """Página principal do dashboard"""
        return render_template('dashboard.html')
    
    @app.route('/config')
    def config_page():
        """Tela de parametrização dos sistemas"""
        return render_template('parameters.html')
    
    @app.route('/tv')
    def tv_display():
        """Versão otimizada para TV - Grid de todos os sistemas"""
        return render_template('tv_display_new.html')
    
    @app.route('/tv/old')
    def tv_display_old():
        """Versão antiga da TV"""
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
            systems = _load_systems_config()
            
            # Retornar apenas sistemas habilitados
            enabled_systems = {
                name: {
                    'name': _format_system_display_name(name, config),
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
            
            # Adicionar informações de timing para contador regressivo (apenas para database)
            system_config = orchestrator.get_system_config(system_name)
            if system_config and system_config.get('type', '').lower() == 'database':
                last_update = orchestrator.status_tracker.last_update.get(system_name)
                collection_interval = system_config.get('collection_interval', 300)
                
                if last_update:
                    status['last_collection'] = last_update.isoformat()
                    status['collection_interval'] = collection_interval
            
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
    
    @app.route('/api/systems/all')
    def get_all_systems():
        """Lista todos os sistemas com status de execução"""
        try:
            systems = _load_systems_config()
            
            from orchestrator.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            
            result = {}
            for name, config in systems.items():
                running = False
                interval = config.get('collection_interval', 300)
                
                if orchestrator and hasattr(orchestrator, 'running_systems'):
                    running = name in orchestrator.running_systems
                
                result[name] = {
                    'name': _format_system_display_name(name, config),
                    'type': config['type'],
                    'enabled': config.get('enabled', False),
                    'running': running,
                    'interval': interval
                }
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Erro ao buscar todos os sistemas: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/systems/<system_name>/start', methods=['POST'])
    def start_system(system_name):
        """Inicia coleta de um sistema específico"""
        try:
            from orchestrator.orchestrator import get_orchestrator_instance
            
            orchestrator = get_orchestrator_instance()
            if not orchestrator:
                return jsonify({'error': 'Orquestrador não iniciado'}), 503
            
            success = orchestrator.start_system(system_name)
            
            if success:
                return jsonify({
                    'status': 'success',
                    'message': f'Sistema {system_name} iniciado',
                    'system': system_name
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': f'Falha ao iniciar sistema {system_name}'
                }), 400
                
        except Exception as e:
            logger.error(f"Erro ao iniciar sistema: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/systems/<system_name>/stop', methods=['POST'])
    def stop_system(system_name):
        """Para coleta de um sistema específico"""
        try:
            from orchestrator.orchestrator import get_orchestrator_instance
            
            orchestrator = get_orchestrator_instance()
            if not orchestrator:
                return jsonify({'error': 'Orquestrador não iniciado'}), 503
            
            success = orchestrator.stop_system(system_name)
            
            if success:
                return jsonify({
                    'status': 'success',
                    'message': f'Sistema {system_name} parado',
                    'system': system_name
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': f'Falha ao parar sistema {system_name}'
                }), 400
                
        except Exception as e:
            logger.error(f"Erro ao parar sistema: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/config/systems', methods=['GET'])
    def list_system_configs():
        """Retorna configuração completa dos sistemas"""
        try:
            configs = _load_systems_config()
            return jsonify(configs)
        except Exception as e:
            logger.error(f"Erro ao buscar config de sistemas: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/config/systems/<system_name>', methods=['GET'])
    def get_system_config(system_name):
        """Retorna configuração de um sistema específico"""
        try:
            configs = _load_systems_config()
            system_config = configs.get(system_name)

            if not system_config:
                return jsonify({'error': 'Sistema não encontrado'}), 404

            return jsonify(system_config)
        except Exception as e:
            logger.error(f"Erro ao buscar config de sistema: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/config/systems/<system_name>', methods=['PUT'])
    def update_system_config(system_name):
        """Atualiza configuração de um sistema"""
        try:
            payload = request.get_json(silent=True) or {}
            sanitized_updates = _sanitize_system_updates(payload)
            updated_config = _update_system_config(system_name, sanitized_updates)
            return jsonify({
                'status': 'success',
                'system': system_name,
                'config': updated_config
            })
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except KeyError as e:
            return jsonify({'error': str(e)}), 404
        except Exception as e:
            logger.error(f"Erro ao atualizar config de sistema: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/config/systems/<system_name>', methods=['DELETE'])
    def delete_system_config(system_name):
        """Remove um sistema de configuração (restrições para sistemas de banco base)"""
        try:
            configs = _load_systems_config()
            if system_name not in configs:
                return jsonify({'error': 'Sistema não encontrado'}), 404

            system_config = configs[system_name]

            # Não permitir remover sistema de banco "raiz" (sem sufixo _db)
            if system_config.get('type') == 'database' and '_db' not in system_name:
                return jsonify({'error': 'Não é permitido remover o primeiro sistema de banco de dados'}), 400

            # TODO: opcionalmente parar o sistema no orquestrador, se estiver rodando
            del configs[system_name]
            _write_systems_config(configs)

            return jsonify({'status': 'success', 'system': system_name})
        except Exception as e:
            logger.error(f"Erro ao remover config de sistema: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/database/list-databases', methods=['POST'])
    def list_databases():
        """Lista databases disponíveis em um servidor SQL Server"""
        try:
            data = request.get_json(silent=True) or {}
            
            db_type = data.get('db_type', 'sqlserver').lower()
            server = data.get('server', '').strip()
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
            port = data.get('port')
            
            if not all([server, username, password]):
                return jsonify({'error': 'Server, username e password são obrigatórios'}), 400
            
            if db_type != 'sqlserver':
                return jsonify({'error': 'Apenas SQL Server é suportado para listagem de databases'}), 400
            
            # Porta padrão
            if not port:
                port = 1433
            else:
                try:
                    port = int(port)
                except (ValueError, TypeError):
                    port = 1433
            
            # Conectar ao SQL Server
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={server},{port};"
                f"UID={username};"
                f"PWD={password};"
                f"TrustServerCertificate=yes;"
                f"Connection Timeout=10;"
            )
            
            databases = []
            connection = None
            
            try:
                connection = pyodbc.connect(conn_str, timeout=10)
                cursor = connection.cursor()
                
                # Query para listar databases
                cursor.execute("""
                    SELECT name 
                    FROM sys.databases 
                    WHERE state_desc = 'ONLINE'
                    ORDER BY name
                """)
                
                databases = [row[0] for row in cursor.fetchall()]
                cursor.close()
                
            except pyodbc.Error as e:
                logger.error(f"Erro ao conectar ao SQL Server: {e}")
                return jsonify({'error': f'Erro ao conectar: {str(e)}'}), 400
            finally:
                if connection:
                    try:
                        connection.close()
                    except Exception:
                        pass
            
            return jsonify({
                'status': 'success',
                'databases': databases
            })
            
        except Exception as e:
            logger.error(f"Erro ao listar databases: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/database/test-connection', methods=['POST'])
    def test_database_connection():
        """Testa conexão com banco de dados"""
        try:
            data = request.get_json(silent=True) or {}
            
            db_type = data.get('db_type', 'sqlserver').lower()
            server = data.get('server', '').strip()
            database = data.get('database', '').strip()
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
            port = data.get('port')
            
            if not all([server, database, username, password]):
                return jsonify({'error': 'Todos os campos são obrigatórios'}), 400
            
            if db_type != 'sqlserver':
                return jsonify({'error': 'Apenas SQL Server é suportado para teste de conexão'}), 400
            
            # Porta padrão
            if not port:
                port = 1433
            else:
                try:
                    port = int(port)
                except (ValueError, TypeError):
                    port = 1433
            
            # Conectar ao SQL Server
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={server},{port};"
                f"DATABASE={database};"
                f"UID={username};"
                f"PWD={password};"
                f"TrustServerCertificate=yes;"
                f"Connection Timeout=10;"
            )
            
            connection = None
            try:
                connection = pyodbc.connect(conn_str, timeout=10)
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                
                return jsonify({
                    'status': 'success',
                    'message': 'Conexão bem-sucedida!'
                })
                
            except pyodbc.Error as e:
                logger.error(f"Erro ao testar conexão: {e}")
                return jsonify({
                    'status': 'error',
                    'error': f'Erro ao conectar: {str(e)}'
                }), 400
            finally:
                if connection:
                    try:
                        connection.close()
                    except Exception:
                        pass
            
        except Exception as e:
            logger.error(f"Erro ao testar conexão: {e}")
            return jsonify({'error': str(e)}), 500
    
    logger.info("✓ Rotas registradas")
