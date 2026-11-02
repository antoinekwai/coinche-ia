import random
import numpy as np
from regles import REGLES_STANDARD
from moteur import distribuer, COULEURS
from partie import phase_annonces
from montecarlo import manques
from test_mc_encheres import MCEncheres

NB_DONNES = 500

def distance_mains(main_predite, main_reelle):
    set_pred = set(main_predite)
    set_reel = set(main_reelle)
    cartes_communes = len(set_pred & set_reel)
    return cartes_communes

def tester_fidelite():
    bot = MCEncheres()
    regles = REGLES_STANDARD
    
    erreurs_atouts = []
    cartes_correctes = []
    chicanes_reelles_totales = 0
    chicanes_reelles_detectees = 0
    
    # Pour les gros contrats (>= 110)
    erreurs_atouts_gros = []
    cartes_correctes_gros = []
    
    print(f"Mesure de fidélité de l'ancien générateur sur {NB_DONNES} donnes réelles...\n")
    
    donnes_traitees = 0
    for num in range(NB_DONNES):
        random.seed(123000 + num)
        mains_reelles = distribuer()
        donneur = num % 4
        
        # Enchères réelles jouées par des bots compétents
        from ia_joueur import JoueurIA
        j_test = [JoueurIA() for _ in range(4)]
        contrat = phase_annonces(mains_reelles, donneur, j_test, regles, afficher=False)
        if contrat is None:
            continue
            
        donnes_traitees += 1
        atout = contrat["atout"]
        val_contrat = contrat["valeur"]
        gros_contrat = (val_contrat >= 110)
        
        # On se place au Pli 1 : Sud (0) cherche à imaginer les mains de 1, 2, 3
        manque = {p: set() for p in range(4)}
        bot.historique = []
        bot.encheres = list(j_test[0].encheres)
        
        # Générer 30 échantillons
        echantillons = []
        for _ in range(30):
            m_sim = bot.imaginer(mains_reelles[0], 0, manque, atout)
            echantillons.append(m_sim)
            
        # Comparer pour chaque joueur adverse et partenaire (1, 2, 3)
        for p in (1, 2, 3):
            vraie_main = mains_reelles[p]
            vrais_atouts = sum(1 for c in vraie_main if c[1] == atout)
            
            # Vérifier les chicanes réelles hors-atout
            for c in COULEURS:
                if c != atout and not any(x[1] == c for x in vraie_main):
                    chicanes_reelles_totales += 1
                    # Est-ce que les échantillons ont vu cette chicane ?
                    pred_chicanes = sum(1 for m in echantillons if not any(x[1] == c for x in m[p]))
                    chicanes_reelles_detectees += (pred_chicanes / len(echantillons))
            
            for m in echantillons:
                main_pred = m[p]
                atouts_pred = sum(1 for c in main_pred if c[1] == atout)
                err_at = abs(atouts_pred - vrais_atouts)
                communes = distance_mains(main_pred, vraie_main)
                
                erreurs_atouts.append(err_at)
                cartes_correctes.append(communes)
                
                if gros_contrat and p == contrat["joueur"]:
                    erreurs_atouts_gros.append(err_at)
                    cartes_correctes_gros.append(communes)

    print("=" * 65)
    print(f"RÉSULTATS DE FIDÉLITÉ DE L'ANCIEN GÉNÉRATEUR ({donnes_traitees} donnes) :")
    print("=" * 65)
    print(f"1. Précision sur les cartes exactes (sur 8 cartes) :")
    print(f"   • En moyenne générale : {np.mean(cartes_correctes):.2f} / 8 cartes bien placées")
    print(f"   • Sur le preneur d'un contrat >= 110 : {np.mean(cartes_correctes_gros):.2f} / 8 cartes bien placées")
    
    print(f"\n2. Erreur sur le nombre d'atouts en main :")
    print(f"   • Écart moyen global : ± {np.mean(erreurs_atouts):.2f} atout(s)")
    print(f"   • Écart moyen sur le preneur (contrat >= 110) : ± {np.mean(erreurs_atouts_gros):.2f} atout(s)")
    
    taux_detect_chicane = 100 * chicanes_reelles_detectees / max(1, chicanes_reelles_totales)
    print(f"\n3. Détection des chicanes réelles :")
    print(f"   • Chicanes réelles détectées par le simulateur : {taux_detect_chicane:.1f} %")
    print("=" * 65)

if __name__ == "__main__":
    tester_fidelite()
