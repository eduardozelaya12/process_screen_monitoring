from flask_socketio import emit, join_room, leave_room
import logging

logger = logging.getLogger(__name__)

# Controle de clientes conectados
connected_clients = set()

def register_socketio_handlers(socketio):
    """Registra handlers de eventos WebSocket"""
    
    @socketio.on('connect')
    def handle_connect():
        """Cliente conectou"""
        client_id = request.sid
        connected_clients.add(client_id)
        
        logger.info(f"✓ Cliente conectado: {client_id} (total: {len(connected_clients)})")
        
        emit('connected', {
            'message': 'Conectado ao servidor',
            'client_id': client_id
        })
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Cliente desconectou"""
        client_id = request.sid
        connected_clients.discard(client_id)
        
        logger.info(f"Cliente desconectado: {client_id} (total: {len(connected_clients)})")
    
    @socketio.on('request_update')
    def handle_update_request(data):
        """Cliente solicitou atualização de dados"""
        system_name = data.get('system')
        
        logger.info(f"Atualização solicitada para: {system_name}")
        
        try:
            from orchestrator.orchestrator import get_orchestrator_instance
            
            orchestrator = get_orchestrator_instance()
            if orchestrator:
                status = orchestrator.status_tracker.get_system(system_name)
                
                emit('update', {
                    'system': system_name,
                    'data': status
                })
            else:
                emit('error', {'message': 'Orquestrador não disponível'})
                
        except Exception as e:
            logger.error(f"Erro ao processar solicitação: {e}")
            emit('error', {'message': str(e)})
    
    @socketio.on('subscribe')
    def handle_subscribe(data):
        """Cliente se inscreve para receber updates de sistemas específicos"""
        systems = data.get('systems', [])
        
        for system in systems:
            join_room(f"system_{system}")
        
        logger.info(f"Cliente inscrito em: {systems}")
        emit('subscribed', {'systems': systems})
    
    @socketio.on('unsubscribe')
    def handle_unsubscribe(data):
        """Cliente cancela inscrição"""
        systems = data.get('systems', [])
        
        for system in systems:
            leave_room(f"system_{system}")
        
        logger.info(f"Cliente desinscrito de: {systems}")
        emit('unsubscribed', {'systems': systems})
    
    @socketio.on('ping')
    def handle_ping():
        """Responde a ping do cliente"""
        emit('pong')
    
    logger.info("✓ Handlers WebSocket registrados")

def broadcast_update(socketio, system_name, data):
    """
    Função auxiliar para broadcast de atualizações
    Chamada pelo orquestrador quando há novos dados
    """
    try:
        logger.info(f"📡 Broadcasting update: {system_name}")
        
        # Emitir para todos os clientes conectados
        socketio.emit('update', {
            'system': system_name,
            'data': data,
            'timestamp': data.get('timestamp')
        }, broadcast=True)
        
        # Emitir também para room específica do sistema
        socketio.emit('system_update', data, room=f"system_{system_name}")
        
    except Exception as e:
        logger.error(f"Erro ao fazer broadcast: {e}")
