#! /usr/local/bin/python
# -*- coding: utf-8 -*-
# Fork du script ...
# cyril.sudre@laposte.net

import Winstar_GraphicOLED
from datetime import datetime
import socket
import time
import json
import logging
import os
import sys
import queue
from threading import Thread

import pylms
from pylms import server
from pylms import player
import telnetlib
from socket import error as socket_error
import traceback
import getopt

# Pour pouvoir utiliser l'unicode avec curses
import locale
locale.setlocale(locale.LC_ALL, '')

try:
	import RPi.GPIO as GPIO
	DISPLAY_INSTALLED = True
except:
	import curses
	DISPLAY_INSTALLED = False

# Définition des pages
import pages

# Fichier de log
LOGFILE='RaspDacDisplay.log'

HESITATION_TIME = 2.5 		# Temps d'hésitation (en secondes) avant scrolling
ANIMATION_SMOOTHING = .15 	# Temps (en secondes) avant rafraichissement de l'écran

# Instance du loggueur
logger=logging.getLogger(__name__)

# Niveau de log
logger.setLevel(logging.DEBUG)

# Notre fichier de log
fh = logging.FileHandler(LOGFILE)

# Niveau de log
fh.setLevel(logging.DEBUG)

# La tronche de notre fichier de log
formatter=logging.Formatter('%(asctime)s - %(name)s (%(lineno)s) - %(levelname)s: %(message)s')

# On précise que notre gestionnaire va utiliser ce format
fh.setFormatter(formatter)

# On ajoute comme gestionnaire de log
logger.addHandler(fh)

class RaspDac_Display():
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
	STARTUP_MSG = u"Démarrage..."

	def __init__(self,player=None,lms_server="127.0.0.1",lms_port=9090,lms_user="",lms_pwd="",dw=16,dh=2):
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
		self.logger.info("Initialisation avec les paramètres : %s,%s,%s,%s,%s", player, lms_server, lms_port, lms_user, lms_pwd)

		# Gestionnaire d'erreurs non capturées
		sys.excepthook = self.excepthook
		
		# Connexion au serveur LMS
		self.lmsserver = pylms.server.Server(lms_server, lms_port, lms_user, lms_pwd)
		#// self.lmsserver.connect()

		# Routine qui cherche le player si précisé, sinon le premier renvoyé par le serveur
		self._getPlayer(player)

	def _getPlayer(self, player):
		"""Récupère le player
		
		Arguments:
			player {str} -- [Adresse MAC du player recherché]
		
		Raises:
			Exception -- [description]
		"""
		self.logger.info("Recherche du player %s sur le serveur LMS", player)

		try:
			# Connection au serveur LMS
			self.lmsserver.connect()

			# Si aucun player spécifié : on prends le premier retourné par le serveur (pratique s'il n'y en a qu'un)
			if player is None:
				self.lmsplayer = self.lmsserver.get_players()[0]
			else:
				# On cherche notre player
				players = self.lmsserver.get_players()
				for p in players:
					# Comparaison des adresses MAC pour trouver notre player
					if p.get_ref().lower() == player.lower():
						self.lmsplayer = p
						break
			
			# Si on a rien c'est pas bon...On fera pas grand chose !
			if self.lmsplayer is None:
				raise Exception('Impossible de trouver un player sur le serveur')
		except (socket_error, AttributeError, IndexError):
			self.logger.debug("La connexion au serveur LMS a échoué lors de la recherche du player")
	
	def status_lms(self):
		"""Récupère le status du player depuis le serveur LMS
		
		Raises:
			Exception -- [description]
		
		Returns:
			[type] -- [description]
		"""

		try:
			lms_status = self.lmsplayer.get_mode()
		except:
			# On essaye de se reconnecter
			try:
				self.lmsserver.connect()
				
				# On retrouve notre player
				self._getPlayer(self.player)
				
				# On récupère le statut
				lms_status = self.lmsplayer.get_mode()

			except (socket_error, AttributeError, IndexError):
				self.logger.debug("Impossible de récupérer le statut depuis le serveur")
				return { 'state':u"stop", 'artist':u"", 'title':u"", 'album':u"", 'remaining':u"", 'current':0, 'duration':0, 'position':u"", 'volume':0, 'playlist_display':u"", 'playlist_position':0, 'playlist_count':0, 'bitrate':u"", 'type':u"", 'current_time':u""}

		if lms_status == "play":
			import urllib

			artist = urllib.parse.unquote(str(self.lmsplayer.request("artist ?", True))).decode('utf-8')
			title = urllib.parse.unquote(str(self.lmsplayer.request("title ?", True))).decode('utf-8')
			album = urllib.parse.unquote(str(self.lmsplayer.request("album ?", True))).decode('utf-8')
			playlist_position = int(self.lmsplayer.request("playlist index ?"))+1
			playlist_count = self.lmsplayer.playlist_track_count()
			volume = self.lmsplayer.get_volume()
			current = self.lmsplayer.get_time_elapsed()
			duration = self.lmsplayer.get_track_duration()
			url = self.lmsplayer.get_track_path()

			# Get bitrate and tracktype if they are available.  Try blocks used to prevent array out of bounds exception if values are not found
			try:
				bitrate = urllib.parse.unquote(str(self.lmsplayer.request("songinfo 2 1 url:"+url+" tags:r", True))).decode('utf-8').split("bitrate:", 1)[1]
			except:
				bitrate = u""

			try:
				tracktype = urllib.parse.unquote(str(self.lmsplayer.request("songinfo 2 1 url:"+url+" tags:o", True))).decode('utf-8').split("type:",1)[1]
			except:
				tracktype = u""

			playlist_display = "{0}/{1}".format(playlist_position, playlist_count)
			# If the track count is greater than 1, we are playing from a playlist and can display track position and track count
			#//if self.lmsplayer.playlist_track_count() > 1:
			#//	playlist_display = "{0}/{1}".format(playlist_position, playlist_count)
			# if the track count is exactly 1, this is either a short playlist or it is streaming
			#//elif self.lmsplayer.playlist_track_count() == 1:
			if self.lmsplayer.playlist_track_count() == 1:
				try:
					# if streaming
					if self.lmsplayer.playlist_get_info()[0]['duration'] == 0.0:
						playlist_display = "Streaming"
					# it really is a short playlist
					#//else:
					#//	playlist_display = "{0}/{1}".format(playlist_position, playlist_count)
				except KeyError:
					self.logger.debug("In LMS couldn't get valid track information")
					playlist_display = u""
			else:
				self.logger.debug("In LMS track length is <= 0")
				playlist_display = u""

		  	# since we are returning the info as a JSON formatted return, convert
		  	# any None's into reasonable values

			if artist is None: artist = u""
			if title is None: title = u""
			if album is None: album = u""
			if current is None: current = 0
			if volume is None: volume = 0
			if bitrate is None: bitrate = u""
			if tracktype is None: tracktype = u""
			if duration is None: duration = 0

			# if duration is not available, then suppress its display
			if int(duration) > 0:
				timepos = time.strftime("%M:%S", time.gmtime(int(current))) + "/" + time.strftime("%M:%S", time.gmtime(int(duration)))
				remaining = time.strftime("%M:%S", time.gmtime(int(duration) - int(current) ) )

			else:
				timepos = time.strftime("%M:%S", time.gmtime(int(current)))
				remaining = timepos

			return { 'state':u"play", 'artist':artist, 'title':title, 'album':album, 'remaining':remaining, 'current':current, 'duration':duration, 'position':timepos, 'volume':volume, 'playlist_display':playlist_display,'playlist_position':playlist_position, 'playlist_count':playlist_count, 'bitrate':bitrate, 'type':tracktype }
		else:
			return { 'state':u"stop", 'artist':u"", 'title':u"", 'album':u"", 'remaining':u"", 'current':0, 'duration':0, 'position':u"", 'volume':0, 'playlist_display':u"", 'playlist_position':0, 'playlist_count':0, 'bitrate':u"", 'type':u""}

	def getCurrentTime(self):
		"""Retourne l'heure courante

		Returns:
			[Time] -- [Heure]
		"""
		return datetime.now().strftime("%H:%M").strip()
	
	def status(self):
		status = self.status_lms()

		# Mise à jour de l'heure courante
		status['current_time'] = self.getCurrentTime()

		return status

	# Routine principale : boucle sur la récupération des informations depuis le serveur LMS
	# Puis push dans la file d'attente des informations à afficher. Le Thread lancé gérera l'affichage depuis
	# la file d'attente.
	def start(self):
		# File d'attente pour l'affichage
		self.dq = queue.Queue()
		
		# Thread qui gère l'affichage à partir de la file d'attente
		dm = Thread(target=self.display)
		dm.setDaemon(True)
		
		self.logger.debug("Démarrage du Thread d'affichage...")
		dm.start()

		# Boucle infinie pour remplir la file d'attente à partir du serveur LMS
		try:
			current_page_number = -1
			current_line_number = 0
			page_expires = 0
			hesitation_expires = 0
			curlines = []
			hesitate_expires = []

			# On force l'état précédent pour une première mise à jour dans la boucle
			prev_state = None

			while True:
				# Récupère le statut du player
				cstatus = self.status()
				self.logger.debug("Statut LMS : %s", cstatus)

				# Etat du player ("play" ou "stop")
				state = cstatus.get('state')

				self.logger.debug("Etat du player : %s", state)
				
				# Besoin de changer l'affichage actuel ?
				if (state != prev_state):
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

					# Passage à la page suivante et vérification si elle doit être affichée ou cachée
					for i in range(len(current_pages['pages'])):
						current_page_number = current_page_number + 1

						# Si on est sur la dernière page on repasse à la première
						if current_page_number > len(current_pages['pages'])-1:
							current_page_number = 0

						# Expiration de la page actuelle, fonction de la durée spécifiée
						page_expires = time.time() + current_pages['pages'][current_page_number]['duration']

						# On stocke la page courante
						#//cp = current_pages['pages'][current_page_number]

				# Set current_page
				current_page = current_pages['pages'][current_page_number]

				# Now display the lines from the current page
				lines = []
				for i in range(len(current_page['lines'])):

					# make sure curlines is big enough.  curlines is used to detect when the display has changed
					# if not expanded here it will cause an IndexError later if it has not already been initialized
					while len(curlines) < len(current_page['lines']):
						curlines.append("")

					# make sure hesitate_expires is big enough as well
					while len(hesitate_expires) < len(current_page['lines']):
						hesitate_expires.append(0)

					current_line = current_page['lines'][i]

					#//try:
					#//	variables = current_line['variables']
					#//except KeyError:
					#//	variables = []

					# Heure courante formattée
					cstatus['current_time_formatted'] = datetime.now().strftime('%d/%m/%Y %H:%M')

					format = current_line['format']
					#//self.logger.debug("Format : %s", format)

					# On récupère les paramètres. On passe si ce paramètre n'existe pas
					parms = []
					for j in range(len(current_line['variables'])):
						try:
							# if type(cstatus[current_line['variables'][j]]) is unicode:
							if type(cstatus[current_line['variables'][j]]) is str:
								parms.append(cstatus[current_line['variables'][j]].encode('utf-8'))
							else:
								parms.append(cstatus[current_line['variables'][j]])
						except KeyError:
							self.logger.debug("Clé non trouvée : %s", current_line['variables'][j])
							pass

					# Création de la ligne à afficher
					self.logger.debug("Chaîne ligne %s : %s", i, parms)

					line = format.format(*parms).decode('utf-8')

					# justify line
					#//try:
					#//	if current_line['justification'] == "center":
					#//		line = "{0:^{1}}".format(line, DISPLAY_WIDTH)
					#//	elif current_line['justification'] == "right":
					#//		line = "{0:>{1}}".format(line, DISPLAY_WIDTH)
					#//except KeyError:
					#//	pass

					lines.append(line)

					# determine whether to scroll or not
					# if scroll is false, set hesitation time to large value which
					# effectively shuts off the scroll function
					if lines[i] != curlines[i]:
						curlines[i] = lines[i]
						try:
							if current_line['scroll']:
								hesitate_expires[i] = time.time() + HESITATION_TIME
							else:
								hesitate_expires[i] = time.time() + 86400 # Do not scroll
						except KeyError:
							hesitate_expires[i] = time.time() + 86400 # Do not scroll

				#? Détermine si l'écran doit hésiter avant de scroller
				dispval = []
				for i in range(len(lines)):
					if hesitate_expires[i] < time.time():
						dispval.append(lines[i])
					else:
						dispval.append(lines[i][0:self.dw])

				# On ajoute les informations à afficher dans la file d'attente
				self.dq.put(dispval)

				# Attente avant prochaine mise à jour
				time.sleep(.25)

		# Interruption du script
		except KeyboardInterrupt:
			pass

	# Les erreurs non gérées sont loguées
	def excepthook(self, exc_type, exc_value, exc_traceback):
		if issubclass(exc_type, KeyboardInterrupt):
			sys.__excepthook__(exc_type, exc_value, exc_traceback)
			return

		self.logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

		sys.__excepthook__(exc_type, exc_value, exc_traceback)

	# Chargement des pages en format json
	def loadPages(self):
		"""Chargement des pages à partir du fichier json
		"""
		fichier = 'pages.json'
		try:
			with open(fichier) as f:
				self.pages = json.load(f)
		except:
			self.logger.error("Impossible de charger les pages depuis %s", fichier)
			sys.exit(1)

	# Affichage du contenu de la file d'attente sur l'écran
	def display(self):

		lines = []
		columns = []

		# Objet LCD correspondant à l'écran OLED ou curses si pas dispo
		if DISPLAY_INSTALLED:
			self.logger.debug("Affichage sur écran OLED")
			lcd = Winstar_GraphicOLED.Winstar_GraphicOLED()
		else:
			self.logger.debug("Affichage avec Curses")
			lcd = CursesLCD()
		
		# Réinit, début écran, effacement
		lcd.oledReset()
		#//lcd.home()
		#//lcd.clear()

		# Message au démarrage
		lcd.message(RaspDac_Display.STARTUP_MSG)
		time.sleep(2)

		#// A quoi çà sert ?
		#//for i in range (0, l):
		#//	lines.append("")
		#//	columns.append(0)

		# Premier élément de la file d'attente
		item = self.dq.get()
		self.dq.task_done()

		# On prends les 2 éléments du tableau (item), on les place dans lines
		# On place le curseur sur la bonne ligne
		# et on affiche en limitant l'affichage au nb de colonnes indiqués en paramètre de Display
		for i in range(len(item)):
			lines[i] = item[i]
			lcd.setCursor(0,i)
			lcd.message( lines[i][0:self.dw] )

		# On stocke le moment présent (nb de secondes depuis 1970)
		prev_time = time.time()

		while True:
			short_lines=True

			# On attend un peu, en fonction de la constante ANIMATION_SMOOTHING pour avoir une animation fluide
			if time.time() - prev_time < ANIMATION_SMOOTHING:
				time.sleep(ANIMATION_SMOOTHING-(time.time()-prev_time))
			try:
				# Affiche les lignes correspondantes à des informations qui ont été modifiées
				for i in range(len(item)):

					# Information à afficher plus longue que l'écran
					if len(item[i])>self.dw:
						short_lines = False

					# Information modifiée ?
					if lines[i] != item[i]:
						# Création d'une ligne au moins aussi longue que l'existante afin d'écraser les caractères en trop sur l'écran
						buf = item[i].ljust(len(lines[i]))

						# Curseur en début de ligne et affichage
						lcd.setCursor(0,i)
						lcd.message(buf[0:self.dw])

						# Stocke le contenu de la ligne courante et remise à zéro de la colonne courante
						lines[i] = item[i]
						columns[i] = 0

				# Si les éléments ne sont pas plus long que l'écran : c'est fini
				if short_lines:
					item=self.dq.get()
					self.dq.task_done()
				# Sinon il faut mettre à jour l'écran pour scroller
				else:
					for i in range(len(lines)):
						if len(lines[i])>self.dw:
							buf = "%s          %s" % (lines[i], lines[i][0:self.dw-1])

							columns[i] = columns[i]+1
							if columns[i] > len(buf)-self.dw:
								columns[i]=0

							lcd.setCursor(0,i)

							# Affiche la partie de la chaîne à rendre visible
							lcd.message(buf[columns[i]:columns[i]+self.dw])
					
					# Rafraichissement continu de l'écran : on vérifie si une mise à jour est nécessaire sans bloquer
					item=self.dq.get_nowait()
					self.dq.task_done()

				prev_time = time.time()
			except queue.Empty:
				prev_time = time.time()
				pass

# Pour récupérer l'adresse IP de la machine sur laquelle tourne ce programme
# https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
def get_ip():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	try:
		# Cette adresse n'a pas besoin d'être atteignable
		s.connect(('10.255.255.255', 1))
		IP = s.getsockname()[0]
	except:
		IP = '127.0.0.1'
	finally:
		s.close()
	logger.debug("Adresse IP locale : %s", IP)
	return IP

# Récupération de l'adresse MAC
def get_mac():
	from uuid import getnode as get_mac
	mac = ':'.join(("%012X" % get_mac())[i:i+2] for i in range(0, 12, 2))
	logger.debug("Adresse MAC locale : %s", mac)
	return mac

# Classe qui simule un écran fictif avec curses
# Méthodes communes avec la classe Winstar_GraphicOLED
class CursesLCD():
	def __init__(self,h=2,w=16):
		"""Constructeur
		
		Keyword Arguments:
			h {int} -- [Nb lignes de l'écran] (default: {2})
			w {int} -- [Nb colonnes de l'écran] (default: {16})
		
		Returns:
			[type] -- [description]
		"""
		curses.initscr()
		curses.noecho()
		curses.cbreak()
		curses.curs_set(0)

		# Fenêtre de la taille de notre écarn LCD
		self.window = curses.newwin(h,w)
		self.window.keypad(1)
		
		# Bordure
		self.window.border(0)

	# Reset écran = curseur au début + effacement
	def oledReset(self):
		"""Reset écran (équivalent d'un home() suivi d'un clear())
		"""
		self.home()
		self.clear()

	# Repositionne le curseur au début de l'écran			
	def home(self):
		"""Repositionne le curseur au début de l'écran			
		"""
		self.setCursor(0,0)
	
	# Effacement écran
	def clear(self):
		"""Efface l'écran
		"""
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
	def setCursor(self,y,x):
		"""Déplace le curseur sur la ligne y, colonne x
		
		Arguments:
			y {integer} -- [N° de ligne sur laquelle le curseur doit se déplacer]
			x {integer} -- [N° de colonne sur laquelle le curseur doit se déplacer]
		"""
		self.window.move(y,x)

	# Attente caractère clavier
	def getch(self):
		return self.window.getch()
	
	# Destructeur : permet de libérer curses
	def __del__(self):
		curses.endwin()

# Gestion des options en ligne de commande
def main(argv):
	# Les logs c'est bien
	logger=logging.getLogger(__name__)

	# On assigne avant
	server = None
	player = None
	
	logger.info('Récupération des paramètres de la ligne de commande')

	try:
		opts, args = getopt.getopt(argv,"hs:p:",["server=","player="])
	except getopt.GetoptError:
		print('RaspDacDisplayCS.py -s <serveur LMS> -p <player>')
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print('RaspDacDisplayCS.py -s <serveur LMS> -p <player pour lequel il faut récupérer les infos>')
			sys.exit()
		elif opt in ("-s", "--server"):
			server = arg
			print('Adresse serveur LMS : ', server)
		elif opt in ("-p", "--player"):
			player = arg
			print('Adresse player : ', player)
	
	logger.debug("Paramètres ligne de commande : %s", opts)

	try:
		# Si pas de serveur précisé en ligne de commande, on prends l'adresse IP locale
		if server is None:
			server = get_ip()
			
		# Adresse MAC du player à surveiller (en gros celle du RaspDAC)
		# Si pas de player on prends l'adresse MAC locale
		if player is None:
			#// player = "B8:27:EB:09:65:F9"
			player = get_mac()
		
		# Initialisation de notre classe qui gère l'affichage du RaspDAC
		rd = RaspDac_Display(player=player, lms_server=server)

		# Lancement
		rd.start()

	except:
		# Impossible d'initialiser la classe ou de lancer le Thread
		logger.critical("Impossible d'initialiser la classe ou de lancer le Thread...")
		logger.critical("Exception", exc_info = (sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2]))

	finally:
		logger.info("Fin de l'application d'affichage sur le Raspdac")

		# Ménage
		if DISPLAY_INSTALLED:
			GPIO.cleanup()
		else:
			curses.endwin()

		# Code sortie différent de 0 pour récupérer via shell éventuellement
		sys.exit(1)

if __name__ == '__main__':

	logger.debug('Début du programme')

	# On parse la ligne de commande et on lance la routine principale
	main(sys.argv[1:])

	#window = CursesLCD()

	#while True:
	#	window.message(0,0,u"Démarrage...".encode('UTF-8'))
	#	window.message(1,0,"Ligne 2")

	#	event = window.getch()

	#	if event == 27:
	#		break

	# Force l'appel au destructeur pour libérer curses
	#del window