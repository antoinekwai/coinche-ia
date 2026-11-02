"""Liste, pour chaque classe de la chaîne, les fonctions qu'elle définit elle-même."""
import os
from bot_coop import BotCoop

for k in BotCoop.__mro__:
    if k is object:
        continue
    fichier = os.path.basename(__import__(k.__module__).__file__)
    propres = [n for n, v in k.__dict__.items() if callable(v) and not n.startswith("__")]
    print(f"{k.__name__:24} ({fichier:22}) : {', '.join(propres) or '-'}")
