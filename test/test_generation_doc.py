# tests/test_generation_doc.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from generation.project_doc import generer_doc_architecture  # ajuste le nom du module


def test_doc_confiance_elevee():
    print("\n=== TEST : Doc architecture avec confiance élevée ===")
    resultat_archi = {
        "architecture": "MVC",
        "confiance": "élevée",
        "justification": "Le projet utilise Django avec une structure controllers/models/views claire.",
        "elements_cles": ["controllers", "models", "django"],
        "scores": {"MVC": 6.6667, "COUCHES": 1.2, "CLEAN": 0.5}  # Scores floats — test du fix
    }
    doc = generer_doc_architecture(resultat_archi)
    print(doc)
    assert "Confiance faible" not in doc
    print("✓ OK — pas de crash avec scores float")


def test_doc_confiance_faible():
    print("\n=== TEST : Doc architecture avec confiance faible (avertissement attendu) ===")
    resultat_archi = {
        "architecture": "CLEAN",
        "confiance": "faible",
        "justification": "",
        "elements_cles": [],
        "scores": {"CLEAN": 0.6667, "COUCHES": 0.6, "MVC": 0.1}
    }
    doc = generer_doc_architecture(resultat_archi)
    print(doc)
    assert "⚠️" in doc
    assert "Détection automatique par scoring, sans confirmation IA disponible." in doc
    print("✓ OK — avertissement bien affiché")


if __name__ == "__main__":
    test_doc_confiance_elevee()
    test_doc_confiance_faible()