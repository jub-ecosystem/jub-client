#!/usr/bin/env python3
"""
seed_client.py — Seeds JUB via the JubClient (the recommended path for Python integrators).

This is the client-based equivalent of seed_api.py. Instead of making raw HTTP
requests with httpx, it uses the official JubClient async wrapper, which handles
authentication, JWT propagation, temporal secret headers, and Result-based error
handling automatically.

Steps executed for each observatory:
  1.  client.setup_observatory()     -> disabled observatory + PENDING task
  2.  client.bulk_assign_catalogs()  -> create & link all catalogs at once
  3.  client.get_catalog()           -> fetch item IDs for product tagging
  4.  client.bulk_assign_products()  -> create & link products with tags
  5.  client.upload_product()        -> upload chart file per product
  6.  client.complete_task()         -> mark task done, enables observatory

Usage:
    python examples/v2/seed_client.py
    python examples/v2/seed_client.py --api-url http://localhost:5000
    python examples/v2/seed_client.py --username admin --password secret
    python examples/v2/seed_client.py --signup --username newuser --password pass \\
                                      --email me@example.com --first-name Ada --last-name Lovelace
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from jub.client.v2 import JubClient
import jub.dto.v2 as DTO


# ---------------------------------------------------------------------------
# Paths — chart files live in the jub_api source/ directory
# ---------------------------------------------------------------------------

# The seed script lives at examples/v2/, so we go up two levels to reach
# the project root, then into the jub_api sibling project's source/ folder.
ROOT_DIR   = Path(__file__).parent.parent.parent.parent / "jub_api"
SOURCE_DIR = ROOT_DIR / "source"

HEATMAP_FILE = SOURCE_DIR / "heatmap.html"
RADAR_FILE   = SOURCE_DIR / "radar.html"


# ---------------------------------------------------------------------------
# Domain data — Mexican public health data (mirrors seed_api.py exactly)
# ---------------------------------------------------------------------------

# Each tuple is (numeric_code, display_name, abbreviation).
MEXICO_STATES: List[tuple] = [
    (1,  "Aguascalientes",                   "AGS"),
    (2,  "Baja California",                  "BC"),
    (3,  "Baja California Sur",              "BCS"),
    (4,  "Campeche",                         "CAM"),
    (5,  "Coahuila de Zaragoza",             "COAH"),
    (6,  "Colima",                           "COL"),
    (7,  "Chiapas",                          "CHIS"),
    (8,  "Chihuahua",                        "CHIH"),
    (9,  "Ciudad de Mexico",                 "CDMX"),
    (10, "Durango",                          "DGO"),
    (11, "Guanajuato",                       "GTO"),
    (12, "Guerrero",                         "GRO"),
    (13, "Hidalgo",                          "HGO"),
    (14, "Jalisco",                          "JAL"),
    (15, "Estado de Mexico",                 "MEX"),
    (16, "Michoacan de Ocampo",              "MICH"),
    (17, "Morelos",                          "MOR"),
    (18, "Nayarit",                          "NAY"),
    (19, "Nuevo Leon",                       "NL"),
    (20, "Oaxaca",                           "OAX"),
    (21, "Puebla",                           "PUE"),
    (22, "Queretaro",                        "QRO"),
    (23, "Quintana Roo",                     "QROO"),
    (24, "San Luis Potosi",                  "SLP"),
    (25, "Sinaloa",                          "SIN"),
    (26, "Sonora",                           "SON"),
    (27, "Tabasco",                          "TAB"),
    (28, "Tamaulipas",                       "TAMS"),
    (29, "Tlaxcala",                         "TLAX"),
    (30, "Veracruz de Ignacio de la Llave",  "VER"),
    (31, "Yucatan",                          "YUC"),
    (32, "Zacatecas",                        "ZAC"),
]

# Report years covered by the public health records.
YEARS = list(range(2015, 2024))

# (numeric_code, display_name, query_value)
SEX_DATA = [
    (1, "Hombre",          "HOMBRE"),
    (2, "Mujer",           "MUJER"),
    (9, "No especificado", "NO_ESPECIFICADO"),
]

# (code, display_name, query_value, description)
AGE_GROUP_DATA = [
    (1, "0-4 años",       "G0_4",    "Infancia temprana"),
    (2, "5-14 años",      "G5_14",   "Infancia y preadolescencia"),
    (3, "15-24 años",     "G15_24",  "Adolescencia y juventud"),
    (4, "25-34 años",     "G25_34",  "Adultos jovenes"),
    (5, "35-44 años",     "G35_44",  "Adultos en edad media"),
    (6, "45-54 años",     "G45_54",  "Adultos maduros"),
    (7, "55-64 años",     "G55_64",  "Adultos mayores tempranos"),
    (8, "65-74 años",     "G65_74",  "Adultos mayores"),
    (9, "75 años y más",  "G75_MAS", "Adultos mayores avanzados"),
]

# (code, display_name, query_value, cie10_range)
CAUSE_DEATH_DATA = [
    (1,  "Enfermedades isquemicas del corazon", "ISQUEMICA_CORAZON",   "I20-I25"),
    (2,  "Diabetes mellitus",                   "DIABETES_MELLITUS",   "E10-E14"),
    (3,  "Tumores malignos",                    "TUMOR_MALIGNO",       "C00-D48"),
    (4,  "Enfermedades cerebrovasculares",       "CEREBROVASCULAR",     "I60-I69"),
    (5,  "Neumonia e influenza",                 "NEUMONIA_INFLUENZA",  "J09-J18"),
    (6,  "Enfermedades del higado",              "ENFERMEDAD_HIGADO",   "K70-K76"),
    (7,  "Accidentes de transito",               "ACCIDENTE_TRANSITO",  "V01-V99"),
    (8,  "Insuficiencia renal cronica",          "INSUFICIENCIA_RENAL", "N17-N19"),
    (9,  "Hipertension arterial sistemica",      "HIPERTENSION",        "I10-I15"),
    (10, "COVID-19",                             "COVID_19",            "U07"),
]

# (code, display_name, query_value, cie10_range)
CANCER_CIE10_DATA = [
    (1,  "Labio, cavidad oral y faringe",       "C_ORAL_FARINGE",        "C00-C14"),
    (2,  "Esofago, estomago e intestinos",      "C_DIGESTIVO",           "C15-C26"),
    (3,  "Higado y vias biliares",              "C_HIGADO",              "C22-C24"),
    (4,  "Pancreas",                            "C_PANCREAS",            "C25"),
    (5,  "Organos respiratorios (pulmon)",      "C_RESPIRATORIO",        "C30-C39"),
    (6,  "Mama",                                "C_MAMA",                "C50"),
    (7,  "Cervix uterino",                      "C_CERVIX",              "C53"),
    (8,  "Cuerpo del utero",                    "C_UTERO",               "C54"),
    (9,  "Ovario",                              "C_OVARIO",              "C56"),
    (10, "Prostata",                            "C_PROSTATA",            "C61"),
    (11, "Vias urinarias (vejiga y rinon)",     "C_URINARIO",            "C64-C68"),
    (12, "Cerebro y sistema nervioso central",  "C_SNC",                 "C70-C72"),
    (13, "Tiroides",                            "C_TIROIDES",            "C73"),
    (14, "Tejido linfoide y hematopoyetico",    "C_LINFOHEMATOPOYETICO", "C81-C96"),
]

# (code, display_name, query_value)
DERECHOHABIENCIA_DATA = [
    (1, "IMSS",                    "IMSS"),
    (2, "ISSSTE",                  "ISSSTE"),
    (3, "PEMEX / SEDENA / MARINA", "PEMEX_SEDENA_MARINA"),
    (4, "Seguro Popular / INSABI", "SEGURO_POPULAR_INSABI"),
    (5, "Seguro privado",          "PRIVADO"),
    (6, "Sin derechohabiencia",    "NINGUNA"),
]


# ---------------------------------------------------------------------------
# Observatory & product definitions
# ---------------------------------------------------------------------------

OBSERVATORIES = [
    {
        "observatory_id": "obs_mortalidad_mx",
        "title":          "Observatorio de Mortalidad — Mexico",
        "description": (
            "Monitorea las principales causas de muerte en Mexico, su distribucion "
            "geografica y temporal, y las tendencias de mortalidad prematura por grupos "
            "de poblacion. Fuente principal: Certificados de Defuncion SINAVE-DGIS."
        ),
        "image_url": None,
        "metadata":  {"fuente": "SINAVE-DGIS", "pais": "MX", "version": "2023"},
    },
    {
        "observatory_id": "obs_cancer_mx",
        "title":          "Observatorio de Cancer — Mexico",
        "description": (
            "Seguimiento epidemiologico de la incidencia y mortalidad por cancer en Mexico, "
            "con base en la clasificacion CIE-10 y los grupos de riesgo IARC. "
            "Fuente: Registro Nacional de Cancer / INCAN."
        ),
        "image_url": None,
        "metadata":  {"fuente": "INCAN / RNEC", "pais": "MX", "version": "2022"},
    },
    {
        "observatory_id": "obs_cronicas_mx",
        "title":          "Observatorio de Enfermedades Cronicas No Transmisibles",
        "description": (
            "Analiza la prevalencia y mortalidad por diabetes mellitus, enfermedades "
            "cardiovasculares e hipertension arterial en la poblacion mexicana, "
            "desagregado por derechohabiencia, sexo y region. Fuente: ENSANUT / SINAVE."
        ),
        "image_url": None,
        "metadata":  {"fuente": "ENSANUT / SINAVE", "pais": "MX", "version": "2022"},
    },
]

# Maps each observatory key to the catalog types it uses.
# These keys must match entries in CATALOG_BUILDERS below.
OBS_CATALOG_SETS: Dict[str, List[str]] = {
    "obs_mortalidad_mx": ["spatial", "temporal", "sex", "age_group", "causa_defuncion"],
    "obs_cancer_mx":     ["spatial", "temporal", "sex", "age_group", "cie10_cancer"],
    "obs_cronicas_mx":   ["spatial", "temporal", "sex", "causa_defuncion", "derechohabiencia"],
}

# Maps each observatory to its products. Each product declares:
#   - product_id / name / description  — identity
#   - tag_catalogs                     — which catalogs supply the item ID tags
#   - chart                            — "heatmap" or "radar" for the upload step
PRODUCTS_BY_OBS: Dict[str, List[Dict]] = {
    "obs_mortalidad_mx": [
        {
            "product_id":   "prod_mort_causa_estado",
            "name":         "Mortalidad por Causa y Estado",
            "description":  "Distribucion de defunciones por causa de muerte (top 10) y entidad federativa.",
            "tag_catalogs": ["causa_defuncion", "spatial"],
            "chart":        "heatmap",
        },
        {
            "product_id":   "prod_mort_edad_sexo",
            "name":         "Mortalidad por Grupo de Edad y Sexo",
            "description":  "Mortalidad segun grupo etario y sexo. Identifica grupos vulnerables.",
            "tag_catalogs": ["sex", "age_group"],
            "chart":        "radar",
        },
        {
            "product_id":   "prod_mort_tendencia",
            "name":         "Tendencia de Mortalidad 2015-2023",
            "description":  "Serie temporal de mortalidad. Incluye el impacto del COVID-19 en 2020-2021.",
            "tag_catalogs": ["temporal", "causa_defuncion"],
            "chart":        "radar",
        },
    ],
    "obs_cancer_mx": [
        {
            "product_id":   "prod_cancer_tipo_cie10",
            "name":         "Cancer por Tipo CIE-10 / IARC",
            "description":  "Casos de cancer agrupados por CIE-10 y categorias IARC.",
            "tag_catalogs": ["cie10_cancer"],
            "chart":        "radar",
        },
        {
            "product_id":   "prod_cancer_mortalidad_estado",
            "name":         "Mortalidad por Cancer por Entidad",
            "description":  "Tasas de mortalidad oncologica por estado. Identifica estados con mayor carga.",
            "tag_catalogs": ["cie10_cancer", "spatial"],
            "chart":        "heatmap",
        },
        {
            "product_id":   "prod_cancer_sexo_edad",
            "name":         "Cancer por Sexo y Grupo de Edad",
            "description":  "Distribucion del cancer por sexo y grupo etario.",
            "tag_catalogs": ["sex", "age_group", "cie10_cancer"],
            "chart":        "radar",
        },
    ],
    "obs_cronicas_mx": [
        {
            "product_id":   "prod_diabetes_estado",
            "name":         "Mortalidad por Diabetes Mellitus por Estado",
            "description":  "Tasa de mortalidad por diabetes por cada 100k hab. por entidad federativa.",
            "tag_catalogs": ["causa_defuncion", "spatial"],
            "chart":        "heatmap",
        },
        {
            "product_id":   "prod_cardio_tendencia",
            "name":         "Tendencia de Mortalidad Cardiovascular",
            "description":  "Evolucion de la mortalidad por enfermedades isquemicas y cerebrovasculares.",
            "tag_catalogs": ["temporal", "causa_defuncion"],
            "chart":        "radar",
        },
        {
            "product_id":   "prod_cronica_derecho",
            "name":         "Enfermedades Cronicas por Derechohabiencia",
            "description":  "Mortalidad cronica segun afiliacion al sistema de salud.",
            "tag_catalogs": ["derechohabiencia", "causa_defuncion"],
            "chart":        "radar",
        },
    ],
}


# ---------------------------------------------------------------------------
# Catalog payload builders — return plain dicts matching CatalogCreateDTO
# ---------------------------------------------------------------------------

def _alias(value: str, value_type: str = "STRING", description: str = "") -> Dict:
    """Build a single alias dict for a catalog item."""
    return {"value": value, "value_type": value_type, "description": description}


def _item(
    name: str,
    value: str,
    code: int,
    value_type: str = "STRING",
    description: str = "",
    aliases: Optional[List[Dict]] = None,
    children: Optional[List[Dict]] = None,
    temporal_value: Optional[str] = None,
) -> Dict:
    """
    Build a catalog item dict.

    The `temporal_value` field is only added when present — the API ignores it
    for non-DATETIME items, but omitting it keeps payloads clean.
    """
    d: Dict[str, Any] = {
        "name":        name,
        "value":       value,
        "code":        code,
        "value_type":  value_type,
        "description": description,
        "aliases":     aliases or [],
        "children":    children or [],
    }
    if temporal_value is not None:
        d["temporal_value"] = temporal_value
    return d


def build_spatial_dto() -> Dict:
    """
    Build the SPATIAL catalog for Mexico.

    The hierarchy is: Mexico (root) -> 32 states (children).
    Each state includes multiple aliases (INEGI code, abbreviation, full name)
    so the DSL can resolve queries using any of those representations.
    """
    state_items = [
        _item(
            name        = name,
            value       = abbr,
            code        = code,
            description = f"Estado de {name}, Mexico (INEGI {code:02d})",
            aliases     = [
                _alias(str(code),     "NUMBER", "Clave INEGI del estado"),
                _alias(abbr,          "STRING", "Abreviatura oficial"),
                _alias(name,          "STRING", "Nombre completo"),
                _alias(f"{code:02d}", "STRING", "Clave INEGI con cero"),
            ],
        )
        for code, name, abbr in MEXICO_STATES
    ]
    # Mexico is the root item; all 32 states are its children.
    mx_root = _item(
        name        = "Mexico",
        value       = "MX",
        code        = 0,
        description = "Republica Mexicana",
        aliases     = [
            _alias("MEX",    "STRING", "ISO 3166-1 alpha-3"),
            _alias("484",    "NUMBER", "ISO 3166-1 numerico"),
            _alias("Mexico", "STRING", "Nombre en ingles"),
        ],
        children    = state_items,
    )
    return {
        "name":         "Dimension Espacial — Mexico",
        "value":        "SPATIAL_MX",
        "catalog_type": "SPATIAL",
        "description":  "Jerarquia geografica de Mexico: Pais -> Estado. Codigos INEGI 2020.",
        "items":        [mx_root],
    }


def build_temporal_dto() -> Dict:
    """
    Build the TEMPORAL catalog covering report years 2015-2023.

    Each year is stored as a DATETIME item so the DSL VT() operator can
    apply range filters (e.g. VT(>= 2020)).
    """
    items = [
        _item(
            name           = str(year),
            value          = f"Y{year}",
            code           = year,
            value_type     = "DATETIME",
            description    = f"Año de reporte {year}",
            temporal_value = f"{year}-01-01T00:00:00Z",
            aliases        = [
                _alias(str(year),      "NUMBER", "Año como entero"),
                _alias(f"AÑO_{year}",  "STRING", "Etiqueta en espanol"),
                _alias(f"YEAR_{year}", "STRING", "Etiqueta en ingles"),
            ],
        )
        for year in YEARS
    ]
    return {
        "name":         "Dimension Temporal — Años de Reporte",
        "value":        "TEMPORAL_ANIOS",
        "catalog_type": "TEMPORAL",
        "description":  "Años calendario 2015-2023 presentes en los registros de salud publica.",
        "items":        items,
    }


def build_sex_dto() -> Dict:
    """Build the INTEREST catalog for biological sex classification (SINAVE codes)."""
    items = [
        _item(
            name    = name,
            value   = val,
            code    = code,
            aliases = [_alias(str(code), "NUMBER", "Codigo numerico SINAVE")],
        )
        for code, name, val in SEX_DATA
    ]
    return {
        "name":         "Sexo Biologico",
        "value":        "SEX",
        "catalog_type": "INTEREST",
        "description":  "Clasificacion por sexo biologico al nacimiento segun registros administrativos de salud.",
        "items":        items,
    }


def build_age_group_dto() -> Dict:
    """Build the INTEREST catalog for epidemiological age group classification."""
    items = [
        _item(
            name        = name,
            value       = val,
            code        = code,
            description = desc,
            aliases     = [_alias(str(code), "NUMBER", "Codigo numerico")],
        )
        for code, name, val, desc in AGE_GROUP_DATA
    ]
    return {
        "name":         "Grupos de Edad",
        "value":        "AGE_GROUP",
        "catalog_type": "INTEREST",
        "description":  "Clasificacion por grupos quinquenales de edad para analisis epidemiologico.",
        "items":        items,
    }


def build_causa_defuncion_dto() -> Dict:
    """Build the INTEREST catalog for the top-10 causes of death (CIE-10 codes)."""
    items = [
        _item(
            name        = name,
            value       = val,
            code        = code,
            description = f"Rango CIE-10: {cie}",
            aliases     = [
                _alias(cie,       "STRING", "Rango CIE-10"),
                _alias(str(code), "NUMBER", "Codigo secuencial"),
            ],
        )
        for code, name, val, cie in CAUSE_DEATH_DATA
    ]
    return {
        "name":         "Causa de Defuncion (Top 10)",
        "value":        "CAUSA_DEFUNCION",
        "catalog_type": "INTEREST",
        "description":  "Principales causas de muerte en Mexico segun CIE-10. Fuente: SINAVE-DGIS.",
        "items":        items,
    }


def build_cie10_cancer_dto() -> Dict:
    """Build the INTEREST catalog for cancer types grouped by CIE-10 / IARC classification."""
    items = [
        _item(
            name        = name,
            value       = val,
            code        = code,
            description = f"CIE-10 {cie}",
            aliases     = [
                _alias(cie,       "STRING", "Rango CIE-10"),
                _alias(str(code), "NUMBER", "Codigo secuencial"),
            ],
        )
        for code, name, val, cie in CANCER_CIE10_DATA
    ]
    return {
        "name":         "Grupos de Cancer CIE-10 / IARC",
        "value":        "CIE10_CANCER",
        "catalog_type": "INTEREST",
        "description":  "Agrupacion de neoplasias malignas segun CIE-10. Fuente: OPS / IARC / INCAN.",
        "items":        items,
    }


def build_derechohabiencia_dto() -> Dict:
    """Build the INTEREST catalog for health system affiliation (derechohabiencia)."""
    items = [
        _item(
            name    = name,
            value   = val,
            code    = code,
            aliases = [_alias(str(code), "NUMBER", "Codigo numerico")],
        )
        for code, name, val in DERECHOHABIENCIA_DATA
    ]
    return {
        "name":         "Derechohabiencia / Afiliacion al Sistema de Salud",
        "value":        "DERECHOHABIENCIA",
        "catalog_type": "INTEREST",
        "description":  "Tipo de afiliacion al sistema de salud en Mexico. Fuente: Certificados de Defuncion / ENSANUT.",
        "items":        items,
    }


# Maps catalog label strings (used in OBS_CATALOG_SETS) to their builder functions.
CATALOG_BUILDERS = {
    "spatial":          build_spatial_dto,
    "temporal":         build_temporal_dto,
    "sex":              build_sex_dto,
    "age_group":        build_age_group_dto,
    "causa_defuncion":  build_causa_defuncion_dto,
    "cie10_cancer":     build_cie10_cancer_dto,
    "derechohabiencia": build_derechohabiencia_dto,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ok(result: Any, label: str) -> Any:
    """
    Unwrap a Result[T, Exception] or abort the script.

    Every JubClient method returns a Result instead of raising. This helper
    extracts the inner value on success. On failure it prints the error and
    calls sys.exit(1), which keeps the seed logic free from nested error checks.

    Args:
        result: The Result returned by a JubClient method.
        label:  Short description used in the error message if the call failed.

    Returns:
        The unwrapped Ok value (typed DTO or raw dict depending on the method).
    """
    if result.is_err:
        print(f"  ERROR {label}: {result.unwrap_err()}")
        sys.exit(1)
    return result.unwrap()


def extract_item_ids(items: List[DTO.CatalogItemResponseDTO]) -> List[str]:
    """
    Flatten a (possibly nested) catalog item tree into a flat list of item IDs.

    The spatial catalog uses a two-level hierarchy (Mexico -> states), so items
    can have children. This function walks the tree depth-first and collects
    every catalog_item_id it finds, including those in nested children.

    Args:
        items: Top-level list of CatalogItemResponseDTO objects from get_catalog().

    Returns:
        A flat list of catalog_item_id strings.
    """
    ids: List[str] = []
    for item in items:
        ids.append(item.catalog_item_id)
        if item.children:
            ids.extend(extract_item_ids(item.children))
    return ids


# ---------------------------------------------------------------------------
# Main seed coroutine
# ---------------------------------------------------------------------------

async def seed(
    api_url:    str,
    username:   str,
    password:   str,
    scope:      str,
    signup:     bool,
    email:      str,
    first_name: str,
    last_name:  str,
    clean:      bool = False,
) -> None:
    """
    Seed the JUB API with three observatories, their catalogs, products,
    and chart uploads, using the JubClient async wrapper.

    Args:
        api_url:    Base URL of the JUB API, e.g. "http://localhost:5000".
                    Do NOT include /api/v2 — the client appends it automatically.
        username:   Login username.
        password:   Login password.
        scope:      Auth scope (default "jub").
        signup:     When True, create the user account before authenticating.
        email:      Email address, used only when signup=True.
        first_name: First name, used only when signup=True.
        last_name:  Last name, used only when signup=True.
        clean:      When True, delete existing observatories before seeding.
    """

    # Validate that the chart HTML files exist before touching the API.
    # Failing here saves time compared to discovering missing files mid-seed.
    for f in (HEATMAP_FILE, RADAR_FILE):
        if not f.exists():
            print(f"  ERROR Source file not found: {f}")
            sys.exit(1)

    # ── Build the client ─────────────────────────────────────────────────────
    # JubClient stores credentials and configuration, but does NOT authenticate
    # in the constructor. We call authenticate() explicitly right after.
    # The `scope` parameter controls which API scope the JWT covers.
    client = JubClient(api_url, username, password, scope=scope)

    # ── Optional: register a new user ────────────────────────────────────────
    print("\n--- Auth ----------------------------------------------------------------")
    if signup:
        # signup() POSTs to /users/signup and returns Ok(response_dict) or Err.
        # We call it before authenticate() because the account must exist first.
        signup_result = await client.signup(DTO.SignUpDTO(
            username   = username,
            email      = email,
            first_name = first_name,
            last_name  = last_name,
            password   = password,
        ))
        if signup_result.is_err:
            print(f"  ERROR signup: {signup_result.unwrap_err()}")
            sys.exit(1)
        print(f"  OK  User '{username}' created")

    # authenticate() POSTs to /users/auth and, on success, stores the JWT token
    # and temporal_secret_key on the client instance. Every method called after
    # this point automatically attaches both as request headers — no manual
    # header management needed.
    auth_result = await client.authenticate()
    if auth_result.is_err:
        print(f"  ERROR authentication: {auth_result.unwrap_err()}")
        sys.exit(1)
    print(f"  OK  Authenticated as '{username}' (user_id={client.user_id})")

    # ── Optional: delete existing observatories before re-seeding ────────────
    if clean:
        print("\n--- Cleaning existing observatories ---------------------------------")
        for obs_def in OBSERVATORIES:
            oid = obs_def["observatory_id"]
            result = await client.delete_observatory(oid)
            if result.is_ok:
                print(f"  OK  Deleted {oid}")
            else:
                # A 404 (not found) is perfectly normal — just skip it.
                print(f"  --  Not found or already deleted: {oid}")

    # ── Seed each observatory ─────────────────────────────────────────────────
    for obs_def in OBSERVATORIES:
        obs_key = obs_def["observatory_id"]
        print(f"\n--- Observatory: {obs_def['title']}")

        # ── Step 1: Setup observatory ────────────────────────────────────────
        # setup_observatory() creates the observatory in a DISABLED state and
        # returns a task_id for the background setup task. The observatory is
        # NOT visible to public users until that task is completed in Step 6.
        # The client automatically injects `user_id` into the request payload,
        # so we don't need to pass it manually here.
        setup_resp = _ok(
            await client.setup_observatory(DTO.ObservatorySetupDTO(
                observatory_id = obs_key,
                title          = obs_def["title"],
                description    = obs_def["description"],
                image_url      = obs_def["image_url"] or "",
                metadata       = obs_def["metadata"],
            )),
            "observatory setup",
        )
        # setup_resp is an ObservatorySetupResponseDTO with observatory_id and task_id.
        obs_id  = setup_resp.observatory_id
        task_id = setup_resp.task_id
        print(f"  OK  Observatory created (disabled)  id={obs_id}")
        print(f"  OK  Setup task queued               task_id={task_id}")

        # ── Step 2: Bulk-create and link catalogs ────────────────────────────
        # Each observatory type has a different set of catalog dimensions
        # (e.g. obs_mortalidad uses age_group, obs_cronicas uses derechohabiencia).
        # We build all required catalog dicts from the CATALOG_BUILDERS map
        # and send them in a single request.
        catalog_labels = OBS_CATALOG_SETS[obs_key]
        catalog_dtos   = [CATALOG_BUILDERS[lbl]() for lbl in catalog_labels]

        # bulk_assign_catalogs() accepts a plain dict matching BulkCatalogsDTO's schema.
        # Returns BulkCatalogsResponseDTO with observatory_id and catalog_ids list.
        bulk_cats = _ok(
            await client.bulk_assign_catalogs(obs_id, {"catalogs": catalog_dtos}),
            "bulk catalogs",
        )
        catalog_ids      = bulk_cats.catalog_ids
        # Map label -> catalog_id so we can fetch each catalog individually in Step 3.
        label_to_cat_id  = dict(zip(catalog_labels, catalog_ids))
        print(f"  OK  {len(catalog_ids)} catalogs created and linked")

        # ── Step 3: Fetch catalogs to retrieve item IDs ──────────────────────
        # The bulk endpoint returns only the top-level catalog IDs. To tag products
        # (Step 4), we need the individual catalog_item_id values. get_catalog()
        # returns a CatalogResponseDTO with a nested item tree.
        label_to_item_ids: Dict[str, List[str]] = {}
        for label, cat_id in label_to_cat_id.items():
            cat_resp = _ok(
                await client.get_catalog(cat_id),
                f"fetch catalog '{label}'",
            )
            # extract_item_ids walks .items recursively — the spatial catalog
            # has a country -> state two-level tree.
            label_to_item_ids[label] = extract_item_ids(cat_resp.items)
        print(f"  OK  Catalog item IDs fetched for product tagging")

        # ── Step 4: Bulk-create and link products ────────────────────────────
        # Each product is tagged with up to 5 item IDs from each of its
        # referenced catalogs. Limiting to 5 keeps tag lists focused;
        # real data loads would typically use all items or filter selectively.
        products_payload: List[Dict] = []
        for prod in PRODUCTS_BY_OBS[obs_key]:
            item_ids: List[str] = []
            for cat_label in prod["tag_catalogs"]:
                # Take up to 5 items per referenced catalog dimension.
                item_ids.extend(label_to_item_ids.get(cat_label, [])[:5])
            products_payload.append({
                "product_id":       prod["product_id"],
                "name":             prod["name"],
                "description":      prod["description"],
                "catalog_item_ids": item_ids,
            })

        # bulk_assign_products() accepts a plain dict matching BulkProductsDTO.
        # Returns BulkProductsResponseDTO with observatory_id and products list.
        bulk_prods = _ok(
            await client.bulk_assign_products(obs_id, {"products": products_payload}),
            "bulk products",
        )
        # bulk_prods.products is a List[BulkProductCreatedDTO] with product_id and name.
        created_products = bulk_prods.products
        print(f"  OK  {len(created_products)} products created and linked")

        # ── Step 5: Upload a chart file to each product ──────────────────────
        # Products carry an HTML chart (heatmap for geographic views, radar for
        # multi-dimensional views). upload_product() sends the file as
        # multipart/form-data and returns a dict with a job_id on success.
        print(f"  -- Uploading chart files ...")
        for prod_def, created in zip(PRODUCTS_BY_OBS[obs_key], created_products):
            pid      = created.product_id
            src_file = HEATMAP_FILE if prod_def["chart"] == "heatmap" else RADAR_FILE

            # upload_product() reads the file, wraps it in multipart, and POSTs
            # to /products/{pid}/upload. It returns Result[dict, Exception].
            upload_resp = _ok(
                await client.upload_product(pid, str(src_file)),
                f"upload for product '{pid}'",
            )
            job_id = upload_resp.get("job_id", "n/a")
            print(f"    -> {prod_def['name'][:40]:<40} [{src_file.name}] job_id={job_id}")

        # ── Step 6: Complete the setup task — enables the observatory ────────
        # Calling complete_task() with success=True signals the API to flip the
        # observatory's `disabled` flag to False, making it publicly queryable.
        # This is the last step of the two-phase provisioning pattern.
        complete_resp = _ok(
            await client.complete_task(task_id, DTO.TaskCompleteDTO(
                success = True,
                message = "Observatory seeded via seed_client.py.",
            )),
            "complete task",
        )
        # complete_resp is a TaskCompleteResponseDTO with an observatory_enabled bool.
        print(f"  OK  Task completed — observatory enabled: {complete_resp.observatory_enabled}")

    print("\n--- Done ----------------------------------------------------------------")
    print("  All observatories, catalogs, products, and files created via JubClient.")
    print(f"  API: {api_url}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed JUB via the async JubClient Python wrapper.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    # Note: JubClient appends /api/v2 to the base URL — do NOT include it here.
    parser.add_argument("--api-url",    default="http://localhost:5000",
                        help="Base URL of the JUB API (without /api/v2).")
    parser.add_argument("--username",   default="invitado",  help="Auth username.")
    parser.add_argument("--password",   default="invitado",  help="Auth password.")
    parser.add_argument("--scope",      default="jub",       help="Auth scope.")
    parser.add_argument("--clean",      action="store_true",
                        help="Delete existing observatories before seeding.")
    parser.add_argument("--signup",     action="store_true",
                        help="Create the user account before logging in.")
    parser.add_argument("--email",      default="invitado@example.com",
                        help="Email address (only used with --signup).")
    parser.add_argument("--first-name", default="Invitado",
                        help="First name (only used with --signup).")
    parser.add_argument("--last-name",  default="JUB",
                        help="Last name (only used with --signup).")
    args = parser.parse_args()

    print("JUB Client Seed Script")
    print(f"  api-url  : {args.api_url}")
    print(f"  username : {args.username}")
    print(f"  signup   : {args.signup}")
    print()

    asyncio.run(seed(
        api_url    = args.api_url,
        username   = args.username,
        password   = args.password,
        scope      = args.scope,
        signup     = args.signup,
        email      = args.email,
        first_name = args.first_name,
        last_name  = args.last_name,
        clean      = args.clean,
    ))


if __name__ == "__main__":
    main()
