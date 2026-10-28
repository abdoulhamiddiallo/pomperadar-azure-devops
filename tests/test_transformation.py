"""Tests unitaires de la transformation (sans réseau : jeu d'exemple local)."""

import json
from pathlib import Path

import pytest

import transformation

EXEMPLE = json.loads((Path(__file__).parent / "donnees_exemple.json").read_text(encoding="utf-8"))


def test_format_long_une_ligne_par_station_et_carburant():
    long = transformation.transformer(EXEMPLE)
    # Metz : 2 prix (SP98 vide), Thionville : 3, Paris : 3.
    assert len(long) == 8
    assert set(long["carburant"]) == {"GAZOLE", "E10", "SP98"}


def test_prix_en_milliemes_convertis_en_euros():
    long = transformation.transformer(EXEMPLE)
    thionville = long[(long["ville"] == "Thionville") & (long["carburant"] == "GAZOLE")]
    assert thionville["prix"].iloc[0] == pytest.approx(1.659)


def test_coordonnees_ancien_format_converties_en_degres():
    long = transformation.transformer(EXEMPLE)
    thionville = long[long["ville"] == "Thionville"].iloc[0]
    assert thionville["latitude"] == pytest.approx(49.358)
    assert thionville["longitude"] == pytest.approx(6.167)


def test_code_postal_numerique_reste_sur_cinq_caracteres():
    long = transformation.transformer(EXEMPLE)
    assert set(long["cp"]) == {"57000", "57100", "75015"}


def test_code_departement_absent_deduit_du_code_postal():
    sans_code = [dict(station) for station in EXEMPLE]
    sans_code[0]["code_departement"] = None
    long = transformation.transformer(sans_code)
    metz = long[long["ville"] == "Metz"]
    assert set(metz["code_departement"]) == {"57"}


def test_contrat_rompu_si_colonne_obligatoire_absente():
    sans_ville = [{k: v for k, v in station.items() if k != "ville"} for station in EXEMPLE]
    with pytest.raises(transformation.ContratRompu):
        transformation.transformer(sans_ville)


def test_synthese_par_departement():
    synthese = transformation.synthese_departements(transformation.transformer(EXEMPLE))
    gazole_57 = synthese[(synthese["code_departement"] == "57") & (synthese["carburant"] == "GAZOLE")]
    assert gazole_57["nb_stations"].iloc[0] == 2
    assert gazole_57["prix_min"].iloc[0] == pytest.approx(1.659)
