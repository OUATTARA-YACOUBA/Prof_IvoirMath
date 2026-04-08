# -*- coding: utf-8 -*-
import os, re, json, secrets, logging
from flask import Flask, request, jsonify, render_template, session, Response, stream_with_context
from flask_cors import CORS
import requests
from database import Database, UserManager, ConversationManager

app = Flask(__name__)
CORS(app, supports_credentials=True)

# ══════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════
app.config['JSON_AS_ASCII']              = False
app.config['JSONIFY_MIMETYPE']           = 'application/json; charset=utf-8'
app.config['SECRET_KEY']                 = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_TYPE']               = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400

API_KEY = os.environ.get('OPENROUTER_API_KEY',
          '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')
API_URL = 'https://openrouter.ai/api/v1/chat/completions'

MODELS = [
    'meta-llama/llama-3.1-8b-instruct:free',
    'mistralai/mistral-7b-instruct:free',
    'openrouter/free',
]

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

Database.init_database()

# ══════════════════════════════════════════════
# PROGRAMME OFFICIEL IVOIRIEN — MENA
# ══════════════════════════════════════════════

CYCLES = {
    'tout':    {'name': '📚 Tout le programme', 'ordre': 99},
    'primaire':{'name': '🎒 Primaire',          'ordre': 1},
    'college': {'name': '📐 Collège',           'ordre': 2},
    'lycee':   {'name': '🎓 Lycée',             'ordre': 3},
}

CLASSES = {
    # Primaire
    'cp':     {'name': 'CP',      'cycle': 'primaire', 'ordre': 1},
    'ce1':    {'name': 'CE1',     'cycle': 'primaire', 'ordre': 2},
    'ce2':    {'name': 'CE2',     'cycle': 'primaire', 'ordre': 3},
    'cm1':    {'name': 'CM1',     'cycle': 'primaire', 'ordre': 4},
    'cm2':    {'name': 'CM2',     'cycle': 'primaire', 'ordre': 5},
    # Collège
    '6eme':   {'name': '6ème',   'cycle': 'college',  'ordre': 6},
    '5eme':   {'name': '5ème',   'cycle': 'college',  'ordre': 7},
    '4eme':   {'name': '4ème',   'cycle': 'college',  'ordre': 8},
    '3eme':   {'name': '3ème',   'cycle': 'college',  'ordre': 9},
    # Lycée série A
    '2ndeA':  {'name': '2nde A', 'cycle': 'lycee',    'ordre': 10},
    '1ereA':  {'name': '1ère A', 'cycle': 'lycee',    'ordre': 11},
    'tleA':   {'name': 'Tle A',  'cycle': 'lycee',    'ordre': 12},
    # Lycée séries C/D (2nde commune)
    '2ndeCD': {'name': '2nde C/D','cycle': 'lycee',   'ordre': 13},
    '1ereC':  {'name': '1ère C', 'cycle': 'lycee',    'ordre': 14},
    'tleC':   {'name': 'Tle C',  'cycle': 'lycee',    'ordre': 15},
    '1ereD':  {'name': '1ère D', 'cycle': 'lycee',    'ordre': 16},
    'tleD':   {'name': 'Tle D',  'cycle': 'lycee',    'ordre': 17},
}

ALL_LEVELS = set(list(CYCLES.keys()) + list(CLASSES.keys()))

PROGRAMME = {
    'cp':  [
        "Numération jusqu'à 100 : lecture, écriture, comparaison",
        "Addition et soustraction de nombres entiers ≤ 100",
        "Tables de multiplication de 2 et 5",
        "Mesures de longueur : mètre et centimètre",
        "Monnaie : pièces et billets en Francs CFA",
        "Formes géométriques : carré, rectangle, triangle, cercle",
        "Repérage dans le temps : jours, semaines, mois",
    ],
    'ce1': [
        "Numération jusqu'à 1000",
        "Addition et soustraction avec retenues",
        "Multiplication : tables de 1 à 5",
        "Division exacte par 2 et 5",
        "Mesures : kilogramme, litre, heure, minute",
        "Périmètre du carré et du rectangle",
        "Calcul mental et résolution de problèmes simples",
    ],
    'ce2': [
        "Numération jusqu'à 10 000",
        "Les quatre opérations sur les nombres entiers",
        "Tables de multiplication jusqu'à 9",
        "Fractions simples : 1/2, 1/4, 3/4",
        "Aire du carré et du rectangle",
        "Angles droits, lignes parallèles et perpendiculaires",
    ],
    'cm1': [
        "Grands nombres jusqu'à 1 000 000",
        "Fractions ordinaires et nombres décimaux",
        "Opérations sur les décimaux",
        "Proportionnalité simple",
        "Périmètre et aire des figures usuelles",
        "Axe de symétrie",
        "Tableaux et diagrammes",
    ],
    'cm2': [
        "Nombres décimaux : quatre opérations",
        "Fractions : addition, soustraction, multiplication",
        "Pourcentages simples",
        "Règle de trois",
        "Volume du cube et du pavé droit",
        "Mesure des angles au rapporteur",
        "Lecture et construction de graphiques statistiques",
    ],
    '6eme': [
        "Leçon 1 : Nombres entiers naturels",
        "Leçon 2 : Nombres décimaux relatifs",
        "Leçon 3 : Fractions",
        "Leçon 1 : Proportionnalité",
        "Leçon 2 : Statistique",
        "Leçon 1 : Droites et points",
        "Leçon 2 : Segments",
        "Leçon 3 : Cercles et disques",
        "Leçon 4 : Angles",
        "Leçon 5 : Triangles",
        "Leçon 6 : Parallélogramme",
        "Leçon : Pavés droits et cylindres droits",
        "Leçon : Figures symétriques par rapport à un point",
    ],
    '5eme': [
        "Leçon 1 : Nombres premiers",
        "Leçon 2 : Nombres décimaux relatifs",
        "Leçon 3 : Fractions",
        "Leçon 1 : Proportionnalité",
        "Leçon 2 : Statistique",
        "Leçon 1 : Segments",
        "Leçon 2 : Cercles",
        "Leçon 3 : Angles",
        "Leçon 4 : Triangles",
        "Leçon 5 : Parallélogrammes particuliers",
        "Leçon : Prisme droits",
        "Leçon : Figures symétriques par rapport à une droite",
    ],
    '4eme': [
        "Leçon 1 : Nombres décimaux relatifs",
        "Leçon 2 : Nombres rationnels",
        "Leçon 3 : Calcul littéral",
        "Leçon 4 : Équations et inéquations dans Q",
        "Leçon : Statistique",
        "Leçon 1 : Angles",
        "Leçon 2 : Distances",
        "Leçon 3 : Cercles et triangles",
        "Leçon 4 : Vecteurs",
        "Leçon : Perspective cavalière",
        "Leçon : Symétries et translations",
    ],
    '3eme': [
        "Leçon 1 : Calcul littéral",
        "Leçon 2 : Racines carrées",
        "Leçon 3 : Calcul numérique",
        "Leçon 4 : Équations et inéquations dans R",
        "Leçon 5 : Équations et inéquations dans R×R",
        "Leçon : Applications affines",
        "Leçon : Statistique",
        "Leçon 1 : Triangle rectangle",
        "Leçon 2 : Propriétés de Thalès dans un triangle",
        "Leçon 3 : Angles inscrits",
        "Leçon 4 : Vecteurs",
        "Leçon 5 : Coordonnées d'un vecteur",
        "Leçon 6 : Équations de droites",
        "Leçon : Pyramides et cônes",
    ],
    '2ndeA': [
        "Leçon 1 : Calcul numérique",
        "Leçon 2 : Calcul littéral",
        "Leçon 3 : Équations et inéquations dans R",
        "Leçon 4 : Systèmes d'équations linéaires",
        "Leçon 1 : Généralités sur les fonctions",
        "Leçon 2 : Études de fonctions élémentaires",
        "Leçon 1 : Statistique à une variable",
        "Leçon 1 : Dénombrement",
    ],
    '1ereA': [
        "Leçon 1 : Équations et inéquations",
        "Leçon 2 : Systèmes linéaires dans R×R",
        "Leçon 1 : Compléments sur les fonctions",
        "Leçon 2 : Étude de fonctions",
        "Leçon 3 : Suites numériques",
        "Leçon 1 : Statistique à une variable",
        "Leçon 1 : Dénombrement",
    ],
    'tleA': [
        "Leçon 1 : Systèmes Linéaires dans R×R",
        "Leçon 1 : Étude de fonctions polynômes et de fonctions rationnelles",
        "Leçon 2 : Fonction logarithme népérien",
        "Leçon 3 : Fonction exponentielle népérienne",
        "Leçon 4 : Primitives et Calcul intégral",
        "Leçon 5 : Suites numériques",
        "Leçon 1 : Statistique à deux variables",
        "Leçon 1 : Probabilités",
    ],
    '2ndeCD': [
        "Leçon 1 : Ensemble des nombres réels",
        "Leçon 2 : Polynômes et fractions rationnelles",
        "Leçon 3 : Équations et inéquations dans R",
        "Leçon 4 : Équations et inéquations dans R×R",
        "Leçon 1 : Généralités sur les fonctions",
        "Leçon 2 : Étude de fonctions",
        "Leçon : Statistique à une variable",
        "Leçon 1 : Vecteurs et points du plan",
        "Leçon 2 : Produit scalaire",
        "Leçon 3 : Angles inscrits",
        "Leçon 4 : Angles orientés et trigonométrie",
        "Leçon : Droites et plans de l'espace",
        "Leçon 1 : Utilisation des symétries et translations",
        "Leçon 2 : Homothéties",
        "Leçon 3 : Rotations",
    ],
    '1ereC': [
        "Leçon 1 : Équations et inéquations du second degré dans R",
        "Leçon 2 : Systèmes d'équations linéaires dans R² et dans R³",
        "Leçon 1 : Généralités sur les fonctions",
        "Leçon 2 : Limites et continuité",
        "Leçon 3 : Extension de la notion de limite",
        "Leçon 4 : Dérivation",
        "Leçon 5 : Étude et représentation graphique d'une fonction",
        "Leçon 6 : Suites numériques",
        "Leçon : Statistique à une variable",
        "Leçon 1 : Dénombrement",
        "Leçon 2 : Probabilité",
        "Leçon 1 : Géométrie analytique du plan",
        "Leçon 2 : Barycentre",
        "Leçon 3 : Angles orientés et trigonométrie",
        "Leçon 1 : Vecteurs de l'espace",
        "Leçon 3 : Orthogonalité dans l'espace",
        "Leçon : Composées de transformations",
    ],
    'tleC': [
        "Leçon : Nombres complexes",
        "Leçon 1 : Limites et continuité",
        "Leçon 2 : Dérivabilité et étude de fonctions",
        "Leçon 3 : Primitives",
        "Leçon 4 : Fonctions logarithmes",
        "Leçon 5 : Fonctions exponentielles et fonctions puissances",
        "Leçon 6 : Calcul Intégral",
        "Leçon 7 : Suites numériques",
        "Leçon 8 : Équations différentielles",
        "Leçon : Statistique à deux variables",
        "Leçon : Probabilité conditionnelle et variable aléatoire",
        "Leçon 1 : Barycentre et lignes de niveaux",
        "Leçon 2 : Coniques",
        "Leçon : Géométrie analytique dans l'espace",
        "Leçon 1 : Isométries du plan",
        "Leçon 2 : Similitudes directes du plan",
        "Leçon 3 : Nombres complexes et transformations du plan",
        "Leçon 1 : Divisibilité dans Z",
        "Leçon 2 : PPCM et PGCD de deux entiers relatifs",
    ],
    '1ereD': [
        "Leçon 1 : Équations et inéquations du second degré dans R",
        "Leçon 2 : Systèmes d'équations linéaires dans R² et dans R³",
        "Leçon 1 : Généralités sur les fonctions",
        "Leçon 2 : Limites et continuité",
        "Leçon 3 : Extension de la notion de limite",
        "Leçon 4 : Dérivation",
        "Leçon 5 : Étude et représentation graphique d'une fonction",
        "Leçon 6 : Suites numériques",
        "Leçon : Statistique à une variable",
        "Leçon 1 : Dénombrement",
        "Leçon 2 : Probabilité",
        "Leçon 1 : Barycentre",
        "Leçon 2 : Angles orientés et trigonométrie",
        "Leçon : Orthogonalité dans l'espace",
        "Leçon : Composées de transformations",
    ],
    'tleD': [
        "Leçon : Nombres complexes",
        "Leçon 1 : Limites et continuité",
        "Leçon 2 : Dérivabilité et étude de fonctions",
        "Leçon 3 : Primitives",
        "Leçon 4 : Fonctions logarithmes",
        "Leçon 5 : Fonctions exponentielles et fonctions puissances",
        "Leçon 6 : Calcul Intégral",
        "Leçon 7 : Suites numériques",
        "Leçon 8 : Équations différentielles",
        "Leçon : Statistique à deux variables",
        "Leçon : Probabilité conditionnelle et variable aléatoire",
    ],
}

# ══════════════════════════════════════════════
# UTILITAIRES NIVEAU
# ══════════════════════════════════════════════

def get_level_info(level_id):
    if level_id in CLASSES: return CLASSES[level_id]
    if level_id in CYCLES:  return {'name': CYCLES[level_id]['name'], 'cycle': level_id, 'ordre': 99}
    return {'name': 'Tout', 'cycle': 'tout', 'ordre': 99}

def get_programme_for_level(level_id):
    if level_id == 'tout': return None, None
    if level_id in CLASSES:
        ordre_max = CLASSES[level_id]['ordre']
        inclus = sorted([(k,v) for k,v in CLASSES.items() if v['ordre'] <= ordre_max],
                        key=lambda x: x[1]['ordre'])
    elif level_id in CYCLES:
        rank = {'primaire':1,'college':2,'lycee':3}
        rmax = rank.get(level_id, 3)
        inclus = sorted([(k,v) for k,v in CLASSES.items()
                         if rank.get(v['cycle'],0) <= rmax],
                        key=lambda x: x[1]['ordre'])
    else:
        return None, None
    lecons, noms = [], []
    for cid, cinfo in inclus:
        noms.append(cinfo['name'])
        lecons.extend(PROGRAMME.get(cid, []))
    return lecons, noms

def get_restriction_msg(level_id):
    info = get_level_info(level_id)
    nom  = info['name'].replace('📚 ','').replace('🎒 ','').replace('📐 ','').replace('🎓 ','')
    if level_id in CLASSES:
        ordre = CLASSES[level_id]['ordre']
        sup   = sorted([(k,v) for k,v in CLASSES.items() if v['ordre'] > ordre],
                       key=lambda x: x[1]['ordre'])
        if sup:
            return (f"Cette notion dépasse le programme de {nom}. "
                    f"Elle est au programme de {sup[0][1]['name']} ou supérieur. "
                    f"Sélectionnez un niveau supérieur dans le menu.")
    return f"Cette notion dépasse le programme de {nom}. Sélectionnez un niveau supérieur."


# ══════════════════════════════════════════════
# POST-CORRECTION LATEX
# Convertit $...$ et $$...$$ → \(...\) et \[...\]
# Supprime l'ASCII art résiduel
# ══════════════════════════════════════════════

def fix_latex(text):
    if not text:
        return text

    # 1. Supprimer les lignes d'ASCII art
    lines   = text.split('\n')
    cleaned = []
    for line in lines:
        stripped = line.strip()
        # Ligne contenant uniquement des caractères de dessin (≥4 caractères)
        if stripped and re.match(r'^[\|\/\\\*\+\-\s=_#]{4,}$', stripped):
            continue
        cleaned.append(line)
    text = '\n'.join(cleaned)

    # 2. Protéger les zones déjà en LaTeX correct \(...\) et \[...\]
    protected = []
    def protect(m):
        protected.append(m.group(0))
        return f'\x00P{len(protected)-1}\x00'

    text = re.sub(r'\\\[[\s\S]*?\\\]', protect, text)
    text = re.sub(r'\\\([\s\S]*?\\\)', protect, text)

    # 3. Convertir $$...$$ → \[...\]  (avant les $ simples)
    text = re.sub(r'\$\$([\s\S]*?)\$\$',
                  lambda m: '\\[' + m.group(1) + '\\]',
                  text, flags=re.DOTALL)

    # 4. Convertir $...$ → \(...\)
    # Exclure les prix comme $5, $20 (chiffres seuls)
    def dollar_replace(m):
        inner = m.group(1)
        if re.match(r'^\d+(\.\d+)?$', inner.strip()):
            return m.group(0)  # garder tel quel
        return '\\(' + inner + '\\)'

    text = re.sub(r'\$([^\$\n]{1,300}?)\$', dollar_replace, text)

    # 5. Symboles Unicode courants → LaTeX
    symbols = {
        '≤': '\\( \\leq \\)', '≥': '\\( \\geq \\)',
        '∈': '\\( \\in \\)',  '∉': '\\( \\notin \\)',
        '∀': '\\( \\forall \\)', '∃': '\\( \\exists \\)',
        '→': '\\( \\rightarrow \\)', '⟺': '\\( \\Leftrightarrow \\)',
        '×': '\\( \\times \\)', '÷': '\\( \\div \\)',
        '±': '\\( \\pm \\)',   '∞': '\\( \\infty \\)',
        'ℝ': '\\( \\mathbb{R} \\)', 'ℕ': '\\( \\mathbb{N} \\)',
        'ℤ': '\\( \\mathbb{Z} \\)', 'ℚ': '\\( \\mathbb{Q} \\)',
    }
    for char, latex in symbols.items():
        text = text.replace(char, latex)

    # 6. Restaurer les zones protégées
    for i, val in enumerate(protected):
        text = text.replace(f'\x00P{i}\x00', val)

    return text


# ══════════════════════════════════════════════
# AUTH DECORATOR
# ══════════════════════════════════════════════

def require_auth(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Vous devez être connecté pour accéder à cette ressource."}), 401
        return f(*args, **kwargs)
    return decorated


# ══════════════════════════════════════════════
# PROMPT SYSTÈME
# ══════════════════════════════════════════════

FIGURE_SYNTAX = (
    "Si et seulement si l'élève demande de TRACER ou DESSINER, génère UNE balise :\n"
    "[FIGURE: type=square cx=0 cy=0 side=5]\n"
    "[FIGURE: type=triangle points=0,0,4,0,2,3 labels=A,B,C]\n"
    "[FIGURE: type=circle cx=0 cy=0 r=3]\n"
    "[FIGURE: type=function expr=x*x xmin=-5 xmax=5 label=f(x)=x2]\n"
    "[FIGURE: type=rectangle x=0 y=0 w=4 h=3 labels=A,B,C,D]\n"
    "[FIGURE: type=segment x1=0 y1=0 x2=5 y2=0 labelA=A labelB=B]\n"
    "INTERDIT ABSOLU : ASCII art, blocs ```, caractères |/*+- pour dessiner.\n"
)


class MathAIService:

    @staticmethod
    def build_prompt(level='tout'):
        info  = get_level_info(level)
        nom   = info['name'].replace('📚 ','').replace('🎒 ','').replace('📐 ','').replace('🎓 ','')
        lecons, noms = get_programme_for_level(level)

        if level == 'tout' or lecons is None:
            prog_text   = "Tout le programme officiel ivoirien du CP à la Terminale (MENA)."
            classes_str = "du CP à la Terminale (A, C, D)"
            restriction = "L'université et l'enseignement supérieur sont exclus."
        else:
            prog_text   = '\n'.join(f'  - {l}' for l in lecons)
            classes_str = ', '.join(noms)
            restriction = get_restriction_msg(level)

        return (
            "Tu es PROF IVOIRMATH, professeur de mathématiques expert du système éducatif ivoirien.\n"
            "Référentiel : MENA — Ministère de l'Éducation Nationale et de l'Alphabétisation de Côte d'Ivoire.\n\n"
            f"NIVEAU ACTIF : {nom}\n"
            f"CLASSES COUVERTES : {classes_str}\n\n"
            "PROGRAMME AUTORISÉ :\n"
            f"{prog_text}\n\n"
            "RESTRICTION ABSOLUE :\n"
            f"{restriction}\n"
            "Si la question porte sur une notion hors programme, réponds UNIQUEMENT par ce message.\n\n"
            "RÈGLES GÉNÉRALES :\n"
            "1. Traite UNIQUEMENT les mathématiques du programme ivoirien ci-dessus.\n"
            "2. Salutations : réponds chaleureusement et invite à poser une question de maths.\n"
            "3. Questions hors maths : redirige poliment.\n"
            "4. Université : jamais dans ton programme.\n\n"
            "FORMULES MATHÉMATIQUES — RÈGLE ABSOLUE :\n"
            "TOUTES les formules et expressions mathématiques DOIVENT être en LaTeX MathJax.\n"
            "- Formule en ligne  : \\( formule \\)\n"
            "- Formule centrée   : \\[ formule \\]\n"
            "NE JAMAIS utiliser $...$ ou $$...$$ ni écrire une formule sans balise LaTeX.\n"
            "EXEMPLES CORRECTS :\n"
            "  \\( ax^2 + bx + c = 0 \\)\n"
            "  \\[ x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a} \\]\n"
            "  \\( \\ln(x) \\)  \\( e^x \\)  \\( \\leq \\)  \\( \\in \\mathbb{R} \\)\n"
            "EXEMPLES INTERDITS : x^2  ln(x)  a/b  $x^2$  $$formule$$\n\n"
            f"FIGURES :\n{FIGURE_SYNTAX}\n"
            f"STYLE : Pédagogue, patient, encourageant. Vocabulaire adapté au niveau {nom}.\n"
            "Structure : rappel de la notion → méthode → exemple résolu → conclusion.\n"
        )

    @staticmethod
    def call_api(messages, level='tout'):
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type":  "application/json; charset=utf-8",
        }
        prompt       = MathAIService.build_prompt(level)
        api_messages = [{"role": "system", "content": prompt}] + messages
        data         = {"messages": api_messages, "temperature": 0.3, "max_tokens": 1800}

        last_err = None
        for model in MODELS:
            try:
                data['model'] = model
                logger.info(f"API → {model}")
                r = requests.post(API_URL, headers=headers, json=data, timeout=50)
                if r.status_code in (429, 404):
                    logger.warning(f"{model} → {r.status_code}")
                    continue
                r.raise_for_status()
                result  = r.json()
                choices = result.get('choices', [])
                if not choices:
                    continue
                content = choices[0].get('message', {}).get('content', '')
                if not content or not content.strip():
                    continue
                # Post-correction LaTeX
                content = fix_latex(content)
                result['choices'][0]['message']['content'] = content
                logger.info(f"OK : {model}")
                return result
            except requests.exceptions.Timeout:
                last_err = "timeout"
            except Exception as e:
                last_err = str(e)
                logger.warning(f"{model} → {e}")

        raise Exception(last_err or "tous les modèles indisponibles")


# ══════════════════════════════════════════════
# AUTH ROUTES
# ══════════════════════════════════════════════

@app.route("/api/auth/register", methods=["POST"])
def register():
    try:
        data     = request.json or {}
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        if not username or not password:
            return jsonify({"error": "Veuillez renseigner un nom d'utilisateur et un mot de passe."}), 400
        if len(username) < 3:
            return jsonify({"error": "Le nom d'utilisateur doit contenir au moins 3 caractères."}), 400
        if len(password) < 6:
            return jsonify({"error": "Le mot de passe doit contenir au moins 6 caractères."}), 400
        result = UserManager.create_user(username, password)
        if result['success']:
            session['user_id']  = result['user_id']
            session['username'] = username
            session.permanent   = True
            return jsonify({"success": True, "username": username})
        return jsonify({"error": result['error']}), 400
    except Exception:
        return jsonify({"error": "Une erreur est survenue lors de l'inscription. Réessayez."}), 500


@app.route("/api/auth/login", methods=["POST"])
def login():
    try:
        data     = request.json or {}
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        if not username or not password:
            return jsonify({"error": "Veuillez renseigner vos identifiants."}), 400
        result = UserManager.authenticate(username, password)
        if result['success']:
            session['user_id']  = result['user_id']
            session['username'] = result['username']
            session.permanent   = True
            return jsonify({"success": True, "username": username})
        return jsonify({"error": result['error']}), 401
    except Exception:
        return jsonify({"error": "Une erreur est survenue lors de la connexion. Réessayez."}), 500


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})


@app.route("/api/auth/status", methods=["GET"])
def auth_status():
    if 'user_id' in session:
        return jsonify({"authenticated": True, "username": session.get('username')})
    return jsonify({"authenticated": False})


# ══════════════════════════════════════════════
# CONVERSATIONS
# ══════════════════════════════════════════════

@app.route("/api/conversations", methods=["GET"])
@require_auth
def get_conversations():
    try:
        return jsonify({"conversations": ConversationManager.get_user_conversations(session['user_id'])})
    except Exception:
        return jsonify({"error": "Impossible de récupérer vos conversations."}), 500


@app.route("/api/conversations/new", methods=["POST"])
@require_auth
def create_conversation():
    try:
        level = (request.json or {}).get('level', 'tout')
        if level not in ALL_LEVELS: level = 'tout'
        conv_id = ConversationManager.create_conversation(session['user_id'], level)
        return jsonify({"success": True, "conversation_id": conv_id})
    except Exception:
        return jsonify({"error": "Impossible de créer la conversation."}), 500


@app.route("/api/conversations/<conv_id>", methods=["GET"])
@require_auth
def get_conversation(conv_id):
    try:
        conv = ConversationManager.get_conversation(conv_id, session['user_id'])
        if not conv: return jsonify({"error": "Conversation introuvable."}), 404
        return jsonify(conv)
    except Exception:
        return jsonify({"error": "Impossible de charger la conversation."}), 500


@app.route("/api/conversations/<conv_id>", methods=["DELETE"])
@require_auth
def delete_conversation(conv_id):
    try:
        result = ConversationManager.delete_conversation(conv_id, session['user_id'])
        if result['success']: return jsonify({"success": True})
        return jsonify({"error": "Conversation introuvable."}), 404
    except Exception:
        return jsonify({"error": "Impossible de supprimer la conversation."}), 500


# ══════════════════════════════════════════════
# MESSAGE
# ══════════════════════════════════════════════

@app.route("/api/conversations/<conv_id>/message", methods=["POST"])
@require_auth
def send_message(conv_id):
    try:
        user_id      = session['user_id']
        user_message = (request.json or {}).get('message', '').strip()
        if not user_message:
            return jsonify({"error": "Le message ne peut pas être vide."}), 400

        conv_data = ConversationManager.get_conversation_messages(conv_id, user_id)
        if not conv_data:
            return jsonify({"error": "Conversation introuvable."}), 404

        ConversationManager.add_message(conv_id, user_id, 'user', user_message)
        messages = conv_data['messages'] + [{"role": "user", "content": user_message}]
        level    = conv_data['level']

        def generate():
            try:
                result     = MathAIService.call_api(messages, level)
                ai_message = result['choices'][0]['message']['content']
                if not ai_message or not ai_message.strip():
                    ai_message = "Je n'ai pas pu générer une réponse. Veuillez reformuler votre question."
                ConversationManager.add_message(conv_id, user_id, 'assistant', ai_message)
                yield f"data: {json.dumps({'message': ai_message, 'success': True})}\n\n"
            except Exception as e:
                logger.error(f"Erreur génération : {e}")
                yield f"data: {json.dumps({'error': 'Le service est momentanément surchargé. Veuillez patienter et réessayer.'})}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
        )
    except Exception as e:
        logger.error(f"Erreur send_message : {e}")
        return jsonify({"error": "Une erreur inattendue est survenue. Réessayez."}), 500


# ══════════════════════════════════════════════
# ROUTES UTILITAIRES
# ══════════════════════════════════════════════

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/levels", methods=["GET"])
def get_levels():
    cycles_list  = [{"id":k,"name":v['name'],"ordre":v['ordre']}
                    for k,v in sorted(CYCLES.items(),  key=lambda x: x[1]['ordre'])]
    classes_list = [{"id":k,"name":v['name'],"cycle":v['cycle'],"ordre":v['ordre']}
                    for k,v in sorted(CLASSES.items(), key=lambda x: x[1]['ordre'])]
    return jsonify({"cycles": cycles_list, "classes": classes_list})

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "online", "service": "IvoirMath AI", "version": "5.0.1"})

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Page introuvable."}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Erreur interne. Veuillez réessayer."}), 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5050))
    logger.info(f"IvoirMath AI v5.0.1 — port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)