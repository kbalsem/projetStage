# generation/prompts.py

# ═══════════════════════════════════════════════════════════════════════════════
# RÈGLE GLOBALE (injectée dans tous les prompts)
# ═══════════════════════════════════════════════════════════════════════════════

REGLE_ANTI_HALLUCINATION = """
RÈGLES STRICTES :
- N'invente AUCUNE information non présente dans les données fournies
- Utilise UNIQUEMENT les classes, fonctions, imports et fichiers mentionnés
- Ne complète pas, ne déduis pas, n'ajoute pas de contenu externe
- Si une section n'a pas d'information, écris "Aucune information disponible"
"""

# ═══════════════════════════════════════════════════════════════════════════════
# PROMPT DOCUMENTATION PAR FICHIER (ENRICHI)
# ═══════════════════════════════════════════════════════════════════════════════

PROMPT_FICHIER = """Tu es un expert en documentation logicielle.
Analyse ce fichier et génère une documentation technique détaillée en Markdown.
Génère toute la documentation en français.

Fichier : {filename}
Architecture du projet : {architecture}

Classes détectées : {classes}
Fonctions détectées : {fonctions}
Imports : {imports}

Code source :
{code}

""" + REGLE_ANTI_HALLUCINATION + """

Génère UNIQUEMENT ce Markdown, sans texte avant ou après :

## 📋 Résumé
(Une phrase qui résume le rôle exact de ce fichier dans le projet)

## 🎯 Rôle du fichier
(2-3 phrases expliquant la responsabilité principale de ce fichier dans l'architecture {architecture})

## 🏗️ Classes et méthodes
(pour chaque classe FOURNIE : 
- **NomClasse** : son rôle, ses responsabilités
- Méthodes : liste avec une courte description par méthode
- Attributs : liste si visible dans le code)

## ⚡ Fonctions principales
(pour chaque fonction FOURNIE : 
- **nom_fonction(params)** : ce qu'elle fait exactement
- Paramètres : description de chaque paramètre
- Retourne : type et description de la valeur retournée)

## 📦 Dépendances et imports
- **Externes** : (libs externes visibles dans les imports)
- **Internes** : (modules du projet utilisés)

## 🔗 Intégration dans le projet
(comment ce fichier s'intègre dans l'architecture {architecture} : 
quels modules il utilise, lesquels l'utilisent, quel pattern il implémente)

## 💡 Exemple d'utilisation
(un court exemple d'utilisation si le code le permet)

## ⚠️ Points notables
(complexité, dépendances, patterns utilisés, particularités du code)"""


# ═══════════════════════════════════════════════════════════════════════════════
# PROMPT DOCUMENTATION GLOBALE (ENRICHI)
# ═══════════════════════════════════════════════════════════════════════════════

PROMPT_GLOBAL = """Tu es un expert en architecture logicielle.
Génère une documentation globale pour ce projet en Markdown.
Génère toute la documentation en français.

Projet : {repo_name}
Architecture détectée : {architecture}
Frameworks : {frameworks}
Nombre de fichiers : {nb_fichiers}
Fichiers principaux : {fichiers_principaux}

""" + REGLE_ANTI_HALLUCINATION + """

Décris uniquement les interactions visibles dans la structure du projet et les imports.
Ne suppose pas de comportements non visibles.

Génère UNIQUEMENT ce Markdown :

## 📋 Résumé du projet
(une phrase qui décrit ce que fait ce projet)

## 🏛️ Architecture générale
(description de l'architecture {architecture} et comment ce projet l'applique concrètement)

## 📁 Modules principaux
(pour chaque dossier/module : son rôle, ce qu'il contient, ses responsabilités)

## 🔄 Flux du programme
(interactions visibles entre modules via les imports, flux de données)

## 🛠️ Technologies utilisées
(liste des frameworks et technologies détectés, avec leur rôle dans le projet)

## 📊 Statistiques
- Nombre total de fichiers : {nb_fichiers}
- Architecture : {architecture}
- Frameworks : {frameworks}

## 🗂️ Organisation du code
(comment les fichiers sont organisés, structure des dossiers)"""


# ═══════════════════════════════════════════════════════════════════════════════
# PROMPT README (ENRICHI)
# ═══════════════════════════════════════════════════════════════════════════════

PROMPT_README = """Tu es un expert en documentation logicielle.
Génère un README complet et professionnel en Markdown.
Génère toute la documentation en français.

Projet : {repo_name}
Auteur : {author}
Architecture : {architecture}
Frameworks : {frameworks}
Description existante : {description}

Voici la VRAIE structure de fichiers du projet :
{structure_fichiers}

INTERDICTION ABSOLUE :
- Ne pas inventer de fichiers
- Ne pas ajouter de dossiers absents de la structure fournie
- Ne pas modifier les noms, l'ordre ou la hiérarchie
- Ne pas ajouter de composants non présents

Génère UNIQUEMENT ce Markdown, rien d'autre :

# {repo_name}

## 📋 Description
(description claire du projet basée sur la description existante)

## 🏛️ Architecture
(type d'architecture {architecture} et organisation visible du code)

## 📁 Structure du projet
(reproduis EXACTEMENT la structure fournie sans modification)

## 🚀 Installation
(étapes d'installation basées sur la structure du projet et les frameworks détectés)

## 💻 Utilisation
(exemples d'utilisation basés sur les fichiers principaux)

## 🛠️ Technologies
(technologies et frameworks détectés)

## 🤝 Contribution
(comment contribuer au projet)

## 📄 Licence
(licence du projet)"""