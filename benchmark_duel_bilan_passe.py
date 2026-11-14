"""
Benchmark Duel Apparié :
BotMCIAv6 (Original) vs BotMCIAv6Correctif (Avec bilan_passe)
Chaque donne est jouée en miroir parfait (Aller et Retour inversé).
"""
import random
import time
import numpy as np
from regles import REGLES_STANDARD
from moteur import distribuer, decompte, equipe_belote, cartes_jouables, gagnant_pli, points
from partie import phase_annonces
from bot_mc_ia_v6 import BotMCIAv6
from bot_mc_ia_v6_correctif import BotMCIAv6Correctif

NB_DONNES = 60  # 60 donnes x 2 (aller-retour) = 120 matchs au total
SIMULS = 25     # 25 simuls pour un benchmark rapide et statistiquement solide (~12 minutes sur M1 Pro)

def jouer_manche_duel(mains_depart, contrat, donneur, bots, regles):
    atout = contrat["atout"]
    mains = [list(m) for m in mains_depart]
    points_eq = [0, 0]
    plis_eq = [0, 0]
    historique = []
    premier = (donneur + 1) % 4
    for _ in range(8):
        pli = []
        for i in range(4):
            j = (premier + i) % 4
            jouables = cartes_jouables(mains[j], pli, atout, j, regles)
            bots[j].historique = list(historique)
            carte = bots[j].jouer_carte(mains[j], jouables, pli, contrat, j, regles)
            if carte not in jouables:
                carte = jouables[0]
            mains[j].remove(carte)
            pli.append((j, carte))
            historique.append((j, carte))
        gagnant = gagnant_pli(pli, atout)[0]
        points_eq[gagnant % 2] += sum(points(c, atout) for _, c in pli)
        plis_eq[gagnant % 2] += 1
        premier = gagnant
    points_eq[premier % 2] += regles["dix_de_der"]
    return points_eq, plis_eq

def evaluer_match(mains, donneur, bot_nord_sud, bot_est_ouest, regles):
    # Les bots Nord/Sud = camp 0, Est/Ouest = camp 1
    bots = [bot_nord_sud, bot_est_ouest, bot_nord_sud, bot_est_ouest]
    contrat = phase_annonces(mains, donneur, bots, regles, afficher=False)
    if contrat is None:
        return 0, 0, False  # Passe générale
    bel = equipe_belote(mains, contrat["atout"])
    pts, pl = jouer_manche_duel(mains, contrat, donneur, bots, regles)
    scores, reussi = decompte(contrat, pts, pl, bel, regles)
    # Marque nette de Nord/Sud vs Est/Ouest
    marque_ns = scores[0] - scores[1]
    return marque_ns, contrat["joueur"] % 2 == 0, reussi

print("=" * 70)
print(f"BENCHMARK DUEL APPARIÉ : V6 ORIGINAL vs V6 AVEC BILAN PASSÉ")
print(f"Nombre de donnes de base : {NB_DONNES} (soit {NB_DONNES*2} manches en miroir)")
print(f"Simulations par décision : {SIMULS}")
print("=" * 70)

v6_orig = BotMCIAv6(nb_simulations=SIMULS)
v6_corr = BotMCIAv6Correctif(nb_simulations=SIMULS)

marques_diff = []
t0 = time.time()

for num in range(1, NB_DONNES + 1):
    graine = num * 10 + 7
    random.seed(graine)
    mains_brutes = distribuer()
    donneur = num % 4

    # MATCH ALLER : Correctif en Nord/Sud, Original en Est/Ouest
    m1 = [list(m) for m in mains_brutes]
    marque_aller, etait_preneur_aller, reussi_aller = evaluer_match(m1, donneur, v6_corr, v6_orig, REGLES_STANDARD)

    # MATCH RETOUR : Original en Nord/Sud, Correctif en Est/Ouest
    m2 = [list(m) for m in mains_brutes]
    marque_retour, etait_preneur_retour, reussi_retour = evaluer_match(m2, donneur, v6_orig, v6_corr, REGLES_STANDARD)

    # Gain net du Correctif sur la donne complète (Aller + (-Retour))
    gain_correctif = marque_aller - marque_retour
    marques_diff.append(gain_correctif)

    cumul = np.mean(marques_diff)
    duree = time.time() - t0
    print(f"Donne {num:2d}/{NB_DONNES} | Aller: {marque_aller:+4d} | Retour: {marque_retour:+4d} | Net Correctif: {gain_correctif:+4d} | Moyenne cumulée: {cumul:+5.1f} pts/donne ({duree:.0f}s)")

arr = np.array(marques_diff, dtype=float)
marge = 1.96 * arr.std(ddof=1) / np.sqrt(len(arr))

print("\n" + "=" * 70)
print("RÉSULTAT DU VERDICT DUEL (SUR LA MARQUE NETTE)")
print(f"Écart moyen du Correctif vs Original : {arr.mean():+5.1f} ± {marge:4.1f} points de marque par donne")
if arr.mean() > 0:
    print("🏆 RÉSULTAT POSITIF : Le correctif surpasse l'original !")
else:
    print("⚠️ RÉSULTAT : Pas d'amélioration démontrée.")
print("=" * 70)
