import os
import sys
import time
import random
import multiprocessing as mp
import numpy as np
from regles import REGLES_STANDARD
from partie import jouer_donne
from systeme_corrige import SysCorrige
from montecarlo import (JoueurMonteCarloContrat, manques, bilan_passe,
                        belote_imaginee, simuler, contrat_reussi)
from ia_encodage import encoder_situation, indice, ordre_couleurs

DOSSIER = "imitation"
PAR_BLOC = 10000
GRAINE = 3000000      # donnes différentes de celles des évaluations
BONUS = 0.2           # même échelle que la récompense de l'IA


class Professeur(JoueurMonteCarloContrat, SysCorrige):
    """Monte Carlo qui note son évaluation de chaque carte autorisée."""
    nom = "Professeur"
    notes = None      # liste où ranger (situation, [(carte, valeur), ...])

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        if len(jouables) == 1:
            return jouables[0]
        atout = contrat["atout"]
        eq, attaque = joueur % 2, contrat["joueur"] % 2
        manque = manques(self.historique, atout, regles)
        plis_faits = (len(self.historique) - len(pli)) // 4
        passe_pts, passe_plis = bilan_passe(self.historique, atout)
        valeurs = {c: 0.0 for c in jouables}

        for _ in range(self.nb_simulations):
            mains = self.imaginer(main, joueur, manque, atout)
            belote = belote_imaginee(mains, self.historique, atout)
            for c in jouables:
                pts, plis = simuler(mains, pli, contrat, joueur, c, plis_faits, regles)
                total = [passe_pts[e] + pts[e] for e in (0, 1)]
                reussi = contrat_reussi(contrat, total[attaque], passe_plis[attaque] + plis[attaque],
                                        belote == attaque, regles)
                gagne = reussi if eq == attaque else not reussi
                valeurs[c] += (1.0 if gagne else -1.0) + BONUS * (total[eq] - total[1 - eq]) / 162

        s = encoder_situation(main, pli, self.historique, contrat, joueur, regles, self.encheres)
        ordre = ordre_couleurs(atout)
        self.notes.append((s, [(indice(c, ordre), valeurs[c] / self.nb_simulations) for c in jouables]))
        return max(jouables, key=lambda c: valeurs[c])


def generer(numero):
    random.seed(numero)
    notes = []
    joueurs = [Professeur() for _ in range(4)]
    for j in joueurs:
        j.notes = notes
    jouer_donne(numero % 4, joueurs, REGLES_STANDARD)
    return notes


def bloc(b, pool):
    fichier = os.path.join(DOSSIER, f"bloc_{b:02d}.npz")
    if os.path.exists(fichier):
        print(f"Bloc {b} déjà présent, on passe.")
        return
    debut = time.time()
    S, D, C, V = [], [], [], []
    numeros = range(GRAINE + b * PAR_BLOC, GRAINE + (b + 1) * PAR_BLOC)
    for k, notes in enumerate(pool.imap_unordered(generer, numeros, chunksize=10)):
        for s, cartes in notes:
            d = len(S)
            S.append(s.astype(np.float16))
            for c, v in cartes:
                D.append(d)
                C.append(c)
                V.append(v)
        if (k + 1) % 2000 == 0:
            ecoule = time.time() - debut
            print(f"  Bloc {b} : {k + 1}/{PAR_BLOC} donnes ({ecoule / 60:.1f} min, "
                  f"encore environ {ecoule / (k + 1) * (PAR_BLOC - k - 1) / 60:.0f} min)")
    np.savez(fichier, S=np.array(S), D=np.array(D, dtype=np.int32),
             C=np.array(C, dtype=np.int8), V=np.array(V, dtype=np.float32))
    print(f"Bloc {b} enregistré : {len(S)} décisions, {len(V)} cartes évaluées "
          f"({(time.time() - debut) / 60:.0f} min)\n")


if __name__ == "__main__":
    nb_blocs = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    os.makedirs(DOSSIER, exist_ok=True)
    with mp.get_context("fork").Pool(os.cpu_count()) as pool:
        for b in range(nb_blocs):
            bloc(b, pool)
    print("Génération terminée.")
