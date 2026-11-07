"""Unit-aware calculations. No trend significance or causal attribution."""

import calendar
import math
from statistics import mean


def valid_number(value, fill_value=-999.0):
    if value is None:
        return None
    value = float(value)
    return value if math.isfinite(value) and value != fill_value else None


def annual_temperature(monthly: dict[str, float | None]) -> list[dict]:
    years = sorted({int(key[:4]) for key in monthly if len(key) == 6 and 1 <= int(key[4:]) <= 12})
    annual = []
    for year in years:
        values = [
            (monthly.get(f"{year}{month:02}"), calendar.monthrange(year, month)[1]) for month in range(1, 13)
        ]
        complete = all(value is not None for value, _ in values)
        value = sum(v * days for v, days in values) / sum(days for _, days in values) if complete else None
        annual.append({"year": year, "value": value, "complete": complete})
    return annual


def monthly_rain_total(rate: float | None, year: int, month: int, unit: str) -> float | None:
    if rate is None:
        return None
    if rate < 0 or not math.isfinite(rate):
        raise ValueError("Invalid precipitation rate")
    factor = {"mm/hr": 24, "mm/day": 1}.get(unit)
    if factor is None:
        raise ValueError(f"Unsupported precipitation unit: {unit}")
    return rate * factor * calendar.monthrange(year, month)[1]


def annual_rainfall(monthly: list[dict]) -> list[dict]:
    years = sorted({int(x["date"][:4]) for x in monthly})
    indexed = {x["date"][:7]: x["value"] for x in monthly}
    if len(indexed) != len(monthly):
        raise ValueError("Duplicate precipitation month")
    result = []
    for year in years:
        values = [indexed.get(f"{year}-{month:02}") for month in range(1, 13)]
        complete = all(x is not None for x in values)
        result.append({"year": year, "value": sum(values) if complete else None, "complete": complete})
    return result


def decade_comparison(annual: list[dict], baseline=(2001, 2010), recent=(2016, 2025)) -> dict | None:
    indexed = {x["year"]: x["value"] for x in annual if x.get("complete", True) and x["value"] is not None}
    if len({x["year"] for x in annual}) != len(annual):
        raise ValueError("Duplicate annual observation")
    old = [indexed.get(year) for year in range(baseline[0], baseline[1] + 1)]
    new = [indexed.get(year) for year in range(recent[0], recent[1] + 1)]
    if len(old) != 10 or len(new) != 10 or any(x is None for x in old + new):
        return None
    return {
        "baseline_period": f"{baseline[0]}–{baseline[1]}",
        "recent_period": f"{recent[0]}–{recent[1]}",
        "baseline_value": mean(old),
        "recent_value": mean(new),
        "difference": mean(new) - mean(old),
    }


def validate_power(payload: dict, strict: bool = True) -> dict:
    parameters = payload["properties"]["parameter"]
    expected_units = {"T2M": "C", "T2M_MAX": "C", "T2M_MIN": "C", "RH2M": "%", "PRECTOTCORR": "mm/day"}
    for name, unit in expected_units.items():
        if payload["parameters"].get(name, {}).get("units") != unit:
            raise ValueError(f"Unexpected POWER units for {name}")
    fill = payload["header"].get("fill_value", -999)
    data = {
        name: {key: valid_number(value, fill) for key, value in values.items()}
        for name, values in parameters.items()
    }
    keys = sorted(data["T2M"])
    monthly_keys = [key for key in keys if 1 <= int(key[4:]) <= 12]
    annual_keys = [key for key in keys if int(key[4:]) == 13]
    if len(monthly_keys) + len(annual_keys) != len(keys):
        raise ValueError("Invalid POWER date key")
    if any(set(values) != set(keys) for values in data.values()):
        raise ValueError("POWER variables have mismatched dates")
    issues = []
    for key in monthly_keys:
        t, low, high, rh, rain = [
            data[name][key] for name in ["T2M", "T2M_MIN", "T2M_MAX", "RH2M", "PRECTOTCORR"]
        ]
        if None in [t, low, high, rh, rain]:
            issues.append("missing_values")
        elif not (low <= t <= high and 0 <= rh <= 100 and rain >= 0):
            raise ValueError(f"Invalid physical ordering/bounds at {key}")
    annual = annual_temperature({key: data["T2M"][key] for key in monthly_keys})
    if strict:
        if issues or any(not x["complete"] for x in annual):
            raise ValueError("Incomplete curated POWER data")
        for item in annual:
            official = data["T2M"].get(f"{item['year']}13")
            if official is None or abs(item["value"] - official) > 0.0050001:
                raise ValueError(f"Annual aggregation differs from NASA for {item['year']}")
    return {
        "data": data,
        "monthly_keys": monthly_keys,
        "annual_keys": annual_keys,
        "annual": annual,
        "issues": sorted(set(issues)),
        "numeric_values": sum(len(values) for values in data.values()),
    }
