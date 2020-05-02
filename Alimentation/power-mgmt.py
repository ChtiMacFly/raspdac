# Cyril Sudre - cyril.sudre@laposte.net

# Voir :
# http://www.barryhubbard.com/raspberry-pi/howto-raspberry-pi-openelec-power-wake-shutdown-button-using-gpio/
# http://forum.audiophonics.fr/viewtopic.php?f=4&t=1578

"""Script de gestion de l'alimentation du RaspDAC."""
# coding: utf8
import sys
import getopt
import RPi.GPIO as GPIO
import time
import subprocess

#######################################################################
# A changer au besoin
#
# Attente interruption (11 = GPIO17)
BOUTON_INTERRUPTION = 11

# Les du bouton pour indiquer quand le boot est terminé (15 = GPIO22)
LED_BOUTON = 15

# Sur cette broche un front montant sera généré pour initier le shutdown (7 = GPIO4)
SIGNAL_SHUTDOWN = 7

# Commande système qui sera utilisée pour initier un shutdown
# Par exemple "shutdown -P now" ou "poweroff"
SHUTDOWN_COMMAND = "poweroff"

# Commande système qui sera utilisée pour initier un reboot
REBOOT_COMMAND = "reboot"
#######################################################################

def usage():
    """Utilisation du script."""
    print("\nUtilisation du script\n")
    print('Lancement d\'un shutdown: ' + sys.argv[0] + ' -s ou ' + sys.argv[0] + ' --softshutdown')
    print('Reboot: ' + sys.argv[0] + ' -r ou ' + sys.argv[0] + ' --softreboot')
    print('Attente bouton poussoir: ' + sys.argv[0] + ' -b ou ' + sys.argv[0] + ' --button')
    print("\n")

def init():
    """Initialisation des ports."""
    # Utilisation de la nomenclature avec le N° des broches du connecteur
    GPIO.setmode(GPIO.BOARD)

    # Désactivation des warnings si un des ports est déjà positionné en sortie(exemple de lancements successifs du script)
    GPIO.setwarnings(False)

    # Demande d'arrêt. A positionner en entrée
    GPIO.setup(BOUTON_INTERRUPTION, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


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

                # Execution du script bloquée en attente de signal haut sur le bouton
                GPIO.wait_for_edge(BOUTON_INTERRUPTION, GPIO.RISING)
                print("Appui sur le bouton poussoir!\n")
                shutdown()
        else:
            assert False, "Argument inconnu"


# Retour Boot OK
def bootok():
    """Envoie le signal boot OK."""
    # Retour du boot. A positionner en sortie
    GPIO.setup(LED_BOUTON, GPIO.OUT)
    GPIO.output(LED_BOUTON, True)


# Séquence d'arrêt logiciel
def softshutdown():
    u"""Séquence d'arrêt logiciel."""
    # Soft shutdown
    GPIO.setup(SIGNAL_SHUTDOWN, GPIO.OUT)
    GPIO.output(SIGNAL_SHUTDOWN, True)
    time.sleep(1)
    GPIO.output(SIGNAL_SHUTDOWN, False)
    shutdown()

# Séquence de redémarrage logiciel
def softreboot():
    u"""Séquence de redémarrage logiciel."""
    GPIO.setup(SIGNAL_SHUTDOWN, GPIO.OUT)
    GPIO.output(SIGNAL_SHUTDOWN, True)
    time.sleep(1)
    reboot()

# Routine de reboot
def reboot():
    """Routine de reboot."""
    subprocess.call(REBOOT_COMMAND, shell=True)

# Routine d'arrêt
def shutdown():
    u"""Routine d'arrêt."""
    #subprocess.call("echo \"standby 0\" | /usr/bin/cec-client -s; shutdown -P now", shell=True)
    #subprocess.call("shutdown -P now", shell=True)
    subprocess.call(SHUTDOWN_COMMAND, shell=True)

# Lacement du programme
if __name__ == "__main__":
    main()
