"""
inspecter_40_mains.py
Radiographie comparative des 40 mains imaginées par v3 et v5 :
Donne réelle :
  Nord (2) ouvre 80 ♥
  Est  (3) intervient 110 ♠ (preneur)
  Sud  (0) passe
  Ouest (1) passe d'entrée
Inspecte les distributions d'atouts, d'honneurs et d'As au Pli 1 et au Pli 3.
"""
from collections import Counter
import random
import numpy as np
from regles import REGLES_STANDARD
from moteur import COULEURS
from detective_v3 import imaginer_v3, rejouer_encheres, nb_differences
from detective_v5 import imaginer_v5

# Main réelle de Sud
main_sud = [('A', '♠'), ('9', '♠'), ('10', '♣'), ('R', '♣'), ('D', '♦'), ('V', '♦'), ('8', '♥'), ('7', '♥')]
ench = [(2, (80, '♥')), (3, (110, '♠')), (0, 'passe'), (1, 'passe'), (2, 'passe')]
atout = '♠'
donneur = 1  # Ouest donne, Nord parle en 1er

# Historique après 2 plis pour le test Pli 3
# Pli 1 : Nord entame V♥, Est met R♥, Sud met 7♥, Ouest met 8♥ (4 Cœurs tombés)
# Pli 2 : Nord joue A♦, Est met 7♦, Sud met D♦, Ouest met 8♦ (4 Carreaux tombés)
hist_p3 = [
    (2, ('V', '♥')), (3, ('R', '♥')), (0, ('7', '♥')), (1, ('8', '♥')),
    (2, ('A', '♦')), (3, ('7', '♦')), (0, ('D', '♦')), (1, ('8', '♦')),
]
main_sud_p3 = [('A', '♠'), ('9', '♠'), ('10', '♣'), ('R', '♣'), ('V', '♦'), ('8', '♥')]

def autopsier_40_mains(nom_det, fn_det, main, hist, nom_pli):
    print(f"\n{'='*75}")
    print(f"ANALYSE DES 40 MAINS — {nom_det} — {nom_pli}")
    print(f"{'='*75}")
    
    # Données collectées sur les 40 simulations
    est_atouts = []
    est_a_valet = 0
    est_a_neuf = 0
    est_as_ext = []
    nord_coeurs = []
    nord_as_ext = []
    ouest_as = []
    d_list = []
    
    for i in range(40):
        random.seed(100_000 + i * 7)
        m = fn_det(main, 0, hist, ench, atout, REGLES_STANDARD)
        
        # 1. Analyse Est (Joueur 3, preneur de 110 ♠)
        p_est = [c for c in m[3] if c[1] == atout]
        est_atouts.append(len(p_est))
        est_a_valet += int(('V', atout) in m[3] or any(j == 3 and c == ('V', atout) for j, c in hist))
        est_a_neuf += int(('9', atout) in m[3] or any(j == 3 and c == ('9', atout) for j, c in hist))
        as_e = sum(1 for c in m[3] if c[0] == 'A' and c[1] != atout)
        as_e += sum(1 for j, c in hist if j == 3 and c[0] == 'A' and c[1] != atout)
        est_as_ext.append(as_e)
        
        # 2. Analyse Nord (Joueur 2, a ouvert à 80 ♥)
        c_nord = [c for c in m[2] if c[1] == '♥']
        c_nord_tot = len(c_nord) + sum(1 for j, c in hist if j == 2 and c[1] == '♥')
        nord_coeurs.append(c_nord_tot)
        as_n = sum(1 for c in m[2] if c[0] == 'A' and c[1] != '♥')
        as_n += sum(1 for j, c in hist if j == 2 and c[0] == 'A' and c[1] != '♥')
        nord_as_ext.append(as_n)
        
        # 3. Analyse Ouest (Joueur 1, a passé d'entrée)
        as_o = sum(1 for c in m[1] if c[0] == 'A')
        as_o += sum(1 for j, c in hist if j == 1 and c[0] == 'A')
        ouest_as.append(as_o)
        
        # 4. Vérification rejeu des enchères
        depart = [list(mm) for mm in m]
        for jj, cc in hist:
            depart[jj].append(cc)
        d = nb_differences(ench, rejouer_encheres(depart, donneur, REGLES_STANDARD))
        d_list.append(d)

    # Affichage des résultats
    print("1. EST (Preneur de 110 ♠) :")
    dist_at = Counter(est_atouts)
    dist_str = ", ".join(f"{k} atouts: {v}/40" for k, v in sorted(dist_at.items()))
    print(f"   • Atouts en main : moyenne = {np.mean(est_atouts):.2f} [{dist_str}]")
    print(f"   • Valet de Pique : {est_a_valet}/40 ({100*est_a_valet/40:.0f} %)")
    print(f"   • Neuf de Pique  : {est_a_neuf}/40 ({100*est_a_neuf/40:.0f} %)")
    print(f"   • As extérieurs  : moyenne = {np.mean(est_as_ext):.2f} (max = {max(est_as_ext)})")

    print("\n2. NORD (Partenaire, a ouvert 80 ♥) :")
    print(f"   • Cœurs au départ : moyenne = {np.mean(nord_coeurs):.2f}")
    print(f"   • As extérieurs   : moyenne = {np.mean(nord_as_ext):.2f}")

    print("\n3. OUEST (Adversaire, a passé d'entrée) :")
    dist_as_o = Counter(ouest_as)
    as_o_str = ", ".join(f"{k} As: {v}/40" for k, v in sorted(dist_as_o.items()))
    print(f"   • As au total     : moyenne = {np.mean(ouest_as):.2f} [{as_o_str}]")

    print("\n4. FIDÉLITÉ AUX ENCHÈRES :")
    parfaits = sum(1 for d in d_list if d == 0)
    print(f"   • Accord parfait (d=0) : {parfaits}/40 ({100*parfaits/40:.0f} %)")
    print(f"   • d moyen              : {np.mean(d_list):.2f} différences")

# Exécution pour Pli 1 et Pli 3
for nom_p, m_sud, h in [("AU PLI 1 (Entame)", main_sud, []), ("AU PLI 3 (Après 2 plis)", main_sud_p3, hist_p3)]:
    autopsier_40_mains("Détective v3 (Aléatoire + Rejeu)", imaginer_v3, m_sud, h, nom_p)
    autopsier_40_mains("Détective v5 (Guidé + As pondérés)", imaginer_v5, m_sud, h, nom_p)
