import time
import random
from regles import REGLES_STANDARD
from moteur import (distribuer, cartes_jouables, gagnant_pli, points, 
                    COULEURS, RANGS, ORDRE_ATOUT, ORDRE_NON_ATOUT)

class SolveurExact:
    def __init__(self, atout, regles=REGLES_STANDARD):
        self.atout = atout
        self.regles = regles
        self.transposition = {} # Mémoire des positions déjà résolues
        self.noeuds_visites = 0

    def cle_position(self, mains, meneur):
        # Clé compacte immuable pour le cache
        return (tuple(tuple(sorted(m)) for m in mains), meneur)

    def trier_coups(self, jouables, couleur_demandee):
        # Ordonnancement : tester d'abord les cartes fortes pour couper l'arbre plus vite
        def cle_force(c):
            r, coul = c
            if coul == self.atout:
                return 100 + ORDRE_ATOUT[r]
            elif coul == couleur_demandee:
                return 50 + ORDRE_NON_ATOUT[r]
            return ORDRE_NON_ATOUT[r]
        return sorted(jouables, key=cle_force, reverse=True)

    def minimax(self, mains, pli, premier, alpha, beta):
        """
        Résout la donne exacte cartes ouvertes.
        Retourne le score net pour l'équipe 0/2 (Sud/Nord) :
        Points faits par 0/2 - Points faits par 1/3.
        """
        self.noeuds_visites += 1

        # Cas 1 : Le pli en cours est complet (4 cartes)
        if len(pli) == 4:
            gagnant, _ = gagnant_pli(pli, self.atout)
            pts_pli = sum(points(c, self.atout) for _, c in pli)
            
            # Vérifier si c'est le dernier pli (Dix de der)
            cartes_restantes = sum(len(m) for m in mains)
            if cartes_restantes == 0:
                pts_pli += self.regles["dix_de_der"]

            gain_02 = pts_pli if (gagnant % 2 == 0) else -pts_pli

            if cartes_restantes == 0:
                return gain_02

            # Suite de la donne avec le gagnant à l'entame
            score_suite = self.minimax(mains, [], gagnant, alpha - gain_02, beta - gain_02)
            return gain_02 + score_suite

        # Cas 2 : Pli en cours (1, 2 ou 3 cartes déjà posées, ou entame)
        joueur = (premier + len(pli)) % 4
        equipe_joueur = joueur % 2 # 0 pour Sud/Nord, 1 pour Ouest/Est
        est_max = (equipe_joueur == 0)

        couleur_demandee = pli[0][1][1] if pli else None
        jouables = cartes_jouables(mains[joueur], pli, self.atout, joueur, self.regles)

        if not pli:
            # Vérification table de transposition uniquement à l'entame d'un pli
            cle = self.cle_position(mains, premier)
            if cle in self.transposition:
                return self.transposition[cle]

        coups_tries = self.trier_coups(jouables, couleur_demandee)

        if est_max: # Équipe 0/2 veut MAXIMISER le score
            valeur = -999
            for c in coups_tries:
                mains[joueur].remove(c)
                pli.append((joueur, c))
                
                score = self.minimax(mains, pli, premier, alpha, beta)
                
                pli.pop()
                mains[joueur].append(c)

                valeur = max(valeur, score)
                alpha = max(alpha, valeur)
                if beta <= alpha:
                    break # Coupure Bêta : l'adversaire a déjà une meilleure option ailleurs
        else: # Équipe 1/3 (Adversaire) veut MINIMISER le score de 0/2
            valeur = 999
            for c in coups_tries:
                mains[joueur].remove(c)
                pli.append((joueur, c))
                
                score = self.minimax(mains, pli, premier, alpha, beta)
                
                pli.pop()
                mains[joueur].append(c)

                valeur = min(valeur, score)
                beta = min(beta, valeur)
                if beta <= alpha:
                    break # Coupure Alpha

        if not pli:
            self.transposition[cle] = valeur

        return valeur

def tester_vitesse_solveur():
    atout = "♠"
    print("=" * 60)
    print("=== TEST DE VITESSE DU SOLVEUR MINIMAX DOUBLE DUMMY ===")
    print("=" * 60)

    # Tirer une donne au hasard
    mains_completes = distribuer()
    
    # Nous allons tester la résolution exacte en partant de différentes profondeurs :
    # 4 plis restants (16 cartes), 6 plis restants (24 cartes), et 8 plis complets (32 cartes)
    for nb_plis_a_jouer in [4, 5, 6, 8]:
        # Réduire les mains au nombre de cartes souhaité pour le test
        nb_cartes = nb_plis_a_jouer
        mains_test = [m[:nb_cartes] for m in mains_completes]
        
        solveur = SolveurExact(atout)
        premier = 0 # Sud entame
        
        debut = time.time()
        score_parfait = solveur.minimax(mains_test, [], premier, -999, 999)
        duree = time.time() - debut

        print(f"\nRésolution sur les {nb_plis_a_jouer} derniers plis ({nb_plis_a_jouer * 4} cartes au total) :")
        print(f"  • Score parfait net pour Sud/Nord : {score_parfait:+d} pts")
        print(f"  • Nœuds arborescents explorés     : {solveur.noeuds_visites}")
        print(f"  • Temps de calcul exact           : {duree:.4f} seconde(s)")
        if duree > 0:
            print(f"  • Vitesse d'exploration           : {int(solveur.noeuds_visites / duree)} nœuds/seconde")

if __name__ == "__main__":
    tester_vitesse_solveur()
