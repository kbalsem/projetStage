# tests/test_detecteur.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from architecture.detecteur import detecter_architecture


def test_petit_projet():
    print("\n=== TEST 1 : Petit projet (court-circuit MONOLITHIQUE) ===")
    data = {
        "fichiers": [f"fichier_{i}.py" for i in range(5)],  # 5 fichiers < seuil de 15
        "contenu_strategique": {}
    }
    resultat = detecter_architecture(data)
    print(resultat)
    assert resultat["architecture"] == "MONOLITHIQUE"
    assert resultat["confiance"] == "élevée"
    assert "raison_court_circuit" in resultat
    print("✓ OK")


def test_projet_mvc_clair():
    print("\n=== TEST 2 : Projet MVC clair (au-dessus du seuil) ===")
    fichiers = (
        [f"controllers/ctrl_{i}.py" for i in range(8)] +
        [f"models/model_{i}.py" for i in range(8)] +
        [f"views/view_{i}.py" for i in range(8)] +
        [f"templates/tpl_{i}.html" for i in range(8)]
    )
    data = {
        "fichiers": fichiers,
        "contenu_strategique": {
            "requirements.txt": "django==4.2\npsycopg2"
        }
    }
    resultat = detecter_architecture(data)
    print(resultat)
    assert resultat["architecture"] == "MVC"
    print("✓ OK")


def test_projet_conflit():
    print("\n=== TEST 3 : Projet ambigu CLEAN vs COUCHES (conflit attendu) ===")
    fichiers = (
        [f"domain/entity_{i}.py" for i in range(6)] +
        [f"repositories/repo_{i}.py" for i in range(6)] +
        [f"infrastructure/infra_{i}.py" for i in range(6)] +
        [f"core/core_{i}.py" for i in range(6)]
    )
    data = {
        "fichiers": fichiers,
        "contenu_strategique": {}
    }
    resultat = detecter_architecture(data)
    print(resultat)
    print(f"Conflit détecté : {resultat['conflit']}")
    print("✓ OK (vérifie manuellement si le conflit est cohérent)")


if __name__ == "__main__":
    test_petit_projet()
    test_projet_mvc_clair()
    test_projet_conflit()