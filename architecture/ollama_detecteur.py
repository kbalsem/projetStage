# architecture/ollama_detecteur.py
"""
Module de détection d'architecture assistée par Ollama (IA locale).

Ce module utilise Ollama pour affiner ou confirmer la détection
d'architecture logicielle quand le scoring automatique est incertain.
"""

import json
import logging
import os
from typing import Dict, Optional, Tuple

from utils.ollama_client import generer

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION DEPUIS .ENV
# ═══════════════════════════════════════════════════════════════════════════════

# Fichiers prioritaires pour l'analyse
FICHIERS_PRIORITAIRES = [
    f.strip() for f in os.getenv(
        "OLLAMA_FICHIERS_PRIORITAIRES",
        "requirements.txt,package.json,pom.xml,build.gradle,composer.json,"
        "cargo.toml,docker-compose.yml,docker-compose.yaml,"
        "main.py,app.py,index.js,server.js"
    ).split(",")
]

# Architectures valides reconnues
ARCHITECTURES_VALIDES = [
    a.strip() for a in os.getenv(
        "OLLAMA_ARCHITECTURES_VALIDES",
        "MVC,MVP,MVVM,COUCHES,CLEAN,MICROSERVICES,MONOLITHIQUE"
    ).split(",")
]

# Paramètres de l'appel Ollama
OLLAMA_MAX_TOKENS = int(os.getenv("OLLAMA_MAX_TOKENS", "200"))
OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.1"))
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))
OLLAMA_MAX_RETRIES = int(os.getenv("OLLAMA_MAX_RETRIES", "2"))

# Limites d'affichage dans les prompts
MAX_DOSSIERS_PROMPT = int(os.getenv("OLLAMA_MAX_DOSSIERS_PROMPT", "15"))
MAX_SIGNAUX_PROMPT = int(os.getenv("OLLAMA_MAX_SIGNAUX_PROMPT", "10"))
MAX_CONTENU_FICHIER = int(os.getenv("OLLAMA_MAX_CONTENU_FICHIER", "300"))
MAX_SCORES_PROMPT = int(os.getenv("OLLAMA_MAX_SCORES_PROMPT", "3"))

# Flag pour le mode debug
DEBUG_OLLAMA = os.getenv("DEBUG_OLLAMA", "false").lower() == "true"

# Mapping de confiance
CONFIANCE_BOOST = {
    "faible": "moyenne",
    "moyenne": "élevée", 
    "élevée": "élevée"
}

# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════

def choisir_fichier_strategique(contenu: Dict[str, str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Choisit le fichier le plus pertinent pour l'analyse.
    
    Args:
        contenu: Dictionnaire {chemin: contenu} des fichiers
        
    Returns:
        Tuple (chemin, contenu) ou (None, None)
    """
    if not contenu:
        return None, None

    # Chercher un fichier prioritaire
    for nom_prioritaire in FICHIERS_PRIORITAIRES:
        for chemin, texte in contenu.items():
            if chemin.lower().endswith(nom_prioritaire.lower()):
                if DEBUG_OLLAMA:
                    logger.debug(f"Fichier stratégique trouvé: {chemin}")
                return chemin, texte

    # Fallback : prendre le premier fichier
    chemin, texte = next(iter(contenu.items()))
    logger.info(f"Aucun fichier prioritaire trouvé, fallback sur: {chemin}")
    return chemin, texte


def _formater_liste_signaux(signaux: Optional[Dict[str, set]], 
                             categorie: str, 
                             limite: int = MAX_SIGNAUX_PROMPT) -> str:
    """
    Formate une catégorie de signaux pour le prompt.
    
    Args:
        signaux: Dictionnaire des signaux par catégorie
        categorie: Nom de la catégorie à formater
        limite: Nombre maximum d'éléments
        
    Returns:
        Chaîne formatée
    """
    if not signaux:
        return "aucun"
    
    valeurs = signaux.get(categorie, set())
    if not valeurs:
        return "aucun"
    
    return ', '.join(list(valeurs)[:limite])


def construire_prompt(data: Dict, 
                      candidat: str, 
                      scores: Dict,
                      conflit: Optional[Dict] = None, 
                      signaux_detectes: Optional[Dict] = None) -> str:
    """
    Construit le prompt enrichi pour l'analyse Ollama.
    
    Args:
        data: Données du projet
        candidat: Architecture candidate principale
        scores: Scores par architecture
        conflit: Informations de conflit éventuel
        signaux_detectes: Signaux détectés par le scoring
        
    Returns:
        Prompt formaté pour Ollama
    """
    # Extraire les informations du projet
    dossiers = data.get("dossiers", [])[:MAX_DOSSIERS_PROMPT]
    frameworks = data.get("frameworks", [])
    contenu = data.get("contenu_strategique", {})

    # Fichier stratégique
    chemin, texte = choisir_fichier_strategique(contenu)
    contenu_formate = f"{chemin}:\n{texte[:MAX_CONTENU_FICHIER]}" if chemin else "aucun"

    # Formater les signaux
    imports_str = _formater_liste_signaux(signaux_detectes, "imports")
    classes_str = _formater_liste_signaux(signaux_detectes, "classes")
    decorateurs_str = _formater_liste_signaux(signaux_detectes, "decorateurs")
    dependances_str = _formater_liste_signaux(signaux_detectes, "dependances")

    dossiers_str = ', '.join(dossiers) if dossiers else 'aucun'
    frameworks_str = ', '.join(frameworks) if frameworks else 'aucun'

    # Prompt pour cas de conflit
    if conflit and conflit.get("conflit"):
        return _construire_prompt_conflit(
            dossiers_str, frameworks_str, imports_str, decorateurs_str, 
            classes_str, dependances_str, contenu_formate, conflit
        )

    # Prompt normal
    return _construire_prompt_normal(
        dossiers_str, frameworks_str, imports_str, decorateurs_str, 
        classes_str, dependances_str, contenu_formate, candidat, scores
    )


def _construire_prompt_conflit(dossiers_str: str, frameworks_str: str,
                                imports_str: str, decorateurs_str: str,
                                classes_str: str, dependances_str: str,
                                contenu_formate: str, conflit: Dict) -> str:
    """Construit le prompt pour un cas de conflit entre deux architectures."""
    candidat_1 = conflit["candidat_1"]
    candidat_2 = conflit["candidat_2"]

    prompt = f"""Tu es un expert en architecture logicielle. Analyse ce projet Git.

Dossiers : {dossiers_str}
Frameworks : {frameworks_str}
Imports : {imports_str}
Décorateurs : {decorateurs_str}
Classes : {classes_str}
Dépendances : {dependances_str}
Fichier clé : {contenu_formate}

Le système de scoring hésite entre deux architectures :
- {candidat_1}
- {candidat_2}

Analyse les indices ci-dessus et choisis celle qui correspond le mieux.
Justifie ton choix en te basant sur les patterns observés.

RÈGLE STRICTE : réponds OBLIGATOIREMENT avec "{candidat_1}" ou "{candidat_2}".

Réponds UNIQUEMENT avec ce JSON :
{{"architecture": "<choix>", "justification": "raison courte", "confiance": "élevée/moyenne/faible", "elements_cles": ["el1", "el2"]}}"""

    return prompt.strip()


def _construire_prompt_normal(dossiers_str: str, frameworks_str: str,
                               imports_str: str, decorateurs_str: str,
                               classes_str: str, dependances_str: str,
                               contenu_formate: str, candidat: str, 
                               scores: Dict) -> str:
    """Construit le prompt standard pour confirmer une architecture."""
    
    top_scores = list(scores.items())[:MAX_SCORES_PROMPT]
    scores_formate = " | ".join(f"{a}:{s}pts" for a, s in top_scores)

    prompt = f"""Tu es un expert en architecture logicielle. Analyse ce projet Git.

Dossiers : {dossiers_str}
Frameworks : {frameworks_str}
Imports : {imports_str}
Décorateurs : {decorateurs_str}
Classes : {classes_str}
Dépendances : {dependances_str}
Fichier clé : {contenu_formate}
Scoring propose : {candidat} ({scores_formate})

Confirme ou infirme cette détection en analysant la cohérence des patterns.

Réponds UNIQUEMENT avec ce JSON :
{{"architecture": "<UNE_DES_OPTIONS>", "justification": "raison courte", "confiance": "élevée/moyenne/faible", "elements_cles": ["el1", "el2"]}}

Choisis parmi : {', '.join(ARCHITECTURES_VALIDES)}"""

    return prompt.strip()


def interroger_ollama(prompt: str, max_retries: int = None) -> Optional[Dict]:
    """
    Interroge Ollama et parse la réponse JSON.
    
    Args:
        prompt: Prompt à envoyer
        max_retries: Nombre maximum de tentatives
        
    Returns:
        Dictionnaire parsé ou None si erreur
    """
    if max_retries is None:
        max_retries = OLLAMA_MAX_RETRIES
    
    try:
        texte = generer(
            prompt=prompt, 
            max_tokens=OLLAMA_MAX_TOKENS, 
            temperature=OLLAMA_TEMPERATURE,
            timeout=OLLAMA_TIMEOUT, 
            max_retries=max_retries, 
            nettoyer=True
        )
    except Exception as e:
        logger.error(f"Erreur appel Ollama: {e}")
        return None

    if not texte or texte.startswith("[Erreur"):
        logger.error(f"Ollama a retourné une erreur ou une réponse vide: {texte[:100] if texte else 'None'}")
        return None

    if DEBUG_OLLAMA:
        logger.debug(f"Réponse brute Ollama: '{texte[:200]}'")

    # Tenter de parser le JSON
    try:
        resultat = json.loads(texte)
    except json.JSONDecodeError:
        logger.error(f"Réponse non parseable: '{texte[:200]}'")
        # Tenter de nettoyer la réponse
        resultat = _tenter_nettoyage_json(texte)
        if not resultat:
            return None

    # Valider l'architecture retournée
    architecture = resultat.get("architecture", "")
    if architecture not in ARCHITECTURES_VALIDES:
        logger.warning(f"Architecture invalide retournée: '{architecture}'")
        return None

    # Valider la confiance
    confiance = resultat.get("confiance", "moyenne")
    if confiance not in ("élevée", "moyenne", "faible"):
        resultat["confiance"] = "moyenne"

    return resultat


def _tenter_nettoyage_json(texte: str) -> Optional[Dict]:
    """
    Tente de nettoyer et parser un JSON malformé.
    
    Args:
        texte: Texte à nettoyer
        
    Returns:
        Dictionnaire parsé ou None
    """
    import re
    
    # Essayer d'extraire un objet JSON avec regex
    match = re.search(r'\{[^{}]*\}', texte, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    
    # Essayer de remplacer les guillemets simples
    try:
        return json.loads(texte.replace("'", '"'))
    except json.JSONDecodeError:
        pass
    
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTION PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════════

def detecter_avec_ollama(data_scanner: Dict, resultat_scoring: Dict) -> Dict:
    """
    Détection d'architecture assistée par Ollama.
    
    Combine le scoring automatique avec l'analyse IA pour:
    - Confirmer une détection incertaine
    - Arbitrer un conflit entre deux architectures
    - Corriger une détection si Ollama est très confiant
    
    Args:
        data_scanner: Données brutes du scanner
        resultat_scoring: Résultat du scoring automatique
        
    Returns:
        Dictionnaire enrichi avec l'analyse Ollama
    """
    candidat = resultat_scoring.get("architecture", "MONOLITHIQUE")
    scores = resultat_scoring.get("scores", {})
    confiance = resultat_scoring.get("confiance", "faible")
    conflit = resultat_scoring.get("conflit", {"conflit": False})
    besoin_ollama = resultat_scoring.get("besoin_ollama", False)
    raison_ollama = resultat_scoring.get("raison_ollama", "")

    # Si Ollama n'est pas nécessaire, retourner directement le scoring
    if not besoin_ollama:
        logger.info(f"Ollama non nécessaire — scoring conservé (confiance: {confiance})")
        return _resultat_scoring_simple(resultat_scoring)

    logger.info(f"Appel Ollama nécessaire : {raison_ollama}")

    # Préparer le contexte
    contexte = {
        "repo_name": data_scanner.get("repo_name", ""),
        "dossiers": resultat_scoring.get("dossiers", []),
        "frameworks": resultat_scoring.get("frameworks", []),
        "contenu_strategique": data_scanner.get("contenu_strategique", {}),
    }

    # Construire et envoyer le prompt
    prompt = construire_prompt(
        contexte, candidat, scores, conflit,
        signaux_detectes=resultat_scoring.get("signaux_detectes", {})
    )
    
    reponse_ollama = interroger_ollama(prompt)

    # Fallback si Ollama est indisponible
    if not reponse_ollama:
        logger.warning("Ollama indisponible — scoring conservé")
        return _resultat_fallback_ollama(resultat_scoring, conflit)

    # Traiter la réponse selon le contexte
    if conflit.get("conflit"):
        return _traiter_reponse_conflit(resultat_scoring, reponse_ollama)
    else:
        return _traiter_reponse_normale(resultat_scoring, reponse_ollama)


def _resultat_scoring_simple(resultat_scoring: Dict) -> Dict:
    """Retourne le résultat du scoring sans analyse Ollama."""
    return {
        "architecture": resultat_scoring["architecture"],
        "confiance": resultat_scoring["confiance"],
        "scores": resultat_scoring.get("scores", {}),
        "dossiers": resultat_scoring.get("dossiers", []),
        "frameworks": resultat_scoring.get("frameworks", []),
        "justification": f"Détection par scoring (confiance {resultat_scoring['confiance']})",
        "elements_cles": resultat_scoring.get("details", {}).get("signaux", [])[:5],
        "source": "scoring uniquement",
        "candidat_scoring": resultat_scoring["architecture"],
        "reponse_ollama": None,
        "etait_en_conflit": False,
    }


def _resultat_fallback_ollama(resultat_scoring: Dict, conflit: Dict) -> Dict:
    """Retourne le résultat quand Ollama est indisponible."""
    confiance = resultat_scoring.get("confiance", "faible")
    confiance_fallback = "faible" if conflit.get("conflit") else confiance
    
    return {
        "architecture": resultat_scoring["architecture"],
        "confiance": confiance_fallback,
        "scores": resultat_scoring.get("scores", {}),
        "dossiers": resultat_scoring.get("dossiers", []),
        "frameworks": resultat_scoring.get("frameworks", []),
        "justification": "Détection par scoring (Ollama indisponible)",
        "elements_cles": [],
        "source": "scoring uniquement",
        "candidat_scoring": resultat_scoring["architecture"],
        "reponse_ollama": None,
        "etait_en_conflit": conflit.get("conflit", False),
    }


def _traiter_reponse_conflit(resultat_scoring: Dict, reponse_ollama: Dict) -> Dict:
    """Traite la réponse Ollama dans un cas de conflit."""
    conflit = resultat_scoring["conflit"]
    candidat_1 = conflit["candidat_1"]
    candidat_2 = conflit["candidat_2"]
    architecture_ollama = reponse_ollama["architecture"]
    
    if architecture_ollama in (candidat_1, candidat_2):
        return {
            "architecture": architecture_ollama,
            "confiance": reponse_ollama["confiance"],
            "scores": resultat_scoring.get("scores", {}),
            "dossiers": resultat_scoring.get("dossiers", []),
            "frameworks": resultat_scoring.get("frameworks", []),
            "justification": reponse_ollama["justification"],
            "elements_cles": reponse_ollama.get("elements_cles", []),
            "source": "ollama (arbitrage de conflit)",
            "candidat_scoring": resultat_scoring["architecture"],
            "reponse_ollama": architecture_ollama,
            "etait_en_conflit": True,
        }
    
    # Ollama propose une 3ème architecture non pertinente
    return {
        "architecture": resultat_scoring["architecture"],
        "confiance": "faible",
        "scores": resultat_scoring.get("scores", {}),
        "dossiers": resultat_scoring.get("dossiers", []),
        "frameworks": resultat_scoring.get("frameworks", []),
        "justification": "Ollama rejeté (proposition hors périmètre)",
        "elements_cles": [],
        "source": "scoring (rejet Ollama)",
        "candidat_scoring": resultat_scoring["architecture"],
        "reponse_ollama": architecture_ollama,
        "etait_en_conflit": True,
    }


def _traiter_reponse_normale(resultat_scoring: Dict, reponse_ollama: Dict) -> Dict:
    """Traite la réponse Ollama dans un cas normal."""
    candidat = resultat_scoring["architecture"]
    architecture_ollama = reponse_ollama["architecture"]
    confiance = resultat_scoring.get("confiance", "faible")
    
    # Accord entre scoring et Ollama
    if architecture_ollama == candidat:
        confiance_finale = CONFIANCE_BOOST.get(confiance, confiance)
        return {
            "architecture": architecture_ollama,
            "confiance": confiance_finale,
            "scores": resultat_scoring.get("scores", {}),
            "dossiers": resultat_scoring.get("dossiers", []),
            "frameworks": resultat_scoring.get("frameworks", []),
            "justification": reponse_ollama["justification"],
            "elements_cles": reponse_ollama.get("elements_cles", []),
            "source": "scoring + ollama (accord)",
            "candidat_scoring": candidat,
            "reponse_ollama": architecture_ollama,
            "etait_en_conflit": False,
        }
    
    # Désaccord
    scores = resultat_scoring.get("scores", {})
    score_ollama = scores.get(architecture_ollama, 0)
    
    # Architecture proposée n'a aucun score
    if score_ollama == 0:
        return {
            "architecture": candidat,
            "confiance": "faible",
            "scores": scores,
            "dossiers": resultat_scoring.get("dossiers", []),
            "frameworks": resultat_scoring.get("frameworks", []),
            "justification": f"Scoring conservé (Ollama proposé {architecture_ollama} sans signal)",
            "elements_cles": [],
            "source": "scoring (Ollama rejeté)",
            "candidat_scoring": candidat,
            "reponse_ollama": architecture_ollama,
            "etait_en_conflit": False,
        }
    
    # Ollama très confiant
    if reponse_ollama["confiance"] == "élevée":
        return {
            "architecture": architecture_ollama,
            "confiance": reponse_ollama["confiance"],
            "scores": scores,
            "dossiers": resultat_scoring.get("dossiers", []),
            "frameworks": resultat_scoring.get("frameworks", []),
            "justification": reponse_ollama["justification"],
            "elements_cles": reponse_ollama.get("elements_cles", []),
            "source": "ollama (correction confiance élevée)",
            "candidat_scoring": candidat,
            "reponse_ollama": architecture_ollama,
            "etait_en_conflit": False,
        }
    
    # Désaccord sans confiance suffisante
    return {
        "architecture": candidat,
        "confiance": "faible",
        "scores": scores,
        "dossiers": resultat_scoring.get("dossiers", []),
        "frameworks": resultat_scoring.get("frameworks", []),
        "justification": f"Scoring conservé (Ollama pas assez confiant: {reponse_ollama['confiance']})",
        "elements_cles": [],
        "source": "scoring (Ollama rejeté)",
        "candidat_scoring": candidat,
        "reponse_ollama": architecture_ollama,
        "etait_en_conflit": False,
    }