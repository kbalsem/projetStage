## 📋 Résumé du projet
Ce projet est une application web construite avec le framework Flask et utilise l'architecture modèle-vue-contrôleur (MVC).

## 🏛️ Architecture générale
L'architecture MVC est appliquée concrètement dans ce projet en séparant les responsabilités entre les modèles, les vues et les contrôleurs. Les modèles représentent les données de l'application, les vues gèrent les affichages et les interactions avec l'utilisateur, tandis que les contrôleurs traitent les requêtes et les réponses.

## 📁 Modules principaux
* `tests/tests`: Contient des tests pour vérifier le fonctionnement du code. Les tests sont divisés en trois sous-modules : `test_views.py`, `test_cli.py` et `test_helpers.py`.
* `src/flask/json/tag.py`: Fichier qui définit une classe pour gérer les balises JSON.
* Aucune information disponible.

## 🔄 Flux du programme
Les interactions visibles entre modules se font via les imports. Voici quelques-uns des flux de données notables :
* Les vues importent les modèles pour récupérer les données.
* Les contrôleurs importent les vues pour gérer les requêtes et les réponses.

## 🛠️ Technologies utilisées
* Flask : Framework web pour construire l'application.
* Aucune autre technologie détectée.

## 📊 Statistiques
- Nombre total de fichiers : 236
- Architecture : MVC
- Frameworks : Flask

## 🗂️ Organisation du code
Le code est organisé dans les dossiers suivants :
* `tests`: Contient des tests pour vérifier le fonctionnement du code.
* `src/flask`: Contient les fichiers source de l'application, notamment le fichier `json/tag.py`.
* Aucun autre dossier détecté.