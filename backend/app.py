from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('storage/logs/backend.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Criar aplicação Flask
app = Flask(__name__, 
            static_folder='../frontend/static',
            template_folder='../frontend/templates')

app.config['SECRET_KEY'] = 'sua-chave-secreta-aqui-change-me'
app.config['DEBUG'] = False

# CORS para permitir conexões externas
CORS(app, resources={r"/*": {"origins": "*"}})

# Inicializar SocketIO
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    logger=False,
    engineio_logger=False
)

# Importar rotas e handlers
from backend.routes import register_routes
from backend.websocket_handlers import register_socketio_handlers

# Registrar rotas
register_routes(app)

# Registrar handlers WebSocket
register_socketio_handlers(socketio)

logger.info("✓ Backend Flask inicializado")
