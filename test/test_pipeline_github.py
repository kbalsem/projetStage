# test/test_pipeline_github.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── À AJUSTER selon le nom réel de ton module scanner ──────────
from scanners.github_scanner import scanner_github  # <-- adapte ce nom

from architecture.detecteur import detecter_architecture
from architecture.ollama_detecteur import detecter_avec_ollama
from generation.project_doc import generer_doc_architecture


# Quelques repos publics simples à tester, choisis pour leur structure connue
REPO_TEST = "https://github.com/pallets/flask"  # Exemple : structure Flask classique
# Autres options à essayer :
# "https://github.com/tiangolo/full-stack-fastapi-template"  # FastAPI / Clean-ish
# "https://github.com/gothinkster/django-realworld-example-app"  # Django MVC clair


def test_pipeline_complet():
    print(f"\n=== TEST PIPELINE COMPLET sur {REPO_TEST} ===\n")

    # ── Étape 1 : scanner le repo ──────────────────────────────
    print("1. Scan du repository...")
    data_scanner = scanner_github(REPO_TEST)
    print(f"   → {len(data_scanner.get('fichiers', []))} fichiers trouvés")
    print(f"   → {len(data_scanner.get('contenu_strategique', {}))} fichiers stratégiques extraits")

    # ── Étape 2 : détection scoring ────────────────────────────
    print("\n2. Détection d'architecture (scoring)...")
    resultat_scoring = detecter_architecture(data_scanner)
    print(f"   → Candidat : {resultat_scoring['architecture']} "
          f"(confiance : {resultat_scoring['confiance']})")
    print(f"   → Scores : {resultat_scoring['scores']}")
    print(f"   → Conflit : {resultat_scoring.get('conflit')}")

    # ── Étape 3 : confirmation/arbitrage Ollama ────────────────
    print("\n3. Confirmation via Ollama...")
    resultat_final = detecter_avec_ollama(data_scanner, resultat_scoring)
    print(f"   → Architecture finale : {resultat_final['architecture']}")
    print(f"   → Confiance finale : {resultat_final['confiance']}")
    print(f"   → Source : {resultat_final['source']}")
    print(f"   → Justification : {resultat_final.get('justification')}")

    # ── Étape 4 : génération de la doc d'architecture ──────────
    print("\n4. Génération de la documentation d'architecture...")
    doc = generer_doc_architecture(resultat_final)
    print("\n" + "=" * 60)
    print(doc)
    print("=" * 60)

    # Sauvegarde dans un fichier pour inspection visuelle
    chemin_sortie = "test/sortie_test_pipeline.md"
    with open(chemin_sortie, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"\n✓ Doc sauvegardée dans {chemin_sortie}")


if __name__ == "__main__":
    test_pipeline_complet()