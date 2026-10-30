import os
import sys
import random
import multiprocessing as mp
import ia_imitation_donnees as base
from ia_imitation_donnees import Professeur
from test_mc_encheres import MCEncheres
from partie import jouer_donne
from regles import REGLES_STANDARD


class ProfesseurEncheres(Professeur):
    """Monte Carlo qui lit les enchères, et note son évaluation de chaque carte."""
    nom = "Professeur-enchères"
    essais = 50
    imaginer = MCEncheres.imaginer


def generer(numero):
    random.seed(numero)
    notes = []
    joueurs = [ProfesseurEncheres() for _ in range(4)]
    for j in joueurs:
        j.notes = notes
    jouer_donne(numero % 4, joueurs, REGLES_STANDARD)
    return notes


base.generer = generer
base.DOSSIER = "imitation_encheres"
base.GRAINE = 4000000          # donnes nouvelles


if __name__ == "__main__":
    nb_blocs = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    os.makedirs(base.DOSSIER, exist_ok=True)
    with mp.get_context("fork").Pool(os.cpu_count()) as pool:
        for b in range(nb_blocs):
            base.bloc(b, pool)
    print("Génération terminée.")
