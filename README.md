# Police et voleur

Petit jeu de plateau local en Python pour deux joueurs. L'interface est réalisée
avec Tkinter, inclus avec Python : aucune dépendance externe n'est nécessaire.

## Structure du projet

```text
controller/   gestion des clics et des tours
model/        plateau, règles et état de la partie
view/         écrans, menus et dessin Tkinter
assets/       téléchargement et cache local des pions CC0
tests/        tests du modèle
main.py       point d'entrée de l'application
```

## Lancer le jeu

Depuis le dossier du projet, exécutez :

```bash
python police_voleur.py
```

Le fichier `police_voleur.py` conserve le lancement habituel et délègue à
`main.py`.

## Menus et personnalisation

Le menu propose **Jouer**, **Paramètres**, **Comment jouer** et **Quitter**.
Dans les paramètres, vous pouvez choisir un thème, les couleurs des policiers
et du voleur, ainsi qu'un style de pion. Les préférences sont sauvegardées dans
le dossier de configuration utilisateur.

Dans **Plateau et pions**, vous pouvez aussi choisir un plateau classique, bois
ou ardoise. La galerie propose trois images de pions de Kenney. Elles sont
téléchargées à la demande, mises en cache pour le jeu hors ligne et publiées
sous licence CC0 : [Board Game Icons](https://kenney.nl/assets/board-game-icons).

Pendant la partie, le plateau est centré entre le panneau du voleur à gauche et
celui de la police à droite. Les règles complètes restent dans l'écran
**Comment jouer**.
