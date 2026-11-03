# inspecter_jsonl.py : LECTURE SEULE, ne modifie aucun fichier.
# Pour chaque fichier .jsonl : nombre de lignes, types de lignes, exemples.
import json
import sys
from collections import Counter

for nom in sys.argv[1:]:
    print("=" * 60)
    print(nom)
    types = Counter()   # combien de lignes ont chaque ensemble de clés
    exemples = {}       # une ligne d'exemple par type
    erreurs = 0
    with open(nom) as f:
        for ligne in f:
            try:
                d = json.loads(ligne)
            except json.JSONDecodeError:
                erreurs += 1
                continue
            cles = tuple(sorted(d.keys())) if isinstance(d, dict) else ("(pas un dictionnaire)",)
            types[cles] += 1
            exemples.setdefault(cles, ligne.strip()[:300])
    print("Lignes illisibles :", erreurs)
    for cles, n in types.most_common():
        print(f"\n{n} lignes avec les clés : {', '.join(cles)}")
        print("  exemple :", exemples[cles])
