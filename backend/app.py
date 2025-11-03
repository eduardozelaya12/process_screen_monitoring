from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
import logging
import io

# Configuração de logging
utf8_stream = None
try:
    import sys
    utf8_stream = io.TextIOWrapper(getattr(sys.stdout, 'buffer', sys.stdout), encoding='utf-8', errors='replace')
except Exception:
    utf8_stream = None

handlers = [logging.FileHandler('storage/logs/backend.log', encoding='utf-8')]
if utf8_stream:
    handlers.append(logging.StreamHandler(stream=utf8_stream))
else:
    handlers.append(logging.StreamHandler())

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=handlers
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
