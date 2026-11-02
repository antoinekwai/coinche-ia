import random
import numpy as np
from regles import REGLES_STANDARD
from moteur import distribuer, COULEURS
from partie import phase_annonces
from ia_joueur import JoueurIA
from test_mc_encheres import MCEncheres
from generateur_contraintes import imaginer_donnes_contraintes
from generateur_souple import imaginer_donnes_souples

NB_DONNES = 400

def distance_mains(main_predite, main_reelle):
    return len(set(main_predite) & set(main_reelle))

def evaluer_generateur(nom_gen, fn_imaginer, donnes_test, regles):
    erreurs_atouts = []
    cartes_correctes = []
    chicanes_totales = 0
    chicanes_detectees = 0
    
    erreurs_atouts_gros = []
    cartes_correctes_gros = []

    for item in donnes_test:
        mains_reelles = item["mains"]
        atout = item["atout"]
        gros = item["gros"]
        preneur = item["preneur"]
        encheres = item["encheres"]
        
        echantillons = []
        for _ in range(25):
            m_sim = fn_imaginer(mains_reelles[0], 0, item["manque"], atout, encheres, regles)
            echantillons.append(m_sim)
            
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

    taux_chicane = 100 * chicanes_detectees / max(1, chicanes_totales)
    return {
        "cartes_gen": np.mean(cartes_correctes),
        "cartes_gros": np.mean(cartes_correctes_gros),
        "err_atouts_gen": np.mean(erreurs_atouts),
        "err_atouts_gros": np.mean(erreurs_atouts_gros),
        "taux_chicane": taux_chicane
    }

if __name__ == "__main__":
    regles = REGLES_STANDARD
    print(f"Génération de {NB_DONNES} donnes réelles de test...")
    
    donnes_test = []
    bot_enchere = MCEncheres()
    
    for num in range(NB_DONNES * 2):
        random.seed(555000 + num)
        mains = distribuer()
        donneur = num % 4
        
        j_test = [JoueurIA() for _ in range(4)]
        contrat = phase_annonces(mains, donneur, j_test, regles, afficher=False)
        if contrat is None: continue
            
        atout = contrat["atout"]
        donnes_test.append({
            "mains": mains,
            "atout": atout,
            "gros": (contrat["valeur"] >= 110),
            "preneur": contrat["joueur"],
            "encheres": list(j_test[0].encheres),
            "manque": {p: set() for p in range(4)}
        })
        if len(donnes_test) >= NB_DONNES:
            break

    print(f"{len(donnes_test)} donnes retenues. Évaluation des 3 générateurs...\n")

    # Wrapper pour les adapter à la même signature
    def wrapper_ancien(main, j, manque, atout, encheres, regles):
        bot_enchere.historique = []
        bot_enchere.encheres = encheres
        return bot_enchere.imaginer(main, j, manque, atout)

    def wrapper_contraintes(main, j, manque, atout, encheres, regles):
        return imaginer_donnes_contraintes(main, j, [], encheres, atout, regles)

    def wrapper_souple(main, j, manque, atout, encheres, regles):
        return imaginer_donnes_souples(main, j, [], encheres, atout, regles)

    res_ancien = evaluer_generateur("1. Ancien (Aléatoire+Rejet)", wrapper_ancien, donnes_test, regles)
    print("  ✓ Ancien générateur évalué.")
    res_dures = evaluer_generateur("2. Contraintes Dures", wrapper_contraintes, donnes_test, regles)
    print("  ✓ Générateur contraintes dures évalué.")
    res_souple = evaluer_generateur("3. Générateur Souple", wrapper_souple, donnes_test, regles)
    print("  ✓ Générateur souple évalué.\n")

    print("=" * 80)
    print(f"{'Métrique de Fidélité Réelle':<38} | {'1. Ancien':<11} | {'2. Dures':<11} | {'3. Souple':<11}")
    print("-" * 80)
    print(f"{'Cartes bien placées / 8 (Global)':<38} | {res_ancien['cartes_gen']:<11.2f} | {res_dures['cartes_gen']:<11.2f} | {res_souple['cartes_gen']:<11.2f}")
    print(f"{'Cartes bien placées / 8 (Preneur >= 110)':<38} | {res_ancien['cartes_gros']:<11.2f} | {res_dures['cartes_gros']:<11.2f} | {res_souple['cartes_gros']:<11.2f}")
    print(f"{'Erreur nb atouts (Global)':<38} | ± {res_ancien['err_atouts_gen']:<9.2f} | ± {res_dures['err_atouts_gen']:<9.2f} | ± {res_souple['err_atouts_gen']:<9.2f}")
    print(f"{'Erreur nb atouts (Preneur >= 110)':<38} | ± {res_ancien['err_atouts_gros']:<9.2f} | ± {res_dures['err_atouts_gros']:<9.2f} | ± {res_souple['err_atouts_gros']:<9.2f}")
    print(f"{'CHICANES RÉELLES DÉTECTÉES (%)':<38} | {res_ancien['taux_chicane']:<10.1f}% | {res_dures['taux_chicane']:<10.1f}% | {res_souple['taux_chicane']:<10.1f}%")
    print("=" * 80)
