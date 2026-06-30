# tests/test_ollama.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from architecture.detecteur import detecter_architecture
from architecture.ollama_detecteur    import detecter_avec_ollama


def test_accord_simple():
    print("\n=== TEST : Cas normal (accord ou désaccord avec Ollama) ===")
    fichiers = (
        [f"controllers/ctrl_{i}.py" for i in range(8)] +
        [f"models/model_{i}.py" for i in range(8)] +
        [f"views/view_{i}.py" for i in range(8)]
    )
    data_scanner = {
        "repo_name": "projet_test",
        "fichiers": fichiers,
        "contenu_strategique": {
            "requirements.txt": "django==4.2"
        }
    }
    resultat_scoring = detecter_architecture(data_scanner)
    print("Résultat scoring :", resultat_scoring)

    resultat_final = detecter_avec_ollama(data_scanner, resultat_scoring)
    print("\nRésultat final (avec Ollama) :", resultat_final)


def test_conflit_avec_ollama():
    print("\n=== TEST : Conflit CLEAN/COUCHES arbitré par Ollama ===")
    fichiers = (
        [f"domain/entity_{i}.py" for i in range(6)] +
        [f"repositories/repo_{i}.py" for i in range(6)] +
        [f"infrastructure/infra_{i}.py" for i in range(6)] +
        [f"core/core_{i}.py" for i in range(6)]
    )
    data_scanner = {
        "repo_name": "projet_conflit",
        "fichiers": fichiers,
        "contenu_strategique": {}
    }
    resultat_scoring = detecter_architecture(data_scanner)
    print("Résultat scoring (conflit) :", resultat_scoring["conflit"])

    resultat_final = detecter_avec_ollama(data_scanner, resultat_scoring)
    print("\nRésultat final (arbitré) :", resultat_final)


if __name__ == "__main__":
    test_accord_simple()
    test_conflit_avec_ollama()