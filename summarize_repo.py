import requests
import logging

logger = logging.getLogger(__name__)

OLLAMA_URL   = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"


def resumer_repo(data: dict) -> str:
    """
    Prend les données du scanner et génère un résumé IA via Ollama.
    Retourne un texte de résumé en français.
    """

    repo_name   = data.get("repo_name", "Inconnu")
    author      = data.get("author", "Inconnu")
    branch      = data.get("branch", "main")
    commits     = data.get("commits", 0)
    stars       = data.get("stars", 0)
    licence     = data.get("licence", "Non spécifiée")
    description = data.get("description", "")
    fichiers    = data.get("fichiers", [])

    # ─── Construire le prompt ──────────────────────────────────────
    # On donne les infos du repo à Ollama pour qu'il génère un résumé
    extensions = extraire_extensions(fichiers)

    prompt = f"""Tu es un assistant technique. Analyse ce dépôt Git et génère un résumé technique en français.

Informations du dépôt :
- Nom : {repo_name}
- Auteur : {author}
- Branche principale : {branch}
- Nombre de commits : {commits}
- Stars : {stars}
- Licence : {licence}
- Description : {description if description else "Non fournie"}
- Nombre de fichiers : {len(fichiers)}
- Technologies détectées : {", ".join(extensions) if extensions else "Non détectées"}
- Exemples de fichiers : {", ".join(fichiers[:10])}

Génère un résumé technique structuré en français avec :
1. Description générale du projet
2. Technologies utilisées
3. Structure du projet
4. Points importants

Sois concis et professionnel."""

    logger.info(f"Envoi du prompt à Ollama pour : {repo_name}")

    # ─── Appel à Ollama ────────────────────────────────────────────
    try:
        reponse = requests.post(
            OLLAMA_URL,
            json={
                "model"  : OLLAMA_MODEL,
                "prompt" : prompt,
                "stream" : False  # On attend la réponse complète
            },
            timeout=120  # 2 minutes max
        )

        if reponse.status_code != 200:
            raise Exception(f"Erreur Ollama : {reponse.status_code}")

        resultat = reponse.json()
        resume   = resultat.get("response", "").strip()

        logger.info(f"Résumé généré avec succès pour : {repo_name}")
        return resume

    except requests.exceptions.ConnectionError:
        raise Exception("Ollama n'est pas lancé. Exécutez 'ollama serve' dans un terminal.")
    except requests.exceptions.Timeout:
        raise Exception("Ollama a mis trop de temps à répondre (timeout 120s).")
    except Exception as e:
        raise Exception(f"Erreur lors du résumé IA : {str(e)}")


def extraire_extensions(fichiers: list) -> list:
    """
    Extrait les extensions uniques des fichiers pour détecter les technologies
    Ex: ["main.py", "index.js"] → ["Python", "JavaScript"]
    """
    # Mapping extension → technologie
    mapping = {
        ".py"    : "Python",
        ".js"    : "JavaScript",
        ".ts"    : "TypeScript",
        ".java"  : "Java",
        ".cpp"   : "C++",
        ".c"     : "C",
        ".cs"    : "C#",
        ".go"    : "Go",
        ".rs"    : "Rust",
        ".php"   : "PHP",
        ".rb"    : "Ruby",
        ".swift" : "Swift",
        ".kt"    : "Kotlin",
        ".html"  : "HTML",
        ".css"   : "CSS",
        ".scss"  : "SCSS",
        ".vue"   : "Vue.js",
        ".jsx"   : "React",
        ".tsx"   : "React/TypeScript",
        ".sql"   : "SQL",
        ".sh"    : "Shell",
        ".yml"   : "YAML/CI-CD",
        ".yaml"  : "YAML/CI-CD",
        ".json"  : "JSON",
        ".md"    : "Markdown",
        ".dockerfile" : "Docker",
    }

    technologies = set()

    for fichier in fichiers:
        # Vérifier aussi si "Dockerfile" est dans le nom
        if "dockerfile" in fichier.lower():
            technologies.add("Docker")
            continue

        ext = "." + fichier.split(".")[-1].lower() if "." in fichier else ""
        if ext in mapping:
            technologies.add(mapping[ext])

    return sorted(list(technologies))