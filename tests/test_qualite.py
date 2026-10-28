"""Tests unitaires de la quarantaine et de la porte qualité."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import qualite
import transformation

EXEMPLE = json.loads((Path(__file__).parent / "donnees_exemple.json").read_text(encoding="utf-8"))
MAINTENANT = datetime(2026, 10, 28, 12, 0, tzinfo=timezone.utc)


def donnees_propres():
    return transformation.transformer(EXEMPLE)


def test_donnees_saines_aucune_anomalie():
    assert qualite.controler(donnees_propres(), seuil_stations=3, maintenant=MAINTENANT) == []


def test_prix_aberrant_mis_en_quarantaine():
    long = donnees_propres()
    long.loc[0, "prix"] = 9.99
    valides, rejetes = qualite.separer(long)
    assert len(rejetes) == 1 and len(valides) == len(long) - 1


def test_departement_inconnu_mis_en_quarantaine():
    long = donnees_propres()
    long.loc[0, "code_departement"] = pd.NA
    valides, rejetes = qualite.separer(long)
    assert len(rejetes) == 1 and valides["code_departement"].notna().all()


def test_taux_de_rejet_trop_eleve_bloque_le_lot():
    anomalies = qualite.controler(donnees_propres(), nb_rejetes=5, seuil_stations=3, maintenant=MAINTENANT)
    assert any(a.startswith("Plausibilité") for a in anomalies)


def test_volume_insuffisant_detecte():
    anomalies = qualite.controler(donnees_propres(), seuil_stations=5000, maintenant=MAINTENANT)
    assert any(a.startswith("Volume") for a in anomalies)


def test_doublon_detecte():
    long = donnees_propres()
    long = pd.concat([long, long.head(1)], ignore_index=True)
    anomalies = qualite.controler(long, seuil_stations=3, maintenant=MAINTENANT)
    assert any(a.startswith("Unicité") for a in anomalies)


def test_donnees_perimees_detectees():
    plus_tard = datetime(2026, 11, 15, tzinfo=timezone.utc)
    anomalies = qualite.controler(donnees_propres(), seuil_stations=3, maintenant=plus_tard)
    assert any(a.startswith("Fraîcheur") for a in anomalies)
