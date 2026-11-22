# Police et voleur

Jeu de plateau en Python pour deux joueurs sur le même PC ou en réseau local (LAN), avec une interface graphique
Tkinter. Aucune dépendance Python externe n'est nécessaire.

## Structure du projet

```text
controller/game_controller.py   clics, sélection des pions et tours
controller/lan_session.py        connexion LAN et échange des coups
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

## Jouer sur deux PC en LAN

1. Mettez la même version du dossier du jeu sur les deux PC et connectez-les
   au même réseau Wi-Fi ou Ethernet. Dans le dossier du projet, lancez
   `python police_voleur.py` sur chacun.
2. Sur le PC du policier, cliquez sur **Héberger (Police)**. Ouvrez un terminal,
   tapez `ipconfig` et relevez l’**Adresse IPv4** de la carte Wi-Fi ou Ethernet
   utilisée, par exemple `192.168.1.24`.
3. Sur le PC du voleur, cliquez sur **Rejoindre (Voleur)** et saisissez cette
   adresse. Une fois connecté, le policier place ses trois pions, puis le
   voleur joue son premier coup.

Si Windows demande d’autoriser Python à communiquer, autorisez-le sur les
**réseaux privés** du PC qui héberge. La connexion utilise le port TCP
`47650`. Le jeu en LAN fonctionne sans Internet.

Pour jouer à deux sur un seul ordinateur, choisissez **Jouer sur ce PC**.

### Si la connexion échoue

- Laissez le PC du policier sur l’écran d’attente et vérifiez que l’adresse
  saisie sur le PC du voleur correspond à la carte réseau utilisée par le PC
  du policier.
- Depuis PowerShell sur le PC du voleur, lancez la commande suivante en
  remplaçant l’adresse d’exemple par celle du policier.

  ```powershell
  Test-NetConnection 192.168.1.24 -Port 47650
  ```

  Si `TcpTestSucceeded` vaut `False`, vérifiez le pare-feu du PC du policier
  et essayez un réseau partagé qui autorise les appareils à communiquer.
  Après ce test, revenez au menu sur le PC du policier et hébergez de nouveau
  avant de rejoindre. Le test PowerShell utilise lui-même la connexion.
- Si un joueur quitte la partie, revenez tous les deux au menu et hébergez
  une nouvelle partie.

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
