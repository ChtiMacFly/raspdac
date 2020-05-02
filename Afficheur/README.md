# Scripts pour gestion d'écran OLED

Officiellement [c'est par ici](https://github.com/audiophonics/Pydpiper-Raspdac)
Mais cette solution me semble un peu lourde (docker pour un script, violent quand même...). Soulignons quand même l'énorme travail qui a été fait avec Pydpiper. Ce qui m'a le plus embếté c'est de devoir installer docker sous TinyCore. A vrai dire je ne suis pas arrivé à le compiler.

*Voir informations intéressantes sur [https://github.com/SergiSM/Raspberry/wiki/piCore](https://github.com/SergiSM/Raspberry/wiki/piCore)*

1. ~~Installer le package `setuptools` via l'interface de piCorePlayer ("extensions" dans "Main")~~
    ```
    sudo pip3 install setuptools
    ```
2. Le script utilise comme le module pylms, qu'il faut donc installer en pré-requis :
    ```
    sudo pip3 install pylms
    ```
7. ~~Installer le package "python-mpd" pour la gestion des serveurs sous MPD : `sudo pip install python-mpd`~~

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