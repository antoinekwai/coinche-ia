"""
generer_donnees_ia_v2.py
Amorçage ultra-rapide du dataset V2 :
- 15 000 donnes jouées par 4 instances de JoueurIA.
- Encodage systématique V2 (situation 290 + carte candidate 34 = 324 entrées).
- Sortie : donnees_amorcage_v2.npz (~250 000 exemples en 3 minutes).
"""
import os
import time
import random
import numpy as np
import torch
from regles import REGLES_STANDARD
from moteur import distribuer, cartes_jouables, gagnant_pli
from partie import phase_annonces
from ia_joueur import JoueurIA
from ia_encodage_v2 import (
    encoder_situation_v2, encoder_carte_v2,
    TAILLE_SITUATION_V2, TAILLE_CARTE_V2
)

NB_DONNES = int(os.environ.get("NB_DONNES", 15000))
FICHIER_SORTIE = "donnees_amorcage_v2.npz"
GRAINE_BASE = 20_000_000

print(f"=== AMORÇAGE DATASET V2 (PAR IA PURE) : {NB_DONNES:,} donnes ===")
print(f"Fichier cible : {FICHIER_SORTIE}")
print("-" * 75)

X_list = []
Y_list = []

t_debut = time.time()
donnes_faites = 0
total_exemples = 0

for g in range(GRAINE_BASE, GRAINE_BASE + NB_DONNES * 2):
    if donnes_faites >= NB_DONNES:
        break

    random.seed(g); np.random.seed(g % 2**32); torch.manual_seed(g)
    mains = distribuer()
    donneur = g % 4
    joueurs_ench = [JoueurIA() for _ in range(4)]
    contrat = phase_annonces(mains, donneur, joueurs_ench, REGLES_STANDARD, afficher=False)
    if contrat is None:
        continue

    donnes_faites += 1
    premier_parle = (donneur + 1) % 4
    encheres = list(joueurs_ench[premier_parle].encheres)
    atout = contrat["atout"]

    bots = [JoueurIA() for _ in range(4)]
    mains_courantes = [list(m) for m in mains]
    historique = []
    premier = (donneur + 1) % 4

    while len(historique) < 32:
        pli = []
        for step in range(4):
            j = (premier + step) % 4
            jbs = cartes_jouables(mains_courantes[j], pli, atout, j, REGLES_STANDARD)

            bot = bots[j]
            bot.historique = list(historique)
            bot.encheres = list(encheres)
            c_choisie = bot.jouer_carte(mains_courantes[j], jbs, pli, contrat, j, REGLES_STANDARD)

            # Enregistrer pour chaque décision non forcée
            if len(jbs) >= 2:
                sit = encoder_situation_v2(mains_courantes[j], pli, historique, contrat, j, REGLES_STANDARD, encheres)
                def_purgee = bool(sit[282] == 1.0)

                for cand in jbs:
                    vec_c = encoder_carte_v2(cand, atout, mains_courantes[j], historique, pli, def_purgee)
                    x_complet = np.concatenate([sit, vec_c])
                    cible = 1.0 if (cand == c_choisie) else -1.0
                    X_list.append(x_complet)
                    Y_list.append(cible)
                    total_exemples += 1

            mains_courantes[j].remove(c_choisie)
            pli.append((j, c_choisie))
            historique.append((j, c_choisie))

        gagnant = gagnant_pli(pli, atout)[0]
        premier = gagnant

    if donnes_faites % 2500 == 0:
        ecoule = time.time() - t_debut
        vitesse = donnes_faites / max(1e-5, ecoule)
        reste = (NB_DONNES - donnes_faites) / vitesse
        print(f"  {donnes_faites:6d}/{NB_DONNES} donnes | {total_exemples:7d} exemples | écoulé {ecoule:4.1f}s | reste ≈ {reste:4.1f}s", flush=True)

print("\nCompression des matrices en format .npz...")
X_arr = np.array(X_list, dtype=np.float32)
Y_arr = np.array(Y_list, dtype=np.float32)

np.savez_compressed(FICHIER_SORTIE, X=X_arr, Y=Y_arr)
duree = time.time() - t_debut
taille_mo = os.path.getsize(FICHIER_SORTIE) / (1024 * 1024)

print("=" * 75)
print(f"✅ AMORÇAGE TERMINÉ AVEC SUCCÈS en {duree:.1f} secondes !")
print(f"   • Donnes jouées           : {donnes_faites:,}")
print(f"   • Exemples d'entraînement : {total_exemples:,}")
print(f"   • Matrice X               : {X_arr.shape}")
print(f"   • Fichier compressé       : {FICHIER_SORTIE} ({taille_mo:.1f} Mo)")
print("=" * 75)
