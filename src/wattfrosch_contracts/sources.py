"""SOURCES catalog and translation maps per README §4–§6.

SOURCES defines the data sources (name, license, url). The two translation
maps translate internal keys to source-specific external keys:

- SOURCE_METRIC_MAP: source -> {internal metric key -> external metric key}
- SOURCE_REGION_MAP: source -> {internal region code -> external region code}

The maps are deliberately NOT part of METRICS/REGIONS, so the catalogs stay
clean. SOURCE_REGION_MAP needs no time logic — region history lives in
REGIONS (SCD Type 2), one entry per internal code is enough.

The maps are v1 stubs filled with what is known. The smard metric filters come
from the SMARD API readme (numeric filter IDs, e.g. 1223 = Braunkohle); the
day-ahead price filter 4169 is documented separately from that readme.
"""

from collections.abc import Mapping
from typing import Final

from pydantic import BaseModel, ConfigDict, model_validator

from wattfrosch_contracts import errors


class SourceEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    license: str
    url: str

    @model_validator(mode="after")
    def _validate_url(self) -> "SourceEntry":
        if not self.url.startswith("https://"):
            raise errors.source_url_not_https_error(self.name, self.url)
        return self


def _entry(
    name: str,
    license: str,
    url: str,
) -> SourceEntry:
    return SourceEntry(name=name, license=license, url=url)


SOURCES: Final[Mapping[str, SourceEntry]] = {
    entry.name: entry
    for entry in (
        _entry("energy-charts", "CC BY 4.0", "https://api.energy-charts.info"),
        _entry("smard", "CC BY 4.0", "https://www.smard.de"),
        _entry("open-meteo", "CC BY 4.0", "https://open-meteo.com"),
    )
}

# smard metric filters from the SMARD API readme; price filter 4169 is
# documented separately. Weather metrics are not covered by smard.
SOURCE_METRIC_MAP: Final[Mapping[str, Mapping[str, str]]] = {
    # energy-charts uses the same key names as the internal metric keys.
    "energy-charts": {
        key: key
        for key in (
            "generation.biomass",
            "generation.gas",
            "generation.hard_coal",
            "generation.hydro",
            "generation.lignite",
            "generation.nuclear",
            "generation.oil",
            "generation.other",
            "generation.other_renewable",
            "generation.pumped_storage",
            "generation.solar",
            "generation.wind_offshore",
            "generation.wind_onshore",
            "consumption.load",
            "consumption.residual_load",
            "consumption.pumped_storage",
            "price.day_ahead",
        )
    },
    # open-meteo uses its raw API variable names for the weather metrics.
    "open-meteo": {
        "weather.temperature_2m": "temperature_2m",
        "weather.wind_speed_10m": "wind_speed_10m",
        "weather.precipitation": "precipitation",
        "weather.cloud_cover": "cloud_cover",
    },
    # SMARD API readme filter IDs; 4169 (price) supplied outside the readme.
    "smard": {
        "generation.lignite": "1223",
        "generation.nuclear": "1224",
        "generation.wind_offshore": "1225",
        "generation.hydro": "1226",
        "generation.other": "1227",
        "generation.other_renewable": "1228",
        "generation.biomass": "4066",
        "generation.wind_onshore": "4067",
        "generation.solar": "4068",
        "generation.hard_coal": "4069",
        "generation.pumped_storage": "4070",
        "generation.gas": "4071",
        "consumption.load": "410",
        "consumption.residual_load": "4359",
        "consumption.pumped_storage": "4387",
        "price.day_ahead": "4169",
    },
}

# energy-charts uses lowercase zone ids; open-meteo takes "lat,lon" strings.
# Weather points are not covered by smard; bidding zones not by open-meteo.
SOURCE_REGION_MAP: Final[Mapping[str, Mapping[str, str]]] = {
    "smard": {
        "DE-AT-LU": "DE-AT-LU",
        "DE-LU": "DE-LU",
    },
    "energy-charts": {
        "DE-AT-LU": "de-at-lu",
        "DE-LU": "de-lu",
    },
    "open-meteo": {
        "DE-BERLIN": "52.52,13.405",
        "DE-HAMBURG": "53.551,9.993",
        "DE-KOELN": "50.937,6.96",
        "DE-MUENCHEN": "48.137,11.575",
    },
}
