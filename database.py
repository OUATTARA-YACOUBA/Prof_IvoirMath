# -*- coding: utf-8 -*-
import sqlite3
from datetime import datetime
import bcrypt
import json

DATABASE_PATH = 'ivoirmath.db'

class Database:
    """Gestionnaire de base de données SQLite"""
    
    @staticmethod
    def get_connection():
        """Crée une connexion à la base de données"""
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row  # Permet d'accéder aux colonnes par nom
        return conn
    
    @staticmethod
    def init_database():
        """Initialise les tables de la base de données"""
        conn = Database.get_connection()
        cursor = conn.cursor()
        
        # Table Users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table Conversations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL DEFAULT 'Nouvelle conversation',
                level TEXT NOT NULL DEFAULT 'tout',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Table Messages
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            )
        ''')
        
        # Index pour améliorer les performances
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id)')
        
        conn.commit()
        conn.close()


class UserManager:
    """Gestionnaire des utilisateurs"""
    
    @staticmethod
    def hash_password(password):
        """Hash un mot de passe avec bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_password(password, password_hash):
        """Vérifie un mot de passe"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    @staticmethod
    def create_user(username, password):
        """Crée un nouveau utilisateur"""
        conn = Database.get_connection()
        cursor = conn.cursor()
        
        try:
            password_hash = UserManager.hash_password(password)
            cursor.execute(
                'INSERT INTO users (username, password_hash) VALUES (?, ?)',
                (username, password_hash)
            )
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return {"success": True, "user_id": user_id}
        except sqlite3.IntegrityError:
            conn.close()
            return {"success": False, "error": "Nom d'utilisateur déjà utilisé"}
    
    @staticmethod
    def authenticate(username, password):
        """Authentifie un utilisateur"""
        conn = Database.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and UserManager.verify_password(password, user['password_hash']):
            return {"success": True, "user_id": user['id'], "username": username}
        return {"success": False, "error": "Identifiants incorrects"}
    
    @staticmethod
    def get_user_by_id(user_id):
        """Récupère un utilisateur par son ID"""
        conn = Database.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, username, created_at FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        return dict(user) if user else None


class ConversationManager:
    """Gestionnaire des conversations"""
    
    @staticmethod
    def generate_conversation_id():
        """Génère un ID unique pour une conversation"""
        import uuid
        return f"chat_{uuid.uuid4().hex[:12]}"
    
    @staticmethod
    def create_conversation(user_id, level='tout'):
        """Crée une nouvelle conversation"""
        conv_id = ConversationManager.generate_conversation_id()
        conn = Database.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT INTO conversations (id, user_id, level) VALUES (?, ?, ?)',
            (conv_id, user_id, level)
        )
        conn.commit()
        conn.close()
        
        return conv_id
    
    @staticmethod
    def get_user_conversations(user_id):
        """Récupère toutes les conversations d'un utilisateur"""
        conn = Database.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, level, created_at, updated_at,
                   (SELECT COUNT(*) FROM messages WHERE conversation_id = conversations.id) as message_count
            FROM conversations
            WHERE user_id = ?
            ORDER BY updated_at DESC
        ''', (user_id,))
        
        conversations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return conversations
    
    @staticmethod
    def get_conversation(conv_id, user_id):
        """Récupère une conversation spécifique"""
        conn = Database.get_connection()
        cursor = conn.cursor()
        
        # Vérifier que la conversation appartient à l'utilisateur
        cursor.execute(
            'SELECT * FROM conversations WHERE id = ? AND user_id = ?',
            (conv_id, user_id)
        )
        conversation = cursor.fetchone()
        
        if not conversation:
            conn.close()
            return None
        
        # Récupérer les messages
        cursor.execute(
            'SELECT role, content, timestamp FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC',
            (conv_id,)
        )
        messages = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            "conversation": dict(conversation),
            "messages": messages
        }
    
    @staticmethod
    def add_message(conv_id, user_id, role, content):
        """Ajoute un message à une conversation"""
        conn = Database.get_connection()
        cursor = conn.cursor()
        
        # Vérifier que la conversation appartient à l'utilisateur
        cursor.execute(
            'SELECT id, title FROM conversations WHERE id = ? AND user_id = ?',
            (conv_id, user_id)
        )
        conversation = cursor.fetchone()
        
        if not conversation:
            conn.close()
            return {"success": False, "error": "Conversation non trouvée"}
        
        # Ajouter le message
        cursor.execute(
            'INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)',
            (conv_id, role, content)
        )
        
        # Mettre à jour le timestamp de la conversation
        cursor.execute(
            'UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (conv_id,)
        )
        
        # Si c'est le premier message utilisateur, mettre à jour le titre
        if role == 'user' and conversation['title'] == 'Nouvelle conversation':
            # Générer un titre à partir du message (max 50 caractères)
            title = content[:47] + '...' if len(content) > 50 else content
            cursor.execute(
                'UPDATE conversations SET title = ? WHERE id = ?',
                (title, conv_id)
            )
        
        conn.commit()
        conn.close()
        
        return {"success": True}
    
    @staticmethod
    def delete_conversation(conv_id, user_id):
        """Supprime une conversation"""
        conn = Database.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'DELETE FROM conversations WHERE id = ? AND user_id = ?',
            (conv_id, user_id)
        )
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return {"success": deleted}
    
    @staticmethod
    def get_conversation_messages(conv_id, user_id):
        """Récupère l'historique des messages pour l'API"""
        conn = Database.get_connection()
        cursor = conn.cursor()
        
        # Vérifier que la conversation appartient à l'utilisateur
        cursor.execute(
            'SELECT level FROM conversations WHERE id = ? AND user_id = ?',
            (conv_id, user_id)
        )
        conversation = cursor.fetchone()
        
        if not conversation:
            conn.close()
            return None
        
        # Récupérer les messages
        cursor.execute(
            'SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC',
            (conv_id,)
        )
        messages = [{"role": row['role'], "content": row['content']} for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            "level": conversation['level'],
            "messages": messages
        }


# Initialiser la base de données au démarrage
Database.init_database()