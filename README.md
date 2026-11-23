# Police et voleur

Jeu de plateau en Python contre l’ordinateur (algorithme minimax) ou en réseau
local (LAN), avec une interface graphique Tkinter. Aucune dépendance Python
externe n'est nécessaire.

## Structure du projet

```text
controller/game_controller.py   clics, sélection des pions et tours
controller/lan_session.py        connexion LAN et échange des coups
controller/minimax.py            adversaire local basé sur minimax
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
2. Sur le premier PC, cliquez sur **Héberger** et choisissez Police ou Voleur. Ouvrez un terminal,
   tapez `ipconfig` et relevez l’**Adresse IPv4** de la carte Wi-Fi ou Ethernet
   utilisée, par exemple `192.168.1.24`.
3. Sur le second PC, cliquez sur **Rejoindre** et saisissez cette adresse. Le
   joueur qui rejoint reçoit automatiquement le rôle opposé. Une fois connecté,
   le policier place ses trois pions, puis le voleur joue son premier coup.

Si Windows demande d’autoriser Python à communiquer, autorisez-le sur les
**réseaux privés** du PC qui héberge. La connexion utilise le port TCP
`47650`. Le jeu en LAN fonctionne sans Internet.

Choisissez **Jouer sur ce PC**, puis **Solo** pour affronter l’ordinateur avec
minimax ou **Multijoueur** pour jouer à deux sur le même ordinateur. En solo,
indiquez si vous jouez la police ou le voleur ; l’ordinateur joue l’autre rôle.
Le niveau de recherche minimax est limité pour conserver des réponses rapides.

En cours de partie, **Recommencer** redémarre immédiatement le jeu local. En
LAN, les deux joueurs doivent appuyer sur **Recommencer** pour confirmer la
demande avant que la partie ne soit réinitialisée sur les deux ordinateurs.

### Si la connexion échoue

- Laissez le PC de l’hébergeur sur l’écran d’attente et vérifiez que l’adresse
  saisie par le joueur qui rejoint correspond à la carte réseau utilisée par
  l’hébergeur.
- Depuis PowerShell sur le PC du joueur qui rejoint, lancez la commande suivante
  en remplaçant l’adresse d’exemple par celle de l’hébergeur.

  ```powershell
  Test-NetConnection 192.168.1.24 -Port 47650
  ```

  Si `TcpTestSucceeded` vaut `False`, vérifiez le pare-feu du PC de l’hébergeur
  et essayez un réseau partagé qui autorise les appareils à communiquer.
  Après ce test, revenez au menu sur le PC de l’hébergeur et hébergez de nouveau
  avant de rejoindre. Le test PowerShell utilise lui-même la connexion.
- Si un joueur quitte la partie, revenez tous les deux au menu et hébergez
  une nouvelle partie.

## Règles et commandes

1. Au début, le joueur policier place un pion sur le cercle intérieur, puis
   deux pions sur des intersections libres du bord.
2. Le voleur commence au centre. Les deux joueurs jouent ensuite à tour de rôle.
   En mode local, l’adversaire est l’ordinateur et choisit ses coups avec minimax.
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
