import random
from moteur import COULEURS, texte_main

ATOUT = "♠"
COTES = [c for c in COULEURS if c != ATOUT]
PETITS_ATOUTS = ["7", "8", "10", "D", "R"]           # jamais V, 9, A
PETITES_COTE = ["7", "8", "9", "V", "D", "R"]        # jamais As ni 10

# atouts : atouts imposés | petits : petits atouts ajoutés | as : as à côté
# as10 : As + 10 dans une même couleur | dix2 : 10 deuxième (10 + une petite, sans l'as)
# belote : True seulement si la main la contient explicitement
MAINS_TYPES = [
    ("01. V + 2 petits, sans as",          {"atouts": ["V"], "petits": 2}),
    ("02. 9 + 2 petits, sans as",          {"atouts": ["9"], "petits": 2}),
    ("03. V + 2 petits + 1 as",            {"atouts": ["V"], "petits": 2, "as": 1}),
    ("04. 9 + 2 petits + 1 as",            {"atouts": ["9"], "petits": 2, "as": 1}),
    ("05. V 9 + 1 petit + 1 as",           {"atouts": ["V", "9"], "petits": 1, "as": 1}),
    ("06. V 9 + 2 petits, sans as",        {"atouts": ["V", "9"], "petits": 2}),
    ("07. V 9 + 2 petits + 1 as",          {"atouts": ["V", "9"], "petits": 2, "as": 1}),
    ("08. V 9 A + 1 petit + 1 as",         {"atouts": ["V", "9", "A"], "petits": 1, "as": 1}),
    ("09. V + 3 petits, sans as",          {"atouts": ["V"], "petits": 3}),
    ("10. V + 2 petits + 2 as",            {"atouts": ["V"], "petits": 2, "as": 2}),
    ("11. V + 2 petits + As-10",           {"atouts": ["V"], "petits": 2, "as10": True}),
    ("12. 9 + 3 petits + 10 deuxième",     {"atouts": ["9"], "petits": 3, "dix2": True}),
    ("13. V 9 A 10 + 1 as",                {"atouts": ["V", "9", "A", "10"], "as": 1}),
    ("14. V 9 + 3 petits + 1 as",          {"atouts": ["V", "9"], "petits": 3, "as": 1}),
    ("15. A R D 8 7 (belote)",             {"atouts": ["A", "R", "D", "8", "7"], "belote": True}),
    ("16. V A R D (belote), sans as",      {"atouts": ["V", "A", "R", "D"], "belote": True}),
    ("17. 3 petits + 2 as (contrôle)",     {"petits": 3, "as": 2}),
    ("18. V 9 + 3 petits + 3 petites",      {"atouts": ["V", "9"], "petits": 3}),
    ("19. V 9 + 3 petits + A 10 x",         {"atouts": ["V", "9"], "petits": 3, "as10x": True}),
    ("20. V 9 + 3 petits + 2 as",           {"atouts": ["V", "9"], "petits": 3, "as": 2}),
    ("21. V 9 A + 2 petits + 2 as",         {"atouts": ["V", "9", "A"], "petits": 2, "as": 2}),
    ("22. V 9 A 10 + 1 petit + 2 as",       {"atouts": ["V", "9", "A", "10"], "petits": 1, "as": 2}),
    ("23. V 9 + 4 petits + 1 as",           {"atouts": ["V", "9"], "petits": 4, "as": 1}),
    ("24. V 9 A 10 + 1 petit + A 10 x",     {"atouts": ["V", "9", "A", "10"], "petits": 1, "as10x": True}),
    ("25. V + 2 petits + 1 as + 10 sec",     {"atouts": ["V"], "petits": 2, "as": 1, "dix_sec": True}),
    ("26. V 9 + 1 petit + 1 as + 10 sec",    {"atouts": ["V", "9"], "petits": 1, "as": 1, "dix_sec": True}),
    ("27. V 9 + 2 petits + 10 sec",          {"atouts": ["V", "9"], "petits": 2, "dix_sec": True}),
    ("28. V 9 secs + 1 as",                 {"atouts": ["V", "9"], "as": 1}),
    ("29. V 9 secs + 2 as",                 {"atouts": ["V", "9"], "as": 2}),
    ("30. V 9 secs + 3 as",                 {"atouts": ["V", "9"], "as": 3}),
    ("31. V + 1 petit + 2 as",              {"atouts": ["V"], "petits": 1, "as": 2}),
    ("32. V + 2 petits + 3 as",             {"atouts": ["V"], "petits": 2, "as": 3}),
    ("33. 4 petits (sans V ni 9) + 1 as",   {"petits": 4, "as": 1}),
    ("34. V 9 + 2 petits + As-10",          {"atouts": ["V", "9"], "petits": 2, "as10": True}),
    ("35. V 9 + 1 petit, sans as",          {"atouts": ["V", "9"], "petits": 1}),
    ("36. V + 3 petits + 1 as",             {"atouts": ["V"], "petits": 3, "as": 1}),
    ("37. 9 + 3 petits + 1 as",             {"atouts": ["9"], "petits": 3, "as": 1}),
    ("38. V 9 + 1 petit + 2 as",            {"atouts": ["V", "9"], "petits": 1, "as": 2}),
    ("39. V + 4 petits, sans as",           {"atouts": ["V"], "petits": 4}),
    ("40. 9 + 4 petits, sans as",           {"atouts": ["9"], "petits": 4}),
    ("41. 9 + 2 petits + 2 as",             {"atouts": ["9"], "petits": 2, "as": 2}),
    ("42. V + 3 petits + 2 as",             {"atouts": ["V"], "petits": 3, "as": 2}),
    ("43. 9 + 3 petits + 2 as",             {"atouts": ["9"], "petits": 3, "as": 2}),
    ("44. V + 4 petits + 1 as",             {"atouts": ["V"], "petits": 4, "as": 1}),
    ("45. 9 + 4 petits + 1 as",             {"atouts": ["9"], "petits": 4, "as": 1}),
    ("46. V 9 + 2 petits + 2 as",           {"atouts": ["V", "9"], "petits": 2, "as": 2}),
    ("47. 4 petits (sans V ni 9), sans as", {"petits": 4}),
    ("48. V 9 + 4 petits, sans as",         {"atouts": ["V", "9"], "petits": 4}),

]


def generer_main(spec):
    """Crée une main au hasard qui respecte la description."""
    while True:
        fixes = spec.get("atouts", [])
        main = [(r, ATOUT) for r in fixes]
        pool = [r for r in PETITS_ATOUTS if r not in fixes]
        main += [(r, ATOUT) for r in random.sample(pool, spec.get("petits", 0))]

        couleurs = COTES[:]
        random.shuffle(couleurs)
        bloquees = set()                       # couleurs à ne pas compléter
        if spec.get("as10"):
            c = couleurs.pop()
            main += [("A", c), ("10", c)]
        if spec.get("as10x"):                  # As + 10 + une petite (As troisième)
            c = couleurs.pop()
            main += [("A", c), ("10", c), (random.choice(PETITES_COTE), c)]
            bloquees.add(c)                    # exactement 3 cartes dans cette couleur

        if spec.get("dix2"):
            c = couleurs.pop()
            main += [("10", c), (random.choice(PETITES_COTE), c)]
            bloquees.add(c)                    # exactement 2 cartes dans cette couleur
        if spec.get("dix_sec"):                # 10 seul dans sa couleur
            c = couleurs.pop()
            main.append(("10", c))
            bloquees.add(c)                    # aucune autre carte dans cette couleur

        for _ in range(spec.get("as", 0)):
            main.append(("A", couleurs.pop()))

        reste = [(r, c) for c in COTES if c not in bloquees
                 for r in PETITES_COTE if (r, c) not in main]
        main += random.sample(reste, 8 - len(main))

        belote = ("R", ATOUT) in main and ("D", ATOUT) in main
        if belote == spec.get("belote", False):
            return main


if __name__ == "__main__":
    # Vérification : 3 exemples de chaque main type
    for nom, spec in MAINS_TYPES:
        print(nom)
        for _ in range(3):
            print("    " + texte_main(generer_main(spec)))
