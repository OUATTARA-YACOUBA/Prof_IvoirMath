#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test de l'API OpenRouter
Utilisez ce script pour vérifier que votre connexion API fonctionne
"""

import requests
import json

# Configuration
API_KEY = "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"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openrouter/free"

def test_api_connection():
    """Test simple de connexion à l'API"""
    print("=" * 60)
    print("TEST DE CONNEXION À L'API OPENROUTER")
    print("=" * 60)
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5050",
        "X-Title": "IvoirMath AI"
    }
    
    data = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": "Bonjour, réponds juste 'OK' si tu me reçois."
            }
        ],
        "temperature": 0.5,
        "max_tokens": 50
    }
    
    print(f"\n📡 URL de l'API: {API_URL}")
    print(f"🤖 Modèle: {MODEL}")
    print(f"🔑 Clé API: {API_KEY[:20]}...{API_KEY[-10:]}")
    print("\n⏳ Envoi de la requête de test...")
    
    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json=data,
            timeout=30
        )
        
        print(f"\n📊 Code de statut: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCÈS - L'API fonctionne !\n")
            result = response.json()
            
            if 'choices' in result and len(result['choices']) > 0:
                message = result['choices'][0]['message']['content']
                print(f"💬 Réponse de l'IA: {message}")
                
                # Afficher les détails d'utilisation
                if 'usage' in result:
                    print(f"\n📈 Statistiques:")
                    print(f"   - Tokens prompt: {result['usage'].get('prompt_tokens', 'N/A')}")
                    print(f"   - Tokens générés: {result['usage'].get('completion_tokens', 'N/A')}")
                    print(f"   - Total tokens: {result['usage'].get('total_tokens', 'N/A')}")
                
                print("\n✅ TEST RÉUSSI - Vous pouvez utiliser IvoirMath AI")
                return True
            else:
                print("⚠️ Réponse reçue mais format inattendu")
                print(f"Réponse complète: {json.dumps(result, indent=2)}")
                return False
                
        elif response.status_code == 401:
            print("❌ ERREUR 401 - Clé API invalide ou expirée")
            print("   Vérifiez votre clé API sur https://openrouter.ai/keys")
            return False
            
        elif response.status_code == 404:
            print("❌ ERREUR 404 - URL incorrecte ou modèle non trouvé")
            print(f"   URL actuelle: {API_URL}")
            print(f"   Modèle actuel: {MODEL}")
            print("\n💡 Solutions possibles:")
            print("   1. Vérifiez que l'URL est: https://openrouter.ai/api/v1/chat/completions")
            print("   2. Essayez le modèle: mistralai/mistral-7b-instruct:free")
            return False
            
        elif response.status_code == 429:
            print("❌ ERREUR 429 - Trop de requêtes")
            print("   Attendez quelques minutes avant de réessayer")
            return False
            
        else:
            print(f"❌ ERREUR {response.status_code}")
            print(f"Réponse: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ ERREUR - Timeout (>30s)")
        print("   La requête a pris trop de temps. Vérifiez votre connexion internet.")
        return False
        
    except requests.exceptions.ConnectionError:
        print("❌ ERREUR - Impossible de se connecter")
        print("   Vérifiez votre connexion internet et que vous pouvez accéder à openrouter.ai")
        return False
        
    except Exception as e:
        print(f"❌ ERREUR INATTENDUE: {str(e)}")
        return False


def test_math_question():
    """Test avec une vraie question de mathématiques"""
    print("\n" + "=" * 60)
    print("TEST AVEC UNE QUESTION DE MATHÉMATIQUES")
    print("=" * 60)
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5050",
        "X-Title": "IvoirMath AI"
    }
    
    data = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Tu es un professeur de mathématiques. Utilise toujours la notation LaTeX avec \\( \\) pour les formules."
            },
            {
                "role": "user",
                "content": "Résous x² = 9"
            }
        ],
        "temperature": 0.5,
        "max_tokens": 500
    }
    
    print("\n⏳ Envoi de la question: 'Résous x² = 9'")
    
    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if 'choices' in result and len(result['choices']) > 0:
                message = result['choices'][0]['message']['content']
                print("\n💬 Réponse de l'IA:")
                print("-" * 60)
                print(message)
                print("-" * 60)
                
                # Vérifier si LaTeX est présent
                if '\\(' in message and '\\)' in message:
                    print("\n✅ Formatage LaTeX détecté !")
                else:
                    print("\n⚠️ Attention: Pas de formatage LaTeX détecté")
                
                return True
        else:
            print(f"❌ Erreur: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return False


if __name__ == "__main__":
    print("\n🧪 SCRIPT DE TEST IVOIRMATH AI\n")
    
    # Test 1: Connexion basique
    test1_ok = test_api_connection()
    
    if test1_ok:
        # Test 2: Question mathématique
        input("\n⏸️  Appuyez sur Entrée pour tester avec une question de maths...")
        test2_ok = test_math_question()
        
        if test1_ok and test2_ok:
            print("\n" + "=" * 60)
            print("🎉 TOUS LES TESTS SONT RÉUSSIS !")
            print("=" * 60)
            print("\n✅ Vous pouvez maintenant utiliser IvoirMath AI normalement.")
            print("   Lancez: python app.py")
        else:
            print("\n⚠️ Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
    else:
        print("\n❌ Test de connexion échoué. Impossible de continuer.")
        print("\n💡 ACTIONS À FAIRE:")
        print("   1. Vérifiez votre connexion internet")
        print("   2. Vérifiez votre clé API sur https://openrouter.ai")
        print("   3. Assurez-vous que l'URL est correcte dans app.py")