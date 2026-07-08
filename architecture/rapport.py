# architecture/rapport.py
"""
Produit un rapport Markdown détaillé de l'analyse architecturale.
"""

import os
from typing import Dict

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION DEPUIS .ENV
# ═══════════════════════════════════════════════════════════════════════════════

# Limites d'affichage
MAX_SIGNAUX_RAPPORT = int(os.getenv("RAPPORT_MAX_SIGNAUX", "15"))
MAX_SIGNAUX_CONTRIBUES = int(os.getenv("RAPPORT_MAX_SIGNAUX_CONTRIBUES", "20"))
MAX_SCORES_BARRE = int(os.getenv("RAPPORT_MAX_SCORES_BARRE", "20"))

# Template de la barre de progression
BARRE_PROGRESSION = os.getenv("RAPPORT_BARRE_PROGRESSION", "█░")

# Titre du rapport
RAPPORT_TITRE = os.getenv("RAPPORT_TITRE", "Rapport de détection d'architecture")

# ═══════════════════════════════════════════════════════════════════════════════
# DESCRIPTIONS DES ARCHITECTURES
# ═══════════════════════════════════════════════════════════════════════════════

DESCRIPTIONS_ARCHITECTURES = {
    "MVC": "Modèle-Vue-Contrôleur — séparation données / affichage / logique",
    "MVP": "Modèle-Vue-Présentateur — Presenter gère toute la logique UI",
    "MVVM": "Modèle-Vue-VueModèle — data binding entre Vue et ViewModel",
    "COUCHES": "Architecture en couches — Présentation / Métier / Données",
    "CLEAN": "Clean Architecture — Use Cases / Entities / Repositories",
    "MICROSERVICES": "Microservices — services indépendants communicants",
    "MONOLITHIQUE": "Application monolithique — structure simple sans séparation claire"
}

# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS DE FORMATAGE
# ═══════════════════════════════════════════════════════════════════════════════

def _generer_barre(score: float, maximum: int = None) -> str:
    """
    Génère une barre de progression ASCII.
    
    Args:
        score: Score à représenter
        maximum: Valeur maximale de la barre
        
    Returns:
        Chaîne représentant la barre
    """
    if maximum is None:
        maximum = MAX_SCORES_BARRE
    
    rempli = min(int(score), maximum)
    vide = max(0, maximum - rempli)
    
    return BARRE_PROGRESSION[0] * rempli + BARRE_PROGRESSION[1] * vide


def _formater_liste_signaux(signaux: set, limite: int = None) -> str:
    """
    Formate une liste de signaux pour le rapport.
    
    Args:
        signaux: Ensemble des signaux
        limite: Nombre maximum à afficher
        
    Returns:
        Chaîne formatée
    """
    if limite is None:
        limite = MAX_SIGNAUX_RAPPORT
    
    if not signaux:
        return "Aucun"
    
    liste = sorted(signaux)[:limite]
    resultat = ', '.join(liste)
    
    if len(signaux) > limite:
        resultat += f" ... et {len(signaux) - limite} autre(s)"
    
    return resultat


# ═══════════════════════════════════════════════════════════════════════════════
# SECTIONS DU RAPPORT
# ═══════════════════════════════════════════════════════════════════════════════

def _section_resultat(architecture: str, confiance: str, 
                      description: str, couverture: float) -> str:
    """Génère la section Résultat du rapport."""
    return f"""
# {RAPPORT_TITRE}

## 📊 Résultat
- **Architecture détectée** : `{architecture}`
- **Description** : {description}
- **Niveau de confiance** : {confiance}
- **Couverture des signaux** : {couverture}%
"""


def _section_signaux_detectes(signaux_detectes: Dict) -> str:
    """Génère la section Signaux détectés."""
    section = "\n## 🔍 Signaux détectés\n"
    
    categories = [
        ("dossiers", "📁 Dossiers"),
        ("frameworks", "🔧 Frameworks"),
        ("fichiers", "📄 Fichiers caractéristiques"),
        ("imports", "📦 Imports"),
        ("decorateurs", "🏷️ Décorateurs"),
        ("classes", "📋 Classes"),
        ("dependances", "📚 Dépendances"),
    ]
    
    for cle, titre in categories:
        if signaux_detectes.get(cle):
            signaux = signaux_detectes[cle]
            section += f"- **{titre}** ({len(signaux)}) : {_formater_liste_signaux(signaux)}\n"
    
    return section


def _section_signaux_contributeurs(details: Dict) -> str:
    """Génère la section des signaux contributeurs."""
    if not details.get("signaux"):
        return ""
    
    section = "\n## ✅ Signaux ayant contribué au score\n"
    for s in details["signaux"][:MAX_SIGNAUX_CONTRIBUES]:
        section += f"- `{s}`\n"
    
    if len(details["signaux"]) > MAX_SIGNAUX_CONTRIBUES:
        section += f"- ... et {len(details['signaux']) - MAX_SIGNAUX_CONTRIBUES} autre(s)\n"
    
    return section


def _section_regles(details: Dict) -> str:
    """Génère la section des règles activées."""
    if not details.get("regles"):
        return ""
    
    section = "\n## 🎯 Règles de combinaison activées\n"
    for r in details["regles"]:
        section += f"- {r}\n"
    
    return section


def _section_anti_signaux(details: Dict) -> str:
    """Génère la section des anti-signaux."""
    if not details.get("anti_signaux"):
        return ""
    
    section = "\n## ⚠️ Anti-signaux détectés (pénalités)\n"
    for a in details["anti_signaux"]:
        section += f"- {a}\n"
    
    return section


def _section_scores(scores: Dict, couverture: Dict) -> str:
    """Génère la section des scores par architecture."""
    section = "\n## 📈 Scores par architecture\n"
    
    for arch, score in scores.items():
        barre = _generer_barre(score)
        couv = couverture.get(arch, 0)
        section += f"- `{arch:<15}` {barre} {score:.1f} pts (couverture: {couv}%)\n"
    
    return section


def _section_couverture(couverture: Dict) -> str:
    """Génère la section de couverture détaillée."""
    if not couverture:
        return ""
    
    section = "\n## 📊 Couverture des signaux par architecture\n"
    
    for arch, pct in couverture.items():
        barre_couv = _generer_barre(pct / 5)
        section += f"- `{arch:<15}` {barre_couv} {pct}%\n"
    
    return section


def _section_ollama(resultat: Dict) -> str:
    """Génère la section analyse Ollama."""
    if not resultat.get("justification"):
        return ""
    
    section = f"""
## 🤖 Analyse Ollama
- **Justification** : {resultat['justification']}
- **Source** : {resultat.get('source', 'N/A')}
"""
    
    if resultat.get("elements_cles"):
        section += "- **Éléments clés** :\n"
        for el in resultat["elements_cles"]:
            section += f"  - {el}\n"

    candidat = resultat.get("candidat_scoring")
    ollama = resultat.get("reponse_ollama")
    
    if candidat and ollama:
        if candidat == ollama:
            section += f"\n✔️ Ollama confirme le scoring : **{ollama}**\n"
        else:
            section += f"\n⚠️ Ollama a corrigé le scoring : **{candidat}** → **{ollama}**\n"

    if resultat.get("raison_ollama"):
        section += f"\n- **Raison appel Ollama** : {resultat['raison_ollama']}\n"
    
    return section


def _section_projet(data: Dict) -> str:
    """Génère la section informations du projet."""
    return f"""
## 📁 Projet analysé
- **Nom** : {data.get('repo_name', 'Inconnu')}
- **Auteur** : {data.get('author', 'Inconnu')}
- **Branche** : {data.get('branch', 'N/A')}
- **Fichiers** : {len(data.get('fichiers', []))}
- **Commits** : {data.get('commits', 0)}
- **Stars** : {data.get('stars', 0)}
- **Licence** : {data.get('licence', 'Non spécifiée')}
- **Description** : {data.get('description', 'Aucune')[:200]}
"""


def _section_footer() -> str:
    """Génère le pied de page du rapport."""
    from datetime import datetime
    return f"""
---
*Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} par GitDoc AI*
"""


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTION PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════════

def generer_rapport(resultat: Dict, data: Dict) -> str:
    """
    Génère un rapport complet de la détection d'architecture.
    
    Args:
        resultat: Résultat de la détection d'architecture
        data: Données du projet analysé
        
    Returns:
        Rapport formaté en Markdown
    """
    # Extraire les informations principales
    architecture = resultat.get("architecture", "Inconnue")
    confiance = resultat.get("confiance", "faible")
    scores = resultat.get("scores", {})
    signaux_detectes = resultat.get("signaux_detectes", {})
    details = resultat.get("details", {})
    couverture = resultat.get("couverture", {})
    
    # Obtenir la description
    description = DESCRIPTIONS_ARCHITECTURES.get(
        architecture, 
        f"Architecture {architecture} — pas de description disponible"
    )
    
    # Couverture de l'architecture détectée
    couv_archi = couverture.get(architecture, 0)
    
    # Construire le rapport section par section
    rapport = _section_resultat(architecture, confiance, description, couv_archi)
    rapport += _section_signaux_detectes(signaux_detectes)
    rapport += _section_signaux_contributeurs(details)
    rapport += _section_regles(details)
    rapport += _section_anti_signaux(details)
    rapport += _section_scores(scores, couverture)
    rapport += _section_couverture(couverture)
    rapport += _section_ollama(resultat)
    rapport += _section_projet(data)
    rapport += _section_footer()
    
    return rapport.strip()


def generer_rapport_json(resultat: Dict, data: Dict) -> Dict:
    """
    Génère un rapport au format JSON (pour API).
    
    Args:
        resultat: Résultat de la détection
        data: Données du projet
        
    Returns:
        Dictionnaire JSON
    """
    return {
        "architecture": resultat.get("architecture"),
        "confiance": resultat.get("confiance"),
        "description": DESCRIPTIONS_ARCHITECTURES.get(
            resultat.get("architecture", ""), ""
        ),
        "scores": resultat.get("scores", {}),
        "couverture": resultat.get("couverture", {}),
        "signaux_detectes": {
            cat: list(signaux)[:MAX_SIGNAUX_RAPPORT]
            for cat, signaux in resultat.get("signaux_detectes", {}).items()
        },
        "projet": {
            "nom": data.get("repo_name"),
            "auteur": data.get("author"),
            "fichiers": len(data.get("fichiers", [])),
            "commits": data.get("commits", 0),
        }
    }


def sauvegarder_rapport(rapport: str, chemin_sortie: str) -> None:
    """
    Sauvegarde le rapport dans un fichier.
    
    Args:
        rapport: Contenu du rapport
        chemin_sortie: Chemin du fichier de sortie
    """
    with open(chemin_sortie, "w", encoding="utf-8") as f:
        f.write(rapport)