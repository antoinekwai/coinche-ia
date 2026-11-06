"""
nuit_entrainement_v2.py
PIPELINE COMPLET DE NUIT POUR LE NOUVEAU RÉSEAU V2 :
Phase 1 : Génération de 4 000 donnes d'élite par BotMCIAv5 en self-play
Phase 2 : Fine-tuning de ia_carte_v2_amorce.pt -> ia_carte_v2_champion.pt
Phase 3 : Benchmark de qualification automatique (500 donnes) v5(V1) vs v5(V2)
"""
import os
import sys
import time
import random
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from regles import REGLES_STANDARD
from moteur import distribuer, cartes_jouables, gagnant_pli, points, equipe_belote, decompte, COULEURS
from partie import phase_annonces
from test_mc_encheres import MCEncheres
from ia_joueur import JoueurIA
from bot_mc_ia_v5 import BotMCIAv5
from ia_modele_v2 import creer_reseau_v2, JoueurIA_V2
from ia_encodage_v2 import encoder_situation_v2, encoder_carte_v2
import bot_mc_ia
from detective_v3 import imaginer_v3

NB_DONNES_GEN = 4000
FICHIER_NPZ = "donnees_v5_distillation.npz"
MODELE_BASE = "ia_carte_v2_amorce.pt"
MODELE_SORTIE = "ia_carte_v2_champion.pt"
NB_DONNES_BENCHMARK = 500
GRAINE_BASE_GEN = 30_000_000
GRAINE_BASE_BENCH = 40_000_000

# =========================================================================
# PHASE 1 : GÉNÉRATION DU DATASET DE DISTILLATION V5
# =========================================================================
print("=" * 75)
print(f"PHASE 1 : GÉNÉRATION DE {NB_DONNES_GEN:,} DONNES PAR LE CHAMPION V5")
print("=" * 75)

X_list, Y_list = [], []
t_debut_gen = time.time()
donnes_faites = 0
total_exemples = 0

for g in range(GRAINE_BASE_GEN, GRAINE_BASE_GEN + NB_DONNES_GEN * 3):
    if donnes_faites >= NB_DONNES_GEN:
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

    bots = [BotMCIAv5() for _ in range(4)]
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

    if donnes_faites % 250 == 0:
        ecoule = time.time() - t_debut_gen
        vitesse = donnes_faites / max(1e-5, ecoule)
        reste = (NB_DONNES_GEN - donnes_faites) / vitesse
        print(f"  {donnes_faites:5d}/{NB_DONNES_GEN} donnes | {total_exemples:7d} exemples | {ecoule/60:4.1f} min écoulées | reste ≈ {reste/60:4.1f} min", flush=True)

print("\nCompression des données d'élite en format .npz...")
X_arr = np.array(X_list, dtype=np.float32)
Y_arr = np.array(Y_list, dtype=np.float32)
np.savez_compressed(FICHIER_NPZ, X=X_arr, Y=Y_arr)
print(f"✅ Dataset sauvegardé : {FICHIER_NPZ} ({len(X_arr):,} exemples, {os.path.getsize(FICHIER_NPZ)/(1024*1024):.1f} Mo)")

# =========================================================================
# PHASE 2 : FINE-TUNING DU MODÈLE V2
# =========================================================================
print("\n" + "=" * 75)
print(f"PHASE 2 : FINE-TUNING DE {MODELE_BASE} -> {MODELE_SORTIE}")
print("=" * 75)

n_total = len(X_arr)
n_val = int(0.10 * n_total)
n_train = n_total - n_val
indices = np.random.RandomState(42).permutation(n_total)
idx_train, idx_val = indices[:n_train], indices[n_train:]

X_train, Y_train = torch.from_numpy(X_arr[idx_train]), torch.from_numpy(Y_arr[idx_train]).unsqueeze(1)
X_val, Y_val = torch.from_numpy(X_arr[idx_val]), torch.from_numpy(Y_arr[idx_val]).unsqueeze(1)

train_loader = DataLoader(TensorDataset(X_train, Y_train), batch_size=512, shuffle=True)
val_loader = DataLoader(TensorDataset(X_val, Y_val), batch_size=512, shuffle=False)

modele = creer_reseau_v2()
if os.path.exists(MODELE_BASE):
    modele.load_state_dict(torch.load(MODELE_BASE, map_location="cpu"))
    print(f"Poids de base chargés depuis {MODELE_BASE} (démarrage à chaud) !")
else:
    print("Démarrage de zéro.")

criterion = nn.MSELoss()
optimizer = torch.optim.AdamW(modele.parameters(), lr=2e-4, weight_decay=1e-4)
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=10)

meilleure_val = float("inf")
for ep in range(1, 11):
    t_ep = time.time()
    modele.train()
    tr_loss = 0.0
    for bx, by in train_loader:
        optimizer.zero_grad()
        pred = modele(bx)
        loss = criterion(pred, by)
        loss.backward()
        optimizer.step()
        tr_loss += loss.item() * len(bx)
    scheduler.step()
    tr_loss /= n_train

    modele.eval()
    va_loss = 0.0
    with torch.no_grad():
        for bx, by in val_loader:
            pred = modele(bx)
            loss = criterion(pred, by)
            va_loss += loss.item() * len(bx)
    va_loss /= n_val

    is_b = ""
    if va_loss < meilleure_val:
        meilleure_val = va_loss
        torch.save(modele.state_dict(), MODELE_SORTIE)
        is_b = " ⭐ (Sauvegardé)"

    print(f"Époque {ep:2d}/10 [{time.time()-t_ep:4.1f}s] | Loss Train: {tr_loss:.4f} | Loss Val: {va_loss:.4f}{is_b}", flush=True)

print(f"✅ Modèle d'élite sauvegardé dans {MODELE_SORTIE} (Loss: {meilleure_val:.4f})")

# =========================================================================
# PHASE 3 : BENCHMARK DE QUALIFICATION AUTOMATIQUE (500 DONNES)
# =========================================================================
print("\n" + "=" * 75)
print(f"PHASE 3 : BENCHMARK DE QUALIFICATION : V5(V1 ancien) vs V5(V2 nouveau)")
print(f"Objectif : {NB_DONNES_BENCHMARK} donnes neuves appariées")
print("=" * 75)


# Classe Bot v5 utilisant le réseau V2
class BotMCIAv5_V2(bot_mc_ia.BotMCIA):
    nom = "v5 (Réseau V2)"
    def __init__(self):
        super().__init__()
        self.nb_simulations = 40
        self.ia_v2 = JoueurIA_V2(fichier=MODELE_SORTIE)

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        if len(jouables) == 1:
            return jouables[0]
        # Plis 1 à 3 en IA V2
        if len(self.historique) < 12:
            self.ia_v2.historique = list(self.historique)
            self.ia_v2.encheres = list(self.encheres) if self.encheres else []
            return self.ia_v2.jouer_carte(main, jouables, pli, contrat, joueur, regles)

        # Plis 4 à 8 : Monte-Carlo 40 sim avec détective v3
        ancien = bot_mc_ia.imaginer_donnes_contraintes
        bot_mc_ia.imaginer_donnes_contraintes = imaginer_v3
        try:
            return super().jouer_carte(main, jouables, pli, contrat, joueur, regles)
        finally:
            bot_mc_ia.imaginer_donnes_contraintes = ancien


MOTS_BENCH = {
    "v5_V1_ancien": BotMCIAv5,
    "v5_V2_nouveau": BotMCIAv5_V2,
}

res_b_pts = {m: [] for m in MOTS_BENCH}
res_b_sec = {m: [] for m in MOTS_BENCH}
res_b_ok = {m: [] for m in MOTS_BENCH}
res_b_marq = {m: [] for m in MOTS_BENCH}

b_donnes = 0
t_debut_bench = time.time()

for g in range(GRAINE_BASE_BENCH, GRAINE_BASE_BENCH + NB_DONNES_BENCHMARK * 2):
    if b_donnes >= NB_DONNES_BENCHMARK:
        break

    random.seed(g); np.random.seed(g % 2**32); torch.manual_seed(g)
    mains = distribuer()
    donneur = g % 4
    joueurs_ench = [JoueurIA() for _ in range(4)]
    contrat = phase_annonces(mains, donneur, joueurs_ench, REGLES_STANDARD, afficher=False)
    if contrat is None:
        continue

    b_donnes += 1
    premier_parle = (donneur + 1) % 4
    encheres = list(joueurs_ench[premier_parle].encheres)
    camp = 0
    role = "attaque" if contrat["joueur"] % 2 == camp else "defense"
    val = contrat["valeur"]
    mult = 2 if contrat.get("coinche", 0) > 0 else 1
    atout = contrat["atout"]

    for nom, cls_m in MOTS_BENCH.items():
        random.seed(g * 10 + 7); np.random.seed((g * 10 + 7) % 2**32); torch.manual_seed(g * 10 + 7)
        mains_c = [list(m) for m in mains]
        b = cls_m()
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
                    b.historique = list(hist)
                    b.encheres = list(encheres)
                    c = b.jouer_carte(mains_c[j], jbs, pli, contrat, j, REGLES_STANDARD)
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
        bel = equipe_belote(mains, atout)
        _, reussi = decompte(contrat, p_eq, pl_eq, bel, REGLES_STANDARD)
        gagne = reussi if role == "attaque" else not reussi
        marque_camp = (val * mult) if gagne else (-val * mult)

        res_b_pts[nom].append(p_eq[camp])
        res_b_sec[nom].append(dt)
        res_b_ok[nom].append(gagne)
        res_b_marq[nom].append(marque_camp)

    if b_donnes % 50 == 0:
        ec = time.time() - t_debut_bench
        m_anc = np.mean(res_b_marq["v5_V1_ancien"])
        m_nouv = np.mean(res_b_marq["v5_V2_nouveau"])
        diff = m_nouv - m_anc
        print(f"  {b_donnes:4d}/{NB_DONNES_BENCHMARK} donnes | {ec/60:4.1f} min | Marque: Ancien={m_anc:+.1f} vs Nouveau={m_nouv:+.1f} (écart: {diff:+.1f})", flush=True)

print("\n" + "=" * 75)
print(f"VERDICT FINAL DE QUALIFICATION SUR {b_donnes} DONNES :")
print("=" * 75)
print(f"{'Moteur':<18} | {'Pts faits':>9} | {'Succès':>7} | {'Temps/partie':>12} | {'Marque moy.':>11} | {'Écart vs Ancien':>16}")
print("-" * 75)

ref = np.array(res_b_marq["v5_V1_ancien"], dtype=float)
for nom in ["v5_V1_ancien", "v5_V2_nouveau"]:
    pts_m = np.mean(res_b_pts[nom])
    taux = 100 * np.mean(res_b_ok[nom])
    sec_m = np.mean(res_b_sec[nom])
    marq = np.array(res_b_marq[nom], dtype=float)
    marq_m = marq.mean()

    ecart = marq - ref
    marge = 1.96 * ecart.std(ddof=1) / np.sqrt(len(ecart)) if nom != "v5_V1_ancien" else 0.0
    txt_ecart = f"{ecart.mean():+6.1f} ± {marge:4.1f}" if nom != "v5_V1_ancien" else "référence"

    print(f"{nom:<18} | {pts_m:9.1f} | {taux:6.1f}% | {sec_m:10.2f}s | {marq_m:+11.1f} | {txt_ecart:>16}")
