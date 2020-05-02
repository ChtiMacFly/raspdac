# Scripts de gestion du bouton d'alimentation

*Note : 2 autres répertoires avec d'anciens scripts OpenElec et RuneAudio sont disponibles mais non maintenus.*

Ci-dessous plusieurs façons de gérer le reboot & shutdown du RaspDac. Personnellement j'utilise un script python (voir dernière partie).

## Version fournie avec piCorePlayer

Un script existe par défaut dans /home/tc : **pcp-powerbutton.sh**. Il faut indiquer cette commande dans les "user commands" via l'interface :

User command #1 : `/home/tc/pcp-powerbutton.sh -i 17 --low`
*(changer le N° par le port GPIO utilisé par le bouton d'alimentation)*

Voir [https://forums.slimdevices.com/showthread.php?108852-Announce-piCorePlayer-3-5-0/page40](https://forums.slimdevices.com/showthread.php?108852-Announce-piCorePlayer-3-5-0/page40)

Quand j'ai voulé tester le script via ssh (`/home/tc/pcp-powerbutton.sh -i 17 --low --debug`) l'executable *pcp-gpio* me demande d'être "root".

## Version Audiophonics

Le script est normalement fourni via un package picore par Audiophonics (Audiophonics-powerscript.tcz). La méthodologie d'installation est décrite sur [http://forum.audiophonics.fr/viewtopic.php?f=12&t=1756](http://forum.audiophonics.fr/viewtopic.php?f=12&t=1756). Pour ma part je n'ai pas trouvé ce paquet disponible dans le repository piCorePlayer ni tinyCore (on le retrouve sur d'anciennes versions de piCorePlayer toutefois).

## Version avec overlays

2 nouveaux scripts existent et peuvent être utilisés tels quels : 

* gpio-shutdown
* gpio-poweroff

Voir la configuration sur [https://forums.slimdevices.com/showthread.php?109270-PiCore-Player-and-gpio-poweroff-gpio-shutdown-overlays](https://forums.slimdevices.com/showthread.php?109270-PiCore-Player-and-gpio-poweroff-gpio-shutdown-overlays)

## Version Python personnelle

Je fournis ici une version python de gestion de l'alimentation. Pourquoi avoir réinventé l'eau chaude ? Pour les raisons ci-dessus (nécessité d'être root, d'avoir à retrouver un package perdu dans les repositories) mais surtout **d'éviter une boucle d'interrogation infinie** pour savoir si le bouton d'alimentation a été pressé. Je ne suis pas un fan non plus de créer un service / un démon pour balayer le port quand l'utilisation d'une simple interruption matérielle suffit, possibilité offerte par le port du raspberry et par Python.

Python 3.6 est installé par défaut lors de l'installation de piCorePlayer. Il faut donc simplement ajouter le paquet **RPi-GPIO-python3.6.tcz** depuis le respository "piCorePlayer repository". Vous pouvez le faire depuis l'interface web, dans *User command #1* : `python3 /home/tc/power-mgmt.py -b`

Vous pouvez la tester vian ssh (dans le répertoire par défaut /home/tc si vous êtes connecté en tant que "tc") : `python3 power-mgmt.py --help`