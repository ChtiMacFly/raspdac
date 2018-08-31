# Script lancé lors de l'arrêt d'OpenElec
# En fonction de la demande (reboot ou arrêt) on lance le script avec le bon paramètre

case "$1" in
  poweroff)
    # shutdown
    python /storage/scripts/power-mgmt.py --softshutdown
    ;;
  *)
    # reboot
    python /storage/scripts/power-mgmt.py --softreboot
    ;;
esac
