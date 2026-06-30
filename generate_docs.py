import os
import yaml
import subprocess

def generer_documentation(data: dict, output_dir: str = "./docs_output"):
  

    repo_name   = data.get("repo_name", "Inconnu")
    author      = data.get("author", "Inconnu")
    branch      = data.get("branch", "main")
    commits     = data.get("commits", 0)
    stars       = data.get("stars", 0)
    licence     = data.get("licence", "Non spécifiée")
    description = data.get("description", "")
    fichiers    = data.get("fichiers", [])

    docs_dir = os.path.join(output_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)

    # ─── Générer index.md ──────────────────────────────────
    contenu_md = f"""# {repo_name}

## Informations générales

| Champ       | Valeur         |
|-------------|----------------|
| Auteur      | {author}       |
| Branche     | {branch}       |
| Commits     | {commits}      |
| Stars       | {stars}        |
| Licence     | {licence}      |

## Description

{description if description else "Aucune description disponible."}

## Fichiers du projet ({len(fichiers)} fichiers)

"""
    # Ajouter la liste des fichiers
    for f in fichiers[:500]:  # limite 500 pour éviter un fichier trop lourd
        contenu_md += f"- `{f}`\n"

    if len(fichiers) > 500:
        contenu_md += f"\n... et {len(fichiers) - 500} fichiers supplémentaires.\n"

    # Écrire index.md
    index_path = os.path.join(docs_dir, "index.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(contenu_md)

    # ─── Générer mkdocs.yml ────────────────────────────────
    config = {
        "site_name": f"Documentation - {repo_name}",
        "site_author": author,
        "theme": {
            "name": "material",
            "language": "fr"
        },
        "nav": [
            {"Accueil": "index.md"}
        ]
    }

   # Chemin absolu pour éviter les problèmes Windows
    output_dir  = os.path.abspath(output_dir)
    docs_dir    = os.path.join(output_dir, "docs")
    config_path = os.path.join(output_dir, "mkdocs.yml")

    os.makedirs(docs_dir, exist_ok=True)

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True)

    # ─── Lancer MkDocs build ───────────────────────────────
    try:
        subprocess.run(
            ["mkdocs", "build"],
            check=True,
            cwd=output_dir   # MkDocs cherche mkdocs.yml dans le dossier courant
        )
        print(f" Documentation générée dans {output_dir}/site/")
        return os.path.join(output_dir, "site")

    except subprocess.CalledProcessError as e:
        print(f" Erreur MkDocs : {e}")
        raise