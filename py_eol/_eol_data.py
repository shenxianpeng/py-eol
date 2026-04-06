import datetime

PYTHON_VERSIONS = {
    "3.16": {
        "eol_date": datetime.date(2032, 10, 31),
    },
    "3.15": {
        "eol_date": datetime.date(2031, 10, 31),
    },
    "3.14": {
        "eol_date": datetime.date(2030, 10, 31),
    },
    "3.13": {
        "eol_date": datetime.date(2029, 10, 31),
    },
    "3.12": {
        "eol_date": datetime.date(2028, 10, 31),
    },
    "3.11": {
        "eol_date": datetime.date(2027, 10, 31),
    },
    "3.10": {
        "eol_date": datetime.date(2026, 10, 31),
    },
    "3.9": {
        "eol_date": datetime.date(2025, 10, 31),
    },
    "3.8": {
        "eol_date": datetime.date(2024, 10, 7),
    },
    "3.7": {
        "eol_date": datetime.date(2023, 6, 27),
    },
    "3.6": {
        "eol_date": datetime.date(2021, 12, 23),
    },
    "3.5": {
        "eol_date": datetime.date(2020, 9, 30),
    },
    "3.4": {
        "eol_date": datetime.date(2019, 3, 18),
    },
    "3.3": {
        "eol_date": datetime.date(2017, 9, 29),
    },
    "3.2": {
        "eol_date": datetime.date(2016, 2, 20),
    },
    "2.7": {
        "eol_date": datetime.date(2020, 1, 1),
    },
    "3.1": {
        "eol_date": datetime.date(2012, 4, 9),
    },
    "3.0": {
        "eol_date": datetime.date(2009, 6, 27),
    },
    "2.6": {
        "eol_date": datetime.date(2013, 10, 29),
    },
}

EOL_DATES = {k: v["eol_date"] for k, v in PYTHON_VERSIONS.items()}
