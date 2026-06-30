import logging

logger = logging.getLogger(__name__)

def detecter_plateforme(url: str) -> str:
    url_lower = url.lower()
    if "github.com" in url_lower:
        return "github"
    elif "gitlab.com" in url_lower:
        return "gitlab"
    else:
        return "git"

def analyser_repo(url: str) -> dict:
    plateforme = detecter_plateforme(url)
    logger.info(f"Plateforme détectée : {plateforme} pour {url}")

    try:
        if plateforme == "github":
            from scanners.github_scanner import scanner_github
            return scanner_github(url)
        
        elif plateforme == "gitlab":
            from scanners.gitlab_scanner import scanner_gitlab
            return scanner_gitlab(url)
        
        
        else:
            logger.info("Utilisation du fallback GitPython")
            from scanner import scanner_repo
            data = scanner_repo(url)
            data.setdefault("stars", 0)
            data.setdefault("licence", "Non spécifiée")
            data.setdefault("description", "")
            return data

    except ImportError as e:
        # Si le scanner spécifique n'existe pas encore, fallback GitPython
        logger.warning(f"Scanner {plateforme} non disponible, fallback GitPython : {e}")
        from scanner import scanner_repo
        from scanner import forcer_suppression
        try:
            data = scanner_repo(url)
            data.setdefault("stars", 0)
            data.setdefault("licence", "Non spécifiée")
            data.setdefault("description", "")
            return data
        finally:
            forcer_suppression("./temp_repo")

    except Exception as e:
        logger.error(f"Erreur dans le router : {str(e)}")
        raise