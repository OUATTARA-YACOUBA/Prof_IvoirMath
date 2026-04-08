# -*- coding: utf-8 -*-
import os
import uuid
import bcrypt

# ─────────────────────────────────────────────
# Détection automatique : PostgreSQL (Render) ou SQLite (local)
# Render injecte automatiquement DATABASE_URL dans les variables d'environnement
# ─────────────────────────────────────────────
DATABASE_URL = os.environ.get('DATABASE_URL', '')

if DATABASE_URL:
    # PostgreSQL — Render.com
    # psycopg2 convertit postgres:// en postgresql://
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    USE_POSTGRES = True
    import psycopg2
    import psycopg2.extras
else:
    # SQLite — développement local
    USE_POSTGRES = False
    import sqlite3
    DATABASE_PATH = 'ivoirmath.db'


# ─────────────────────────────────────────────
# CONNEXION
# ─────────────────────────────────────────────

class Database:

    @staticmethod
    def get_connection():
        if USE_POSTGRES:
            conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
            return conn
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            conn.row_factory = sqlite3.Row
            return conn

    @staticmethod
    def init_database():
        conn = Database.get_connection()
        cursor = conn.cursor()

        if USE_POSTGRES:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    title TEXT NOT NULL DEFAULT 'Nouvelle conversation',
                    level TEXT NOT NULL DEFAULT 'tout',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conversation_id)')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
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
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conversation_id)')

        conn.commit()
        conn.close()


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _ph(n):
    """Placeholder : %s pour PostgreSQL, ? pour SQLite"""
    return '%s' if USE_POSTGRES else '?'

def _row(row):
    """Convertit une ligne en dict (compatible SQLite Row et psycopg2 RealDictRow)"""
    if row is None:
        return None
    return dict(row)


# ─────────────────────────────────────────────
# UTILISATEURS
# ─────────────────────────────────────────────

class UserManager:

    @staticmethod
    def hash_password(password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def verify_password(password, password_hash):
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

    @staticmethod
    def create_user(username, password):
        conn = Database.get_connection()
        cursor = conn.cursor()
        ph = _ph(0)
        try:
            password_hash = UserManager.hash_password(password)
            cursor.execute(
                f'INSERT INTO users (username, password_hash) VALUES ({ph}, {ph})',
                (username, password_hash)
            )
            conn.commit()
            if USE_POSTGRES:
                cursor.execute(f'SELECT id FROM users WHERE username = {ph}', (username,))
                user_id = _row(cursor.fetchone())['id']
            else:
                user_id = cursor.lastrowid
            conn.close()
            return {"success": True, "user_id": user_id}
        except Exception as e:
            conn.close()
            if 'unique' in str(e).lower() or 'UNIQUE' in str(e):
                return {"success": False, "error": "Ce nom d'utilisateur est déjà pris."}
            return {"success": False, "error": "Erreur lors de la création du compte."}

    @staticmethod
    def authenticate(username, password):
        conn = Database.get_connection()
        cursor = conn.cursor()
        ph = _ph(0)
        cursor.execute(
            f'SELECT id, password_hash FROM users WHERE username = {ph}',
            (username,)
        )
        user = _row(cursor.fetchone())
        conn.close()
        if user and UserManager.verify_password(password, user['password_hash']):
            return {"success": True, "user_id": user['id'], "username": username}
        return {"success": False, "error": "Nom d'utilisateur ou mot de passe incorrect."}


# ─────────────────────────────────────────────
# CONVERSATIONS
# ─────────────────────────────────────────────

class ConversationManager:

    @staticmethod
    def generate_conversation_id():
        return f"chat_{uuid.uuid4().hex[:12]}"

    @staticmethod
    def create_conversation(user_id, level='tout'):
        conv_id = ConversationManager.generate_conversation_id()
        conn = Database.get_connection()
        cursor = conn.cursor()
        ph = _ph(0)
        cursor.execute(
            f'INSERT INTO conversations (id, user_id, level) VALUES ({ph}, {ph}, {ph})',
            (conv_id, user_id, level)
        )
        conn.commit()
        conn.close()
        return conv_id

    @staticmethod
    def get_user_conversations(user_id):
        conn = Database.get_connection()
        cursor = conn.cursor()
        ph = _ph(0)
        cursor.execute(f'''
            SELECT id, title, level, created_at, updated_at,
                   (SELECT COUNT(*) FROM messages WHERE conversation_id = conversations.id) as message_count
            FROM conversations
            WHERE user_id = {ph}
            ORDER BY updated_at DESC
        ''', (user_id,))
        conversations = [_row(r) for r in cursor.fetchall()]
        conn.close()
        return conversations

    @staticmethod
    def get_conversation(conv_id, user_id):
        conn = Database.get_connection()
        cursor = conn.cursor()
        ph = _ph(0)
        cursor.execute(
            f'SELECT * FROM conversations WHERE id = {ph} AND user_id = {ph}',
            (conv_id, user_id)
        )
        conversation = _row(cursor.fetchone())
        if not conversation:
            conn.close()
            return None
        cursor.execute(
            f'SELECT role, content, timestamp FROM messages WHERE conversation_id = {ph} ORDER BY timestamp ASC',
            (conv_id,)
        )
        messages = [_row(r) for r in cursor.fetchall()]
        conn.close()
        return {"conversation": conversation, "messages": messages}

    @staticmethod
    def add_message(conv_id, user_id, role, content):
        # Sécurité : contenu jamais vide
        if not content or not content.strip():
            content = "..."
        conn = Database.get_connection()
        cursor = conn.cursor()
        ph = _ph(0)
        cursor.execute(
            f'SELECT id, title FROM conversations WHERE id = {ph} AND user_id = {ph}',
            (conv_id, user_id)
        )
        conversation = _row(cursor.fetchone())
        if not conversation:
            conn.close()
            return {"success": False, "error": "Conversation non trouvée"}

        cursor.execute(
            f'INSERT INTO messages (conversation_id, role, content) VALUES ({ph}, {ph}, {ph})',
            (conv_id, role, content)
        )
        cursor.execute(
            f'UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = {ph}',
            (conv_id,)
        )
        if role == 'user' and conversation['title'] == 'Nouvelle conversation':
            title = content[:47] + '...' if len(content) > 50 else content
            cursor.execute(
                f'UPDATE conversations SET title = {ph} WHERE id = {ph}',
                (title, conv_id)
            )
        conn.commit()
        conn.close()
        return {"success": True}

    @staticmethod
    def delete_conversation(conv_id, user_id):
        conn = Database.get_connection()
        cursor = conn.cursor()
        ph = _ph(0)
        cursor.execute(
            f'DELETE FROM conversations WHERE id = {ph} AND user_id = {ph}',
            (conv_id, user_id)
        )
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return {"success": deleted}

    @staticmethod
    def get_conversation_messages(conv_id, user_id):
        conn = Database.get_connection()
        cursor = conn.cursor()
        ph = _ph(0)
        cursor.execute(
            f'SELECT level FROM conversations WHERE id = {ph} AND user_id = {ph}',
            (conv_id, user_id)
        )
        conversation = _row(cursor.fetchone())
        if not conversation:
            conn.close()
            return None
        cursor.execute(
            f'SELECT role, content FROM messages WHERE conversation_id = {ph} ORDER BY timestamp ASC',
            (conv_id,)
        )
        messages = [{"role": r['role'], "content": r['content']} for r in cursor.fetchall()]
        conn.close()
        return {"level": conversation['level'], "messages": messages}


# Init au démarrage
Database.init_database()