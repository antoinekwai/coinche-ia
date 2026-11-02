import os
from jouer import BotIA
for k in BotIA.__mro__:
    if k is object:
        continue
    fichier = os.path.basename(__import__(k.__module__).__file__)
    propres = [n for n, v in k.__dict__.items() if callable(v) and not n.startswith("__")]
    print(f"{k.__name__:24} ({fichier:22}) : {', '.join(propres) or '-'}")
