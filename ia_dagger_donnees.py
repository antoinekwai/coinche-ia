import os
import sys
import random
import multiprocessing as mp
import ia_imitation_donnees as base
from ia_imitation_donnees import Professeur
from ia_joueur import JoueurIA, FICHIER
from partie import jouer_donne
from regles import REGLES_STANDARD


class Eleve(Professeur):
    """Monte Carlo (50 simulations) évalue, mais c'est l'IA qui joue le plus souvent."""
    nom = "Élève"
    part_ia = 0.8          # 80 % des cartes jouées par l'IA, 20 % par Monte Carlo
    epsilon = 0.0
    memoire = None
    fichier = FICHIER

    def __init__(self):
        super().__init__(50)

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        choix_mc = super().jouer_carte(main, jouables, pli, contrat, joueur, regles)
        if len(jouables) > 1 and random.random() < self.part_ia:
            return JoueurIA.jouer_carte(self, main, jouables, pli, contrat, joueur, regles)
        return choix_mc


def generer(numero):
    random.seed(numero)
    notes = []
    joueurs = [Eleve() for _ in range(4)]
    for j in joueurs:
        j.notes = notes
    jouer_donne(numero % 4, joueurs, REGLES_STANDARD)
    return notes


base.generer = generer     # le programme de base utilisera cette version


if __name__ == "__main__":
    nb_blocs = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    with mp.get_context("fork").Pool(os.cpu_count()) as pool:
        for b in range(10, 10 + nb_blocs):      # blocs 10 à 19 : nouvelles donnes
            base.bloc(b, pool)
    print("Génération DAgger terminée.")
