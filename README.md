# Scripts RaspDAC

Ces scripts sont conçus pour être utilisés avec le [RaspDAC Audiophonics I-Sabre ESS9023](https://www.audiophonics.fr/fr/lecteurs-reseau-audio-raspdac/audiophonics-raspdac-i-sabre-v4-kit-diy-lecteur-reseau-raspberry-pi-30-dac-p-11136.html). Pour ma part il me semble avoir la version 3; je suppose que ce qui suit est applicable à l'ensemble des versions mais à confirmer. Il y a notamment eu un changement dans les broches GPIO utilisées pour l'afficheur entre la version 2 et 3, il faudra peut-être adapter les références des E/S utilisées.

Voir les [différentes générations du DAC](https://www.audiophonics.fr/fr/blog-diy-audio/19-audiophonics-i-sabre-dac-les-differentes-generations-du-dac-pour-raspberry-pi.html) sur le blog AudioPhonics.

## Versions utilisées

J'i utilisé l'image de la version standard du 7 mars 2020 (pCP6.0.0 Standard Version) disponible sur [https://www.picoreplayer.org/main_downloads.shtml](https://www.picoreplayer.org/main_downloads.shtml)

Une fois installée, les version indiquées sur l'interface sont les suivantes :

* piCorePlayer v6.0.0
* piCore v10.3pCP
* Squeezelite v1.9.6-1206-pCP

### Installation de piCorePlayer

Choisir la version "standard" et pas audio si vous choisissez d'installer LMS sur la même machine, ce qui est mon cas. De toute façon, si vous n'envisagez pas d'aller jusqu'à un débit très élévé (de mémoire autour  de 350kbits/s c'est globalement inutile).

Aucune difficulté ici, il suffit de suivre les instructions. Récapitulatif "à l'arrache" (remplacer par votre fichier / le périphérique de la carte SD que vous allez insérer dans le raspberry):

1. Récupérer l'image sur le site de [piCorePlayer](https://picoreplayer.org/)
2. Mettez l'image sur votre carte SD (mieux vaut tout supprimer dessus avant) :   
    ```
    dd if=/path/to/fichier img of=/dev/sdc bs=1M
    ```
    ___(remplacez `/dev/sdc` par votre périphérique bien sûr)___

### Configuration

Changer le nom du host : RaspDacPlayer

Tweaks : auto start LMS "randomplay tracks"

## Utilisation de piCorePlayer

_Les commandes ci-dessous sont à taper en ligne de commande une fois connecté en ssh sur le RaspDAC (via putty par exemple)_

### Ajout(s) dans cmdline

Voici les étapes à suivre pour configurer votre piCorePlayer en français :

1. Installer le paquet `getlocale` via l'interface de piCorePlayer ("extensions" dans "Main", repository piCore officiel)
2. Générer les caractères : `sudo getlocale.sh` puis choisissez "fr_FR.UTF-8"
3. Monter la partition fat depuis laquelle a été monté l'OS : `mount /dev/mmcblk0p1` - Voir [ici](https://iotbytes.wordpress.com/change-picore-boot-codes-boot-options/)
4. Ajouter à la fin du fichier cmdline.txt l'option `lang=fr_FR.UTF-8/UTF-8`

### Montage disque externe

Installer l'extention xfsprogs si vous souhaitez utilisez un disque XFS comme celà est mon cas.

### Extensions piCore

1. Audiophonics-powerscripts

### Extensions LMS

1. Démarrage automatique de la musique

### Paramétrage du Wifi

Pas de difficulté : il faut activer le wifi (j'ai aussi activé le bluetooth sans soucis) et mettre les informations de connexion sur la page dédiée. Vous pourrez ensuite vous affranchir du cordon réseau !

### Utilisation de l'écran

Officiellement [c'est par ici](https://github.com/audiophonics/Pydpiper-Raspdac)
Mais cette solution me semble un peu lourde (docker pour un script, violent quand même...). Soulignons quand même l'énorme travail qui a été fait avec Pydpiper. Ce qui m'a le plus embếté c'est de devoir installer docker sous TinyCore. A vrai dire je ne suis pas arrivé à le compiler.

Le script utilise comme le module pylms, qu'il faut donc installer en pré-requis (Voir [https://github.com/SergiSM/Raspberry/wiki/piCore](https://github.com/SergiSM/Raspberry/wiki/piCore)) :

1. Installer le package `setuptools` via l'interface de piCorePlayer ("extensions" dans "Main")
2. Installer le package `rpi.gpio` via l'interface de piCorePlayer ("extensions" dans "Main")
3. Connectez-vous en ssh sur le RaspDac
4. Installer les extensions "dev" de python : `tce-load -wi python-dev` (pour avoir Python.h, nécessaire pour pip)
5. Installer pip : 
    ```
    wget https://bootstrap.pypa.io/get-pip.py
    sudo python get-pip.py
    ```
6. Installer pylms : `sudo pip install pylms`
7. Installer le package "python-mpd" pour la gestion des serveurs sous MPD : `sudo pip install python-mpd`

Sauvegardez pour les prochains reboot :

```
echo /usr/local/bin/pip >> /opt/.filetool.lst
echo /usr/local/lib/python2.7/site-packages/pip/ >> /opt/.filetool.lst

echo /usr/local/bin/pylms >> /opt/.filetool.lst
echo /usr/local/lib/python2.7/site-packages/pylms/ >> /opt/.filetool.lst

echo /usr/local/lib/python2.7/site-packages/mpd.pyc >> /opt/.filetool.lst

sudo filetool.sh -b
```

Puis l'installation du script :

1. Récupérer les scripts `RaspDacDisplay.py` et `Winstar_GraphicOLED.py` et copiez-les dans `/home/tc`
2. Rendez-le executable : `chmod +x RaspDacDisplayCS.py`
3. Ajoutez-le au démarrage : `echo /home/tc/RaspDacDisplayCS.py >> /opt/bootlocal.sh`

### Configuration du bluetooth

Comment connecter une enceinte bluetooth et la voir comme un player squeezelite ? Même si la qualité n'aura rien à voir avec votre DAC, c'est une option intéressante pour du multiroom par exemple.

Il vous faut la suite blue-alsa pour ne pas avoir à passer par PulseAudio comme vous l'indiquent de nombreux tutoriels.