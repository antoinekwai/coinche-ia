from collections import defaultdict
from regles import REGLES_STANDARD
from moteur import distribuer, texte_main
from match_mc import Systeme30, SystemeMCContrat
from experience_audace import joueur_audace
from partie import jouer_donne

ORIGINES = {1: "capot d'entrée", 3: "après réponse", 5: "après demande"}


def diagnostic_capot(nb_capots, regles):
    adv = joueur_audace(20)
    stats = defaultdict(lambda: [0, 0])   # clé -> [annoncés, réussis]
    exemples = []
    trouves = 0

    while trouves < nb_capots:
        mains = distribuer()
        js = [Systeme30(), adv(), Systeme30(), adv()]
        res = jouer_donne(0, js, regles, mains=mains)
        if res is None or not res["contrat"]["capot"] or res["contrat"]["joueur"] % 2 != 0:
            continue
        trouves += 1
        encheres = list(js[1].encheres)      # J1 parle toujours en premier
        nb_annonces = len([d for (j, d) in encheres if isinstance(d, tuple) and j % 2 == 0])
        origine = ORIGINES.get(nb_annonces, "autre")
        entame = "on entame" if encheres[0][0] % 2 == 0 else "adversaire entame"

        r = jouer_donne(0, [SystemeMCContrat(), adv(), SystemeMCContrat(), adv()], regles, mains=mains)
        for cle in (origine, entame):
            stats[cle][0] += 1
            stats[cle][1] += r["reussi"]
        if not r["reussi"] and len(exemples) < 3:
            exemples.append((mains, encheres, origine))

    print("Origine / situation   | Annoncés | Réussis")
    for cle, (n, ok) in stats.items():
        print(f"{cle:21} | {n:8} | {ok:4} ({100 * ok / n:.0f} %)")

    print("\n=== Exemples de capots chutés ===")
    for mains, encheres, origine in exemples:
        print(f"\n[{origine}]")
        print("  Enchères : " + ", ".join(
            f"J{j}:{d if isinstance(d, str) else str(d[0]) + d[1]}" for (j, d) in encheres))
        for j in range(4):
            print(f"  J{j} : {texte_main(mains[j])}")


if __name__ == "__main__":
    diagnostic_capot(60, REGLES_STANDARD)
