"""
test_purge_pli2.py
Teste l'impact d'une règle doctrinale de purge au Pli 2 :
- IA_V2_brute : Réseau V2 pur actuel (ia_carte_v2_champion.pt)
- IA_V2_purge : Réseau V2 + règle de poursuite de purge au Pli 2 si défense non purgée
Sur 300 donnes neuves appariées face à MC-Enchères.
"""
import time
import random
import numpy as np
import torch
from regles import REGLES_STANDARD
from moteur import distribuer, cartes_jouables, gagnant_pli, points, equipe_belote, decompte, COULEURS
from partie import phase_annonces
from test_mc_encheres import MCEncheres
from ia_modele_v2 import JoueurIA_V2
from bot_mc_ia_v6 import FICHIER_V6_RESEAU

NB_DONNES = 300
PREMIERE_GRAINE = 70_000_000


class JoueurIA_V2_Purge(JoueurIA_V2):
    nom = "IA_V2 (Purge P2)"

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        if len(jouables) == 1:
            return jouables[0]

        atout = contrat["atout"]
        camp_preneur = contrat["joueur"] % 2
        mon_camp = joueur % 2

        # Détecter le début du Pli 2 : 4 cartes dans l'historique et pli actuel vide
        est_entame_pli_2 = (len(self.historique) == 4 and len(pli) == 0)

        # Si mon camp est le preneur et qu'on entame le Pli 2 :
        if est_entame_pli_2 and (mon_camp == camp_preneur):
            # Vérifier si des atouts adverses sont encore vivants dehors
            atouts_vus_ou_main = sum(1 for _, c in self.historique if c[1] == atout) + sum(1 for c in main if c[1] == atout)
            atouts_dehors = 8 - atouts_vus_ou_main

            atouts_en_main = [c for c in jouables if c[1] == atout]

            # Règle doctrinale : s'il reste des atouts dehors et que j'en ai en main, jouer atout !
            if atouts_dehors > 0 and atouts_en_main:
                # Préférer le maître si on l'a (As/10 ou Valet/9), sinon le plus petit
                # On utilise le réseau pour choisir LEQUEL des atouts poser
                notes_atouts = []
                for c in atouts_en_main:
                    notes_atouts.append(c)
                # Trier par ordre naturel décroissant (les maîtres en premier)
                ordre_atout = ["V", "9", "A", "10", "R", "D", "8", "7"]
                atouts_en_main.sort(key=lambda c: ordre_atout.index(c[0]))
                return atouts_en_main[0]

        # Sinon décision standard du réseau V2
        return super().jouer_carte(main, jouables, pli, contrat, joueur, regles)


MOTS = {
    "V2_brut": lambda: JoueurIA_V2(fichier=FICHIER_V6_RESEAU),
    "V2_purge_P2": JoueurIA_V2_Purge,
}

print(f"=== TEST IMPACT PURGE PLI 2 : {NB_DONNES} donnes appariées ===")
print("V2_brut (référence) vs V2_purge_P2")
print("-" * 75)

donnes_jouees = 0
res_pts = {m: [] for m in MOTS}
res_ok = {m: [] for m in MOTS}
res_marque = {m: [] for m in MOTS}

t_debut = time.time()

for g in range(PREMIERE_GRAINE, PREMIERE_GRAINE + NB_DONNES * 2):
    if donnes_jouees >= NB_DONNES:
        break

    random.seed(g); np.random.seed(g % (2**32)); torch.manual_seed(g)
    mains_init = distribuer()
    donneur = g % 4
    joueurs_ench = [JoueurIA_V2(fichier=FICHIER_V6_RESEAU) for _ in range(4)]
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
    atout = contrat["atout"]

    for nom, fabrique in MOTS.items():
        random.seed(g * 10 + 7); np.random.seed((g * 10 + 7) % (2**32)); torch.manual_seed(g * 10 + 7)
        mains_c = [list(m) for m in mains_init]
        bot = fabrique()
        adv = MCEncheres()

        hist, p_eq, pl_eq = [], [0, 0], [0, 0]
        premier = (donneur + 1) % 4

        while len(hist) < 32:
            pli = []
            for k in range(4):
                j = (premier + k) % 4
                jbs = cartes_jouables(mains_c[j], pli, atout, j, REGLES_STANDARD)
                if j % 2 == camp_teste:
                    bot.historique = list(hist)
                    bot.encheres = list(encheres)
                    c = bot.jouer_carte(mains_c[j], jbs, pli, contrat, j, REGLES_STANDARD)
                else:
                    adv.historique = list(hist)
                    adv.encheres = list(encheres)
                    c = adv.jouer_carte(mains_c[j], jbs, pli, contrat, j, REGLES_STANDARD)
                mains_c[j].remove(c)
                pli.append((j, c))
                hist.append((j, c))

            gagnant = gagnant_pli(pli, atout)[0]
            premier = gagnant
            p = sum(points(c, atout) for _, c in pli)
            if len(hist) == 32: p += REGLES_STANDARD["dix_de_der"]
            p_eq[gagnant % 2] += p
            pl_eq[gagnant % 2] += 1

        bel = equipe_belote(mains_init, atout)
        marque_table, reussi = decompte(contrat, p_eq, pl_eq, bel, REGLES_STANDARD)

        gagne = reussi if role == "attaque" else not reussi
        pts_faits = p_eq[camp_teste]
        marque_camp = (valeur_contrat * mult_coinche) if gagne else (-valeur_contrat * mult_coinche)

        res_pts[nom].append(pts_faits)
        res_ok[nom].append(gagne)
        res_marque[nom].append(marque_camp)

print("\n" + "=" * 75)
print(f"RÉSULTATS SUR {donnes_jouees} DONNES APPARIÉES (en {time.time()-t_debut:.1f}s) :")
print("=" * 75)
print(f"{'Moteur':<16} | {'Pts faits':>9} | {'Succès':>7} | {'Marque moy.':>11} | {'Écart vs Brut':>16}")
print("-" * 75)

ref = np.array(res_marque["V2_brut"], dtype=float)
for nom in MOTS:
    pts_m = np.mean(res_pts[nom])
    taux = 100 * np.mean(res_ok[nom])
    marq = np.array(res_marque[nom], dtype=float)
    marq_m = marq.mean()

    ecart = marq - ref
    marge = 1.96 * ecart.std(ddof=1) / np.sqrt(len(ecart)) if nom != "V2_brut" else 0.0
    txt_ecart = f"{ecart.mean():+6.1f} ± {marge:4.1f}" if nom != "V2_brut" else "référence"

    print(f"{nom:<16} | {pts_m:9.1f} | {taux:6.1f}% | {marq_m:+11.1f} | {txt_ecart:>16}")
