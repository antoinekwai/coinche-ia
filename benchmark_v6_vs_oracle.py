"""
benchmark_v6_vs_oracle.py
Mesure officielle de réduction de l'écart avec l'Oracle :
Compare :
1. Oracle (plafond parfait)
2. v6 (Nouveau champion : Réseau V2 + MC 40s)
3. v5 (Précédent champion : Réseau V1 + MC 40s)
4. v3 (Ancien champion : Tout MC 20s)
5. IA_V2 (Nouveau réseau pur issu de la distillation v5, 11 ms)
6. IA_V1 (Ancien réseau historique pur, 11 ms)
Sur 400 donnes neuves appariées.
"""
import time
import random
import numpy as np
import torch
from regles import REGLES_STANDARD
from moteur import distribuer, cartes_jouables, gagnant_pli, points, equipe_belote, decompte
from partie import phase_annonces
from test_mc_encheres import MCEncheres
from solveur_exact import SolveurExact
from ia_joueur import JoueurIA
from ia_modele_v2 import JoueurIA_V2
from bot_mc_ia_v3 import BotMCIAv3
from bot_mc_ia_v5 import BotMCIAv5
from bot_mc_ia_v6 import BotMCIAv6, FICHIER_V6_RESEAU

NB_DONNES = 400
PREMIERE_GRAINE = 50_000_000


class OracleBot:
    nom = "Oracle (plafond)"
    def __init__(self):
        self.ia = JoueurIA()
        self.historique = []
        self.encheres = []

    def jouer_carte(self, mains_ouvertes, jouables, pli, contrat, joueur, regles):
        atout = contrat["atout"]
        if len(self.historique) < 4:
            self.ia.historique = list(self.historique)
            self.ia.encheres = list(self.encheres)
            return self.ia.jouer_carte(mains_ouvertes[joueur], jouables, pli, contrat, joueur, regles)

        solveur = SolveurExact(atout, regles)
        best_val = -9999
        c_opt = jouables[0]
        premier = (joueur - len(pli)) % 4

        for cand in jouables:
            m_test = [list(m) for m in mains_ouvertes]
            m_test[joueur].remove(cand)
            pli_test = list(pli) + [(joueur, cand)]
            solveur.transposition.clear()
            net = solveur.minimax(m_test, pli_test, premier, -1000, 1000)
            val = net if joueur % 2 == 0 else -net
            if val > best_val:
                best_val = val
                c_opt = cand
        return c_opt


MOTS = {
    "Oracle": OracleBot,
    "v6 (Nouveau)": BotMCIAv6,
    "v5 (Précédent)": BotMCIAv5,
    "v3 (Ancien)": BotMCIAv3,
    "IA_V2 (Nouveau)": lambda: JoueurIA_V2(fichier=FICHIER_V6_RESEAU),
    "IA_V1 (Ancien)": JoueurIA,
}

print(f"=== GRAND BENCHMARK DE QUALIFICATION FACE À L'ORACLE : {NB_DONNES} donnes ===")
print("Chaîne complète : IA_V1 -> IA_V2 -> v3 -> v5 -> v6 -> Oracle")
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

    random.seed(g); np.random.seed(g % 2**32); torch.manual_seed(g)
    mains_init = distribuer()
    donneur = g % 4
    joueurs_ench = [JoueurIA() for _ in range(4)]
    contrat = phase_annonces(mains_init, donneur, joueurs_ench, REGLES_STANDARD, afficher=False)
    if contrat is None:
        continue

    donnes_jouees += 1
    premier_parle = (donneur + 1) % 4
    encheres = list(joueurs_ench[premier_parle].encheres)
    camp = 0
    role = "attaque" if contrat["joueur"] % 2 == camp else "defense"
    val = contrat["valeur"]
    mult = 2 if contrat.get("coinche", 0) > 0 else 1
    atout = contrat["atout"]

    for nom, cls_m in MOTS.items():
        random.seed(g * 10 + 7); np.random.seed((g * 10 + 7) % 2**32); torch.manual_seed(g * 10 + 7)
        mains_c = [list(m) for m in mains_init]
        bot = cls_m()
        adv = MCEncheres()
        hist, p_eq, pl_eq = [], [0, 0], [0, 0]
        prem = (donneur + 1) % 4

        t0 = time.time()
        while len(hist) < 32:
            pli = []
            for k in range(4):
                j = (prem + k) % 4
                jbs = cartes_jouables(mains_c[j], pli, atout, j, REGLES_STANDARD)
                if j % 2 == camp:
                    bot.historique = list(hist)
                    bot.encheres = list(encheres)
                    if nom == "Oracle":
                        c = bot.jouer_carte(mains_c, jbs, pli, contrat, j, REGLES_STANDARD)
                    else:
                        c = bot.jouer_carte(mains_c[j], jbs, pli, contrat, j, REGLES_STANDARD)
                else:
                    adv.historique = list(hist)
                    adv.encheres = list(encheres)
                    c = adv.jouer_carte(mains_c[j], jbs, pli, contrat, j, REGLES_STANDARD)
                mains_c[j].remove(c)
                pli.append((j, c))
                hist.append((j, c))
            g = gagnant_pli(pli, atout)[0]
            prem = g
            p = sum(points(c, atout) for _, c in pli)
            if len(hist) == 32: p += REGLES_STANDARD["dix_de_der"]
            p_eq[g % 2] += p
            pl_eq[g % 2] += 1

        dt = time.time() - t0
        bel = equipe_belote(mains_init, atout)
        _, reussi = decompte(contrat, p_eq, pl_eq, bel, REGLES_STANDARD)
        gagne = reussi if role == "attaque" else not reussi
        marque_camp = (val * mult) if gagne else (-val * mult)

        res_pts[nom].append(p_eq[camp])
        res_sec[nom].append(dt)
        res_ok[nom].append(gagne)
        res_marque[nom].append(marque_camp)

    if donnes_jouees % 50 == 0:
        ec = time.time() - t_debut
        m_ora = np.mean(res_marque["Oracle"])
        m_v6 = np.mean(res_marque["v6 (Nouveau)"])
        m_v5 = np.mean(res_marque["v5 (Précédent)"])
        m_iav2 = np.mean(res_marque["IA_V2 (Nouveau)"])
        print(f"  {donnes_jouees:4d}/{NB_DONNES} donnes | {ec/60:4.1f} min | Marque: Oracle={m_ora:+.1f} | v6={m_v6:+.1f} | v5={m_v5:+.1f} | IA_V2={m_iav2:+.1f}", flush=True)

print("\n" + "=" * 75)
print(f"RÉSULTATS SUR {donnes_jouees} DONNES APPARIÉES :")
print("=" * 75)
print(f"{'Moteur':<18} | {'Pts faits':>9} | {'Succès':>7} | {'Temps/partie':>12} | {'Marque moy.':>11} | {'Écart vs Oracle':>16}")
print("-" * 75)

ref_ora = np.array(res_marque["Oracle"], dtype=float)
for nom in MOTS:
    pts_m = np.mean(res_pts[nom])
    taux = 100 * np.mean(res_ok[nom])
    sec_m = np.mean(res_sec[nom])
    marq = np.array(res_marque[nom], dtype=float)
    marq_m = marq.mean()

    ecart = marq - ref_ora
    marge = 1.96 * ecart.std(ddof=1) / np.sqrt(len(ecart)) if nom != "Oracle" else 0.0
    txt_ecart = f"{ecart.mean():+6.1f} ± {marge:4.1f}" if nom != "Oracle" else "référence (plafond)"

    print(f"{nom:<18} | {pts_m:9.1f} | {taux:6.1f}% | {sec_m:10.2f}s | {marq_m:+11.1f} | {txt_ecart:>16}")
