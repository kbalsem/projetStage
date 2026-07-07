# generation/swagger_page_generator.py
"""
Génère la page Swagger UI intégrée au site MkDocs.
"""
import json
import os


TEMPLATE_PAGE_SWAGGER = """# API REST détectée

Cette page est générée automatiquement par GitDoc AI à partir de l'analyse
statique du code source de **{nom_projet}**. Les routes ci-dessous ont été
détectées par reconnaissance de motifs (décorateurs Flask/FastAPI) — ce
n'est pas une validation d'exécution réelle de l'API.

<div id="swagger-ui"></div>

<link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
<script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>
  window.onload = function() {{
    SwaggerUIBundle({{
      url: "./openapi.json",
      dom_id: "#swagger-ui",
      presets: [SwaggerUIBundle.presets.apis],
      layout: "BaseLayout"
    }});
  }};
</script>
"""


def generer_page_swagger(spec: dict, docs_dir: str, nom_projet: str) -> dict:
    """
    Écrit openapi.json et api.md dans le dossier docs/ du projet MkDocs.

    Args:
        spec: spécification OpenAPI (dict)
        docs_dir: chemin vers le dossier docs/ du projet MkDocs
        nom_projet: nom du dépôt analysé

    Returns:
        dict avec les chemins des fichiers créés, ou {} si aucune route.
    """
    if not spec.get("paths"):
        return {}

    os.makedirs(docs_dir, exist_ok=True)

    chemin_openapi_json = os.path.join(docs_dir, "openapi.json")
    with open(chemin_openapi_json, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2, ensure_ascii=False, sort_keys=False)

    chemin_api_md = os.path.join(docs_dir, "api.md")
    with open(chemin_api_md, "w", encoding="utf-8") as f:
        f.write(TEMPLATE_PAGE_SWAGGER.format(nom_projet=nom_projet))

    return {"openapi_json": chemin_openapi_json, "api_md": chemin_api_md}


def entree_nav_mkdocs() -> dict:
    """Retourne l'entrée de navigation pour mkdocs.yml."""
    return {"API REST": "api.md"}