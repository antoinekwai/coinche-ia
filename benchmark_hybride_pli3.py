"""
benchmark_hybride_pli3.py
Encadrement du point d'inflexion IA / Monte-Carlo :
- hyb_p1    : IA Pli 1      (MC Plis 2-8)
- hyb_p1_p2 : IA Plis 1-2   (MC Plis 3-8) -> référence actuelle
- hyb_p1_p3 : IA Plis 1-2-3 (MC Plis 4-8) -> nouveau candidat
Mesure appariée sur 300 donnes neuves.
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

NB_DONNES = 300
PREMIERE_GRAINE = 10_000_000


class BotHybride(BotMCIAv3):
    def __init__(self, max_plis_ia, nom="Hybride"):
        super().__init__()
        self.max_cartes_ia = max_plis_ia * 4
        self.nom = nom
        self.ia = JoueurIA()

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        if len(jouables) == 1:
            return jouables[0]
        # Si on est dans les plis réservés à l'IA
        if len(self.historique) < self.max_cartes_ia:
            self.ia.historique = list(self.historique)
            self.ia.encheres = list(self.encheres)
            return self.ia.jouer_carte(main, jouables, pli, contrat, joueur, regles)
        # Sinon Monte-Carlo v3
        return super().jouer_carte(main, jouables, pli, contrat, joueur, regles)


MOTS = {
    "hyb_p1_p2": lambda: BotHybride(2, "Hybride Plis 1-2 (Réf)"),
    "hyb_p1_p3": lambda: BotHybride(3, "Hybride Plis 1-2-3"),
    "hyb_p1":    lambda: BotHybride(1, "Hybride Pli 1"),
}

print(f"=== BENCHMARK OPTIMISATION SEUIL IA (PLIS 1, 2, 3) : {NB_DONNES} donnes ===")
print("Référence : hyb_p1_p2 (MC démarre au Pli 3)")
print("-" * 75)

donnes_jouees = 0
res_pts = {m: [] for m in MOTS}
res_sec = {m: [] for m in MOTS}
res_ok = {m: [] for m in MOTS}
res_marque = {m: [] for m in MOTS}

t_debut = time.time()

for g in range(PREMIERE_GRAINE, PREMIERE_GRAINE + NB_DONNES * 2):
    if donnes_jouees >= NB_DONNES:
        break

    random.seed(g); np.random.seed(g % (2**32)); torch.manual_seed(g)
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

    for nom, fabrique in MOTS.items():
        random.seed(g * 10 + 7)
        np.random.seed((g * 10 + 7) % (2**32))
        torch.manual_seed(g * 10 + 7)

        mains = [list(m) for m in mains_init]
        bot = fabrique()
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
        ecoule = time.time() - t_debut
        m_p12 = np.mean(res_marque["hyb_p1_p2"])
        m_p13 = np.mean(res_marque["hyb_p1_p3"])
        m_p1  = np.mean(res_marque["hyb_p1"])
        print(f"  {donnes_jouees:3d}/{NB_DONNES} donnes | {ecoule/60:4.1f} min | Marque: Pli1-2={m_p12:+.1f} | Pli1-3={m_p13:+.1f} | Pli1={m_p1:+.1f}", flush=True)

print("\n" + "=" * 75)
print(f"RÉSULTATS SUR {donnes_jouees} DONNES APPARIÉES :")
print("=" * 75)
print(f"{'Moteur':<16} | {'Pts faits':>9} | {'Succès':>7} | {'Temps/partie':>12} | {'Marque moy.':>11} | {'Écart vs Pli1-2':>16}")
print("-" * 75)

ref = np.array(res_marque["hyb_p1_p2"], dtype=float)
for nom in ["hyb_p1_p2", "hyb_p1_p3", "hyb_p1"]:
    pts_m = np.mean(res_pts[nom])
    taux = 100 * np.mean(res_ok[nom])
    sec_m = np.mean(res_sec[nom])
    marq = np.array(res_marque[nom], dtype=float)
    marq_m = marq.mean()

    ecart = marq - ref
    marge = 1.96 * ecart.std(ddof=1) / np.sqrt(len(ecart)) if nom != "hyb_p1_p2" else 0.0
    txt_ecart = f"{ecart.mean():+6.1f} ± {marge:4.1f}" if nom != "hyb_p1_p2" else "référence"

    print(f"{nom:<16} | {pts_m:9.1f} | {taux:6.1f}% | {sec_m:10.2f}s | {marq_m:+11.1f} | {txt_ecart:>16}")
