"""Qualité : les prix aberrants partent en quarantaine, puis la porte qualité
vérifie que le lot restant est publiable. Une règle violée et le pipeline s'arrête."""

from datetime import datetime, timedelta, timezone

import pandas as pd

PRIX_MIN = 0.5
PRIX_MAX = 4.0
SEUIL_STATIONS = 5000
FRAICHEUR_JOURS = 3
TAUX_REJET_MAX = 0.01  # au-delà de 1 % de lignes rejetées, le lot entier est suspect


def separer(long: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Sépare les lignes publiables des lignes à mettre en quarantaine :
    prix hors bornes ou département impossible à déterminer."""
    plausible = long["prix"].between(PRIX_MIN, PRIX_MAX) & long["code_departement"].notna()
    return long[plausible].reset_index(drop=True), long[~plausible].reset_index(drop=True)


def controler(
    valides: pd.DataFrame,
    nb_rejetes: int = 0,
    seuil_stations: int = SEUIL_STATIONS,
    maintenant: datetime | None = None,
) -> list[str]:
    """Renvoie la liste des anomalies ; liste vide = lot publiable."""
    anomalies = []
    maintenant = maintenant or datetime.now(timezone.utc)

    nb_stations = valides["station_id"].nunique()
    if nb_stations < seuil_stations:
        anomalies.append(f"Volume : {nb_stations} stations, minimum attendu {seuil_stations}.")

    for colonne in ("station_id", "carburant", "prix", "code_departement"):
        nb_vides = int(valides[colonne].isna().sum())
        if nb_vides:
            anomalies.append(f"Complétude : {nb_vides} valeurs vides dans '{colonne}'.")

    doublons = int(valides.duplicated(subset=["station_id", "carburant"]).sum())
    if doublons:
        anomalies.append(f"Unicité : {doublons} doublons (station, carburant).")

    total = len(valides) + nb_rejetes
    taux_rejet = nb_rejetes / total if total else 1.0
    if taux_rejet > TAUX_REJET_MAX:
        anomalies.append(f"Plausibilité : {taux_rejet:.1%} de prix rejetés, maximum {TAUX_REJET_MAX:.0%}.")

    derniere_maj = valides["date_maj"].max()
    if pd.isna(derniere_maj) or derniere_maj < maintenant - timedelta(days=FRAICHEUR_JOURS):
        anomalies.append(f"Fraîcheur : dernière mise à jour {derniere_maj}, trop ancienne.")

    return anomalies
