# Scripts RaspDAC

_Note : les commandes indiquées dans un bloc de code ci-dessous sont à taper en ligne de commande (soit sur la machine qui sert à préparer l'image soit connecté en ssh sur le RaspDAC, via putty par exemple)_

Ces scripts sont conçus pour être utilisés avec le [RaspDAC Audiophonics I-Sabre ESS9023](https://www.audiophonics.fr/fr/lecteurs-reseau-audio-raspdac/audiophonics-raspdac-i-sabre-v4-kit-diy-lecteur-reseau-raspberry-pi-30-dac-p-11136.html). Pour ma part il me semble avoir la version 3; je suppose que ce qui suit est applicable à l'ensemble des versions mais à confirmer. Il y a notamment eu un changement dans les broches GPIO utilisées pour l'afficheur entre la version 2 et 3, il faudra peut-être adapter les références des E/S utilisées.

Voir les [différentes générations du DAC](https://www.audiophonics.fr/fr/blog-diy-audio/19-audiophonics-i-sabre-dac-les-differentes-generations-du-dac-pour-raspberry-pi.html) sur le blog AudioPhonics.

# Installation de piCorePlayer

## Installation de l'image

J'ai utilisé l'image de la version standard du 7 mars 2020 (pCP6.0.0 Standard Version) disponible sur [https://www.picoreplayer.org/main_downloads.shtml](https://www.picoreplayer.org/main_downloads.shtml)

Choisir la version "standard" et pas audio si vous choisissez d'installer LMS sur la même machine, ce qui est mon cas. De toute façon, si vous n'envisagez pas d'aller jusqu'à un débit très élévé (de mémoire autour  de 350kbits/s c'est globalement inutile).

Pour l'installation, il suffit de suivre les instructions (notamment [ici](https://docs.picoreplayer.org/how-to/burn_pcp_onto_a_sd_card/linux/dd/)). J'utilise la version "dd" qui a le mérite d'être native sur tous les systèmes UNIX. Récapitulatif "à l'arrache" (remplacer par votre fichier / le périphérique de la carte SD que vous allez insérer dans le raspberry):

1. Récupérer l'image sur le site de [piCorePlayer](https://picoreplayer.org/) et dézipper là. Ce qui nous intéresse c'est le fichier .IMG
2. Insérer votre carte SD, trouver son petit nom, démonter les partitions et copier l'image:
    
    2.1 ```lsblk```
    
    2.2 ```sudo umount </dev/sdc1>```
        ___(remplacer `sdc1` par votre partition puis répéter l'opération pour chaque partition montée)___
    
    2.3 ```dd if=</path/to/fichier img> of=</dev/sdc> bs=1M```
    ___(remplacez `/dev/sdc` par votre périphérique bien sûr)___

## Configuration du Wifi

Cette étape permet de préciser la configuration Wifi dans un fichier texte avant d'installer la carte SD dans le raspberry.

1. Vous devez avoir une partition de boot de montée sur votre PC une fois l'installation ci-dessus effectuée. Copier le fichier `wpa_supplicant.conf.sample` vers `wpa_supplicant.conf`
2. editez le fichier et renseignez votre paramètres Wifi. Voir [https://docs.picoreplayer.org/how-to/setup_wifi_on_pcp_without_ethernet/](https://docs.picoreplayer.org/how-to/setup_wifi_on_pcp_without_ethernet/)

## Démarrage

1. Insérer la carte SD dans le raspberry et...Démarrez !
2. Trouver l'adresse IP de votre raspberry via l'interface de votre BOX si vous n'avez pas branché d'écran. Sinon lisez sur l'écran de démarrage...

## Versions

Une fois installée, les version indiquées sur l'interface sont les suivantes :

* piCorePlayer v8.1.0
* piCore v13.1
* Squeezelite v1.9.9-1391-pCP

## Configuration

### Gestion de l'alimentation

Il y a plusieurs scripts disponibles mais j'ai créé mon propre script python pour une raison simple : l'utilisation d'une interruption pour détecter l'appui sur le bouton d'alimentation. Voir le fichier README dans le dossier "Alimentation".

### Extention de la partition

Dans l'onglet "Main Page", cliquez sur "Resize FS" pour pouvoir ajouter des extentions. Choisissez "Whole SD Card" pour utiliser l'ensemble de l'espace disponible de la carte.

### Onglet Squeezelite Settings

Nécessaire pour configurer la partie audio, c'est quand même ce qu'on cherche (écouter de la zik)...

* Audio output : **ESS9023 DAC**
* Name of your player : **RaspdacPlayer** (pas obligatoire mais il est conseillé de changer de nom)

### Onglet Tweaks

* Host name : **RaspdacPlayer** (*pas obligatoire*)
* (*Attention il faut au préalable avoir suivi les instructions du dossier "Alimentation")*.
User command #1 : **python3 /home/tc/power-mgmt.py -b**

### Installez les "locales" en français

Voici les étapes à suivre pour configurer votre piCorePlayer en français :

1. Installer le paquet `getlocale` via l'interface de piCorePlayer ("extensions" dans "Main", repository piCore officiel)
2. Installez le paquet "nano" pour pouvoir éditer le fichier `cmdline.txt` un peu plus tard.
3. Une fois connecté en SSH, générez les caractères : `sudo getlocale.sh` puis choisissez "fr_FR.UTF-8"
4. Monter la partition fat depuis laquelle a été monté l'OS : `mount /dev/mmcblk0p1` - Voir [ici](https://iotbytes.wordpress.com/change-picore-boot-codes-boot-options/). Allez dans le répertoire de montage (par défaut /mnt/mmcblk0p1)
5. Ajouter à la fin du fichier cmdline.txt l'option `lang=fr_FR.UTF-8/UTF-8` (à la fin de la ligne, sans passer à la ligne)
6. Rebootez le player.

## Partie LMS (serveur audio)

### Onglet Tweaks

* Auto start LMS : **randomplay tracks** (*pour lire aléatoirement des morceaux une fois LMS lancé)

### Montage disque externe

~~Installer l'extention xfsprogs si vous souhaitez utilisez un disque XFS comme celà est mon cas.~~ (*ma partition a été reconnue sans avoir à le faire et de toute façon l'extension n'est plus disponible dans les repositories*)

### Extensions piCore que j'ai ajouté

1. ~~Audiophonics-powerscripts~~ (*plus disponible apparemment dans le repositiory par défaut*)
2. RPi-GPIO-Python3.6.tcz (pour gestion de l'alimentation)
3. nano.tcz (*pas obligatoire mais pratique pour éditer un fichier localement une fois connecté en ssh*)

## Paramétrage du Bluetooth

Pour appairer une enceinte BT :

1. Dans "Main Page", cliquez sur le bouton "Bluetooth" puis "Install".
2. Activer l'option `RPi built-in Bluetooth`
3. Démarrez le BT ("Power On")

## Utilisation de l'afficheur LCD

Voir répertoire "Afficheur".