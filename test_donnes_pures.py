import random
import numpy as np
from regles import REGLES_STANDARD
from moteur import distribuer, COULEURS, RANGS
from montecarlo import manques
from systeme_v2 import niveau_v2
from partie import phase_annonces
from ia_joueur import JoueurIA

NB_DONNES = 400

def distance_mains(main_predite, main_reelle):
    return len(set(main_predite) & set(main_reelle))

def coherent_strict(m, p, encheres):
    """Filtre strict : la main doit être à la hauteur de l'annonce."""
    for j, d in encheres:
        if isinstance(d, tuple):
            val, coul = d
            if j == p:
                if niveau_v2(m, coul) < max(80, val - 10):
                    return False
        elif d == "passe" and j == p:
            idx = encheres.index((j, d))
            if idx < 4 and max(niveau_v2(m, c) for c in COULEURS) >= 80:
                return False
    return True

def imaginer_donnes_pures(main, joueur, manque, atout, encheres, max_essais=250, cible=20):
    """
    Ne conserve QUE des donnes 100 % conformes aux annonces.
    Aucune donne polluée n'est jamais renvoyée.
    """
    autres = [p for p in range(4) if p != joueur]
    toutes_vues = set(main)
    inconnues = [(r, c) for c in COULEURS for r in RANGS if (r, c) not in toutes_vues]
    
    valides = []
    for _ in range(max_essais):
        random.shuffle(inconnues)
        m = [None] * 4
        m[joueur] = list(main)
        m[autres[0]] = inconnues[:8]
        m[autres[1]] = inconnues[8:16]
        m[autres[2]] = inconnues[16:24]
        
        coupes_ok = all(all(c[1] not in manque[p] for c in m[p]) for p in autres)
        if coupes_ok and all(coherent_strict(m[p], p, encheres) for p in autres):
            valides.append(m)
            if len(valides) >= cible:
                break
                
    return valides

def mesurer_donnes_pures():
    regles = REGLES_STANDARD
    print(f"Évaluation sur {NB_DONNES} donnes avec ÉCHANTILLONNAGE PUR (zéro pollution)...")
    
    erreurs_atouts = []
    cartes_correctes = []
    chicanes_totales = 0
    chicanes_detectees = 0
    
    erreurs_atouts_gros = []
    cartes_correctes_gros = []
    nb_echantillons_recoltes = []

    donnes_traitees = 0
    for num in range(NB_DONNES * 2):
        random.seed(555000 + num)
        mains_reelles = distribuer()
        donneur = num % 4
        
        j_test = [JoueurIA() for _ in range(4)]
        contrat = phase_annonces(mains_reelles, donneur, j_test, regles, afficher=False)
        if contrat is None: 
            continue
            
        donnes_traitees += 1
        atout = contrat["atout"]
        gros = (contrat["valeur"] >= 110)
        preneur = contrat["joueur"]
        encheres = list(j_test[0].encheres)
        manque = {p: set() for p in range(4)}
        
        # Récolter uniquement les donnes 100% conformes
        echantillons = imaginer_donnes_pures(mains_reelles[0], 0, manque, atout, encheres)
        if not echantillons:
            # Même en 250 essais, aucune donne trouvée (cas extrême de bluff)
            continue
            
        nb_echantillons_recoltes.append(len(echantillons))
            
        for p in (1, 2, 3):
            vraie_main = mains_reelles[p]
            vrais_atouts = sum(1 for c in vraie_main if c[1] == atout)
            
            # Détection chicanes réelles
            for c in COULEURS:
                if c != atout and not any(x[1] == c for x in vraie_main):
                    chicanes_totales += 1
                    pred = sum(1 for m in echantillons if not any(x[1] == c for x in m[p]))
                    chicanes_detectees += (pred / len(echantillons))
            
            for m in echantillons:
                main_pred = m[p]
                at_pred = sum(1 for c in main_pred if c[1] == atout)
                err_at = abs(at_pred - vrais_atouts)
                communes = distance_mains(main_pred, vraie_main)
                
                erreurs_atouts.append(err_at)
                cartes_correctes.append(communes)
                
                if gros and p == preneur:
                    erreurs_atouts_gros.append(err_at)
                    cartes_correctes_gros.append(communes)

        if donnes_traitees >= NB_DONNES:
            break

    taux_chicane = 100 * chicanes_detectees / max(1, chicanes_totales)

    print("\n" + "=" * 65)
    print(f"RÉSULTATS DE L'ÉCHANTILLONNAGE PUR (100% CONFORME) :")
    print("=" * 65)
    print(f"Nombre moyen de donnes pures par décision : {np.mean(nb_echantillons_recoltes):.1f} / 20")
    print(f"Cartes bien placées / 8 (Global)         : {np.mean(cartes_correctes):.2f} (Ancien: 2.95)")
    print(f"Cartes bien placées / 8 (Preneur >= 110) : {np.mean(cartes_correctes_gros):.2f} (Ancien: 3.20)")
    print(f"Erreur atouts (Global)                  : ± {np.mean(erreurs_atouts):.2f} (Ancien: ± 0.88)")
    print(f"Erreur atouts (Preneur >= 110)          : ± {np.mean(erreurs_atouts_gros):.2f} (Ancien: ± 0.83)")
    print(f"CHICANES RÉELLES DÉTECTÉES (%)           : {taux_chicane:.1f} % (Ancien: 15.2 %)")
    print("=" * 65)

if __name__ == "__main__":
    mesurer_donnes_pures()
