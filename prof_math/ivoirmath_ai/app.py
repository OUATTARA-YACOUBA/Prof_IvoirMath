# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import logging

app = Flask(__name__)
CORS(app)

# Configuration Flask pour UTF-8
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'

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


class MathAIService:
    """Service pour gérer les interactions avec l'API d'IA"""
    
    @staticmethod
    def generate_prompt(user_message, level='tout'):
        """Génère le prompt pour l'IA avec restrictions de niveau hiérarchique"""
        
        # Instruction de base
        base_instruction = """Tu es un professeur de mathématiques ivoirien expert, spécialisé UNIQUEMENT dans le programme de mathématiques de Côte d'Ivoire.

RÈGLE ABSOLUE: Tu ne réponds QU'aux questions de mathématiques. Pour toute question non-mathématique (salutations basiques comme "comment tu vas", "bonjour", discussions générales, etc.), tu dois REFUSER POLIMENT.

Pour les salutations simples ("bonjour", "salut", "comment ça va"), réponds brièvement et redirige vers les mathématiques:
"Bonjour ! Je suis là pour vous aider en mathématiques. Quelle est votre question ?"

Pour toute autre question hors mathématiques, réponds UNIQUEMENT:
"Je suis un assistant spécialisé en mathématiques du programme ivoirien. Je ne peux vous aider qu'avec des questions de mathématiques. Posez-moi une question sur un chapitre du programme !"

RÈGLES STRICTES POUR LES FORMULES MATHÉMATIQUES:
1. Utilise TOUJOURS la notation LaTeX pour les formules:
   - Formules en ligne: \\( formule \\)
   - Formules en bloc: \\[ formule \\]
   
2. Exemples LaTeX:
   - Fractions: \\( \\frac{a}{b} \\)
   - Puissances: \\( x^2 \\), \\( 2^n \\)
   - Racines: \\( \\sqrt{x} \\)
   - Intégrales: \\( \\int_0^1 x^2 dx \\)
   - Symboles: \\( \\geq \\), \\( \\leq \\), \\( \\forall \\), \\( \\in \\)
"""
        
        # Instructions spécifiques selon le niveau avec hiérarchie
        if level == 'tout':
            level_instruction = f"""
NIVEAU SÉLECTIONNÉ: {PROGRAMMES['tout']['name']}
Tu peux répondre à TOUTES les questions de mathématiques du programme ivoirien {PROGRAMMES['tout']['description']}.
L'université n'est PAS incluse.
"""
        else:
            # Récupérer les niveaux autorisés (hiérarchie)
            allowed_levels = LEVEL_HIERARCHY.get(level, [level])
            programmes_inclus = []
            all_chapitres = []
            
            for lvl in allowed_levels:
                if lvl in PROGRAMMES and 'chapitres' in PROGRAMMES[lvl]:
                    programmes_inclus.append(f"{PROGRAMMES[lvl]['name']} ({PROGRAMMES[lvl]['description']})")
                    all_chapitres.extend(PROGRAMMES[lvl]['chapitres'])
            
            programmes_text = '\n'.join([f"   • {p}" for p in programmes_inclus])
            chapitres_text = '\n'.join([f"   - {ch}" for ch in all_chapitres])
            
            # Déterminer les niveaux supérieurs interdits
            niveau_superieur = ""
            if level == 'primaire':
                niveau_superieur = "premier cycle, second cycle ou université"
            elif level == 'premier':
                niveau_superieur = "second cycle ou université"
            elif level == 'second':
                niveau_superieur = "université"
            
            level_instruction = f"""
NIVEAU SÉLECTIONNÉ: {PROGRAMMES[level]['name']}

PROGRAMMES COUVERTS (du niveau actuel et inférieurs):
{programmes_text}

TOUS LES CHAPITRES AUTORISÉS:
{chapitres_text}

RÈGLE STRICTE: 
✓ Tu peux répondre aux questions de mathématiques de TOUS ces chapitres (niveau actuel + niveaux inférieurs).
✗ Tu ne peux PAS répondre aux questions de mathématiques du {niveau_superieur}.

Si la question de mathématiques dépasse ces niveaux, réponds UNIQUEMENT:
"Cette question de mathématiques dépasse le programme autorisé ({PROGRAMMES[level]['name']} et niveaux inférieurs). Pour aborder ce sujet, veuillez sélectionner un niveau supérieur ou 'Tout le programme'."
"""
        
        # Instruction finale
        final_instruction = """
STRUCTURE DE RÉPONSE (pour questions mathématiques valides):
1. Introduction claire
2. Explications étape par étape avec formules LaTeX
3. Exemples concrets adaptés au niveau
4. Conclusion/résumé

Sois pédagogique, clair et précis.
RAPPEL: Ne réponds qu'aux questions de mathématiques !
"""
        
        full_prompt = f"""{base_instruction}
{level_instruction}
{final_instruction}

Question de l'élève: {user_message}
"""
        
        return full_prompt
    
    @staticmethod
    def call_ai_api(prompt):
        """Appelle l'API OpenRouter et retourne la réponse"""
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json; charset=utf-8",
        }
        
        data = {
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 2000,
            "top_p": 0.9
        }
        
        try:
            response = requests.post(
                API_URL,
                headers=headers,
                json=data,
                timeout=30
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
        "version": "2.0.0",
        "model": MODEL,
        "niveaux_disponibles": list(PROGRAMMES.keys())
    })


@app.route("/api/chat", methods=["POST"])
def chat():
    """Endpoint principal pour les requêtes de chat"""
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
        
        # Génération du prompt avec niveau
        logger.info(f"Question reçue (niveau: {level}): {user_message[:100]}...")
        prompt = MathAIService.generate_prompt(user_message, level)
        
        # Appel à l'API
        ai_response = MathAIService.call_ai_api(prompt)
        
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
    logger.info("🚀 Démarrage de IvoirMath AI...")
    logger.info(f"📚 Modèle: {MODEL}")
    logger.info("📋 Niveaux disponibles: " + ", ".join(PROGRAMMES.keys()))
    logger.info("🌐 Serveur disponible sur: http://localhost:5050")
    app.run(host="0.0.0.0", port=5050, debug=True)