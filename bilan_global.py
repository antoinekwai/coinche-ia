from regles import REGLES_STANDARD
from systeme_v2 import SysV2
from experience_coinche import variante
from experience_reponse import reponse_variante
from montecarlo import JoueurMonteCarloContrat
from rapide import afficher_rapide

# 1. Système d'origine (votre façon de jouer initiale)
SysOrigine = variante(4)

# 2. Système recommandé complet (Ouvertures v2 + Réponse prudente 80 + Coinche atouts + Marge 30)
class SysRecommande(SysV2):
    nom = "Système Recommandé"
    reponse = reponse_variante("court")

# Joueurs avec jeu de la carte par simulation classique (juge neutre)
class OrigineMC(JoueurMonteCarloContrat, SysOrigine):
    nom = "Système d'origine (MC)"

class RecommandeMC(JoueurMonteCarloContrat, SysRecommande):
    nom = "Système recommandé (MC)"

if __name__ == "__main__":
    regles = REGLES_STANDARD
    print("=== BILAN GLOBAL : Système Recommandé contre Système d'Origine (10 000 donnes) ===")
    afficher_rapide(RecommandeMC, OrigineMC, 10000, regles, graine=999999)
