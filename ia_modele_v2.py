"""
ia_modele_v2.py
Modèle neuronal et classe joueur pour l'encodage V2 (324 entrées).
Autonome et indépendant de ia_joueur.py / ia_carte.pt.
"""
import os
import numpy as np
import torch
import torch.nn as nn
from ia_encodage_v2 import (
    encoder_situation_v2, encoder_carte_v2,
    TAILLE_SITUATION_V2, TAILLE_CARTE_V2
)
from ia_joueur import cartes_sont_equivalentes_rapide
from systeme_v2 import SysV2
from moteur import gagnant_pli

torch.set_num_threads(1)
FICHIER_V2_DEFAUT = "ia_carte_v2_champion.pt"


def creer_reseau_v2():
    """Réseau MLP à 3 couches cachées pour l'encodage V2 (324 entrées)."""
    entree = TAILLE_SITUATION_V2 + TAILLE_CARTE_V2  # 290 + 34 = 324
    return nn.Sequential(
        nn.Linear(entree, 512), nn.ReLU(),
        nn.Linear(512, 256), nn.ReLU(),
        nn.Linear(256, 128), nn.ReLU(),
        nn.Linear(128, 1)
    )


_CACHE_V2 = {}


def charger_v2(fichier):
    """Charge le réseau V2 avec mise en cache mémoire."""
    cle = (fichier, os.path.getmtime(fichier) if os.path.exists(fichier) else 0)
    if cle not in _CACHE_V2:
        r = creer_reseau_v2()
        if os.path.exists(fichier):
            r.load_state_dict(torch.load(fichier, map_location="cpu"))
        r.eval()
        _CACHE_V2.clear()
        _CACHE_V2[cle] = r
    return _CACHE_V2[cle]


class JoueurIA_V2(SysV2):
    """Joueur IA autonome utilisant l'encodage et le réseau V2."""
    nom = "IA_V2"
    arbitrage_defensif = True   # pli perdu à coup sûr : plus basse de la séquence

    def __init__(self, fichier=FICHIER_V2_DEFAUT):
        super().__init__()
        self.fichier = fichier
        self.historique = []
        self.encheres = []

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        if len(jouables) == 1:
            return jouables[0]

        atout = contrat["atout"]

        # 1. Encodage de la situation V2
        s = encoder_situation_v2(
            main, pli, self.historique, contrat, joueur, regles, self.encheres
        )
        defense_purgee = bool(s[282] == 1.0)

        # 2. Encodage de chaque carte candidate V2 (avec bits maîtres)
        vec_cartes = np.stack([
            encoder_carte_v2(c, atout, main, self.historique, pli, defense_purgee)
            for c in jouables
        ])

        # Concaténation : N cartes x 324 descripteurs
        s_rep = np.repeat(s[None, :], len(jouables), axis=0)
        x = np.concatenate([s_rep, vec_cartes], axis=1)

        # 3. Évaluation par le réseau V2
        with torch.no_grad():
            notes = charger_v2(self.fichier)(torch.from_numpy(x)).squeeze(1).numpy()

        k = int(notes.argmax())
        top_c = jouables[k]

        # 4. Arbitrage déterministe des cartes équivalentes (séquence maîtresse / As-10)
        equivs = [
            c for c in jouables
            if cartes_sont_equivalentes_rapide(c, top_c, main, pli, atout, self.historique)
        ]
        if len(equivs) > 1:
            ordre_naturel = (["V", "9", "A", "10", "R", "D", "8", "7"] if top_c[1] == atout
                             else ["A", "10", "R", "D", "V", "9", "8", "7"])
            equivs.sort(key=lambda c: ordre_naturel.index(c[0]))
            top_c = equivs[0]
            # Correctif doctrine : pli PERDU À COUP SÛR -> plus basse de la séquence
            if self.arbitrage_defensif and pli:
                g_actuel, c_gag = gagnant_pli(pli, atout)
                g_apres, _ = gagnant_pli(list(pli) + [(joueur, top_c)], atout)
                if g_actuel % 2 != joueur % 2 and g_apres != joueur:
                    # 3e/4e : le partenaire a déjà joué. 2e : seulement si la carte adverse est un atout (forcément maître)
                    perdu_sur = len(pli) >= 2 or c_gag[1] == atout
                    if perdu_sur:
                        top_c = equivs[-1]

        return top_c
