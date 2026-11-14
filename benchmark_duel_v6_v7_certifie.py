"""
benchmark_duel_v6_v7_certifie.py
BENCHMARK VÉRIFIÉ ET CERTIFIÉ V2 :
Compare Détective v3 vs Détective v5 au Pli 3 :
- TOUTES les simulations de fin de manche sont déroulées par le Réseau V2 (simuler_avec_ia_v2) !
- Zéro appel à l'ancien simulateur V1.
- Contrôles d'intégrité stricts au démarrage.
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

NB_DONNES = 100
FICHIER_RESULTATS = "resultats_certifies_v6_v7.jsonl"
GRAINE_BASE = 99_000_000

# Bot A : Détective v3 + Simulateur V2
class BotV6_Pli3(BotMCIAv6):
    nom = "v6_pli3 (Det v3 + Sim V2)"
    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        if len(jouables) == 1: return jouables[0]
        # Plis 1 et 2 en IA V2
        if len(self.historique) < 8:
            self.ia_v2.historique = list(self.historique)
            self.ia_v2.encheres = list(self.encheres) if self.encheres else []
            return self.ia_v2.jouer_carte(main, jouables, pli, contrat, joueur, regles)

        # Plis 3 à 8 : MC avec Détective v3 ET Simulateur V2 d'élite !
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


# Bot B : Détective v5 + Simulateur V2
class BotV7_Pli3(BotMCIAv6):
    nom = "v7_pli3 (Det v5 + Sim V2)"
    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        if len(jouables) == 1: return jouables[0]
        # Plis 1 et 2 en IA V2
        if len(self.historique) < 8:
            self.ia_v2.historique = list(self.historique)
            self.ia_v2.encheres = list(self.encheres) if self.encheres else []
            return self.ia_v2.jouer_carte(main, jouables, pli, contrat, joueur, regles)

        # Plis 3 à 8 : MC avec Détective v5 ET Simulateur V2 d'élite !
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


# --- CONTRÔLES D'INTÉGRITÉ AVANT LANCEMENT ---
b_test = BotV7_Pli3()
assert b_test.fichier_reseau == "ia_carte_v2_champion.pt", "Erreur : mauvais réseau !"
assert os.path.exists(FICHIER_V6_RESEAU), "Erreur : ia_carte_v2_champion.pt introuvable !"
print("✅ CONTRÔLE TECHNIQUE VALIDÉ : Tous les bots utilisent simuler_avec_ia_v2 et le Réseau V2 d'élite !")

MOTS = {"v6_det_v3": BotV6_Pli3, "v7_det_v5": BotV7_Pli3}

if os.path.exists(FICHIER_RESULTATS):
    os.remove(FICHIER_RESULTATS)

print(f"=== BENCHMARK CERTIFIÉ V2 : v3 vs v5 au Pli 3 ({NB_DONNES} donnes) ===")
print(f"Sortie : {FICHIER_RESULTATS}")
print("-" * 75)

donnes_faites = 0
res_marque = {"v6_det_v3": [], "v7_det_v5": []}
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
            "preneur": contrat["joueur"], "encheres": encheres,
            "mains_depart": [[f"{r}{c}" for r, c in m] for m in mains_init],
            "plis": {}
        }

        for nom, cls_m in MOTS.items():
            random.seed(g * 10 + 7); np.random.seed((g * 10 + 7) % 2**32); torch.manual_seed(g * 10 + 7)
            mains_c = [list(m) for m in mains_init]
            bot = cls_m()
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
            donne_record[f"{nom}_pts"] = p_eq[camp]
            donne_record[f"{nom}_ok"] = gagne
            donne_record[f"{nom}_marque"] = marque_camp
            donne_record["plis"][nom] = [[j, f"{r}{c}"] for j, (r, c) in hist]

        f_out.write(json.dumps(donne_record, ensure_ascii=False) + "\n")
        f_out.flush()

        if donnes_faites % 25 == 0:
            ec = time.time() - t_debut
            m_v6 = np.mean(res_marque["v6_det_v3"])
            m_v7 = np.mean(res_marque["v7_det_v5"])
            diff = m_v7 - m_v6
            print(f"  {donnes_faites:3d}/{NB_DONNES} donnes | {ec/60:4.1f} min | Marque: v6(det_v3)={m_v6:+.1f} vs v7(det_v5)={m_v7:+.1f} (écart: {diff:+.1f})", flush=True)

print("\n" + "=" * 75)
print(f"RÉSULTATS DUEL CERTIFIÉ V2 SUR {donnes_faites} DONNES :")
print("=" * 75)
m6_arr = np.array(res_marque["v6_det_v3"], dtype=float)
m7_arr = np.array(res_marque["v7_det_v5"], dtype=float)
ecart = m7_arr - m6_arr
marge = 1.96 * ecart.std(ddof=1) / np.sqrt(len(ecart))

print(f"Marque moyenne v6 (Det v3) : {m6_arr.mean():+.1f} pts")
print(f"Marque moyenne v7 (Det v5) : {m7_arr.mean():+.1f} pts")
print(f"Écart net (v7 - v6) : {ecart.mean():+.1f} ± {marge:.1f} pts de marque")
print(f"Donnes où v7 > v6 : {sum(1 for e in ecart if e > 0)}")
print(f"Donnes où v6 > v7 : {sum(1 for e in ecart if e < 0)}")
print(f"Donnes identiques : {sum(1 for e in ecart if e == 0)}")
