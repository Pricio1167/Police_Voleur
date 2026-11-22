# Police et voleur

Jeu de plateau local en Python pour deux joueurs, avec une interface graphique
Tkinter. Aucune dépendance Python externe n'est nécessaire.

## Structure du projet

```text
controller/game_controller.py   clics, sélection des pions et tours
model/game_state.py              plateau et règles
view/game_view.py                menus, écrans et affichage
assets/pawn_assets.py            téléchargement et cache des pions CC0
tests/                           tests automatisés
main.py                          point d'entrée
police_voleur.py                 lanceur
```

## Lancer le jeu

Python 3 avec Tkinter est requis. Depuis le dossier du projet, lancez :

```bash
python police_voleur.py
```

`police_voleur.py` délègue le démarrage à `main.py`.

## Règles et commandes

1. Au début, le joueur policier place un pion sur le cercle intérieur, puis
   deux pions sur des intersections libres du bord.
2. Le voleur commence au centre. Les deux joueurs jouent ensuite à tour de rôle.
3. Sélectionnez un pion, puis une intersection libre reliée par un trait. Un
   joueur déplace un seul pion par tour.
4. Le voleur gagne en revenant au centre. La police gagne si le voleur n'a plus
   de déplacement possible.

Cliquez sur **Comment jouer** dans le menu pour consulter le rappel des règles.
Pendant la partie, les destinations légales sont indiquées en vert.

## Personnalisation

Le menu propose **Jouer**, **Paramètres**, **Comment jouer** et **Quitter**.
Les paramètres permettent de choisir un thème d'interface, les couleurs des
pions et l'apparence du plateau : classique, bois ou ardoise.

La galerie propose trois styles de pions du pack
[Kenney Board Game Icons](https://kenney.nl/assets/board-game-icons), publié
sous licence CC0. Les images sont téléchargées à la demande, puis conservées
dans le dossier de configuration utilisateur pour être réutilisées hors ligne.
Une connexion Internet est donc nécessaire uniquement pour le premier
téléchargement.

Pendant la partie, le plateau est au centre, avec le panneau du voleur à gauche
et celui de la police à droite.

## Tests

Depuis le dossier du projet, exécutez :

```bash
python -m unittest discover -v
```
