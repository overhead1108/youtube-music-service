import time
import os
import logging
from pypresence import Presence
import socketio
import eventlet
from constants import CLIENT_ID, DEFAULT_PRESENCE

class YouTubeDiscordRPCService:
    def __init__(self, client_id, port):
        self.client_id = client_id
        self.port = port
        self.rpc = None
        self.last_presence = None
        
        # Setup logging
        log_path = os.path.expanduser("~/.youtube-music-service")
        if not os.path.exists(log_path):
            os.makedirs(log_path)
            
        current_time = time.strftime("%Y%m%dT%H%M%S")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_path, f"youtube-mp3-error-{current_time}.log")),
                logging.FileHandler(os.path.join(log_path, f"youtube-mp3-{current_time}.log")),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("youtube-music")
        
        self.sio = socketio.Server(cors_allowed_origins='*', async_mode='eventlet')
        self.app = socketio.WSGIApp(self.sio)
        
        @self.sio.on('connect')
        def connect(sid, environ):
            self.logger.info(f'Connected to Youtube Music Browser Plugin: {sid}')

        @self.sio.on('update')
        def update(sid, data):
            self.update_presence(data)

        @self.sio.on('disconnect')
        def disconnect(sid):
            self.logger.info(f'Disconnected from Youtube Music Browser Plugin: {sid}')

    def start_rpc(self):
        try:
            self.rpc = Presence(self.client_id)
            self.rpc.connect()
            initial_presence = DEFAULT_PRESENCE.copy()
            initial_presence["start"] = int(time.time())
            self.rpc.update(**initial_presence)
            self.logger.info("Connected to Discord RPC")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to Discord RPC: {e}")
            self.rpc = None
            return False

    def update_presence(self, data):
        self.logger.info(f'Updating presence: {data}')
        self.last_presence = data
        
        if not self.rpc:
            if not self.start_rpc():
                return
        
        try:
            presence_data = {
                "state": data.get("state", "In menu"),
                "details": data.get("details", "--") if data.get("details") != "" else "--",
            }
            
            if "startTimestamp" in data:
                presence_data["start"] = data["startTimestamp"] / 1000 
            
            if "largeImageKey" in data:
                presence_data["large_image"] = data["largeImageKey"]
            if "largeImageText" in data:
                presence_data["large_text"] = data["largeImageText"]
            if "smallImageKey" in data:
                presence_data["small_image"] = data["smallImageKey"]
            if "smallImageText" in data:
                presence_data["small_text"] = data["smallImageText"]
                
            self.rpc.update(**presence_data)
            self.logger.info('Updated Discord RPC')
        except Exception as e:
            self.logger.error(f'Failed to update Discord RPC: {e}')
            self.rpc = None # Trigger reconnect on next update

    def run(self):
        self.start_rpc()
        self.logger.info(f"Starting SocketIO server on port {self.port}")
        eventlet.wsgi.server(eventlet.listen(('', self.port)), self.app)

if __name__ == "__main__":
    service = YouTubeDiscordRPCService(CLIENT_ID, 5432)
    service.run()
