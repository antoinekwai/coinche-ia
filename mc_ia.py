from moteur import cartes_jouables, gagnant_pli, points
from montecarlo import (JoueurMonteCarloContrat, manques, bilan_passe,
                        belote_imaginee, contrat_reussi)
from systeme_corrige import SysCorrige
from ia_joueur import JoueurIA

BONUS = 0.2


def simuler_ia(mains, pli, contrat, joueur, carte, plis_faits, historique, encheres, regles):
    """Joue la fin de la donne avec l'IA aux 4 places, après avoir posé `carte`."""
    atout = contrat["atout"]
    robot = JoueurIA()
    robot.encheres = encheres
    hist = list(historique) + [(joueur, carte)]
    robot.historique = hist
    mains = [m[:] for m in mains]
    mains[joueur].remove(carte)
    pli = pli + [(joueur, carte)]
    prochain = (joueur + 1) % 4
    pts_eq, plis_eq = [0, 0], [0, 0]

    while plis_faits < 8:
        while len(pli) < 4:
            j = prochain
            jouables = cartes_jouables(mains[j], pli, atout, j, regles)
            c = robot.jouer_carte(mains[j], jouables, pli, contrat, j, regles)
            mains[j].remove(c)
            pli.append((j, c))
            hist.append((j, c))
            prochain = (j + 1) % 4
        gagnant = gagnant_pli(pli, atout)[0]
        plis_faits += 1
        pts = sum(points(c, atout) for _, c in pli)
        if plis_faits == 8:
            pts += regles["dix_de_der"]
        pts_eq[gagnant % 2] += pts
        plis_eq[gagnant % 2] += 1
        pli = []
        prochain = gagnant
    return pts_eq, plis_eq


class JoueurMCIA(JoueurMonteCarloContrat, SysCorrige):
    """Monte Carlo dont les donnes imaginées sont jouées par l'IA."""
    nom = "MC-IA"

    def __init__(self, nb_simulations=10):
        super().__init__(nb_simulations)

    def evaluer_cartes(self, main, jouables, pli, contrat, joueur, regles):
        atout = contrat["atout"]
        eq, attaque = joueur % 2, contrat["joueur"] % 2
        manque = manques(self.historique, atout, regles)
        plis_faits = (len(self.historique) - len(pli)) // 4
        passe_pts, passe_plis = bilan_passe(self.historique, atout)
        valeurs = {c: 0.0 for c in jouables}
        for _ in range(self.nb_simulations):
            mains = self.imaginer(main, joueur, manque, atout)
            belote = belote_imaginee(mains, self.historique, atout)
            for c in jouables:
                pts, plis = simuler_ia(mains, pli, contrat, joueur, c, plis_faits,
                                       self.historique, self.encheres, regles)
                total = [passe_pts[e] + pts[e] for e in (0, 1)]
                reussi = contrat_reussi(contrat, total[attaque],
                                        passe_plis[attaque] + plis[attaque],
                                        belote == attaque, regles)
                gagne = reussi if eq == attaque else not reussi
                valeurs[c] += (1.0 if gagne else -1.0) + BONUS * (total[eq] - total[1 - eq]) / 162
        return {c: v / self.nb_simulations for c, v in valeurs.items()}

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        if len(jouables) == 1:
            return jouables[0]
        v = self.evaluer_cartes(main, jouables, pli, contrat, joueur, regles)
        return max(jouables, key=v.get)
