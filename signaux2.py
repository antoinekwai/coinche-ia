"""
signaux.py
Les garanties de défausse en attaque (conventions « dures ») :
 1. As défaussé  -> j'ai la carte maître suivante de cette couleur.
 2. 10 défaussé alors que l'As n'est pas tombé -> je n'ai pas l'As.
Utilisé des deux côtés : l'émetteur les respecte, le détective les vérifie.
"""
ORDRE_COULEUR = ["A", "10", "R", "D", "V", "9", "8", "7"]


def maitre_suivante(couleur, jouees, sauf):
    """Plus forte carte de la couleur encore en jeu, en excluant 'sauf'."""
    for r in ORDRE_COULEUR:
        c = (r, couleur)
        if c not in jouees and c != sauf:
            return c
    return None


def est_defausse(carte, pli, atout):
    return bool(pli) and carte[1] != pli[0][1][1] and carte[1] != atout


def viole_garantie(carte, main, pli, atout, jouees):
    """True si défausser 'carte' avec cette 'main' contredit une garantie."""
    if not est_defausse(carte, pli, atout):
        return False
    r, coul = carte
    if r == "A":
        suivante = maitre_suivante(coul, jouees, carte)
        return suivante is not None and suivante not in main
    if r == "10" and ("A", coul) not in jouees:
        return ("A", coul) in main
    return False


def filtrer_jouables(jouables, main, pli, atout, historique, en_attaque):
    """ÉMETTEUR : retire les défausses interdites (si possible)."""
    if not en_attaque:
        return jouables
    jouees = {c for _, c in historique} | {c for _, c in pli}
    autorisees = [c for c in jouables if not viole_garantie(c, main, pli, atout, jouees)]
    return autorisees or jouables


def compter_violations(mains_restantes, historique, atout, camp_attaque):
    """DÉTECTIVE : nombre de garanties contredites par la donne imaginée.
    0 = cohérente. Ne rejette jamais : le détective transforme ce nombre en pénalité.
    En cas de souci imprévu, renvoie 0 (on ignore les signaux plutôt que planter)."""
    try:
        mains = [list(m) for m in mains_restantes]
        for j, c in historique:
            mains[j].append(c)              # mains de départ
        jouees, violations = set(), 0
        for debut in range(0, len(historique), 4):
            pli = []
            for j, c in historique[debut:debut + 4]:
                if j % 2 == camp_attaque and viole_garantie(c, mains[j], pli, atout, jouees):
                    violations += 1
                mains[j].remove(c)
                pli.append((j, c))
                jouees.add(c)
        return violations
    except Exception:
        return 0
