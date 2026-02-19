"""
Gestionnaire de connexions WebSocket
"""
import asyncio
from typing import List, Dict
from fastapi import WebSocket
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class ConnectionManager:
    """
    Gère les connexions WebSocket multiples
    Broadcast des messages à tous les clients
    """
    
    def __init__(self):
        """Initialise le gestionnaire"""
        self.active_connections: List[WebSocket] = []
        self.client_info: Dict[WebSocket, dict] = {}
        self.logger = setup_logger(__name__)
    
    async def connect(self, websocket: WebSocket, client_id: str = None):
        """
        Accepte une nouvelle connexion
        
        Args:
            websocket: WebSocket client
            client_id: ID client (optionnel)
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Stockage info client
        self.client_info[websocket] = {
            "client_id": client_id or f"client_{len(self.active_connections)}",
            "connected_at": asyncio.get_event_loop().time()
        }
        
        self.logger.info(f"✅ Client connecté : {self.client_info[websocket]['client_id']} (total: {len(self.active_connections)})")
    
    def disconnect(self, websocket: WebSocket):
        """
        Déconnecte un client
        
        Args:
            websocket: WebSocket à déconnecter
        """
        if websocket in self.active_connections:
            client_id = self.client_info.get(websocket, {}).get("client_id", "unknown")
            self.active_connections.remove(websocket)
            
            if websocket in self.client_info:
                del self.client_info[websocket]
            
            self.logger.info(f"❌ Client déconnecté : {client_id} (restants: {len(self.active_connections)})")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """
        Envoie un message à un client spécifique
        
        Args:
            message: Message à envoyer (dict → JSON)
            websocket: WebSocket destinataire
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            self.logger.error(f"❌ Erreur envoi message : {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: dict, exclude: WebSocket = None):
        """
        Broadcast un message à tous les clients connectés
        
        Args:
            message: Message à broadcaster (dict → JSON)
            exclude: WebSocket à exclure (optionnel)
        """
        disconnected = []
        
        for connection in self.active_connections:
            if connection == exclude:
                continue
            
            try:
                await connection.send_json(message)
            except Exception as e:
                self.logger.error(f"❌ Erreur broadcast : {e}")
                disconnected.append(connection)
        
        # Nettoyage connexions mortes
        for conn in disconnected:
            self.disconnect(conn)
    
    def get_connected_count(self) -> int:
        """Nombre de clients connectés"""
        return len(self.active_connections)
    
    def get_client_info(self, websocket: WebSocket) -> dict:
        """Info sur un client spécifique"""
        return self.client_info.get(websocket, {})


# Instance globale (singleton)
_connection_manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    """
    Factory pour obtenir l'instance du manager
    """
    return _connection_manager