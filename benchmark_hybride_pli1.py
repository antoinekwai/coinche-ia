"""
benchmark_hybride_pli1.py
Test statistique sur 500 donnes neuves appariées :
v3 Standard (100% MC) vs v3 Hybride (Pli 1 IA, Plis 2-8 MC) vs IA pure.
Mesure : Points faits, Taux de succès, Temps moyen, et POINTS DE MARQUE.
"""
import time
import random
import numpy as np
import torch
from regles import REGLES_STANDARD
from moteur import distribuer, cartes_jouables, gagnant_pli, points, equipe_belote, decompte
from partie import phase_annonces
from test_mc_encheres import MCEncheres
from ia_joueur import JoueurIA
from bot_mc_ia_v3 import BotMCIAv3

NB_DONNES = 500
PREMIERE_GRAINE = 9_000_000


class BotMCIAv3Pli1IA(BotMCIAv3):
    nom = "v3 Hybride (Pli 1 IA)"

    def __init__(self):
        super().__init__()
        self.ia_pli1 = JoueurIA()

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        if len(jouables) == 1:
            return jouables[0]
        # Pli 1 (moins de 4 cartes jouées dans l'historique de la donne) : IA Réseau pure
        if len(self.historique) < 4:
            self.ia_pli1.historique = list(self.historique)
            self.ia_pli1.encheres = list(self.encheres)
            return self.ia_pli1.jouer_carte(main, jouables, pli, contrat, joueur, regles)
        # Plis 2 à 8 : Monte-Carlo v3 standard
        return super().jouer_carte(main, jouables, pli, contrat, joueur, regles)


MOTS = {
    "v3_std": BotMCIAv3,
    "v3_hybride": BotMCIAv3Pli1IA,
    "ia_pure": JoueurIA
}

print(f"=== BENCHMARK HYBRIDE PLI 1 : {NB_DONNES} donnes appariées ===")
print("Camp testé : Équipe 0 (Sud/Nord) | Adversaire : MC-Enchères")
print("-" * 75)

donnes_jouees = 0
res_pts = {m: [] for m in MOTS}
res_sec = {m: [] for m in MOTS}
res_ok = {m: [] for m in MOTS}
res_marque = {m: [] for m in MOTS}

t_debut_global = time.time()

for g in range(PREMIERE_GRAINE, PREMIERE_GRAINE + NB_DONNES * 2):
    if donnes_jouees >= NB_DONNES:
        break

    random.seed(g)
    np.random.seed(g % (2**32))
    torch.manual_seed(g)

    mains_init = distribuer()
    donneur = g % 4
    joueurs_ench = [JoueurIA() for _ in range(4)]
    contrat = phase_annonces(mains_init, donneur, joueurs_ench, REGLES_STANDARD, afficher=False)

    if contrat is None:
        continue

    donnes_jouees += 1
    premier_parle = (donneur + 1) % 4
    encheres = list(joueurs_ench[premier_parle].encheres)

    camp_teste = 0
    role = "attaque" if contrat["joueur"] % 2 == camp_teste else "defense"
    valeur_contrat = contrat["valeur"]
    mult_coinche = 2 if contrat.get("coinche", 0) > 0 else 1

    for nom, cls_bot in MOTS.items():
        random.seed(g * 10 + 7)
        np.random.seed((g * 10 + 7) % (2**32))
        torch.manual_seed(g * 10 + 7)

        mains = [list(m) for m in mains_init]
        bot = cls_bot()
        adversaire = MCEncheres()

        historique, pts_eq, plis_eq = [], [0, 0], [0, 0]
        premier = (donneur + 1) % 4
        atout = contrat["atout"]

        t0 = time.time()
        while len(historique) < 32:
            pli = []
            for k in range(4):
                j = (premier + k) % 4
                jouables = cartes_jouables(mains[j], pli, atout, j, REGLES_STANDARD)
                if j % 2 == camp_teste:
                    bot.historique = list(historique)
                    bot.encheres = list(encheres)
                    c = bot.jouer_carte(mains[j], jouables, pli, contrat, j, REGLES_STANDARD)
                else:
                    adversaire.historique = list(historique)
                    adversaire.encheres = list(encheres)
                    c = adversaire.jouer_carte(mains[j], jouables, pli, contrat, j, REGLES_STANDARD)
                mains[j].remove(c)
                pli.append((j, c))
                historique.append((j, c))

            gagnant = gagnant_pli(pli, atout)[0]
            premier = gagnant
            p = sum(points(c, atout) for _, c in pli)
            if len(historique) == 32:
                p += REGLES_STANDARD["dix_de_der"]
            pts_eq[gagnant % 2] += p
            plis_eq[gagnant % 2] += 1

        dt = time.time() - t0
        bel = equipe_belote(mains_init, atout)
        marque_table, reussi = decompte(contrat, pts_eq, plis_eq, bel, REGLES_STANDARD)

        gagne = reussi if role == "attaque" else not reussi
        pts_faits = pts_eq[camp_teste]
        marque_camp = (valeur_contrat * mult_coinche) if gagne else (-valeur_contrat * mult_coinche)

        res_pts[nom].append(pts_faits)
        res_sec[nom].append(dt)
        res_ok[nom].append(gagne)
        res_marque[nom].append(marque_camp)

    if donnes_jouees % 25 == 0:
        ecoule = time.time() - t_debut_global
        v3_m = np.mean(res_marque["v3_std"])
        hyb_m = np.mean(res_marque["v3_hybride"])
        diff = hyb_m - v3_m
        print(f"  {donnes_jouees:3d}/{NB_DONNES} donnes | écoulé {ecoule/60:4.1f} min | Marque: v3={v3_m:+.1f} vs Hyb={hyb_m:+.1f} (écart: {diff:+.1f})", flush=True)

print("\n" + "=" * 75)
print(f"RÉSULTATS SUR {donnes_jouees} DONNES APPARIÉES :")
print("=" * 75)
print(f"{'Moteur':<16} | {'Pts faits':>9} | {'Succès':>7} | {'Temps/partie':>12} | {'Marque moy.':>11} | {'Écart vs v3':>14}")
print("-" * 75)

ref_m = np.array(res_marque["v3_std"], dtype=float)
for nom in ["v3_std", "v3_hybride", "ia_pure"]:
    pts_m = np.mean(res_pts[nom])
    taux = 100 * np.mean(res_ok[nom])
    sec_m = np.mean(res_sec[nom])
    marq = np.array(res_marque[nom], dtype=float)
    marq_m = marq.mean()
    
    ecart = marq - ref_m
    marge = 1.96 * ecart.std(ddof=1) / np.sqrt(len(ecart)) if nom != "v3_std" else 0.0
    txt_ecart = f"{ecart.mean():+6.1f} ± {marge:4.1f}" if nom != "v3_std" else "référence"
    
    print(f"{nom:<16} | {pts_m:9.1f} | {taux:6.1f}% | {sec_m:10.2f}s | {marq_m:+11.1f} | {txt_ecart:>14}")
