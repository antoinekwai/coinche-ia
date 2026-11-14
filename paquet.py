# paquet.py — Coupe traditionnelle et ramassage sans mélange
import random

def couper(paquet, nb_souleve):
    """Le coupeur soulève nb_souleve cartes du dessus et les place dessous.
    Règle : au moins 3 cartes de chaque côté."""
    if not 3 <= nb_souleve <= len(paquet) - 3:
        raise ValueError(f"Coupe illégale : {nb_souleve} cartes")
    return paquet[nb_souleve:] + paquet[:nb_souleve]

def coupe_aleatoire(paquet, rng):
    """Coupe faite par un bot (le joueur à droite du donneur)."""
    return couper(paquet, rng.randint(3, len(paquet) - 3))

def distribuer_323(paquet, donneur):
    """Distribution 3-2-3 dans le sens horaire, en commençant
    par le joueur après le donneur. paquet[0] = dessus du paquet."""
    mains = {j: [] for j in range(4)}
    i = 0
    for taille in (3, 2, 3):
        for k in range(1, 5):
            joueur = (donneur + k) % 4
            mains[joueur].extend(paquet[i:i + taille])
            i += taille
    return mains

def ramasser_plis(plis, camp_dessus):
    """plis = liste de (camp_gagnant, [4 cartes dans l'ordre joué]).
    Chaque camp empile ses plis, puis le tas de camp_dessus
    est posé sur l'autre."""
    tas = {0: [], 1: []}
    for camp, cartes in plis:
        tas[camp].extend(cartes)
    return tas[camp_dessus] + tas[1 - camp_dessus]

def ramasser_mains(mains, donneur):
    """Cas 'tout le monde passe' : les mains sont empilées
    sans mélange, en partant du joueur après le donneur."""
    paquet = []
    for k in range(1, 5):
        paquet.extend(mains[(donneur + k) % 4])
    return paquet

if __name__ == "__main__":
    # Test d'intégrité : on doit toujours avoir 32 cartes distinctes
    rng = random.Random(42)
    paquet = list(range(32))
    rng.shuffle(paquet)
    for donne in range(1000):
        paquet = coupe_aleatoire(paquet, rng)
        mains = distribuer_323(paquet, donneur=donne % 4)
        assert sum(len(m) for m in mains.values()) == 32
        paquet = ramasser_mains(mains, donne % 4)
        assert sorted(paquet) == list(range(32))
    print("✅ 1000 coupes/distributions/ramassages : paquet intact")
