"""Orchestrateur PompeRadar : ingestion, transformation, quarantaine, porte qualité, écriture.

Exemples :
    python src/executer.py
    python src/executer.py --source data/brut/carburants_20261028_1200.json
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import ingestion
import qualite
import transformation

DOSSIER_PROPRE = Path("data/propre")
OPTIONS_CSV = {"sep": ";", "decimal": ",", "index": False, "encoding": "utf-8-sig"}


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    journal = logging.getLogger("pompe_radar")

    parametres = argparse.ArgumentParser(description="Pipeline des prix des carburants")
    parametres.add_argument("--source", type=Path, help="fichier brut déjà téléchargé")
    parametres.add_argument("--seuil-stations", type=int, default=qualite.SEUIL_STATIONS)
    arguments = parametres.parse_args()

    chemin_brut = arguments.source or ingestion.telecharger()
    long = transformation.transformer(ingestion.lire(chemin_brut))
    valides, rejetes = qualite.separer(long)
    journal.info("Transformation : %s lignes valides, %s en quarantaine", len(valides), len(rejetes))

    anomalies = qualite.controler(valides, len(rejetes), seuil_stations=arguments.seuil_stations)
    DOSSIER_PROPRE.mkdir(parents=True, exist_ok=True)
    rapport = {
        "source": str(chemin_brut),
        "stations": int(valides["station_id"].nunique()),
        "lignes_valides": int(len(valides)),
        "lignes_quarantaine": int(len(rejetes)),
        "anomalies": anomalies,
        "statut": "REFUSE" if anomalies else "ACCEPTE",
    }
    (DOSSIER_PROPRE / "rapport_qualite.json").write_text(
        json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    rejetes.to_csv(DOSSIER_PROPRE / "quarantaine.csv", **OPTIONS_CSV)
    if anomalies:
        for anomalie in anomalies:
            journal.error("Porte qualité : %s", anomalie)
        return 1

    valides.to_csv(DOSSIER_PROPRE / "prix_carburants.csv", **OPTIONS_CSV)
    transformation.synthese_departements(valides).to_csv(
        DOSSIER_PROPRE / "synthese_departements.csv", **OPTIONS_CSV
    )

    moselle = valides[(valides["code_departement"] == "57") & (valides["carburant"] == "GAZOLE")]
    for _, ligne in moselle.nsmallest(5, "prix").iterrows():
        journal.info("Gazole Moselle : %.3f euros, %s (%s)", ligne["prix"], ligne["ville"], ligne["cp"])
    journal.info("Porte qualité franchie : %s stations publiées.", rapport["stations"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
