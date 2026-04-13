# 🎓 IvoirMath AI — Version 5.0

Assistant de mathématiques spécialisé dans le **programme officiel ivoirien (MENA)**, du CP à la Terminale.

---

## ✨ Fonctionnalités

- ✅ **Programme officiel MENA complet** — toutes les leçons du CP à la Tle A, C et D
- ✅ **Niveaux par classe** — sélection cycle → classe (6ème, 5ème, 4ème, 3ème, 2nde C/D, 1ère C, Tle C…)
- ✅ **Restriction stricte par niveau** — l'IA refuse les notions hors programme du niveau sélectionné
- ✅ **Rendu LaTeX** — toutes les formules mathématiques affichées proprement via MathJax
- ✅ **Figures interactives** — construction géométrique et graphes via JSXGraph (local, sans API)
- ✅ **Authentification utilisateur** — Inscription / Connexion sécurisée
- ✅ **Gestion de conversations** — historique sauvegardé, multi-conversations
- ✅ **Base de données** — SQLite (local) ou PostgreSQL (production/Render)
- ✅ **Déployable partout** — Docker, Render.com, PythonAnywhere

---

## 📁 Structure du projet

```
ivoirmath-ai/
├── app.py              # Backend Flask — logique IA, routes API
├── database.py         # Base de données (SQLite local / PostgreSQL Render)
├── templates/
│   └── index.html      # Interface utilisateur
├── static/
│   └── app.js          # Logique JavaScript (LaTeX, figures, chat)
├── requirements.txt    # Dépendances Python
├── render.yaml         # Configuration déploiement Render.com ← À LA RACINE
├── Dockerfile          # Déploiement Docker (optionnel)
└── README.md           # Ce fichier
```

> ⚠️ **`render.yaml` doit être placé à la racine du projet** (au même niveau que `app.py`).

---

## 🚀 Installation locale

### Prérequis

- Python 3.8+
- pip

### 1. Cloner le projet

```bash
git clone https://github.com/OUATTARA-YACOUBA/Prof_IvoirMath.git
cd Prof_IvoirMath
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Lancer l'application

```bash
python app.py
```

Disponible sur : **http://localhost:5050**

---

## 📖 Utilisation

### Première utilisation

1. **Inscription** — nom d'utilisateur (min. 3 caractères) et mot de passe (min. 6 caractères)
2. **Connexion** — avec vos identifiants
3. **Sélectionner un cycle** — Primaire, Collège ou Lycée
4. **Sélectionner une classe** — ex. 3ème, 1ère C, Tle D…
5. **Créer une conversation** — cliquer sur "➕ Nouvelle conversation"
6. **Poser vos questions** — l'IA répond selon le programme exact de la classe choisie

### Niveaux disponibles

| Cycle | Classes |
|-------|---------|
| 🎒 **Primaire** | CP, CE1, CE2, CM1, CM2 |
| 📐 **Collège** | 6ème, 5ème, 4ème, 3ème |
| 🎓 **Lycée** | 2nde A, 1ère A, Tle A · 2nde C/D, 1ère C, Tle C · 1ère D, Tle D |
| 📚 **Tout** | CP à Terminale |

### Figures interactives

Pour afficher une figure, demandez explicitement :
- *"Trace la courbe de f(x) = x²"*
- *"Dessine un triangle ABC"*
- *"Représente un cercle de rayon 3"*

---

## 🌐 Déploiement sur Render.com (gratuit)

### Prérequis

- Compte sur [render.com](https://render.com)
- Code poussé sur GitHub

### Étapes

1. Connectez-vous sur **render.com**
2. Cliquez **New → Blueprint**
3. Connectez votre repo GitHub `Prof_IvoirMath`
4. Render détecte automatiquement `render.yaml` et crée :
   - Le service web Flask
   - La base de données PostgreSQL gratuite
5. Cliquez **Apply** — déploiement automatique en ~3 minutes

### Variables d'environnement (automatiques via render.yaml)

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Clé secrète Flask (générée automatiquement) |
| `OPENROUTER_API_KEY` | Clé API OpenRouter |
| `DATABASE_URL` | URL PostgreSQL (injectée automatiquement par Render) |

### Garder l'app éveillée (optionnel)

Render met l'app en veille après 15 min d'inactivité sur le plan gratuit.
Pour l'éviter : créer un compte sur [uptimerobot.com](https://uptimerobot.com) et ajouter un moniteur HTTP sur votre URL Render toutes les 10 minutes.

---

## 🔒 Sécurité

- Mots de passe hashés avec **bcrypt**
- Sessions Flask sécurisées (clé secrète via variable d'environnement)
- Isolation des données par utilisateur
- Validation des entrées côté serveur et côté client

---

## 🗄️ Base de données

Compatible **SQLite** (local) et **PostgreSQL** (production) — détection automatique via `DATABASE_URL`.

3 tables :

| Table | Colonnes principales |
|-------|---------------------|
| `users` | id, username, password_hash |
| `conversations` | id, user_id, title, level |
| `messages` | id, conversation_id, role, content |

---

## 🛠️ Configuration

### Changer le modèle IA

Dans `app.py` :

```python
MODELS = [
    'meta-llama/llama-3.1-8b-instruct:free',  # Rapide
    'mistralai/mistral-7b-instruct:free',       # Fallback
    'openrouter/free',                          # Dernier recours
]
```

### Changer le port (local)

```python
app.run(host="0.0.0.0", port=5050, debug=False)
```

### Durée de session

```python
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 heures
```

---

## 🐛 Dépannage

### `ModuleNotFoundError: No module named 'bcrypt'`
```bash
pip install bcrypt
```

### `ModuleNotFoundError: No module named 'psycopg2'`
```bash
pip install psycopg2-binary
```

### Base de données corrompue (SQLite local)
```bash
rm ivoirmath.db
python app.py  # Recrée automatiquement
```

### Port 5050 déjà utilisé
```python
app.run(port=5051)
```

### L'app Render ne répond pas
- Attendez 30 secondes (réveil depuis la veille)
- Vérifiez les logs dans le dashboard Render

---

## 📝 Changelog

### Version 5.0.0
- ✅ Programme officiel MENA complet (toutes les leçons par classe)
- ✅ Sélecteur hiérarchique cycle → classe
- ✅ Restriction stricte par niveau de classe
- ✅ Post-correction LaTeX automatique ($$...$$ → MathJax)
- ✅ Figures interactives JSXGraph (local, sans API externe)
- ✅ Support PostgreSQL pour déploiement Render
- ✅ Messages d'erreur professionnels
- ✅ `render.yaml` pour déploiement en un clic

### Version 3.0.0
- ✅ Authentification complète
- ✅ Gestion de conversations multi-utilisateurs
- ✅ Interface moderne avec sidebar

### Version 2.0.0
- Conversation avec historique de session
- Niveaux hiérarchiques (cycles)

### Version 1.0.0
- Assistant de base sans sauvegarde

---

## 📄 Licence

MIT License — Libre d'utilisation et de modification

---

## 🙏 Remerciements

- Programme officiel ivoirien de mathématiques — **MENA**
- [OpenRouter](https://openrouter.ai) pour l'API IA
- [MathJax](https://www.mathjax.org) pour le rendu LaTeX
- [JSXGraph](https://jsxgraph.uni-bayreuth.de) pour les figures interactives
- [Render.com](https://render.com) pour l'hébergement gratuit

---

**Créé avec ❤️ pour les élèves ivoiriens 🇨🇮**