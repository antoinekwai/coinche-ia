"""
grand_duel_v3_vs_v5_3000.py
LE GRAND VERDICT STATISTIQUE SUR 3 000 DONNES APPARIÉES :
- Plis 1-2 : IA Réseau V2 pure
- Plis 3-8 : Monte-Carlo 20 simulations
  * v3_pli3 : Détective v3 classique (tirage naturel + rejeu)
  * v5_pli3 : Détective v5 guidé (atouts calibrés sur 1re annonce + As pondérés)
Adversaire étalon : MC-Enchères
"""
import os, sys, time, json, random
import numpy as np
import torch
from regles import REGLES_STANDARD
from moteur import distribuer, cartes_jouables, gagnant_pli, points, equipe_belote, decompte
from partie import phase_annonces
from test_mc_encheres import MCEncheres
from ia_modele_v2 import JoueurIA_V2
from bot_mc_ia_v6 import BotMCIAv6, FICHIER_V6_RESEAU
from detective_v3 import imaginer_v3
from detective_v5 import imaginer_v5
from montecarlo import belote_imaginee, contrat_reussi
import bot_mc_ia

NB_DONNES = 3000
FICHIER_RESULTATS = "resultats_3000_v3_v5.jsonl"
GRAINE_BASE = 150_000_000


class BotPli3_V3(BotMCIAv6):
    nom = "v3 (Aléatoire)"
    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        if len(jouables) == 1: return jouables[0]
        if len(self.historique) < 8:
            self.ia_v2.historique = list(self.historique)
            self.ia_v2.encheres = list(self.encheres) if self.encheres else []
            return self.ia_v2.jouer_carte(main, jouables, pli, contrat, joueur, regles)

        atout = contrat["atout"]
        eq, attaque = joueur % 2, contrat["joueur"] % 2
        mains_ech = [imaginer_v3(main, joueur, self.historique, self.encheres, atout, regles) for _ in range(self.nb_simulations)]
        scores = {c: 0.0 for c in jouables}
        for m_sim in mains_ech:
            bel = belote_imaginee(m_sim, self.historique, atout)
            for c in jouables:
                pts_t, pl_t = self.simuler_avec_ia_v2(m_sim, pli, atout, contrat, joueur, c, regles)
                reussi = contrat_reussi(contrat, pts_t[attaque], pl_t[attaque], bel == attaque, regles)
                gagne = reussi if eq == attaque else not reussi
                scores[c] += (1000.0 if gagne else -1000.0) + (pts_t[eq] - pts_t[1 - eq])
        return max(jouables, key=scores.get)


class BotPli3_V5(BotMCIAv6):
    nom = "v5 (Guidé)"
    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        if len(jouables) == 1: return jouables[0]
        if len(self.historique) < 8:
            self.ia_v2.historique = list(self.historique)
            self.ia_v2.encheres = list(self.encheres) if self.encheres else []
            return self.ia_v2.jouer_carte(main, jouables, pli, contrat, joueur, regles)

        atout = contrat["atout"]
        eq, attaque = joueur % 2, contrat["joueur"] % 2
        mains_ech = [imaginer_v5(main, joueur, self.historique, self.encheres, atout, regles) for _ in range(self.nb_simulations)]
        scores = {c: 0.0 for c in jouables}
        for m_sim in mains_ech:
            bel = belote_imaginee(m_sim, self.historique, atout)
            for c in jouables:
                pts_t, pl_t = self.simuler_avec_ia_v2(m_sim, pli, atout, contrat, joueur, c, regles)
                reussi = contrat_reussi(contrat, pts_t[attaque], pl_t[attaque], bel == attaque, regles)
                gagne = reussi if eq == attaque else not reussi
                scores[c] += (1000.0 if gagne else -1000.0) + (pts_t[eq] - pts_t[1 - eq])
        return max(jouables, key=scores.get)


MOTS = {"v3": BotPli3_V3, "v5": BotPli3_V5}

if os.path.exists(FICHIER_RESULTATS):
    os.remove(FICHIER_RESULTATS)

print(f"=== GRAND DUEL STATISTIQUE : v3 vs v5 au Pli 3 ({NB_DONNES:,} donnes) ===")
print(f"Fichier de sortie : {FICHIER_RESULTATS}")
print("-" * 75)

donnes_faites = 0
res_marque = {"v3": [], "v5": []}
res_pts = {"v3": [], "v5": []}
res_ok = {"v3": [], "v5": []}
t_debut = time.time()

with open(FICHIER_RESULTATS, "w", encoding="utf-8") as f_out:
    for g in range(GRAINE_BASE, GRAINE_BASE + NB_DONNES * 3):
        if donnes_faites >= NB_DONNES:
            break

        random.seed(g); np.random.seed(g % 2**32); torch.manual_seed(g)
        mains_init = distribuer()
        donneur = g % 4
        joueurs_ench = [JoueurIA_V2(fichier=FICHIER_V6_RESEAU) for _ in range(4)]
        contrat = phase_annonces(mains_init, donneur, joueurs_ench, REGLES_STANDARD, afficher=False)
        if contrat is None:
            continue

        donnes_faites += 1
        premier_parle = (donneur + 1) % 4
        encheres = list(joueurs_ench[premier_parle].encheres)
        camp = 0
        role = "attaque" if contrat["joueur"] % 2 == camp else "defense"
        val = contrat["valeur"]
        mult = 2 if contrat.get("coinche", 0) > 0 else 1
        atout = contrat["atout"]

        donne_record = {
            "graine": g, "role": role, "valeur": val, "atout": atout, "donneur": donneur,
            "preneur": contrat["joueur"], "encheres": encheres
        }

        for nom, cls_m in MOTS.items():
            random.seed(g * 10 + 7); np.random.seed((g * 10 + 7) % 2**32); torch.manual_seed(g * 10 + 7)
            mains_c = [list(m) for m in mains_init]
            bot = cls_m(nb_simulations=20)
            adv = MCEncheres()
            hist, p_eq = [], [0, 0]
            prem = (donneur + 1) % 4

            while len(hist) < 32:
                pli = []
                for step in range(4):
                    j = (prem + step) % 4
                    jbs = cartes_jouables(mains_c[j], pli, atout, j, REGLES_STANDARD)
                    if j % 2 == camp:
                        bot.historique = list(hist); bot.encheres = list(encheres)
                        c = bot.jouer_carte(mains_c[j], jbs, pli, contrat, j, REGLES_STANDARD)
                    else:
                        adv.historique = list(hist); adv.encheres = list(encheres)
                        c = adv.jouer_carte(mains_c[j], jbs, pli, contrat, j, REGLES_STANDARD)
                    mains_c[j].remove(c)
                    pli.append((j, c))
                    hist.append((j, c))
                g_pli = gagnant_pli(pli, atout)[0]
                prem = g_pli
                p_eq[g_pli % 2] += sum(points(cc, atout) for _, cc in pli)
                if len(hist) == 32: p_eq[g_pli % 2] += REGLES_STANDARD["dix_de_der"]

            bel = equipe_belote(mains_init, atout)
            _, reussi = decompte(contrat, p_eq, [0,0], bel, REGLES_STANDARD)
            gagne = reussi if role == "attaque" else not reussi
            marque_camp = (val * mult) if gagne else (-val * mult)

            res_marque[nom].append(marque_camp)
            res_pts[nom].append(p_eq[camp])
            res_ok[nom].append(gagne)
            donne_record[f"{nom}_pts"] = p_eq[camp]
            donne_record[f"{nom}_ok"] = gagne
            donne_record[f"{nom}_marque"] = marque_camp

        f_out.write(json.dumps(donne_record, ensure_ascii=False) + "\n")
        f_out.flush()

        if donnes_faites % 100 == 0:
            ec = time.time() - t_debut
            vitesse = donnes_faites / ec
            reste = (NB_DONNES - donnes_faites) / vitesse
            m_v3 = np.mean(res_marque["v3"])
            m_v5 = np.mean(res_marque["v5"])
            diff = m_v5 - m_v3
            print(f"  {donnes_faites:4d}/{NB_DONNES} donnes | {ec/60:4.1f} min écoulées | reste ≈ {reste/60:4.1f} min | Marque: v3={m_v3:+.1f} vs v5={m_v5:+.1f} (diff: {diff:+.1f})", flush=True)

print("\n" + "=" * 75)
print(f"RÉSULTATS FINAUX SUR {donnes_faites:,} DONNES APPARIÉES :")
print("=" * 75)
m3_arr = np.array(res_marque["v3"], dtype=float)
m5_arr = np.array(res_marque["v5"], dtype=float)
ecart = m5_arr - m3_arr
marge = 1.96 * ecart.std(ddof=1) / np.sqrt(len(ecart))

for nom in ["v3", "v5"]:
    p_m = np.mean(res_pts[nom])
    tx = 100 * np.mean(res_ok[nom])
    mq = np.mean(res_marque[nom])
    txt_diff = f"{ecart.mean():+.1f} ± {marge:.1f}" if nom == "v5" else "référence"
    print(f"{nom:<10} | Pts faits: {p_m:5.1f} | Succès: {tx:5.1f}% | Marque moy: {mq:+6.1f} | Écart vs v3: {txt_diff}")

print("-" * 75)
print(f"Donnes où v5 > v3 : {sum(1 for e in ecart if e > 0):,}")
print(f"Donnes où v3 > v5 : {sum(1 for e in ecart if e < 0):,}")
print(f"Donnes identiques : {sum(1 for e in ecart if e == 0):,}")
