import os
import random
import numpy as np
import torch
import torch.nn as nn
from ia_encodage import encoder_situation, encoder_carte, TAILLE_SITUATION, TAILLE_CARTE
from systeme_v2 import SysV2

torch.set_num_threads(1)
FICHIER = "ia_carte.pt"


def creer_reseau_carte():
    return nn.Sequential(
        nn.Linear(TAILLE_SITUATION + TAILLE_CARTE, 512), nn.ReLU(),
        nn.Linear(512, 256), nn.ReLU(),
        nn.Linear(256, 128), nn.ReLU(),
        nn.Linear(128, 1))


_CACHE = {}


def charger(fichier):
    cle = (fichier, os.path.getmtime(fichier))
    if cle not in _CACHE:
        r = creer_reseau_carte()
        r.load_state_dict(torch.load(fichier, map_location="cpu"))
        r.eval()
        _CACHE.clear()
        _CACHE[cle] = r
    return _CACHE[cle]


def cartes_sont_equivalentes_rapide(c1, c2, main, pli, atout, historique):
    """
    Détermine si c1 et c2 sont strictement équivalentes en pouvoir de levée
    (détenues toutes les deux en main au même moment).
    """
    if c1[1] != c2[1]:
        return False
    coul = c1[1]
    ordre = (["V", "9", "A", "10", "R", "D", "8", "7"] if coul == atout
             else ["A", "10", "R", "D", "V", "9", "8", "7"])

    # 1. Cartes maîtresses consécutives en main
    vues = {c for _, c in historique} | {c for _, c in pli}
    restantes = [r for r in ordre if (r, coul) not in vues]

    maitres_en_main = []
    for r in restantes:
        if (r, coul) in main:
            maitres_en_main.append(r)
        else:
            break

    if c1[0] in maitres_en_main and c2[0] in maitres_en_main:
        return True

    # 2. Petites cartes neutres sans valeur (7 et 8 hors atout)
    if coul != atout and c1[0] in ("7", "8") and c2[0] in ("7", "8"):
        return True

    return False


class JoueurIA(SysV2):
    """Annonces du système recommandé, jeu de la carte par réseau + arbitrage canonique."""
    nom = "IA"
    fichier = FICHIER
    epsilon = 0.0
    historique = []
    encheres = []
    memoire = None

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        if len(jouables) == 1:
            return jouables[0]

        atout = contrat["atout"]

        # --- Principe de non-dominance à l'entame ---
        if not pli:
            if ("V", atout) in main:
                petits_atouts = [c for c in jouables if c[1] == atout and c[0] != "V"]
                choix = [c for c in jouables if c not in petits_atouts]
                if choix:
                    jouables = choix

            defense = (contrat["joueur"] % 2 != joueur % 2)
            if defense:
                nb_atouts = sum(1 for c in main if c[1] == atout)
                tient_valet = ("V", atout) in main
                if not tient_valet and nb_atouts < 3:
                    hors_atout = [c for c in jouables if c[1] != atout]
                    if hors_atout:
                        jouables = hors_atout

        if len(jouables) == 1:
            return jouables[0]

        s = encoder_situation(main, pli, self.historique, contrat, joueur, regles, self.encheres)
        cartes = np.stack([encoder_carte(c, atout) for c in jouables])
        x = np.concatenate([np.repeat(s[None, :], len(jouables), axis=0), cartes], axis=1)

        if random.random() < self.epsilon:
            k = random.randrange(len(jouables))
        else:
            with torch.no_grad():
                notes = charger(self.fichier)(torch.from_numpy(x)).squeeze(1).numpy()
            k = int(notes.argmax())

            # --- Harmonisation des cartes équivalentes ---
            top_c = jouables[k]
            equivs = [c for c in jouables
                      if cartes_sont_equivalentes_rapide(c, top_c, main, pli, atout, self.historique)]
            if len(equivs) > 1:
                ordre_naturel = (["V", "9", "A", "10", "R", "D", "8", "7"] if top_c[1] == atout
                                 else ["A", "10", "R", "D", "V", "9", "8", "7"])
                equivs.sort(key=lambda c: ordre_naturel.index(c[0]))
                top_c = equivs[0]
                k = jouables.index(top_c)

        if self.memoire is not None:
            self.memoire.append((joueur, x[k]))
        return jouables[k]


if __name__ == "__main__":
    from regles import REGLES_STANDARD
    from rapide import afficher_rapide
    print("Vérification JoueurIA...")
    afficher_rapide(JoueurIA, SysV2, 1000, REGLES_STANDARD)
