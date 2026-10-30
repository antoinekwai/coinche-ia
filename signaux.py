import random
from moteur import gagnant_pli
from montecarlo import imaginer_mains
from match_mc import SystemeMCContrat


# ============================================================
# 1. ÉMETTRE : choisir la carte à défausser selon la convention
# ============================================================

def choisir_defausse(main, jouables, pli, atout, joueur):
    """Carte à défausser selon la convention, ou None (Monte Carlo décide alors)."""
    if not pli:
        return None
    demandee = pli[0][1][1]
    defausses = [c for c in jouables if c[1] != demandee and c[1] != atout]
    if not defausses:
        return None                      # pas une défausse (on fournit ou on coupe)

    partenaire_maitre = gagnant_pli(pli, atout)[0] == (joueur + 2) % 4
    couleurs = {c[1] for c in defausses}

    if partenaire_maitre:
        for x in couleurs:               # As défaussé = "je suis maître derrière"
            if ("A", x) in main and ("10", x) in main:
                return ("A", x)
        for x in couleurs:               # 10 défaussé = "je n'ai pas l'as"
            if ("10", x) in main and ("A", x) not in main:
                return ("10", x)

    # Petite carte dans la couleur de son as = "j'ai peut-être l'as"
    for c in defausses:
        if c[0] not in ("A", "10") and ("A", c[1]) in main:
            return c
    return None


# ============================================================
# 2. LIRE : retrouver les signaux du partenaire dans l'historique
# ============================================================

def lire_signaux(historique, joueur, atout):
    """Liste de (carte, True = il l'a probablement / False = il ne l'a probablement pas)."""
    partenaire = (joueur + 2) % 4
    signaux = []
    for i, (j, (rang, x)) in enumerate(historique):
        if i % 4 == 0 or j != partenaire:
            continue
        demandee = historique[i - i % 4][1][1]
        if x == demandee or x == atout:
            continue                     # ce n'est pas une défausse
        if rang == "A":
            signaux.append((("10", x), True))
        elif rang == "10":
            signaux.append((("A", x), False))
        else:
            signaux.append((("A", x), True))
    return signaux


def deplacer(mains, carte, src, dst, manque, proteges):
    """Fait passer `carte` de la main src à la main dst, en échange d'une autre carte."""
    if carte[1] in manque[dst]:
        return
    echanges = [y for y in mains[dst] if y[1] not in manque[src] and y not in proteges]
    if not echanges:
        return
    y = random.choice(echanges)
    mains[src].remove(carte)
    mains[dst].remove(y)
    mains[src].append(y)
    mains[dst].append(carte)
    proteges.add(carte)


# ============================================================
# 3. LE JOUEUR : vos annonces + Monte Carlo (contrat) + signaux
# ============================================================

class JoueurSignaux(SystemeMCContrat):
    nom = "Signaux"
    confiance = 0.8     # probabilité qu'une défausse soit un vrai signal
    emettre = True      # applique la convention en défaussant

    def imaginer(self, main, joueur, manque, atout):
        mains = imaginer_mains(main, joueur, self.historique, manque)
        partenaire = (joueur + 2) % 4
        adversaires = [p for p in range(4) if p not in (joueur, partenaire)]
        proteges = set()

        for carte, il_l_a in lire_signaux(self.historique, joueur, atout):
            if random.random() > self.confiance:
                continue                 # cette fois, on considère que ce n'était pas un signal
            if il_l_a and carte not in mains[partenaire]:
                src = next((p for p in adversaires if carte in mains[p]), None)
                if src is not None:
                    deplacer(mains, carte, src, partenaire, manque, proteges)
            elif not il_l_a and carte in mains[partenaire]:
                dst = [p for p in adversaires if carte[1] not in manque[p]]
                if dst:
                    deplacer(mains, carte, partenaire, random.choice(dst), manque, proteges)
        return mains

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        if self.emettre:
            carte = choisir_defausse(main, jouables, pli, contrat["atout"], joueur)
            if carte is not None:
                return carte
        return super().jouer_carte(main, jouables, pli, contrat, joueur, regles)
