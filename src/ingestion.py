"""Ingestion : téléchargement du flux officiel des prix des carburants.

Source : Ministère de l'Économie, jeu de données « Prix des carburants en France,
flux instantané v2 » (data.economie.gouv.fr), Licence Ouverte Etalab.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

import requests

URL_FLUX = (
    "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/"
    "prix-des-carburants-en-france-flux-instantane-v2/exports/json"
)
DOSSIER_BRUT = Path("data/brut")

journal = logging.getLogger(__name__)


def telecharger(url: str = URL_FLUX, dossier: Path = DOSSIER_BRUT) -> Path:
    """Télécharge le flux complet et l'enregistre tel quel (couche brute)."""
    dossier.mkdir(parents=True, exist_ok=True)
    reponse = requests.get(url, timeout=180)
    reponse.raise_for_status()
    stations = reponse.json()
    if not isinstance(stations, list) or not stations:
        raise ValueError("Flux vide ou inattendu : une liste de stations était attendue.")
    horodatage = datetime.now().strftime("%Y%m%d_%H%M")
    chemin = dossier / f"carburants_{horodatage}.json"
    chemin.write_text(json.dumps(stations, ensure_ascii=False), encoding="utf-8")
    journal.info("Ingestion : %s stations enregistrées dans %s", len(stations), chemin)
    return chemin


def lire(chemin: Path) -> list[dict]:
    """Relit un fichier brut déjà téléchargé."""
    return json.loads(Path(chemin).read_text(encoding="utf-8"))
