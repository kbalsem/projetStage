# ─── Prompt documentation par fichier ────────────────────────────────────────
PROMPT_FICHIER = """Tu es un expert en documentation logicielle.
Analyse ce fichier et génère une documentation technique en Markdown.ENTIÈREMENT EN FRANÇAIS

Fichier : {filename}
Architecture du projet : {architecture}

Classes détectées : {classes}
Fonctions détectées : {fonctions}
Imports : {imports}

Code source :
{code}

Génère UNIQUEMENT ce Markdown, sans texte avant ou après :

## Rôle du fichier
(une phrase claire)

## Classes et méthodes
(liste des classes avec leur rôle)

## Fonctions principales
(pour chaque fonction : rôle et paramètres)

## Rôle dans le projet
(comment ce fichier s'intègre dans l'architecture {architecture})
"""

# ─── Prompt documentation globale ────────────────────────────────────────────
PROMPT_GLOBAL = """Tu es un expert en architecture logicielle.
Génère une documentation globale pour ce projet en Markdown.ENTIÈREMENT EN FRANÇAIS

Projet : {repo_name}
Architecture détectée : {architecture}
Frameworks : {frameworks}
Nombre de fichiers : {nb_fichiers}
Fichiers principaux : {fichiers_principaux}

Génère UNIQUEMENT ce Markdown :

## Architecture générale
(description de l'architecture {architecture} et comment ce projet l'applique)

## Modules principaux
(liste et rôle de chaque module)

## Flux du programme
(comment les composants interagissent)

## Technologies utilisées
(liste des technologies détectées)
"""

# ─── Prompt README ────────────────────────────────────────────────────────────
PROMPT_README = """Tu es un expert en documentation logicielle.
Génère un README complet et professionnel en Markdown, ENTIÈREMENT EN FRANÇAIS.

Projet : {repo_name}
Auteur : {author}
Architecture : {architecture}
Frameworks : {frameworks}
Description existante : {description}

Voici la VRAIE structure de fichiers du projet (utilise UNIQUEMENT ces fichiers réels, n'invente aucun fichier) :
{structure_fichiers}

Génère UNIQUEMENT ce Markdown, rien d'autre, pas de phrase avant ou après :

# {repo_name}

## Description
(description claire du projet)

## Architecture
(type d'architecture et organisation)

## Installation
(étapes d'installation)

## Utilisation
(comment utiliser le projet)

## Structure du projet
(reprends la structure de fichiers réelle donnée ci-dessus, ne l'invente pas)

## Contribution
(comment contribuer)

## Licence
(licence du projet)
"""