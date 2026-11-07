import calendar
import json
import math
import zipfile

import numpy as np
import pytest
from climate.config import ROOT

from pipelines.imagery import pc_id, sensor_mask
from pipelines.science import (
    annual_rainfall,
    annual_temperature,
    decade_comparison,
    monthly_rain_total,
    valid_number,
    validate_power,
)


def test_all_supplied_power_values_and_annual_aggregation():
    count = 0
    with zipfile.ZipFile(ROOT / "climate_data.zip") as archive:
        filenames = [
            n
            for n in archive.namelist()
            if n.startswith("climate_data/raw_nasa_power/NASA_POWER_") and n.endswith(".json")
        ]
        assert len(filenames) == 12
        for filename in filenames:
            result = validate_power(json.loads(archive.read(filename)))
            assert len(result["monthly_keys"]) == 540
            assert len(result["annual_keys"]) == 45
            assert all(item["complete"] for item in result["annual"])
            count += result["numeric_values"]
        assert count == 35100


def test_bhola_and_barishal_preserve_identical_values():
    with zipfile.ZipFile(ROOT / "climate_data.zip") as archive:
        a = json.loads(archive.read("climate_data/raw_nasa_power/NASA_POWER_bhola.json"))
        b = json.loads(archive.read("climate_data/raw_nasa_power/NASA_POWER_barishal.json"))
    assert a["properties"]["parameter"] == b["properties"]["parameter"]
    assert a["geometry"]["coordinates"] != b["geometry"]["coordinates"]


def test_annual_temperature_weights_leap_month_and_excludes_month13():
    monthly = {f"2024{month:02}": float(month) for month in range(1, 13)}
    monthly["202413"] = 1000
    result = annual_temperature(monthly)
    expected = sum(month * calendar.monthrange(2024, month)[1] for month in range(1, 13)) / 366
    assert result == [{"year": 2024, "value": expected, "complete": True}]
    assert not math.isclose(expected, 6.5)


@pytest.mark.parametrize(
    "year,month,unit,expected", [(2024, 2, "mm/hr", 696), (2023, 2, "mm/hr", 672), (2025, 4, "mm/day", 30)]
)
def test_precipitation_calendar_conversion(year, month, unit, expected):
    assert monthly_rain_total(1, year, month, unit) == expected


def test_missing_values_never_become_zero():
    assert valid_number(-999) is None
    assert valid_number(float("nan")) is None
    assert valid_number(0) == 0
    monthly = {f"2025{m:02}": 20 for m in range(1, 13)}
    monthly["202502"] = None
    assert annual_temperature(monthly)[0]["value"] is None
    assert monthly_rain_total(None, 2025, 2, "mm/hr") is None


def test_partial_rainfall_year_is_not_an_annual_total():
    monthly = [{"date": f"2025-{m:02}-01", "value": 30.0} for m in range(1, 10)]
    assert annual_rainfall(monthly) == [{"year": 2025, "value": None, "complete": False}]
    complete = [{"date": f"2024-{m:02}-01", "value": 30.0} for m in range(1, 13)]
    assert annual_rainfall(complete)[0]["value"] == 360
    with pytest.raises(ValueError, match="Duplicate"):
        annual_rainfall(complete + [complete[0]])


def test_decade_comparison_requires_every_year():
    data = [
        {"year": year, "value": 20 if year <= 2010 else 21, "complete": True} for year in range(2001, 2026)
    ]
    result = decade_comparison(data)
    assert result["difference"] == 1
    assert result["baseline_period"] == "2001–2010"
    assert decade_comparison([x for x in data if x["year"] != 2005]) is None
    with pytest.raises(ValueError, match="Duplicate"):
        decade_comparison(data + [data[0]])


def test_sensor_qa_keeps_water_and_distinguishes_cirrus():
    qa = np.array([[0, 128, 4, 8, 16, 32, 1, 2]], dtype=np.uint16)
    saturation = np.zeros_like(qa)
    assert sensor_mask(qa, saturation, True).tolist() == [
        [True, True, False, False, False, False, False, False]
    ]
    assert sensor_mask(qa, saturation, False)[0, 2]
    saturation[0, 0] = 2
    assert not sensor_mask(qa, saturation, True)[0, 0]


def test_official_mirror_item_mapping():
    assert pc_id("LC08_L2SP_137044_20250208_20250214_02_T1_SR") == "LC08_L2SP_137044_20250208_02_T1"
