# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
import requests
import logging
import secrets
from database import Database, UserManager, ConversationManager

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Configuration Flask
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 heures

# Configuration API

API_KEY = "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"
#MODEL = "mistralai/mistral-7b-instruct"
MODEL = "openrouter/free"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialiser la base de données
Database.init_database()

# Définition des programmes par niveau
LEVEL_HIERARCHY = {
    'tout': ['primaire', 'premier', 'second'],
    'primaire': ['primaire'],
    'premier': ['primaire', 'premier'],
    'second': ['primaire', 'premier', 'second']
}

PROGRAMMES = {
    'tout': {
        'name': 'Tout le programme ivoirien',
        'description': 'du primaire au lycée (hors université)'
    },
    'primaire': {
        'name': 'Primaire',
        'description': 'CP, CE1, CE2, CM1, CM2'
    },
    'premier': {
        'name': 'Premier cycle',
        'description': '6ème, 5ème, 4ème, 3ème'
    },
    'second': {
        'name': 'Second cycle',
        'description': 'Seconde, Première, Terminale (A, C, D)'
    }
}


def require_auth(f):
    """Décorateur pour vérifier l'authentification"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Non authentifié"}), 401
        return f(*args, **kwargs)
    return decorated_function


class MathAIService:
    """Service pour gérer les interactions avec l'API d'IA"""
    
    @staticmethod
    def generate_system_prompt(level='tout'):
        """Génère le prompt système basé sur le niveau"""
        
        base_instruction = """Tu es un professeur de mathématiques ivoirien expert, spécialisé UNIQUEMENT dans le programme de mathématiques de Côte d'Ivoire.

PERSONNALITÉ:
- Pédagogue, patient et encourageant
- Adapte ton langage au niveau de l'élève
- Suis la conversation et référence les échanges précédents
- Peux demander des clarifications

RÈGLES ABSOLUES:
- Tu ne réponds QU'aux questions de mathématiques du programme ivoirien
- Pour les salutations, réponds chaleureusement et propose ton aide
- Pour les questions hors mathématiques, redirige poliment
- L'UNIVERSITÉ N'EST PAS DANS TON PROGRAMME

FORMULES MATHÉMATIQUES (OBLIGATOIRE - TRÈS IMPORTANT):
1. TOUJOURS utiliser la notation LaTeX avec doubles backslashes
2. Formules en ligne: \\( formule \\) 
3. Formules en bloc (centrées): \\[ formule \\]
4. JAMAIS de formules sans LaTeX

EXEMPLES CORRECTS:
- Fraction: \\( \\frac{a}{b} \\)
- Puissance: \\( x^2 \\) ou \\( a^n \\)
- Racine: \\( \\sqrt{x} \\) ou \\( \\sqrt[n]{x} \\)
- Intégrale: \\( \\int_a^b f(x) dx \\)
- Logarithme: \\( \\ln(x) \\) ou \\( \\log(x) \\)
- Exponentielle: \\( e^x \\) ou \\( a^x \\)
- Symboles: \\( \\geq \\), \\( \\leq \\), \\( \\in \\), \\( \\forall \\)
- Multiplication: \\( x \\times y \\) ou \\( xy \\)
- Division: \\( \\frac{x}{y} \\) ou \\( x \\div y \\)

EXEMPLES INCORRECTS (NE JAMAIS FAIRE):
❌ log(x) sans LaTeX
❌ x^2 sans LaTeX
❌ 1/x sans LaTeX
❌ x * y sans LaTeX

EXEMPLE DE RÉPONSE BIEN FORMATÉE:
"Pour résoudre l'équation \\( x^2 = 4 \\), nous prenons la racine carrée des deux côtés:
\\[ x = \\pm \\sqrt{4} = \\pm 2 \\]
Donc les solutions sont \\( x = 2 \\) ou \\( x = -2 \\)."
"""
        
        # Instructions spécifiques par niveau avec RESTRICTIONS STRICTES
        if level == 'tout':
            level_instruction = f"""
NIVEAU: {PROGRAMMES['tout']['name']} - {PROGRAMMES['tout']['description']}
Tu couvres TOUT le programme du primaire au lycée (CP à Terminale).
L'UNIVERSITÉ EST EXCLUE.
"""
        
        elif level == 'primaire':
            level_instruction = f"""
NIVEAU: {PROGRAMMES['primaire']['name']} UNIQUEMENT - {PROGRAMMES['primaire']['description']}

CHAPITRES AUTORISÉS (ET UNIQUEMENT CEUX-LÀ):
- Addition et soustraction (nombres entiers et décimaux)
- Multiplication et division (tables, calculs simples)
- Mesures de longueur (mètre, centimètre, kilomètre)
- Temps et durée (heures, minutes, secondes)
- Monnaie (francs CFA, calculs simples)
- Formes géométriques simples (carré, rectangle, triangle, cercle)
- Nombres décimaux (lecture, écriture, comparaison)
- Tableaux et graphiques simples

STRICTEMENT INTERDIT:
❌ Équations algébriques
❌ Fonctions
❌ Dérivées
❌ Intégrales
❌ Logarithmes
❌ Exponentielles
❌ Nombres complexes
❌ Trigonométrie avancée
❌ Probabilités avancées
❌ Tout ce qui dépasse le primaire

Si une question dépasse ce niveau, réponds EXACTEMENT:
"Cette notion (nom de la notion) fait partie du programme du premier cycle ou du second cycle. En primaire, nous n'étudions pas encore ce sujet. Sélectionnez 'Premier cycle' ou 'Second cycle' pour aborder cette question."
"""
        
        elif level == 'premier':
            level_instruction = f"""
NIVEAU: {PROGRAMMES['premier']['name']} - {PROGRAMMES['premier']['description']}
INCLUT AUSSI: Tout le programme du primaire

CHAPITRES AUTORISÉS:
- Tout le primaire (addition, soustraction, multiplication, division, etc.)
- Nombres relatifs (positifs, négatifs, opérations)
- Fractions et nombres décimaux (opérations)
- Géométrie plane (triangles, quadrilatères, cercles)
- Périmètres et aires (formules de base)
- Volumes et solides (cube, pavé, cylindre, sphère)
- Proportionnalité (règle de trois, pourcentages)
- Équations du 1er degré (ax + b = c)
- Statistiques descriptives (moyenne, médiane, mode)
- Théorème de Pythagore (a² + b² = c²)
- Systèmes d'équations simples (2 équations, 2 inconnues)

STRICTEMENT INTERDIT:
❌ Équations du 2nd degré (ax² + bx + c = 0)
❌ Fonctions (notion de fonction f(x))
❌ Dérivées
❌ Intégrales
❌ Logarithmes
❌ Exponentielles
❌ Nombres complexes
❌ Limites
❌ Suites (sauf suites simples)
❌ Trigonométrie avancée (sinus, cosinus au-delà du cercle)
❌ Probabilités avancées

Si une question dépasse ce niveau, réponds EXACTEMENT:
"Cette notion (nom de la notion) fait partie du programme du second cycle (2nde, 1ère, Tle). Sélectionnez 'Second cycle' ou 'Tout le programme' pour aborder cette question."
"""
        
        elif level == 'second':
            level_instruction = f"""
NIVEAU: {PROGRAMMES['second']['name']} - {PROGRAMMES['second']['description']}
INCLUT AUSSI: Tout le primaire ET le premier cycle

CHAPITRES AUTORISÉS:
- Tout le primaire et premier cycle
- Équations du 2nd degré (ax² + bx + c = 0, discriminant)
- Fonctions numériques (domaine, image, variations)
- Dérivées et études de fonctions (dérivée, tangente, extremums)
- Primitives et intégrales (calcul d'aires, primitives)
- Suites numériques (arithmétiques, géométriques, récurrence)
- Probabilités (loi binomiale, espérance, variance)
- Géométrie analytique (équations de droites, cercles)
- Vecteurs et barycentres (opérations, colinéarité)
- Trigonométrie (cercle trigonométrique, équations)
- Limites de fonctions (limite finie, infinie, asymptotes)
- Nombres complexes (Terminale C et D uniquement: forme algébrique, module, argument)
- Logarithme népérien (ln(x), propriétés)
- Exponentielle (e^x, propriétés)

STRICTEMENT INTERDIT:
❌ Mathématiques de l'enseignement supérieur
❌ Analyse complexe avancée
❌ Topologie
❌ Algèbre linéaire avancée
❌ Équations différentielles avancées
❌ Analyse fonctionnelle
❌ Tout ce qui dépasse le lycée

Si une question dépasse ce niveau, réponds EXACTEMENT:
"Cette notion fait partie des mathématiques de l'enseignement supérieur (université). Mon programme s'arrête au niveau du lycée (Terminale). Je ne peux pas traiter ce sujet."
"""
        
        return base_instruction + "\n" + level_instruction
    
    @staticmethod
    def call_ai_api(messages, level='tout'):
        """Appelle l'API avec l'historique"""
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json; charset=utf-8",
        }
        
        system_prompt = MathAIService.generate_system_prompt(level)
        api_messages = [{"role": "system", "content": system_prompt}] + messages
        
        data = {
            "model": MODEL,
            "messages": api_messages,
            "temperature": 0.5,  # Réduit pour plus de précision
            "max_tokens": 2500,  # Augmenté pour réponses complètes
            "top_p": 0.85,       # Réduit pour éviter la divagation
            "frequency_penalty": 0.3,  # Évite les répétitions
            "presence_penalty": 0.2    # Encourage la diversité
        }
        
        try:
            response = requests.post(API_URL, headers=headers, json=data, timeout=60)
            response.encoding = 'utf-8'
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            raise Exception("La requête a pris trop de temps")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erreur API: {str(e)}")


# ==================== ROUTES D'AUTHENTIFICATION ====================

@app.route("/api/auth/register", methods=["POST"])
def register():
    """Inscription d'un nouvel utilisateur"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({"error": "Nom d'utilisateur et mot de passe requis"}), 400
        
        if len(username) < 3:
            return jsonify({"error": "Le nom d'utilisateur doit contenir au moins 3 caractères"}), 400
        
        if len(password) < 6:
            return jsonify({"error": "Le mot de passe doit contenir au moins 6 caractères"}), 400
        
        result = UserManager.create_user(username, password)
        
        if result['success']:
            session['user_id'] = result['user_id']
            session['username'] = username
            session.permanent = True
            logger.info(f"Nouvel utilisateur inscrit: {username}")
            return jsonify({"success": True, "username": username})
        else:
            return jsonify({"error": result['error']}), 400
    
    except Exception as e:
        logger.error(f"Erreur lors de l'inscription: {str(e)}")
        return jsonify({"error": "Erreur lors de l'inscription"}), 500


@app.route("/api/auth/login", methods=["POST"])
def login():
    """Connexion d'un utilisateur"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({"error": "Nom d'utilisateur et mot de passe requis"}), 400
        
        result = UserManager.authenticate(username, password)
        
        if result['success']:
            session['user_id'] = result['user_id']
            session['username'] = result['username']
            session.permanent = True
            logger.info(f"Utilisateur connecté: {username}")
            return jsonify({"success": True, "username": username})
        else:
            return jsonify({"error": result['error']}), 401
    
    except Exception as e:
        logger.error(f"Erreur lors de la connexion: {str(e)}")
        return jsonify({"error": "Erreur lors de la connexion"}), 500


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    """Déconnexion de l'utilisateur"""
    username = session.get('username', 'Inconnu')
    session.clear()
    logger.info(f"Utilisateur déconnecté: {username}")
    return jsonify({"success": True})


@app.route("/api/auth/status", methods=["GET"])
def auth_status():
    """Vérifie si l'utilisateur est connecté"""
    if 'user_id' in session:
        return jsonify({
            "authenticated": True,
            "username": session.get('username')
        })
    return jsonify({"authenticated": False})


# ==================== ROUTES DE GESTION DES CONVERSATIONS ====================

@app.route("/api/conversations", methods=["GET"])
@require_auth
def get_conversations():
    """Récupère toutes les conversations de l'utilisateur"""
    try:
        user_id = session['user_id']
        conversations = ConversationManager.get_user_conversations(user_id)
        return jsonify({"conversations": conversations})
    except Exception as e:
        logger.error(f"Erreur récupération conversations: {str(e)}")
        return jsonify({"error": "Erreur lors de la récupération"}), 500


@app.route("/api/conversations/new", methods=["POST"])
@require_auth
def create_conversation():
    """Crée une nouvelle conversation"""
    try:
        user_id = session['user_id']
        level = request.json.get('level', 'tout') if request.json else 'tout'
        
        if level not in PROGRAMMES:
            level = 'tout'
        
        conv_id = ConversationManager.create_conversation(user_id, level)
        logger.info(f"Nouvelle conversation créée: {conv_id} pour user {user_id}")
        
        return jsonify({"success": True, "conversation_id": conv_id})
    except Exception as e:
        logger.error(f"Erreur création conversation: {str(e)}")
        return jsonify({"error": "Erreur lors de la création"}), 500


@app.route("/api/conversations/<conv_id>", methods=["GET"])
@require_auth
def get_conversation(conv_id):
    """Récupère une conversation spécifique"""
    try:
        user_id = session['user_id']
        conversation = ConversationManager.get_conversation(conv_id, user_id)
        
        if not conversation:
            return jsonify({"error": "Conversation non trouvée"}), 404
        
        return jsonify(conversation)
    except Exception as e:
        logger.error(f"Erreur récupération conversation: {str(e)}")
        return jsonify({"error": "Erreur lors de la récupération"}), 500


@app.route("/api/conversations/<conv_id>", methods=["DELETE"])
@require_auth
def delete_conversation(conv_id):
    """Supprime une conversation"""
    try:
        user_id = session['user_id']
        result = ConversationManager.delete_conversation(conv_id, user_id)
        
        if result['success']:
            logger.info(f"Conversation supprimée: {conv_id}")
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Conversation non trouvée"}), 404
    except Exception as e:
        logger.error(f"Erreur suppression conversation: {str(e)}")
        return jsonify({"error": "Erreur lors de la suppression"}), 500


@app.route("/api/conversations/<conv_id>/message", methods=["POST"])
@require_auth
def send_message(conv_id):
    """Envoie un message dans une conversation"""
    try:
        user_id = session['user_id']
        data = request.json
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({"error": "Message vide"}), 400
        
        # Récupérer l'historique de la conversation
        conv_data = ConversationManager.get_conversation_messages(conv_id, user_id)
        
        if not conv_data:
            return jsonify({"error": "Conversation non trouvée"}), 404
        
        # Ajouter le message utilisateur à la BDD
        ConversationManager.add_message(conv_id, user_id, 'user', user_message)
        
        # Préparer les messages pour l'API
        messages = conv_data['messages'] + [{"role": "user", "content": user_message}]
        
        # Appeler l'IA
        ai_response = MathAIService.call_ai_api(messages, conv_data['level'])
        
        if ai_response and 'choices' in ai_response:
            ai_message = ai_response['choices'][0]['message']['content']
            
            # Sauvegarder la réponse de l'IA
            ConversationManager.add_message(conv_id, user_id, 'assistant', ai_message)
            
            return jsonify({
                "success": True,
                "message": ai_message
            })
        else:
            return jsonify({"error": "Pas de réponse de l'IA"}), 500
    
    except Exception as e:
        logger.error(f"Erreur envoi message: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ==================== ROUTES PRINCIPALES ====================

@app.route("/")
def home():
    """Page principale"""
    return render_template("index.html")


@app.route("/api/health", methods=["GET"])
def health_check():
    """Vérification de l'état du service"""
    return jsonify({
        "status": "online",
        "service": "IvoirMath AI",
        "version": "3.0.0",
        "model": MODEL,
        "features": ["authentication", "conversations", "context_aware"]
    })


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Route non trouvée"}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Erreur 500: {str(error)}")
    return jsonify({"error": "Erreur interne du serveur"}), 500


if __name__ == "__main__":
    logger.info("🚀 Démarrage de IvoirMath AI v3.0...")
    logger.info(f"📚 Modèle: {MODEL}")
    logger.info("🔐 Authentification: Activée")
    logger.info("💾 Base de données: SQLite")
    logger.info("💬 Gestion des conversations: Activée")
    logger.info("🌐 Serveur disponible sur: http://localhost:5050")
    app.run(host="0.0.0.0", port=5050, debug=True)

# Configuration Flask pour UTF-8 et sessions
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SESSION_TYPE'] = 'filesystem'

# Configuration API
API_KEY = "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"
MODEL = "mistralai/mistral-7b-instruct"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Stockage des conversations en mémoire (par session)
conversations = {}

# Définition des programmes par niveau
LEVEL_HIERARCHY = {
    'tout': ['primaire', 'premier', 'second'],
    'primaire': ['primaire'],
    'premier': ['primaire', 'premier'],
    'second': ['primaire', 'premier', 'second']
}

PROGRAMMES = {
    'tout': {
        'name': 'Tout le programme ivoirien',
        'description': 'du primaire au lycée (hors université)'
    },
    'primaire': {
        'name': 'Primaire',
        'description': 'CP, CE1, CE2, CM1, CM2',
        'chapitres': [
            'Addition et soustraction',
            'Multiplication et division',
            'Mesures de longueur',
            'Temps et durée',
            'Monnaie et prix',
            'Formes géométriques simples',
            'Nombres décimaux',
            'Tableaux et graphiques simples'
        ]
    },
    'premier': {
        'name': 'Premier cycle',
        'description': '6ème, 5ème, 4ème, 3ème',
        'chapitres': [
            'Nombres relatifs et opérations',
            'Fractions et nombres décimaux',
            'Géométrie plane',
            'Périmètres et aires',
            'Volumes et solides',
            'Proportionnalité',
            'Équations du 1er degré',
            'Statistiques descriptives',
            'Théorème de Pythagore',
            'Systèmes d\'équations'
        ]
    },
    'second': {
        'name': 'Second cycle',
        'description': 'Seconde, Première, Terminale (A, C, D)',
        'chapitres': [
            'Équations du 2nd degré',
            'Fonctions numériques',
            'Dérivées et études de fonctions',
            'Primitives et intégrales',
            'Suites numériques',
            'Probabilités',
            'Géométrie analytique',
            'Vecteurs et barycentres',
            'Trigonométrie',
            'Limites de fonctions',
            'Nombres complexes (Tle C, D)',
            'Logarithme et exponentielle'
        ]
    }
}


class ConversationManager:
    """Gestionnaire de conversation avec historique"""
    
    @staticmethod
    def get_or_create_session():
        """Récupère ou crée un ID de session"""
        if 'session_id' not in session:
            session['session_id'] = secrets.token_hex(16)
        return session['session_id']
    
    @staticmethod
    def get_conversation_history(session_id, level):
        """Récupère l'historique de conversation"""
        key = f"{session_id}_{level}"
        if key not in conversations:
            conversations[key] = []
        return conversations[key]
    
    @staticmethod
    def add_to_history(session_id, level, user_msg, ai_msg):
        """Ajoute un échange à l'historique"""
        key = f"{session_id}_{level}"
        if key not in conversations:
            conversations[key] = []
        
        conversations[key].append({
            "role": "user",
            "content": user_msg
        })
        conversations[key].append({
            "role": "assistant",
            "content": ai_msg
        })
        
        # Limiter l'historique à 20 messages (10 échanges)
        if len(conversations[key]) > 20:
            conversations[key] = conversations[key][-20:]
    
    @staticmethod
    def clear_history(session_id, level):
        """Efface l'historique pour un niveau donné"""
        key = f"{session_id}_{level}"
        if key in conversations:
            conversations[key] = []


class MathAIService:
    """Service pour gérer les interactions avec l'API d'IA"""
    
    @staticmethod
    def generate_system_prompt(level='tout'):
        """Génère le prompt système basé sur le niveau"""
        
        base_instruction = """Tu es un professeur de mathématiques ivoirien expert, spécialisé UNIQUEMENT dans le programme de mathématiques de Côte d'Ivoire.

PERSONNALITÉ:
- Tu es pédagogue, patient et encourageant
- Tu adaptes ton langage au niveau de l'élève
- Tu peux suivre une conversation et te référer aux échanges précédents
- Tu peux répondre à des questions de suivi, demander des clarifications
- Tu peux donner des exemples supplémentaires si l'élève ne comprend pas

RÈGLES DE CONVERSATION:
- Pour les salutations ("bonjour", "salut", "comment ça va"), réponds chaleureusement et propose ton aide
- Si l'élève demande une clarification sur un concept déjà abordé, référence ta réponse précédente
- Si l'élève dit ne pas comprendre, propose une explication différente ou plus simple
- Tu peux poser des questions pour mieux comprendre les difficultés de l'élève

RÈGLES STRICTES:
- Tu ne réponds QU'aux questions de mathématiques du programme ivoirien
- Pour toute question totalement hors mathématiques (politique, actualité, etc.), redirige poliment vers les mathématiques
- L'université n'est PAS dans ton programme

FORMULES MATHÉMATIQUES (OBLIGATOIRE):
Utilise TOUJOURS la notation LaTeX:
- Formules en ligne: \\( formule \\)
- Formules en bloc: \\[ formule \\]
Exemples: \\( \\frac{a}{b} \\), \\( x^2 \\), \\( \\sqrt{x} \\), \\( \\int_0^1 x dx \\)
"""
        
        if level == 'tout':
            level_instruction = f"""
NIVEAU: {PROGRAMMES['tout']['name']} - {PROGRAMMES['tout']['description']}
Tu couvres TOUT le programme du primaire au lycée.
"""
        else:
            allowed_levels = LEVEL_HIERARCHY.get(level, [level])
            programmes_inclus = []
            all_chapitres = []
            
            for lvl in allowed_levels:
                if lvl in PROGRAMMES and 'chapitres' in PROGRAMMES[lvl]:
                    programmes_inclus.append(f"{PROGRAMMES[lvl]['name']} ({PROGRAMMES[lvl]['description']})")
                    all_chapitres.extend(PROGRAMMES[lvl]['chapitres'])
            
            programmes_text = ', '.join(programmes_inclus)
            chapitres_text = ', '.join(all_chapitres)
            
            niveau_superieur = ""
            if level == 'primaire':
                niveau_superieur = "premier cycle, second cycle ou université"
            elif level == 'premier':
                niveau_superieur = "second cycle ou université"
            elif level == 'second':
                niveau_superieur = "université"
            
            level_instruction = f"""
NIVEAU: {PROGRAMMES[level]['name']}
PROGRAMMES COUVERTS: {programmes_text}
CHAPITRES: {chapitres_text}

✓ Tu peux traiter ces chapitres et tous les niveaux inférieurs
✗ Tu ne peux PAS traiter: {niveau_superieur}

Si une question mathématique dépasse ce niveau, explique que c'est hors programme et suggère de sélectionner un niveau supérieur.
"""
        
        return base_instruction + "\n" + level_instruction
    
    @staticmethod
    def call_ai_api(messages, level='tout'):
        """Appelle l'API avec l'historique de conversation"""
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json; charset=utf-8",
        }
        
        # Construire les messages avec le système
        system_prompt = MathAIService.generate_system_prompt(level)
        
        api_messages = [
            {"role": "system", "content": system_prompt}
        ] + messages
        
        data = {
            "model": MODEL,
            "messages": api_messages,
            "temperature": 0.7,
            "max_tokens": 2000,
            "top_p": 0.9
        }
        
        try:
            response = requests.post(
                API_URL,
                headers=headers,
                json=data,
                timeout=45
            )
            response.encoding = 'utf-8'
            response.raise_for_status()
            
            result = response.json()
            logger.info("Réponse API reçue avec succès")
            return result
            
        except requests.exceptions.Timeout:
            logger.error("Timeout lors de l'appel API")
            raise Exception("La requête a pris trop de temps")
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur API: {str(e)}")
            raise


@app.route("/")
def home():
    """Route principale - Interface utilisateur"""
    return render_template("index.html")


@app.route("/api/health", methods=["GET"])
def health_check():
    """Vérification de l'état du service"""
    return jsonify({
        "status": "online",
        "service": "IvoirMath AI",
        "version": "3.0.0",
        "model": MODEL,
        "niveaux_disponibles": list(PROGRAMMES.keys()),
        "features": ["conversation_history", "context_aware"]
    })


@app.route("/api/chat", methods=["POST"])
def chat():
    """Endpoint principal pour les requêtes de chat avec historique"""
    try:
        # Validation de la requête
        if not request.json:
            logger.warning("Requête sans JSON")
            return jsonify({"error": "Requête invalide"}), 400
        
        if "message" not in request.json:
            logger.warning("Message manquant dans la requête")
            return jsonify({"error": "Message manquant"}), 400
        
        user_message = request.json.get("message", "").strip()
        level = request.json.get("level", "tout")
        
        # Validation du niveau
        if level not in PROGRAMMES:
            level = "tout"
        
        if not user_message:
            return jsonify({"error": "Le message ne peut pas être vide"}), 400
        
        if len(user_message) > 5000:
            return jsonify({"error": "Le message est trop long (max 5000 caractères)"}), 400
        
        # Récupérer ou créer la session
        session_id = ConversationManager.get_or_create_session()
        
        # Récupérer l'historique de conversation
        history = ConversationManager.get_conversation_history(session_id, level)
        
        # Ajouter le nouveau message utilisateur
        current_messages = history + [{"role": "user", "content": user_message}]
        
        logger.info(f"Question reçue (niveau: {level}, historique: {len(history)} messages): {user_message[:100]}...")
        
        # Appel à l'API avec historique
        ai_response = MathAIService.call_ai_api(current_messages, level)
        
        # Extraire la réponse
        if ai_response and 'choices' in ai_response and len(ai_response['choices']) > 0:
            ai_message = ai_response['choices'][0]['message']['content']
            
            # Ajouter à l'historique
            ConversationManager.add_to_history(session_id, level, user_message, ai_message)
            
            logger.info(f"Réponse ajoutée à l'historique (total: {len(ConversationManager.get_conversation_history(session_id, level))} messages)")
        
        # Retour de la réponse avec encodage UTF-8
        response = jsonify(ai_response)
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response
    
    except Exception as e:
        logger.error(f"Erreur dans /api/chat: {str(e)}")
        return jsonify({
            "error": "Une erreur s'est produite",
            "details": str(e)
        }), 500


@app.route("/api/clear-history", methods=["POST"])
def clear_history():
    """Efface l'historique de conversation pour un niveau"""
    try:
        level = request.json.get("level", "tout") if request.json else "tout"
        
        if 'session_id' in session:
            session_id = session['session_id']
            ConversationManager.clear_history(session_id, level)
            logger.info(f"Historique effacé pour session {session_id}, niveau {level}")
            return jsonify({"success": True, "message": "Historique effacé"})
        
        return jsonify({"success": True, "message": "Aucun historique à effacer"})
    
    except Exception as e:
        logger.error(f"Erreur lors de l'effacement de l'historique: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """Gestion des erreurs 404"""
    return jsonify({"error": "Route non trouvée"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Gestion des erreurs 500"""
    logger.error(f"Erreur 500: {str(error)}")
    return jsonify({"error": "Erreur interne du serveur"}), 500


if __name__ == "__main__":
    logger.info("🚀 Démarrage de IvoirMath AI v3.0...")
    logger.info(f"📚 Modèle: {MODEL}")
    logger.info("💬 Fonctionnalité: Conversation avec historique activée")
    logger.info("📋 Niveaux disponibles: " + ", ".join(PROGRAMMES.keys()))
    logger.info("🌐 Serveur disponible sur: http://localhost:5050")
    app.run(host="0.0.0.0", port=5050, debug=True)