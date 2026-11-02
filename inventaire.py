"""
inventaire.py
Liste les fichiers Python réellement utilisés par les programmes principaux.
Ne modifie rien.
"""
import ast
import os

POINTS_DE_DEPART = ["app.py", "benchmark_confirmation.py", "rapport.py", "jouer.py",
                    "ia_entrainer_mix3.py"]

locaux = {f[:-3] for f in os.listdir(".") if f.endswith(".py")}


def imports_de(module):
    """Modules du projet importés par ce fichier (y compris dans les fonctions)."""
    with open(module + ".py", encoding="utf-8") as f:
        arbre = ast.parse(f.read())
    noms = set()
    for n in ast.walk(arbre):
        if isinstance(n, ast.Import):
            noms.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            noms.add(n.module.split(".")[0])
    return noms & locaux


utiles = set()
a_voir = [p[:-3] for p in POINTS_DE_DEPART if os.path.exists(p)]
while a_voir:
    m = a_voir.pop()
    if m in utiles:
        continue
    utiles.add(m)
    try:
        a_voir.extend(imports_de(m))
    except SyntaxError:
        print(f"⚠️ Impossible de lire {m}.py")

inutiles = sorted(locaux - utiles - {"inventaire"})
print(f"=== UTILISÉS ({len(utiles)}) ===")
print("  " + "\n  ".join(sorted(utiles)))
print(f"\n=== NON UTILISÉS par les programmes principaux ({len(inutiles)}) ===")
print("  " + "\n  ".join(inutiles))
