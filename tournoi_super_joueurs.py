import sys
import time
from regles import REGLES_STANDARD
from rapide import afficher_rapide
from test_mc_encheres import MCEncheres
from bot_mc_ia import BotMCIA
from bot_candidat3_vrai import BotCandidat3Vrai

if __name__ == "__main__":
    regles = REGLES_STANDARD
    
    print("=" * 70)
    print("🏆 GRAND TOURNOI DES SUPER-JOUEURS (BENCHMARK FINAL)")
    print("=" * 70)
    print("Système d'annonces identique pour tous (Recommandé v2).")
    print("Comparaison pure de la force de jeu de la carte.\n")
    
    # -------------------------------------------------------------
    # MATCH 1 : Confirmation statistique Candidat 2 vs MC-Enchères
    # -------------------------------------------------------------
    nb_m1 = int(sys.argv[1]) if len(sys.argv) > 1 else 3600
    print(f"--- MATCH 1 : Candidat 2 (Bot-MC-IA) vs MC-Enchères ({nb_m1} donnes) ---")
    print("Objectif : Réduire la marge sous ±2.4 pour valider la supériorité.")
    t0 = time.time()
    afficher_rapide(BotMCIA, MCEncheres, nb_m1, regles, graine=555000)
    print(f"Match 1 terminé en {(time.time() - t0) / 60:.1f} minutes.\n")

    # -------------------------------------------------------------
    # MATCH 2 : La Finale directe — Candidat 2 vs Candidat 3
    # -------------------------------------------------------------
    nb_m2 = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    print(f"--- MATCH 2 (FINALE) : Candidat 2 (Bot-MC-IA) vs Candidat 3 (Bot-Candidat3-Vrai) ({nb_m2} donnes) ---")
    print("Duel direct : Déroulement IA fluide vs Arborescence Minimax Symétrique.")
    t1 = time.time()
    afficher_rapide(BotMCIA, BotCandidat3Vrai, nb_m2, regles, graine=888000)
    print(f"Match 2 terminé en {(time.time() - t1) / 60:.1f} minutes.\n")
    
    print("=" * 70)
    print("Tournoi terminé avec succès !")
    print("=" * 70)
