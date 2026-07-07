# pluginbase

## 📋 Description
Le pluginbase est un framework de développement de plugins pour les applications web. Il utilise l'architecture MVC et fournit une structure claire pour organiser vos plugins.

## 🏛️ Architecture
L'architecture du pluginbase est basée sur le modèle-vue-contrôleur (MVC). Les vues sont chargées par les contrôleurs qui gèrent les requêtes HTTP. Les modèles représentent les données de l'application et sont utilisés pour stocker et récupérer les informations.

## 📁 Structure du projet
Voici la structure actuelle du projet :

* `.gitignore`
* `.travis.yml`
* `LICENSE`
* `MANIFEST.in`
* `Makefile`
* `Pipfile`
* `README.rst`
* `docs/Makefile`
* `docs/_static/itsdangerous.png`
* `docs/_themes/.gitignore`
* `docs/_themes/LICENSE`
* `docs/_themes/README`
* `docs/_themes/flask_small/layout.html`
* `docs/_themes/flask_small/static/flasky.css_t`
* `docs/_themes/flask_small/theme.conf`
* `docs/_themes/flask_theme_support.py`
* `docs/conf.py`
* `docs/index.rst`
* `docs/make.bat`
* `example/README`
* `example/app1/plugins/secret.py`
* `example/app2/plugins/randomstr.py`
* `example/builtin_plugins/lowercase.py`
* `example/builtin_plugins/uppercase.py`
* `example/example.py`
* `pluginbase.py`
* `setup.py`
* `tests/conftest.py`
* `tests/dummy.py`
* `tests/plugins/advanced.py`
* `tests/plugins/hello.py`
* `tests/plugins/hello2.py`
* `tests/plugins/withresources/__init__.py`
* `tests/plugins/withresources/hello.txt`
* `tests/shutdown.py`
* `tests/test_advanced.py`
* `tests/test_basics.py`
* `tests/test_shutdown.py`
* `tox.ini`

## 🚀 Installation
Pour installer le pluginbase, vous pouvez utiliser pip :
```
pip install pluginbase
```
Ensuite, vous pouvez créer un nouveau projet en utilisant le fichier `pluginbase.py` comme modèle.

## 💻 Utilisation
Voici quelques exemples d'utilisation du pluginbase :

* Créez un nouveau projet en copiant le fichier `pluginbase.py` et en modifiant les noms des fichiers et des variables.
* Ajoutez vos propres plugins au répertoire `plugins/`.
* Utilisez les fonctions de base pour gérer les requêtes HTTP.

## 🛠️ Technologies
Le pluginbase utilise les frameworks suivants :

* Flask

## 🤝 Contribution
Pour contribuer au pluginbase, vous pouvez :

* Envoyer des pull requests avec vos modifications.
* Ouvrir des issues pour signaler les bugs ou demander de nouvelles fonctionnalités.

## 📄 Licence
Le pluginbase est sous licence MIT.