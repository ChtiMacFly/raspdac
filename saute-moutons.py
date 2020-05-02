# -*- coding: utf-8 -*-

chariots=["X","X","X"," ","_","_","_"]

# Nombre de chariots
nb_chariots = 6

# L'index du tableau correspondant àun emplacement vide = case du milieu au début
index_emplacement_vide = nb_chariots / 2

# Chariot de gauche seront les nombres pairs
chariots_vides=range(nb_chariots)[::2]

# Chariot de droite seront les nombres impairs
chariots_pleins=range(nb_chariots)[1::2]

# Génération du tableau avec les chariots
def genere_chariots(nb):
    pass

def deplace(index_chariot):
    """Déplacement chariot

    Arguments:
        index_chariot {integer} -- index du chariot à déplacer dans le tableau

    Returns:
        [type] -- [description]
    """
    # Nombre de case de différence entre le chariot et l'emplacement vide
    nb_case_diff = index_chariot - index_emplacement_vide

    if nb_case_diff > 2:
        raise Exception("Déplacement impossible")

    if chariots[index_chariot]=="D" and nb_case_diff > 0:
        affiche("D",index_chariot)
    else:
        if chariots[index_chariot]=="G" and nb_case_diff < 0:
            affiche("G",index_chariot)
        else:
            raise Exception("Déplacement impossible")
    
    # fin?
	n=0;
	for (i=0; i<=4; i++) {
		if (tableau[i]=="D") {n+=1;}
	}
	
    if (tableau[5]=="V") {n+=1;}
		for (i=0; i<=4; i++) {
			if (tableau[i+6]=="G") {n+=1;}
	}
	
    //si fini
	if (n==11) {
		print("Gagné !")
	} else {
		test=0;
	}

def affiche(cote,num):
	# case vide
    tableau[num]=" "
    tableau[numvide]=cote
    numvide=num

def swap(x,y):
    return y,x