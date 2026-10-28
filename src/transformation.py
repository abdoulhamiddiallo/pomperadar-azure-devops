"""Transformation : du flux brut (une ligne par station) au format long
(une ligne par station et par carburant), propre et typé."""

import pandas as pd

CARBURANTS = ("gazole", "sp95", "sp98", "e10", "e85", "gplc")
COLONNES_OBLIGATOIRES = ("id", "ville", "cp")
COLONNES_SORTIE = [
    "station_id", "adresse", "ville", "cp", "code_departement", "departement",
    "region", "latitude", "longitude", "carburant", "prix", "date_maj",
]


class ContratRompu(ValueError):
    """Le schéma reçu ne correspond plus à ce que le pipeline attend."""


def verifier_contrat(brut: pd.DataFrame) -> list[str]:
    """Vérifie le contrat de schéma et renvoie les carburants présents."""
    manquantes = [c for c in COLONNES_OBLIGATOIRES if c not in brut.columns]
    presents = [c for c in CARBURANTS if f"{c}_prix" in brut.columns]
    if manquantes or not presents:
        raise ContratRompu(
            f"Contrat de schéma rompu. Colonnes manquantes : {manquantes or 'aucune'}. "
            f"Colonnes reçues : {sorted(brut.columns)}"
        )
    return presents


def _code_postal(serie: pd.Series) -> pd.Series:
    texte = serie.astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
    return texte.str.zfill(5)


def _code_departement(cp: pd.Series) -> pd.Series:
    """Déduit le département du code postal ; vide si le code postal est invalide."""
    valide = cp.str.fullmatch(r"\d{5}").fillna(False).astype(bool)
    outre_mer = cp.str.startswith(("97", "98")).fillna(False).astype(bool)
    code = cp.str[:2].where(~outre_mer, cp.str[:3])
    return code.where(valide, pd.NA)


def _coordonnee(serie: pd.Series, limite: float) -> pd.Series:
    valeurs = pd.to_numeric(serie, errors="coerce")
    # L'ancien format stockait les degrés multipliés par 100 000.
    return valeurs.where(valeurs.abs() <= limite, valeurs / 100_000)


def _position(brut: pd.DataFrame, colonne: str, cle_geom: str) -> pd.Series:
    """Lit la colonne de position, complétée au besoin par le point géographique 'geom'."""
    valeurs = brut[colonne] if colonne in brut.columns else pd.Series(pd.NA, index=brut.index)
    if "geom" in brut.columns:
        depuis_geom = brut["geom"].map(lambda g: g.get(cle_geom) if isinstance(g, dict) else None)
        valeurs = valeurs.fillna(depuis_geom)
    return valeurs


def _prix(serie: pd.Series) -> pd.Series:
    valeurs = pd.to_numeric(serie, errors="coerce")
    # Certains flux publient le prix en millièmes d'euro (1789 au lieu de 1.789).
    return valeurs.where(valeurs <= 10, valeurs / 1000).round(3)


def transformer(stations: list[dict]) -> pd.DataFrame:
    """Aplatit le flux brut en table longue station x carburant."""
    brut = pd.DataFrame(stations)
    presents = verifier_contrat(brut)

    base = pd.DataFrame({"station_id": brut["id"].astype(str)})
    base["cp"] = _code_postal(brut["cp"])
    base["ville"] = brut["ville"].astype(str).str.strip().str.title()
    for colonne in ("adresse", "departement", "region"):
        base[colonne] = brut[colonne] if colonne in brut.columns else pd.NA
    # Code département : celui du flux s'il est renseigné, sinon déduit du code postal.
    deduit = _code_departement(base["cp"])
    if "code_departement" in brut.columns:
        code = brut["code_departement"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(2)
        base["code_departement"] = code.where(brut["code_departement"].notna(), deduit)
    else:
        base["code_departement"] = deduit

    base["latitude"] = _coordonnee(_position(brut, "latitude", "lat"), 90)
    base["longitude"] = _coordonnee(_position(brut, "longitude", "lon"), 180)

    morceaux = []
    for carburant in presents:
        morceau = base.copy()
        morceau["carburant"] = carburant.upper()
        morceau["prix"] = _prix(brut[f"{carburant}_prix"])
        colonne_maj = f"{carburant}_maj"
        if colonne_maj in brut.columns:
            morceau["date_maj"] = pd.to_datetime(brut[colonne_maj], errors="coerce", utc=True)
        else:
            morceau["date_maj"] = pd.NaT
        morceaux.append(morceau)

    long = pd.concat(morceaux, ignore_index=True)
    long = long.dropna(subset=["prix"])
    return long[COLONNES_SORTIE].reset_index(drop=True)


def synthese_departements(long: pd.DataFrame) -> pd.DataFrame:
    """Prix moyen, minimum et maximum par département et par carburant."""
    return (
        long.groupby(["code_departement", "carburant"], as_index=False)
        .agg(
            nb_stations=("station_id", "nunique"),
            prix_moyen=("prix", "mean"),
            prix_min=("prix", "min"),
            prix_max=("prix", "max"),
        )
        .round({"prix_moyen": 3})
        .sort_values(["code_departement", "carburant"])
        .reset_index(drop=True)
    )
