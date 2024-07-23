"""_summary_
    Module d'affichage RaspDac
Raises:
    BaseException: _description_

Returns:
    _type_: _description_
"""

# -*- coding: utf-8 -*-
# cyril.sudre@laposte.net

# Standards
import curses
from datetime import datetime
import socket
import time
import json
import logging
import sys
import queue
from threading import Thread
from socket import error as socket_error
import getopt
import locale

# Spécifiques
import Winstar_GraphicOLED
from pylms.server import Server
import pages

# Pour pouvoir utiliser l'unicode avec curses
locale.setlocale(locale.LC_ALL, "fr_FR.utf8")

# Si le code s'execute sur Raspberry on arrivera à importer le module.
# Dans le cas contraire on est donc sur PC.
try:
    from RPi import GPIO

    DISPLAY_INSTALLED = True
except ImportError:

    DISPLAY_INSTALLED = False
    print("Lancement en dehors d'un raspberry, utilisation de Curses")

# Fichier de log
LOGFILE = "RaspDacDisplay.log"

# Temps d'hésitation (en secondes) avant scrolling
HESITATION_TIME = 2.5

# Temps (en secondes) avant rafraichissement de l'écran
ANIMATION_SMOOTHING = 0.15

# Loggueur
logger = logging.getLogger(__name__)

# Niveau de log
logger.setLevel(logging.DEBUG)

# Notre fichier de log
fh = logging.FileHandler(LOGFILE)

# Niveau de log
fh.setLevel(logging.DEBUG)

# La tronche de notre fichier de log
formatter = logging.Formatter(
    "%(asctime)s - %(name)s (%(lineno)s) - %(levelname)s: %(message)s"
)

# On précise que notre gestionnaire va utiliser ce format
fh.setFormatter(formatter)

# On ajoute comme gestionnaire de log
logger.addHandler(fh)

# Pour récupérer l'adresse IP de la machine sur laquelle tourne ce programme
# https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
def get_ip():
    """Pour récupérer l'adresse IP de la machine sur laquelle tourne ce programme

    Returns:
        _type_: _description_
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Cette adresse n'a pas besoin d'être atteignable
        s.connect(("10.255.255.255", 1))
        IP = s.getsockname()[0]
    except socket.error:
        IP = "127.0.0.1"
    finally:
        s.close()
    logger.debug("Adresse IP locale : %s", IP)
    return IP

# Récupération de l'adresse MAC
def get_mac():
    """Récupération de l'adresse MAC

    Returns:
        _type_: _description_
    """
    from uuid import getnode

    mac = ":".join(("%012X" % getnode())[i : i + 2] for i in range(0, 12, 2))
    logger.debug("Adresse MAC locale : %s", mac)
    return mac

class RaspDacDisplay:
    """Classe de gestion de l'écran du RaspDAC

    Keyword Arguments:
                    dw {int} -- [largeur de l'écran en nombre de caractères] (default: {16})
                    dh {int} -- [hauteur de l'écran en nombre de lignes] (default: {2})

    Raises:
                    Exception -- [description]
                    Exception -- [description]

    Returns:
                    [type] -- [description]
    """

    # Message de démarrage
    STARTUP_MSG = "Démarrage..."

    def __init__(
        self,
        lms_server="127.0.0.1",
        lms_port=9000,
        player=None,
        lms_user="",
        lms_pwd="",
        dw=16,
        dh=2,
    ):
        """Constructeur

        Arguments:
                        player {[string]} -- [Adresse MAC du player à gérer]

        Keyword Arguments:
                        lms_server {str} -- [Adresse IP du serveur LMS] (default: {"localhost"})
                        lms_port {int} -- [Port du serveur LMS] (default: {9090})
                        lms_user {str} -- [User pour se connecter au serveur LMS] (default: {""})
                        lms_pwd {str} -- [Mot de passe pour se connecter au serveur LMS] (default: {""})
                        dw {int} -- [Nombre de caractères de l'écran] (default: {16})
                        dh {int} -- [Nombre de lignes de l'écran] (default: {2})
        """

        # On affecte simplement à l'instance les paramètres passés
        self.player = player
        self.lms_port = lms_port
        self.lms_user = lms_user
        self.lms_pwd = lms_pwd
        self.dw = dw
        self.dh = dh

        # Initialisation fichier de log
        self.logger = logging.getLogger(__name__)

        # Premier message dans le fichier de log...
        self.logger.info(
            "Initialisation avec les paramètres :\n\
            player : %s\n\
            server : %s\n\
            port : %s\n\
            user : %s\n\
            password : %s",
            player,
            lms_server,
            lms_port,
            lms_user,
            lms_pwd,
        )

        # Gestionnaire d'erreurs non capturées
        sys.excepthook = self.excepthook

        # File d'attente pour l'affichage
        self.dq = queue.Queue()

        # Pour l'instant les informations de pages ne sont pas chargées
        self.pages = None

        # Notre objet PyLMS server
        self.lmsserver = Server(lms_server, lms_port, lms_user, lms_pwd)

        # Routine qui cherche le player si précisé, sinon le premier renvoyé par le serveur
        self._get_player(player)

    def _get_player(self, player=None):
        """Récupère le player

        Arguments:
                        player {str} -- [Adresse MAC du player recherché]

        Raises:
                        Exception -- [description]
        """

        self.logger.debug("Dans _get_player")
        
        try:
            # Connection au serveur LMS
            self.logger.debug("Connexion au serveur %s", self.lmsserver.hostname)
            self.lmsserver.connect()

            # Si aucun player spécifié : on prends le premier retourné
            # par le serveur (pratique s'il n'y en a qu'un)
            if player is None:
                self.logger.debug("Aucun player spécifié, on prends le premier sur le serveur")
                self.lmsplayer = self.lmsserver.get_players()[0]
            else:
                # On cherche notre player
                self.logger.debug("Adrese de player précisée, on cherche ce player")
                players = self.lmsserver.get_players()
                for p in players:
                    # Comparaison des adresses MAC pour trouver notre player
                    if p.get_ref().lower() == player.lower():
                        self.lmsplayer = p
                        break

            # Si on a rien c'est pas bon...On fera pas grand chose !
            if self.lmsplayer is None:
                raise Exception("Impossible de trouver un player avec cette adresse sur le serveur")
        except socket_error:
            raise Exception("Impossible de se connecter sur le serveur")
        except(AttributeError, IndexError):
            raise Exception("La recherche du player sur le serveur LMS a échoué")

    def status_lms(self):
        """Récupère le status du player depuis le serveur LMS

        Raises:
                        Exception -- [description]

        Returns:
                        [type] -- [description]
        """

        try:
            lms_status = self.lmsplayer.get_mode()
        except Exception:
            # On essaye de se reconnecter
            try:
                self.lmsserver.connect()

                # On retrouve notre player
                self._getPlayer(self.player)

                # On récupère le statut
                lms_status = self.lmsplayer.get_mode()
            except socket_error:
                self.logger.debug("Impossible de se connecter au serveur")

            except (AttributeError, IndexError):
                self.logger.debug("Impossible de récupérer le statut depuis le serveur")
                return {
                    "state": "stop",
                    "artist": "",
                    "title": "",
                    "album": "",
                    "remaining": "",
                    "current": 0,
                    "duration": 0,
                    "position": "",
                    "volume": 0,
                    "playlist_display": "",
                    "playlist_position": 0,
                    "playlist_count": 0,
                    "bitrate": "",
                    "type": "",
                    "current_time": "",
                }

        if lms_status == "play":
            import urllib

            artist = urllib.parse.unquote(
                str(self.lmsplayer.request("artist ?", True))
            ).decode("utf-8")
            title = urllib.parse.unquote(
                str(self.lmsplayer.request("title ?", True))
            ).decode("utf-8")
            album = urllib.parse.unquote(
                str(self.lmsplayer.request("album ?", True))
            ).decode("utf-8")
            playlist_position = int(self.lmsplayer.request("playlist index ?")) + 1
            playlist_count = self.lmsplayer.playlist_track_count()
            volume = self.lmsplayer.get_volume()
            current = self.lmsplayer.get_time_elapsed()
            duration = self.lmsplayer.get_track_duration()
            url = self.lmsplayer.get_track_path()

            # Get bitrate and tracktype if they are available.
            # Try blocks used to prevent array out of bounds exception if values are not found
            try:
                bitrate = (
                    urllib.parse.unquote(
                        str(
                            self.lmsplayer.request(
                                "songinfo 2 1 url:" + url + " tags:r", True
                            )
                        )
                    )
                    .decode("utf-8")
                    .split("bitrate:", 1)[1]
                )
            except Exception:
                bitrate = ""

            try:
                tracktype = (
                    urllib.parse.unquote(
                        str(
                            self.lmsplayer.request(
                                "songinfo 2 1 url:" + url + " tags:o", True
                            )
                        )
                    )
                    .decode("utf-8")
                    .split("type:", 1)[1]
                )
            except Exception:
                tracktype = ""

            playlist_display = "{0}/{1}".format(playlist_position, playlist_count)
            # If the track count is greater than 1, we are playing from a playlist
            # and can display track position and track count
            # //if self.lmsplayer.playlist_track_count() > 1:
            # //	playlist_display = "{0}/{1}".format(playlist_position, playlist_count)
            # if the track count is exactly 1, this is either a short playlist or it is streaming
            # //elif self.lmsplayer.playlist_track_count() == 1:
            if self.lmsplayer.playlist_track_count() == 1:
                try:
                    # if streaming
                    if self.lmsplayer.playlist_get_info()[0]["duration"] == 0.0:
                        playlist_display = "Streaming"
                    # it really is a short playlist
                    # //else:
                    # //	playlist_display = "{0}/{1}".format(playlist_position, playlist_count)
                except KeyError:
                    self.logger.debug("In LMS couldn't get valid track information")
                    playlist_display = ""
            else:
                self.logger.debug("In LMS track length is <= 0")
                playlist_display = ""

                # since we are returning the info as a JSON formatted return, convert
                # any None's into reasonable values

            if artist is None:
                artist = ""
            if title is None:
                title = ""
            if album is None:
                album = ""
            if current is None:
                current = 0
            if volume is None:
                volume = 0
            if bitrate is None:
                bitrate = ""
            if tracktype is None:
                tracktype = ""
            if duration is None:
                duration = 0

            # if duration is not available, then suppress its display
            if int(duration) > 0:
                timepos = (
                    time.strftime("%M:%S", time.gmtime(int(current)))
                    + "/"
                    + time.strftime("%M:%S", time.gmtime(int(duration)))
                )
                remaining = time.strftime(
                    "%M:%S", time.gmtime(int(duration) - int(current))
                )

            else:
                timepos = time.strftime("%M:%S", time.gmtime(int(current)))
                remaining = timepos

            return {
                "state": "play",
                "artist": artist,
                "title": title,
                "album": album,
                "remaining": remaining,
                "current": current,
                "duration": duration,
                "position": timepos,
                "volume": volume,
                "playlist_display": playlist_display,
                "playlist_position": playlist_position,
                "playlist_count": playlist_count,
                "bitrate": bitrate,
                "type": tracktype,
            }
        else:
            return {
                "state": "stop",
                "artist": "",
                "title": "",
                "album": "",
                "remaining": "",
                "current": 0,
                "duration": 0,
                "position": "",
                "volume": 0,
                "playlist_display": "",
                "playlist_position": 0,
                "playlist_count": 0,
                "bitrate": "",
                "type": "",
            }

    def get_current_time(self):
        """Retourne l'heure courante

        Returns:
                        [Time] -- [Heure]
        """
        return datetime.now().strftime("%H:%M").strip()

    def status(self):
        """Statut du lecteur

        Returns:
            string: état du lecteur ("stop", "play")
        """
        status = self.status_lms()

        # Mise à jour de l'heure courante
        # status["current_time"] = self.get_current_time()

        return status

    # Routine principale : boucle sur la récupération des informations depuis le serveur LMS
    # Puis push dans la file d'attente des informations à afficher. Le Thread lancé gérera
    # l'affichage depuis la file d'attente.
    def start(self):
        """Récupération des informations du serveur LMS"""

        # Thread qui gère l'affichage à partir de la file d'attente
        dm = Thread(target=self.display, daemon=True)

        self.logger.debug("Démarrage du Thread d'affichage...")
        dm.start()

        # Boucle infinie pour remplir la file d'attente à partir du serveur LMS
        try:
            current_page_number = -1
            # current_line_number = 0
            page_expires = 0
            # hesitation_expires = 0
            curlines = []
            hesitate_expires = []

            # On force l'état précédent pour une première mise à jour dans la boucle
            prev_state = None

            while True:
                # Récupère le statut du player
                cstatus = self.status()
                self.logger.debug("Statut LMS : %s", cstatus)

                # Etat du player ("play" ou "stop")
                state = cstatus.get("state")

                self.logger.debug("Etat du player : %s", state)

                # Besoin de changer l'affichage actuel ?
                if state != prev_state:
                    current_page_number = -1
                    current_line_number = 0
                    page_expires = 0
                    curlines = []
                    hesitate_expires = []

                    prev_state = state

                    # Affichage de la page avec les informations quand aucune musique n'est en cours
                    if state != "play":
                        current_pages = pages.PAGES_Stop
                    # Affichage de la page avec les informations sur la musique en cours
                    else:
                        current_pages = pages.PAGES_Play

                # Si page expirée on passe à la page suivante
                if page_expires < time.time():
                    # Passage à la page suivante et vérification si elle doit
                    # être affichée ou cachée
                    for i in range(len(current_pages["pages"])):
                        current_page_number = current_page_number + 1

                        # Si on est sur la dernière page on repasse à la première
                        if current_page_number > len(current_pages["pages"]) - 1:
                            current_page_number = 0

                        # Expiration de la page actuelle, fonction de la durée spécifiée
                        page_expires = (
                            time.time()
                            + current_pages["pages"][current_page_number]["duration"]
                        )

                        # On stocke la page courante
                        # //cp = current_pages['pages'][current_page_number]

                # Set current_page
                current_page = current_pages["pages"][current_page_number]

                # Now display the lines from the current page
                lines = []
                for i in range(len(current_page["lines"])):
                    # make sure curlines is big enough. curlines is used to detect
                    # when the display has changed if not expanded here it will cause
                    # an IndexError later if it has not already been
                    # initialized
                    while len(curlines) < len(current_page["lines"]):
                        curlines.append("")

                    # make sure hesitate_expires is big enough as well
                    while len(hesitate_expires) < len(current_page["lines"]):
                        hesitate_expires.append(0)

                    current_line = current_page["lines"][i]

                    # //try:
                    # //	variables = current_line['variables']
                    # //except KeyError:
                    # //	variables = []

                    # Heure courante formattée
                    cstatus["current_time_formatted"] = datetime.now().strftime(
                        "%d/%m/%Y %H:%M"
                    )

                    format_ligne = current_line["format"]
                    # //self.logger.debug("Format : %s", format)

                    # On récupère les paramètres. On passe si ce paramètre n'existe pas
                    parms = []
                    for j in range(len(current_line["variables"])):
                        try:
                            # if type(cstatus[current_line['variables'][j]]) is unicode:
                            if isinstance(cstatus[current_line["variables"][j]], str):
                                parms.append(
                                    cstatus[current_line["variables"][j]].encode(
                                        "utf-8"
                                    )
                                )
                            else:
                                parms.append(cstatus[current_line["variables"][j]])
                        except KeyError:
                            self.logger.debug(
                                "Clé non trouvée : %s", current_line["variables"][j]
                            )

                    # Création de la ligne à afficher
                    self.logger.debug("Chaîne ligne %s : %s", i, parms)

                    #line = format_ligne.format(*parms).decode("utf-8")
                    line = format_ligne.format(*parms)

                    # justify line
                    # //try:
                    # //	if current_line['justification'] == "center":
                    # //		line = "{0:^{1}}".format(line, DISPLAY_WIDTH)
                    # //	elif current_line['justification'] == "right":
                    # //		line = "{0:>{1}}".format(line, DISPLAY_WIDTH)
                    # //except KeyError:
                    # //	pass

                    lines.append(line)

                    # determine whether to scroll or not
                    # if scroll is false, set hesitation time to large value which
                    # effectively shuts off the scroll function
                    if lines[i] != curlines[i]:
                        curlines[i] = lines[i]
                        try:
                            if current_line["scroll"]:
                                hesitate_expires[i] = time.time() + HESITATION_TIME
                            else:
                                hesitate_expires[i] = (
                                    time.time() + 86400
                                )  # Do not scroll
                        except KeyError:
                            # Do not scroll
                            hesitate_expires[i] = time.time() + 86400

                # ? Détermine si l'écran doit hésiter avant de scroller
                dispval = []
                for i, line in enumerate(lines):
                    if hesitate_expires[i] < time.time():
                        dispval.append(line)
                    else:
                        dispval.append(line[0 : self.dw])

                # On ajoute les informations à afficher dans la file d'attente
                self.dq.put(dispval)

                # Attente avant prochaine mise à jour
                time.sleep(0.25)

        # Interruption du script
        except KeyboardInterrupt:
            pass

    # Les erreurs non gérées sont loguées
    def excepthook(self, exc_type, exc_value, exc_traceback):
        """Gestion des erreurs non capturées

        Args:
            exc_type (_type_): _description_
            exc_value (_type_): _description_
            exc_traceback (_type_): _description_
        """
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        self.logger.error(
            "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
        )

        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    # Chargement des pages en format json
    def load_pages(self):
        """Chargement des pages à partir du fichier json"""
        fichier = "pages.json"
        try:
            with open(file=fichier, mode="r", encoding="utf8") as f:
                self.pages = json.load(f)
        except FileNotFoundError:
            self.logger.error("Fichier %s introuvable!", fichier)
            sys.exit(1)
        except IOError:
            self.logger.error("Erreur lors de l'ouverture de %s!", fichier)
            sys.exit(1)

    # Affichage du contenu de la file d'attente sur l'écran
    def display(self):
        """Affichage du contenu de la file d'attente sur l'écran"""
        lines = []
        columns = []

        # Objet LCD correspondant à l'écran OLED ou curses si pas dispo
        if DISPLAY_INSTALLED:
            self.logger.debug("Affichage sur écran OLED")
            lcd = Winstar_GraphicOLED.Winstar_GraphicOLED()
        else:
            self.logger.debug("Affichage avec Curses")
            lcd = CursesLCD()

        # Réinit
        lcd.oled_reset()

        # Message au démarrage
        lcd.message(RaspDacDisplay.STARTUP_MSG)
        time.sleep(2)

        # Premier élément de la file d'attente
        item = self.dq.get()
        self.dq.task_done()

        # On prends les 2 éléments du tableau (item), on les place dans lines
        # On place le curseur sur la bonne ligne
        # et on affiche en limitant l'affichage au nb de colonnes indiqués en paramètre de Display
        for i in range(len(item)):
            lines[i] = item[i]
            lcd.set_cursor(0, i)
            lcd.message(lines[i][0 : self.dw])

        # On stocke le moment présent (nb de secondes depuis 1970)
        prev_time = time.time()

        while True:
            short_lines = True

            # On attend un peu, en fonction de la constante ANIMATION_SMOOTHING
            # pour avoir une animation fluide
            if time.time() - prev_time < ANIMATION_SMOOTHING:
                time.sleep(ANIMATION_SMOOTHING - (time.time() - prev_time))
            try:
                # Affiche les lignes correspondantes à des informations qui ont été modifiées
                for i in range(len(item)):
                    # Information à afficher plus longue que l'écran
                    if len(item[i]) > self.dw:
                        short_lines = False

                    # Information modifiée ?
                    if lines[i] != item[i]:
                        # Création d'une ligne au moins aussi longue que l'existante afin
                        # d'écraser les caractères en trop sur l'écran
                        buf = item[i].ljust(len(lines[i]))

                        # Curseur en début de ligne et affichage
                        lcd.set_cursor(0, i)
                        lcd.message(buf[0 : self.dw])

                        # Stocke le contenu de la ligne courante et
                        # remise à zéro de la colonne courante
                        lines[i] = item[i]
                        columns[i] = 0

                # Si les éléments ne sont pas plus long que l'écran : c'est fini
                if short_lines:
                    item = self.dq.get()
                    self.dq.task_done()
                # Sinon il faut mettre à jour l'écran pour scroller
                else:
                    for i in range(len(lines)):
                        if len(lines[i]) > self.dw:
                            buf = "%s          %s" % (
                                lines[i],
                                lines[i][0 : self.dw - 1],
                            )

                            columns[i] = columns[i] + 1
                            if columns[i] > len(buf) - self.dw:
                                columns[i] = 0

                            lcd.set_cursor(0, i)

                            # Affiche la partie de la chaîne à rendre visible
                            lcd.message(buf[columns[i] : columns[i] + self.dw])

                    # Rafraichissement continu de l'écran : on vérifie si une mise
                    # à jour est nécessaire sans bloquer
                    item = self.dq.get_nowait()
                    self.dq.task_done()

                prev_time = time.time()
            except queue.Empty:
                prev_time = time.time()
class CursesLCD:
    """Gestion de l'affichage sur PC via Curses"""

    # Classe qui simule un écran fictif avec curses
    # Méthodes communes avec la classe Winstar_GraphicOLED

    def __init__(self, h=2, w=16):
        """Constructeur

        Keyword Arguments:
                        h {int} -- [Nb lignes de l'écran] (default: {2})
                        w {int} -- [Nb colonnes de l'écran] (default: {16})

        Returns:
            None
        """
        self.window = None

        self.init_curses()
        
        # Fenêtre de la taille de notre écarn LCD
        self.window = curses.newwin(h, w)
        self.window.keypad(1)

        # Bordure
        self.window.border(0)

    def init_curses(self):
        """Initialisation de Curses

        Returns:
            None
        """
        self.window = curses.initscr

        curses.noecho()
        curses.cbreak()

        #curses.start_color()
        #curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        #curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)

        curses.curs_set(0)

    # Reset écran = curseur au début + effacement
    def oled_reset(self):
        """Reset écran (équivalent d'un home() suivi d'un clear())"""
        self.home()
        self.clear()

    # Repositionne le curseur au début de l'écran
    def home(self):
        """Repositionne le curseur au début de l'écran"""
        self.set_cursor(0, 0)

    # Effacement écran
    def clear(self):
        """Efface l'écran"""
        self.window.clear()

    # Affichage d'un message
    def message(self, ligne, colonne, message):
        """Affichage d'un message sur l'écran

        Arguments:
                        ligne {integer} -- [N° de ligne sur laquelle le message sera affiché]
                        colonne {integer} -- [N° de colonne sur laquelle le message sera affiché]
                        message {string} -- [Chaîne avec le message à afficher]
        """
        self.window.addstr(ligne, colonne, message)

    # Déplace le curseur sur la ligne y, colonne x
    def set_cursor(self, y, x):
        """Déplace le curseur sur la ligne y, colonne x

        Arguments:
                        y {integer} -- [N° de ligne sur laquelle le curseur doit se déplacer]
                        x {integer} -- [N° de colonne sur laquelle le curseur doit se déplacer]
        """
        self.window.move(y, x)

    # Attente caractère clavier
    def getch(self):
        """Récupération caractère clavier

        Returns:
            str: le caractère du clavier
        """
        return self.window.getch()

    # Destructeur : permet de libérer curses
    def __del__(self):
        curses.endwin()

def main(argv):
    """Routine principale

    Args:
        argv (_type_): _description_
    """
    # Les logs c'est bien
    # logger = logging.getLogger(__name__)

    # On assigne avant
    server = None
    player = None

    logger.info("Récupération des paramètres de la ligne de commande")

    try:
        opts, args = getopt.getopt(argv, "hs:p:", ["server=", "player="])
    except getopt.GetoptError:
        print("RaspDacDisplayCS.py -s <serveur LMS> -p <player>")
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            print(
                "RaspDacDisplayCS.py -s <serveur LMS> -p <player pour lequel il faut récupérer les infos>"
            )
            sys.exit()
        elif opt in ("-s", "--server"):
            server = arg
            print("Adresse serveur LMS : ", server)
        elif opt in ("-p", "--player"):
            player = arg
            print("Adresse player : ", player)

    logger.debug("Paramètres ligne de commande : %s", opts)

    try:
        # Si pas de serveur précisé en ligne de commande, on prends l'adresse IP locale
        if server is None:
            server = get_ip()

        # Adresse MAC du player à surveiller (en gros celle du RaspDAC)
        # Si pas de player on prends l'adresse MAC locale
        #if player is None:
        #    logger.debug("Pas de player précisé, on prends l'adresse MAC de cette machine")
            # // player = "B8:27:EB:09:65:F9"
        #    player = get_mac()

        # Initialisation de notre classe qui gère l'affichage du RaspDAC
        # logger.debug("Player: %s", player)
        # logger.debug("Server: %s", server)
        if player is None:
            rd = RaspDacDisplay(lms_server=server)
        else:
            rd = RaspDacDisplay(lms_server=server, player=player)

        # Lancement
        rd.start()

    except Exception:
        # Impossible d'initialiser la classe ou de lancer le Thread
        logger.critical("Impossible d'initialiser la classe ou de lancer le Thread...")
        logger.critical(
            "Exception",
            exc_info=(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2]),
        )

    finally:
        logger.info("Fin de l'application d'affichage sur le Raspdac")

        # Ménage
        if DISPLAY_INSTALLED:
            GPIO.cleanup()

        # Code sortie différent de 0 pour récupérer via shell éventuellement
        sys.exit(1)


if __name__ == "__main__":
    logger.debug("Début du programme")

    # On parse la ligne de commande et on lance la routine principale
    main(sys.argv[1:])

    # window = CursesLCD()

    # while True:
    # 	window.message(0,0,u"Démarrage...".encode('UTF-8'))
    # 	window.message(1,0,"Ligne 2")

    # 	event = window.getch()

    # 	if event == 27:
    # 		break

    # Force l'appel au destructeur pour libérer curses
    # del window
