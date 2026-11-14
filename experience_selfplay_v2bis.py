"""
experience_selfplay_v2bis.py
TEST D'AUTO-APPRENTISSAGE PAR RENFORCEMENT (SELF-PLAY V2) :
1. 20 000 donnes en self-play V2 avec exploration (température).
2. Apprentissage guidé par la MARQUE réelle de la donne (+valeur / -valeur).
3. Entraînement de ia_carte_v2_bis.pt.
4. Duel de qualification : V2_bis vs V2_actuel sur 400 donnes appariées.
"""
import os
import time
import random
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from regles import REGLES_STANDARD
from moteur import distribuer, cartes_jouables, gagnant_pli, points, equipe_belote, decompte
from partie import phase_annonces
from test_mc_encheres import MCEncheres
from ia_modele_v2 import creer_reseau_v2, charger_v2, JoueurIA_V2, FICHIER_V2_DEFAUT
from ia_encodage_v2 import encoder_situation_v2, encoder_carte_v2
from bot_mc_ia_v6 import FICHIER_V6_RESEAU

NB_DONNES_SELFPLAY = 20000
FICHIER_V2_ACTUEL = FICHIER_V6_RESEAU
FICHIER_V2_BIS = "ia_carte_v2_bis.pt"
NB_DONNES_DUEL = 400

# =========================================================================
# PHASE 1 : SELF-PLAY DE V2 AVEC APPRENTISSAGE PAR LA MARQUE
# =========================================================================
print("=" * 75)
print(f"PHASE 1 : SELF-PLAY IA_V2 ({NB_DONNES_SELFPLAY:,} donnes avec exploration)")
print("=" * 75)

X_list, Y_list = [], []
reseau_v2 = charger_v2(FICHIER_V2_ACTUEL)

t_deb_self = time.time()
donnes_jouees = 0
total_decisions = 0

for g in range(80_000_000, 80_000_000 + NB_DONNES_SELFPLAY * 2):
    if donnes_jouees >= NB_DONNES_SELFPLAY:
        break

    random.seed(g); np.random.seed(g % 2**32); torch.manual_seed(g)
    mains_init = distribuer()
    donneur = g % 4
    joueurs_ench = [JoueurIA_V2(fichier=FICHIER_V2_ACTUEL) for _ in range(4)]
    contrat = phase_annonces(mains_init, donneur, joueurs_ench, REGLES_STANDARD, afficher=False)
    if contrat is None:
        continue

    donnes_jouees += 1
    premier_parle = (donneur + 1) % 4
    encheres = list(joueurs_ench[premier_parle].encheres)
    atout = contrat["atout"]
    preneur = contrat["joueur"]
    camp_preneur = preneur % 2
    valeur_c = contrat["valeur"]
    mult_coinche = 2 if contrat.get("coinche", 0) > 0 else 1

    mains_c = [list(m) for m in mains_init]
    historique = []
    premier = (donneur + 1) % 4
    pts_eq, plis_eq = [0, 0], [0, 0]

    # Tampon des décisions de cette donne : (joueur, x_complet, cand, c_choisie)
    decisions_donne = []

    while len(historique) < 32:
        pli = []
        for step in range(4):
            j = (premier + step) % 4
            jbs = cartes_jouables(mains_c[j], pli, atout, j, REGLES_STANDARD)

            if len(jbs) == 1:
                c_choisie = jbs[0]
            else:
                sit = encoder_situation_v2(mains_c[j], pli, historique, contrat, j, REGLES_STANDARD, encheres)
                def_p = bool(sit[282] == 1.0)
                vec_cartes = np.stack([encoder_carte_v2(c, atout, mains_c[j], historique, pli, def_p) for c in jbs])
                s_rep = np.repeat(sit[None, :], len(jbs), axis=0)
                x_eval = np.concatenate([s_rep, vec_cartes], axis=1)

                with torch.no_grad():
                    notes = reseau_v2(torch.from_numpy(x_eval)).squeeze(1).numpy()

                # Exploration Softmax légère (T=0.4) pour tester des variantes autour du meilleur coup
                exp_notes = np.exp((notes - notes.max()) / 0.4)
                probs = exp_notes / exp_notes.sum()
                idx_c = np.random.choice(len(jbs), p=probs)
                c_choisie = jbs[idx_c]

                # Mémoriser les candidats pour l'attribution de la marque à la fin
                for k_cand, cand in enumerate(jbs):
                    decisions_donne.append((j, x_eval[k_cand], (cand == c_choisie)))

            mains_c[j].remove(c_choisie)
            pli.append((j, c_choisie))
            historique.append((j, c_choisie))

        g = gagnant_pli(pli, atout)[0]
        premier = g
        p = sum(points(c, atout) for _, c in pli)
        if len(historique) == 32: p += REGLES_STANDARD["dix_de_der"]
        pts_eq[g % 2] += p
        plis_eq[g % 2] += 1

    # Bilan de la donne : marque finale
    bel = equipe_belote(mains_init, atout)
    _, reussi = decompte(contrat, pts_eq, plis_eq, bel, REGLES_STANDARD)
    marque_brute = (valeur_c * mult_coinche) if reussi else (-valeur_c * mult_coinche)
    gain_normalise = np.clip(marque_brute / 160.0, -2.0, 2.0)

    # Rétro-propagation du résultat sur chaque décision :
    # Si le joueur était dans le camp preneur, sa récompense est gain_normalise
    # S'il était en défense, sa récompense est -gain_normalise
    for j_dec, x_comp, est_choisie in decisions_donne:
        recompense_camp = gain_normalise if (j_dec % 2 == camp_preneur) else (-gain_normalise)
        if est_choisie:
            cible = float(np.clip(recompense_camp, -1.0, 1.0))
        else:
            cible = float(np.clip(-recompense_camp, -1.0, 1.0))
        X_list.append(x_comp)
        Y_list.append(cible)
        total_decisions += 1

    if donnes_jouees % 5000 == 0:
        ec = time.time() - t_deb_self
        print(f"  {donnes_jouees:6d}/{NB_DONNES_SELFPLAY} donnes générées | {total_decisions:,} décisions | {ec:4.1f}s", flush=True)

X_arr = np.array(X_list, dtype=np.float32)
Y_arr = np.array(Y_list, dtype=np.float32)
print(f"✅ Self-play terminé en {time.time()-t_deb_self:.1f}s : {len(X_arr):,} exemples générés !")

# =========================================================================
# PHASE 2 : ENTRAÎNEMENT DU MODÈLE V2_BIS
# =========================================================================
print("\n" + "=" * 75)
print(f"PHASE 2 : ENTRAÎNEMENT DE {FICHIER_V2_BIS}")
print("=" * 75)

n_tot = len(X_arr)
n_val = int(0.10 * n_tot)
n_tr = n_tot - n_val
perm = np.random.RandomState(42).permutation(n_tot)
idx_tr, idx_va = perm[:n_tr], perm[n_tr:]

loader_tr = DataLoader(TensorDataset(torch.from_numpy(X_arr[idx_tr]), torch.from_numpy(Y_arr[idx_tr]).unsqueeze(1)), batch_size=512, shuffle=True)
loader_va = DataLoader(TensorDataset(torch.from_numpy(X_arr[idx_va]), torch.from_numpy(Y_arr[idx_va]).unsqueeze(1)), batch_size=512, shuffle=False)

mod_bis = creer_reseau_v2()
mod_bis.load_state_dict(torch.load(FICHIER_V2_ACTUEL, map_location="cpu"))

crit = nn.MSELoss()
opt = torch.optim.AdamW(mod_bis.parameters(), lr=1.5e-4, weight_decay=1e-4)
sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=8)

best_loss = float("inf")
for ep in range(1, 9):
    t_ep = time.time()
    mod_bis.train()
    tr_l = 0.0
    for bx, by in loader_tr:
        opt.zero_grad()
        p = mod_bis(bx)
        loss = crit(p, by)
        loss.backward()
        opt.step()
        tr_l += loss.item() * len(bx)
    sched.step()
    tr_l /= n_tr

    mod_bis.eval()
    va_l = 0.0
    with torch.no_grad():
        for bx, by in loader_va:
            p = mod_bis(bx)
            loss = crit(p, by)
            va_l += loss.item() * len(bx)
    va_l /= n_val

    is_b = ""
    if va_l < best_loss:
        best_loss = va_l
        torch.save(mod_bis.state_dict(), FICHIER_V2_BIS)
        is_b = " ⭐ (Sauvegardé)"

    print(f"Époque {ep}/8 [{time.time()-t_ep:4.1f}s] | Loss Train: {tr_l:.4f} | Loss Val: {va_l:.4f}{is_b}", flush=True)

print(f"✅ V2_bis entraîné et sauvegardé dans {FICHIER_V2_BIS} !")

# =========================================================================
# PHASE 3 : LE DUEL DE QUALIFICATION : V2_BIS vs V2_ACTUEL (400 donnes)
# =========================================================================
print("\n" + "=" * 75)
print(f"PHASE 3 : DUEL DE QUALIFICATION SUR {NB_DONNES_DUEL} DONNES APPARIÉES")
print("IA_V2_bis (auto-appris) vs IA_V2_actuel (maître d'origine)")
print("-" * 75)

MOTS_DUEL = {
    "V2_actuel (Maître)": lambda: JoueurIA_V2(fichier=FICHIER_V2_ACTUEL),
    "V2_bis (Élève)":    lambda: JoueurIA_V2(fichier=FICHIER_V2_BIS),
}

res_pts = {m: [] for m in MOTS_DUEL}
res_ok = {m: [] for m in MOTS_DUEL}
res_marq = {m: [] for m in MOTS_DUEL}

d_faites = 0
t_duel = time.time()

for g in range(90_000_000, 90_000_000 + NB_DONNES_DUEL * 2):
    if d_faites >= NB_DONNES_DUEL:
        break

    random.seed(g); np.random.seed(g % 2**32); torch.manual_seed(g)
    mains = distribuer()
    donneur = g % 4
    joueurs_ench = [JoueurIA_V2(fichier=FICHIER_V2_ACTUEL) for _ in range(4)]
    contrat = phase_annonces(mains, donneur, joueurs_ench, REGLES_STANDARD, afficher=False)
    if contrat is None:
        continue

    d_faites += 1
    premier_parle = (donneur + 1) % 4
    encheres = list(joueurs_ench[premier_parle].encheres)
    camp = 0
    role = "attaque" if contrat["joueur"] % 2 == camp else "defense"
    val = contrat["valeur"]
    mult = 2 if contrat.get("coinche", 0) > 0 else 1
    atout = contrat["atout"]

    for nom, fab in MOTS_DUEL.items():
        random.seed(g * 10 + 7); np.random.seed((g * 10 + 7) % 2**32); torch.manual_seed(g * 10 + 7)
        mains_c = [list(m) for m in mains]
        bot = fab()
        adv = MCEncheres()
        hist, p_eq, pl_eq = [], [0, 0], [0, 0]
        prem = (donneur + 1) % 4

        while len(hist) < 32:
            pli = []
            for k in range(4):
                j = (prem + k) % 4
                jbs = cartes_jouables(mains_c[j], pli, atout, j, REGLES_STANDARD)
                if j % 2 == camp:
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
            g = gagnant_pli(pli, atout)[0]
            prem = g
            p = sum(points(c, atout) for _, c in pli)
            if len(hist) == 32: p += REGLES_STANDARD["dix_de_der"]
            p_eq[g % 2] += p
            pl_eq[g % 2] += 1

        bel = equipe_belote(mains, atout)
        _, reussi = decompte(contrat, p_eq, pl_eq, bel, REGLES_STANDARD)
        gagne = reussi if role == "attaque" else not reussi
        marq = (val * mult) if gagne else (-val * mult)

        res_pts[nom].append(p_eq[camp])
        res_ok[nom].append(gagne)
        res_marq[nom].append(marq)

print("\n" + "=" * 75)
print(f"VERDICT DUEL : L'ÉLÈVE A-T-IL DÉPASSÉ LE MAÎTRE ? ({d_faites} donnes en {time.time()-t_duel:.1f}s)")
print("=" * 75)
print(f"{'Moteur':<20} | {'Pts faits':>9} | {'Succès':>7} | {'Marque moy.':>11} | {'Écart vs Maître':>16}")
print("-" * 75)

ref_m = np.array(res_marq["V2_actuel (Maître)"], dtype=float)
for nom in MOTS_DUEL:
    pts_m = np.mean(res_pts[nom])
    taux = 100 * np.mean(res_ok[nom])
    marq = np.array(res_marq[nom], dtype=float)
    marq_m = marq.mean()

    ecart = marq - ref_m
    marge = 1.96 * ecart.std(ddof=1) / np.sqrt(len(ecart)) if nom != "V2_actuel (Maître)" else 0.0
    txt_ecart = f"{ecart.mean():+6.1f} ± {marge:4.1f}" if nom != "V2_actuel (Maître)" else "référence"

    print(f"{nom:<20} | {pts_m:9.1f} | {taux:6.1f}% | {marq_m:+11.1f} | {txt_ecart:>16}")
