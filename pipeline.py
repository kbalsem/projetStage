import logging
from generation.ecrivain import ecrire_documentation_complete, nettoyer_nom_repo
from generation.mkdocs_generator import generer_mkdocs_yml
from scanners.github_scanner       import scanner_github
from architecture.detecteur        import detecter_architecture
from architecture.ollama_detecteur import detecter_avec_ollama
from generation.analyzer           import analyser_projet_memoire
from generation.doc_generator      import generer_doc_tous_fichiers
from generation.project_doc        import generer_doc_globale, generer_doc_architecture
from generation.readme_generator   import generer_readme
from generation.ecrivain           import ecrire_documentation_complete

logging.basicConfig(level=logging.INFO)

def pipeline_complet(url_repo: str, dossier_sortie: str = "output") -> dict:
    print("1. Scan du repository...")
    data_scanner = scanner_github(url_repo)
    print(f"   → {len(data_scanner['fichiers'])} fichiers trouvés")
    print(f"   → {len(data_scanner['sources_ast'])} fichiers sources téléchargés pour l'analyse")

    print("\n2. Détection d'architecture...")
    resultat_scoring = detecter_architecture(data_scanner)
    resultat_archi    = detecter_avec_ollama(data_scanner, resultat_scoring)
    print(f"   → Architecture : {resultat_archi['architecture']} (confiance : {resultat_archi['confiance']})")

    print("\n3. Analyse du code (tree-sitter)...")
    infos_ast = analyser_projet_memoire(data_scanner["sources_ast"])
    print(f"   → {len(infos_ast)} fichiers analysés")

    print("\n4. Génération de la documentation...")
    docs_fichiers    = generer_doc_tous_fichiers(infos_ast, resultat_archi["architecture"])
    doc_globale      = generer_doc_globale(data_scanner, resultat_archi, infos_ast)
    doc_architecture = generer_doc_architecture(resultat_archi)
    readme           = generer_readme(data_scanner, resultat_archi)

    print("\n5. Écriture des fichiers sur disque...")
    nom_propre = nettoyer_nom_repo(data_scanner["repo_name"])
    racine_doc = ecrire_documentation_complete(
        repo_name        = data_scanner["repo_name"],
        dossier_sortie   = dossier_sortie,
        readme           = readme,
        doc_globale      = doc_globale,
        doc_architecture = doc_architecture,
        docs_fichiers    = docs_fichiers
    )

    print("\n6. Génération de la configuration MkDocs...")
    chemin_mkdocs = generer_mkdocs_yml(
        nom_propre     = nom_propre,
        docs_fichiers  = docs_fichiers,
        dossier_sortie = dossier_sortie
    )
    print(f"   → mkdocs.yml généré : {chemin_mkdocs}")

    print(f"\n✓ Documentation complète générée dans : {racine_doc}")

    return {
        "data_scanner":     data_scanner,
        "resultat_archi":   resultat_archi,
        "infos_ast":        infos_ast,
        "docs_fichiers":    docs_fichiers,
        "doc_globale":      doc_globale,
        "doc_architecture": doc_architecture,
        "readme":           readme,
        "racine_doc":       racine_doc,
        "chemin_doc":       racine_doc,      # alias explicite pour le wrapper web
        "chemin_mkdocs":    chemin_mkdocs,
    }


if __name__ == "__main__":
    pipeline_complet("https://github.com/pallets/flask-sqlalchemy")