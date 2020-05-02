	try:
		current_page_number = -1
		current_line_number = 0
		page_expires = 0
		hesitation_expires = 0
		curlines = []
		hesitate_expires = []

		# Initialisation de l'état précédent avec la valeur du statut LMS
		prev_state = rd.status()

		# Force the system to recognize the start state as a change
		prev_state['state'] = ""

		while True:
			# Récupère le statut du player
			cstatus = rd.status()

			# Etat stocké du player
			state = cstatus.get('state')
			
			# Besoin de changer l'affichage actuel ?
			if (state != prev_state['state']):
				current_page_number = -1
				current_line_number = 0
				page_expires = 0
				curlines = []
				hesitate_expires = []

				prev_state['state'] = state

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
					cp = current_pages['pages'][current_page_number]

					try:
						hwe = cp['hidewhenempty']
					except KeyError:
						hwe = 'False'

					# to prevent old pages format from causing problems, convert values to strings
					if type(hwe) is bool:
						hwe = str(hwe)

					if hwe.lower() == 'all' or hwe.lower() == 'true':
						allempty = True
						try:
							hvars = cp['hidewhenemptyvars']
						except KeyError:
							hvars = [ ]

						for v in hvars:
							try:
								# if the variable is a string
								if type(cstatus[v]) is unicode:
									# and it is not empty, then set allempty False and exit loop
									if len(cstatus[v]) > 0:
										allempty = False
										break
								elif type(cstatus[v]) is int:
									if not cstatus[v] == 0:
										allempty = False
										break
								else:
									# All other variable types are considered not empty
									allempty = False
									break
							except KeyError:
								# if the variable is not in cstatus consider it empty
								pass
						if not allempty:
							break
					elif hwe.lower() == 'any':
						anyempty = False
						try:
							hvars = cp['hidewhenemptyvars']
						except KeyError:
							hvars = [ ]

						for v in hvars:
							try:
								# if the variable is a string
								if type(cstatus[v]) is unicode:
									# and it is empty, then set anyempty True and exit loop
									if len(cstatus[v]) == 0:
										anyempty = True
										break

								# if the value is 0 consider it empty
								elif type(cstatus[v]) is int:
									if cstatus[v] == 0:
										anyempty = True
										break
							except KeyError:
								# if the variable is not in cstatus consider it empty
								anyempty = True
								break
						if not anyempty:
							break

					else:
						# If not hidewhenempty then exit loop
						break



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
				try:
					justification = current_line['justification']
				except KeyError:
					justification = "left"

				try:
					scroll = current_line['scroll']
				except KeyError:
					scroll = False

				try:
					variables = current_line['variables']
				except KeyError:
					variables = []

				# Heure courante formattée
				cstatus['current_time_formatted'] = datetime.now().strftime('%d/%m/%Y %H:%M')

				format = current_line['format']

				# Get paramaters
				# ignore KeyError exceptions if variable is unavailable
				parms = []
				try:
					for j in range(len(current_line['variables'])):
						try:
							if type(cstatus[current_line['variables'][j]]) is unicode:
								parms.append(cstatus[current_line['variables'][j]].encode('utf-8'))
							else:
								parms.append(cstatus[current_line['variables'][j]])
						except KeyError:
							pass
				except KeyError:
					pass

				# create line to display
				line = format.format(*parms).decode('utf-8')

				# justify line
				try:
					if current_line['justification'] == "center":
						line = "{0:^{1}}".format(line, DISPLAY_WIDTH)
					elif current_line['justification'] == "right":
						line = "{0:>{1}}".format(line, DISPLAY_WIDTH)
				except KeyError:
					pass

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
					dispval.append(lines[i][0:DISPLAY_WIDTH])

			# On ajoute les informations à afficher dans la file d'attente
			dq.put(dispval)

			# Attente avant prochaine mise à jour
			time.sleep(.25)

	# Interruption du script
	except KeyboardInterrupt:
		pass
