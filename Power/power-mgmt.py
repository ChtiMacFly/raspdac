# Cyril Sudre - cyril.sudre@laposte.net

"""Script de gestion de l'alimentation du RaspDAC."""
# coding: utf8
import sys
import getopt
sys.path.append('/storage/.kodi/addons/python.RPi.GPIO/lib')
import RPi.GPIO as GPIO
import time
import subprocess

# Voir :
# http://www.barryhubbard.com/raspberry-pi/howto-raspberry-pi-openelec-power-wake-shutdown-button-using-gpio/
# http://forum.audiophonics.fr/viewtopic.php?f=4&t=1578


def usage():
    """Utilisation du script."""
    print("\nUtilisation du script\n")
    print('Lancement d\'un shutdown: ' + sys.argv[0] + ' -s ou ' + sys.argv[0] + ' --softshutdown')
    print('Reboot: ' + sys.argv[0] + ' -r ou ' + sys.argv[0] + ' --softreboot')
    print('Attente bouton poussoir: ' + sys.argv[0] + ' -b ou ' + sys.argv[0] + ' --button')
    print("\n")
print "t"


def init():
    """Initialisation des ports."""
    # Utilisation de la nomenclature avec le N° des broches du connecteur
    GPIO.setmode(GPIO.BOARD)

    # Désactivation des warnings si un des ports est déjà positionné en sortie(exemple de lancements successifs du script)
    GPIO.setwarnings(False)

    # PIN 11 (GPIO17) : Demande d'arrêt. A positionner en entrée
    GPIO.setup(11, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


def main():
    """Lancement."""
    # Arguments de la ligne de commande
    if(len(sys.argv) == 1):
        usage()
        exit(2)
    try:
        opts, args = getopt.getopt(sys.argv[1:], "srb", ["softshutdown",
                                                         "softreboot",
                                                         "button"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    # Initialisation des ports
    init()

    for opt, arg in opts:
        if opt in ("-h", "--help"):
                usage()
                sys.exit()
        elif opt in ("-s", "--softshutdown"):
                # On lance le shutdown
                softshutdown()
        elif opt in ("-r", "--softreboot"):
                # On lance le reboot
                softreboot()
        elif opt in ("-b", "--button"):
                # Si ce script est en train de s'executer, c'est que le raspDAC est démarré! On positionne donc GPIO22 à True
                bootok()

                # Execution du script bloquée en attente de signal haut sur GPIO17
                GPIO.wait_for_edge(11, GPIO.RISING)
                print("Appui sur le bouton poussoir!\n")
                shutdown()
        else:
            assert False, "Argument inconnu"


# Retour Boot OK
def bootok():
    """Envoie le signal boot OK sur GPIO22."""
    # PIN 15 (GPIO22) : retour du boot. A positionner en sortie
    GPIO.setup(15, GPIO.OUT)
    GPIO.output(15, True)


# Séquence d'arrêt logiciel
def softshutdown():
    u"""Séquence d'arrêt logiciel."""
    # PIN 7 (GPIO04) : soft shutdown
    GPIO.setup(7, GPIO.OUT)
    GPIO.output(7, True)
    time.sleep(1)
    GPIO.output(7, False)
    # shutdown()


# Séquence de redémarrage logiciel
def softreboot():
    u"""Séquence de redémarrage logiciel."""
    GPIO.setup(7, GPIO.OUT)
    GPIO.output(7, True)
    time.sleep(1)
    # reboot()


# Routine de reboot
def reboot():
    """Routine de reboot."""
    subprocess.call("reboot", shell=True)


# Routine d'arrêt
def shutdown():
    u"""Routine d'arrêt. On en profite pour passer l'écran en standby en amont."""
    subprocess.call("echo \"standby 0\" | /usr/bin/cec-client -s; shutdown -P now", shell=True)

# Lacement du programme
if __name__ == "__main__":
    main()
