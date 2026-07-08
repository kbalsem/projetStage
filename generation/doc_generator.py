# generation/doc_generator.py
"""
Générateur de documentation par fichier avec cache et batch LLM.
Génère un résumé dynamique pour chaque fichier et module.
"""

import logging
import time
import hashlib
import json
import os
import re
from typing import Dict, List, Tuple

from utils.ollama_client import generer

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION DEPUIS .ENV
# ═══════════════════════════════════════════════════════════════════════════════

CACHE_DIR = os.getenv("DOCGEN_CACHE_DIR", ".cache/docs")
CACHE_ENABLED = os.getenv("DOCGEN_CACHE_ENABLED", "true").lower() == "true"
SEUIL_LLM = int(os.getenv("DOCGEN_SEUIL_LLM", "5"))
SCORE_MOYEN_HAUT = int(os.getenv("DOCGEN_SCORE_MOYEN_HAUT", "20"))
SCORE_MOYEN_BAS = int(os.getenv("DOCGEN_SCORE_MOYEN_BAS", "10"))
BATCH_TAILLE_HAUT = int(os.getenv("DOCGEN_BATCH_HAUT", "2"))
BATCH_TAILLE_MOYEN = int(os.getenv("DOCGEN_BATCH_MOYEN", "4"))
BATCH_TAILLE_BAS = int(os.getenv("DOCGEN_BATCH_BAS", "6"))
MAX_CLASSES_PROMPT = int(os.getenv("DOCGEN_MAX_CLASSES_PROMPT", "5"))
MAX_FONCTIONS_PROMPT = int(os.getenv("DOCGEN_MAX_FONCTIONS_PROMPT", "5"))
MAX_IMPORTS_PROMPT = int(os.getenv("DOCGEN_MAX_IMPORTS_PROMPT", "3"))
MAX_CODE_PROMPT = int(os.getenv("DOCGEN_MAX_CODE_PROMPT", "250"))
DOCGEN_MAX_TOKENS = int(os.getenv("DOCGEN_MAX_TOKENS", "1500"))

DOSSIERS_IGNORES = set(
    d.strip() for d in os.getenv(
        "DOCGEN_DOSSIERS_IGNORES",
        "tests,test,docs,examples,node_modules,vendor,__pycache__,.git"
    ).split(",")
)

PROMPT_VERSION = os.getenv("DOCGEN_PROMPT_VERSION", "3.0")

# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS DE CACHE
# ═══════════════════════════════════════════════════════════════════════════════

def _hash_fichier(chemin: str, infos: dict) -> str:
    data = json.dumps({
        "chemin": chemin, 
        "ast": infos, 
        "prompt_version": PROMPT_VERSION
    }, sort_keys=True, default=str)
    return hashlib.md5(data.encode()).hexdigest()[:12]


def _lire_cache(hash_fichier: str) -> str | None:
    if not CACHE_ENABLED:
        return None
    chemin_cache = os.path.join(CACHE_DIR, f"{hash_fichier}.md")
    if os.path.exists(chemin_cache):
        with open(chemin_cache, "r", encoding="utf-8") as f:
            return f.read()
    return None


def _ecrire_cache(hash_fichier: str, doc: str) -> None:
    if not CACHE_ENABLED:
        return
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(os.path.join(CACHE_DIR, f"{hash_fichier}.md"), "w", encoding="utf-8") as f:
        f.write(doc)


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS DE SCORING
# ═══════════════════════════════════════════════════════════════════════════════

def _score_fichier(infos: dict) -> int:
    return (
        len(infos.get("classes", [])) * 8 +
        len(infos.get("fonctions", [])) * 3 +
        len(infos.get("imports", [])) * 1
    )


def _batch_size_dynamique(fichiers: List[Tuple]) -> int:
    if not fichiers:
        return BATCH_TAILLE_BAS
    score_moyen = sum(_score_fichier(inf) for _, inf in fichiers) / len(fichiers)
    if score_moyen > SCORE_MOYEN_HAUT:
        return BATCH_TAILLE_HAUT
    elif score_moyen > SCORE_MOYEN_BAS:
        return BATCH_TAILLE_MOYEN
    return BATCH_TAILLE_BAS


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS DE GROUPEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def grouper_fichiers(fichiers: List[Tuple]) -> List[List[Tuple]]:
    par_dossier = {}
    for chemin, infos in fichiers:
        dossier = os.path.dirname(chemin)
        par_dossier.setdefault(dossier, []).append((chemin, infos))
    batches = []
    for dossier, fichiers_dossier in par_dossier.items():
        taille = _batch_size_dynamique(fichiers_dossier)
        for i in range(0, len(fichiers_dossier), taille):
            batches.append(fichiers_dossier[i:i + taille])
    return batches


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS DE FORMATAGE
# ═══════════════════════════════════════════════════════════════════════════════

def formater_classes(classes: list) -> str:
    if not classes:
        return "Aucune"
    return " | ".join(c['nom'] for c in classes[:MAX_CLASSES_PROMPT])


def formater_fonctions(fonctions: list) -> str:
    if not fonctions:
        return "Aucune"
    return " | ".join(
        f"{f['nom']}({', '.join(f.get('args', []))})"
        for f in fonctions[:MAX_FONCTIONS_PROMPT]
    )


# ═══════════════════════════════════════════════════════════════════════════════
# RÉSUMÉS DYNAMIQUES
# ═══════════════════════════════════════════════════════════════════════════════

def _extraire_resume(contenu: str) -> str:
    """Extrait le résumé (première phrase après ## 📋 Résumé) du contenu généré."""
    match = re.search(r'##\s*📋\s*Résumé\s*\n+(.*?)(?:\n|$)', contenu, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # Fallback : prendre la première ligne après le titre
    lignes = contenu.strip().split('\n')
    for ligne in lignes:
        ligne = ligne.strip()
        if ligne and not ligne.startswith('#'):
            return ligne[:200]
    return "Documentation générée automatiquement."


def _generer_resume_module(dossier: str, fichiers_docs: Dict[str, str]) -> str:
    """
    Génère un résumé dynamique pour un module (dossier).
    Agrège les résumés de tous les fichiers du dossier.
    """
    resumes = []
    for chemin, doc in fichiers_docs.items():
        if chemin.startswith(dossier):
            resume = _extraire_resume(doc)
            nom_fichier = chemin.split("/")[-1]
            resumes.append(f"- **{nom_fichier}** : {resume}")
    
    if not resumes:
        return "Aucun fichier documenté dans ce module."
    
    return "\n".join(resumes[:10])  # Limiter à 10 fichiers


def _generer_index_module(dossier: str, fichiers_docs: Dict[str, str]) -> str:
    """
    Génère une page index.md pour un module avec :
    - Description du module
    - Liste des fichiers avec résumé
    - Statistiques du module
    """
    fichiers_du_module = {c: d for c, d in fichiers_docs.items() if c.startswith(dossier)}
    nb_fichiers = len(fichiers_du_module)
    
    # Calculer des stats
    total_classes = 0
    total_fonctions = 0
    langages = set()
    
    contenu = f"""# 📁 Module : {dossier if dossier else 'Racine'}

## 📋 Vue d'ensemble
Ce module contient **{nb_fichiers} fichier(s)**.

## 📄 Fichiers du module

"""
    for chemin, doc in sorted(fichiers_du_module.items()):
        nom_fichier = chemin.split("/")[-1]
        resume = _extraire_resume(doc)
        lien = chemin.replace("/", "_").replace(".", "_") + ".md"
        contenu += f"### [{nom_fichier}]({nom_fichier}.md)\n{resume}\n\n"
    
    contenu += f"""
## 📊 Statistiques du module
- **Fichiers** : {nb_fichiers}
- **Classes** : {total_classes}
- **Fonctions** : {total_fonctions}
"""
    return contenu


# ═══════════════════════════════════════════════════════════════════════════════
# GÉNÉRATION
# ═══════════════════════════════════════════════════════════════════════════════

def generer_doc_batch(fichiers_batch: List[Tuple], architecture: str) -> str:
    prompt = "Tu es un expert en documentation de code. Génère toute la documentation en français.\n\n"
    for chemin, infos in fichiers_batch:
        prompt += f"""### FICHIER: {chemin}
Architecture: {architecture}
Classes: {formater_classes(infos.get('classes', []))}
Fonctions: {formater_fonctions(infos.get('fonctions', []))}
Imports: {', '.join(infos.get('imports', [])[:MAX_IMPORTS_PROMPT])}
Code: {infos.get('code_brut', '')[:MAX_CODE_PROMPT]}

"""
    prompt += """RÈGLES STRICTES - Format EXACT pour chaque fichier:

## FILE: {chemin}
## 📋 Résumé
(une phrase)
## 🎯 Rôle du fichier
(2-3 phrases)
## 🏗️ Classes et méthodes
(liste)
## ⚡ Fonctions principales
(liste)
## 📦 Dépendances et imports
(liste)
## 🔗 Intégration dans le projet
(description)
## 💡 Exemple d'utilisation
(court exemple)
## ⚠️ Points notables
(particularités)
---"""

    debut = time.time()
    doc = generer(prompt, max_tokens=DOCGEN_MAX_TOKENS)
    logger.info(f"Batch {len(fichiers_batch)} fichiers en {time.time() - debut:.2f}s")
    return doc


def _parser_sortie_batch(texte: str, chemins: set) -> dict:
    docs = {}
    for chemin in chemins:
        pattern = rf"(?:##\s*)?FILE:\s*{re.escape(chemin)}\s*\n(.*?)(?=\n(?:##\s*)?FILE:\s|\Z)"
        match = re.search(pattern, texte, re.DOTALL)
        if match:
            contenu = match.group(1).strip()
            contenu = re.sub(r"\n---\s*$", "", contenu)
            docs[chemin] = f"# {chemin}\n\n{contenu}"
        else:
            docs[chemin] = f"# {chemin}\n\nDocumentation non générée."
    return docs


def generer_doc_rapide(chemin: str, infos_ast: dict) -> str:
    """
    Génère une documentation rapide SANS LLM, avec résumé dynamique.
    """
    classes = infos_ast.get("classes", [])
    fonctions = infos_ast.get("fonctions", [])
    imports = infos_ast.get("imports", [])[:MAX_IMPORTS_PROMPT]
    langage = infos_ast.get("langage", "Inconnu")

    # Générer un résumé automatique basé sur le contenu
    resume_parts = []
    if classes:
        resume_parts.append(f"Contient {len(classes)} classe(s) : {', '.join(c['nom'] for c in classes[:3])}")
    if fonctions:
        resume_parts.append(f"Expose {len(fonctions)} fonction(s)")
    if imports:
        resume_parts.append(f"Utilise {len(imports)} import(s)")
    
    resume = ". ".join(resume_parts) if resume_parts else f"Fichier {langage} sans classe ni fonction détectée."

    doc = f"""# {chemin}

## 📋 Résumé
{resume}

**Langage** : {langage}
**Chemin dans l'architecture cible** : `{chemin}`

"""
    if classes:
        doc += f"## 🏗️ Classes ({len(classes)})\n"
        for c in classes[:MAX_CLASSES_PROMPT]:
            doc += f"- **{c['nom']}** (ligne {c.get('ligne', '?')})\n"
            for m in c.get('methodes', [])[:5]:
                doc += f"  - `{m['nom']}({', '.join(m.get('args', []))})`\n"

    if fonctions:
        doc += f"## ⚡ Fonctions ({len(fonctions)})\n"
        for f in fonctions[:MAX_FONCTIONS_PROMPT]:
            args = ", ".join(f.get("args", []))
            doc += f"- **{f['nom']}({args})** (ligne {f.get('ligne', '?')})\n"

    if imports:
        doc += "## 📦 Imports\n"
        for imp in imports[:10]:
            doc += f"- `{imp}`\n"

    return doc


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTION PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════════

def generer_doc_tous_fichiers(infos_ast: dict, architecture: str) -> dict:
    """
    Génère la documentation pour tous les fichiers avec résumés dynamiques.
    Retourne aussi les index de modules.
    """
    docs = {}
    fichiers_ollama = []
    fichiers_rapides = []

    # 1. Classification + cache
    for chemin, infos in infos_ast.items():
        if any(chemin.startswith(d) for d in DOSSIERS_IGNORES):
            fichiers_rapides.append((chemin, infos))
            continue
        if _score_fichier(infos) < SEUIL_LLM:
            fichiers_rapides.append((chemin, infos))
            continue
        hash_f = _hash_fichier(chemin, infos)
        cache = _lire_cache(hash_f)
        if cache:
            docs[chemin] = cache
        else:
            fichiers_ollama.append((chemin, infos))

    total = len(infos_ast)
    logger.info(f"LLM: {len(fichiers_ollama)}, Rapide: {len(fichiers_rapides)}, Cache: {len(docs)}")

    # 2. Trier par importance
    fichiers_ollama.sort(key=lambda x: _score_fichier(x[1]), reverse=True)

    # 3. Fichiers rapides
    compteur = len(docs)
    for chemin, infos in fichiers_rapides:
        compteur += 1
        print(f"  [{compteur}/{total}] Rapide : {chemin}")
        docs[chemin] = generer_doc_rapide(chemin, infos)

    # 4. Batch LLM
    for batch in grouper_fichiers(fichiers_ollama):
        try:
            chemins_batch = {chemin for chemin, _ in batch}
            texte_batch = generer_doc_batch(batch, architecture)
            docs_batch = _parser_sortie_batch(texte_batch, chemins_batch)
            for chemin, doc in docs_batch.items():
                docs[chemin] = doc
                infos = next((inf for c, inf in batch if c == chemin), {})
                if infos:
                    _ecrire_cache(_hash_fichier(chemin, infos), doc)
                compteur += 1
                print(f"  [{compteur}/{total}] Batch LLM : {chemin}")
        except Exception as e:
            logger.error(f"Erreur batch : {e}")
            for chemin, infos in batch:
                docs[chemin] = generer_doc_rapide(chemin, infos)
                compteur += 1
                print(f"  [{compteur}/{total}] Fallback : {chemin}")

    # 5. Générer les index de modules
    modules = set()
    for chemin in docs.keys():
        dossier = os.path.dirname(chemin)
        if dossier:
            modules.add(dossier)
    
    for module in sorted(modules):
        index_path = f"{module}/index.md" if module else "index.md"
        docs[index_path] = _generer_index_module(module, docs)
        print(f"  Index module généré : {index_path}")

    return docs