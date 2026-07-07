# Calculatrice-en-java

## 📋 Description
La calculatrice en Java est un outil simple et efficace pour effectuer des opérations mathématiques. Elle propose plusieurs modes de fonctionnement, notamment scientifique et simple, ainsi que des fonctions d'import/export de fichiers.

## 🏛️ Architecture
L'architecture du projet est monolithique, ce qui signifie qu'elle est conçue comme un seul bloc logiciel sans composants distincts. Cela permet une organisation claire et facile à comprendre du code source.

## 📁 Structure du projet

* `README.md`: fichier de documentation principal
* `bin/Calculatrice.jar`: fichier exécutable du projet
* `class/.gitignore`: fichier d'ignorance pour Git
* `src/`
	+ `Affichage.java`: classe responsable de l'affichage des résultats
	+ `CalcEventAbout.java`, `CalcEventButton.java`, `CalcEventClear.java`, `CalcEventImport.java`, `CalcEventMode.java`, `CalcEventRes.java`, `CalcEventShortcut.java`: classes gérant les événements du projet
	+ `Calculatrice.java`, `CalculatriceScientifique.java`, `CalculatriceSimple.java`: classes principales du projet
	+ `ModeleCalcul.java`: classe modélisant les opérations mathématiques
	+ `ReadCalcFile.java`, `WriteCalcFile.java`: classes gérant l'import/export de fichiers

## 🚀 Installation
Pour installer le projet, il suffit de télécharger et d'exécuter le fichier `Calculatrice.jar` dans un environnement Java compatible.

## 💻 Utilisation
Voici quelques exemples d'utilisation du projet :

* Pour utiliser la calculatrice simple, exécutez le fichier `Calculatrice.jar` et suivez les instructions affichées.
* Pour utiliser la calculatrice scientifique, exécutez le fichier `CalculatriceScientifique.jar` (si présent) et suivez les instructions affichées.

## 🛠️ Technologies
Les technologies et frameworks utilisés dans ce projet sont :

* Java

## 🤝 Contribution
Pour contribuer au projet, veuillez contacter l'auteur Yasminemlk. Les contributions sont appréciées sous forme de pull requests sur le dépôt Git du projet.

## 📄 Licence
Le projet Calculatrice-en-java est sous licence Apache 2.0.