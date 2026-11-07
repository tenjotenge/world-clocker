import json
from dataclasses import asdict
from importlib.resources import files
from math import log
from statistics import mean

import numpy as np

from .calibration import Calibration
from .metrics import analyze, packing

SCORING_VERSION = 1


def city_catalog() -> dict:
    resource = files("world_clocker").joinpath("data", "cities-v1.json")
    return json.loads(resource.read_text(encoding="utf-8"))


def closest_city(population: int, entries: list[dict]) -> dict:
    target = log(population)
    return min(
        entries,
        key=lambda city: (abs(log(city["population"]) - target), city["city"], city["country"]),
    )


def condition_repertoire(
    metrics: dict,
    candidates: set[str],
    distances: dict,
    threshold: float,
) -> tuple[list[str], list[str]]:
    representatives = {}
    for name, halves in zip(
        metrics["configurations"],
        metrics["repeat_half_probabilities"],
        strict=True,
    ):
        if name not in candidates or not metrics["stability"][name]["passes_gate"]:
            continue
        fingerprint = tuple(value for half in halves for family in half for value in family)
        representatives.setdefault(fingerprint, name)
    order = [representatives[key] for key in sorted(representatives)]
    return packing(order, set(order), distances, threshold)[0], order


def city_equivalent(manifest: dict, raw: dict, catalog: dict) -> dict:
    settings = manifest["settings"]
    coverage = raw["coverage"]
    metrics = raw["metrics"]
    calibration = Calibration(**settings.get("calibration", {}))
    total = coverage["planned"]
    valid_fraction = coverage["valid"] / total if total else 0
    result = {
        "status": "uncalibrated",
        "confidence": "insufficient-evidence",
        "scoring_version": SCORING_VERSION,
        "calibration": asdict(calibration),
        "city_catalog_version": catalog["version"],
        "city_boundary_policy": catalog["boundary_policy"],
        "aspirational_tiers": catalog["aspirational_tiers"],
        "formula": "max(0, weak_repertoire - 1) / (reference_repertoire - 1)",
        "population_mapping": "minimum_population * (reference_population / minimum_population)^normalized_complexity",
        "interpretation": "Metaphorical complexity index, not a human simulation capacity estimate.",
        "weights": {"stable_weak_repertoire": 1, "descriptive_rank": 0, "entropy": 0},
        "normalized_complexity": None,
        "equivalent_population": None,
        "closest_city": None,
        "population_order_sensitivity_95": None,
        "condition_diagnostics": {},
        "valid_fraction": valid_fraction,
        "warnings": [],
    }
    reasons = result["warnings"]
    if manifest["benchmark_version"] != "0.2.0":
        reasons.append("Population calibration requires the v0.2 factorial pilot.")
        return result
    if metrics is None or coverage["recorded"] != total:
        reasons.append("Population calibration requires a finished run with scorable data.")
        return result

    distances = {
        (pair["left"], pair["right"]): min(pair["replicated_discovery"], pair["replicated_heldout"])
        for pair in metrics["distances"]
    }
    configs = manifest["configurations"]
    packs = {}
    for condition, expected in (("weak", 48), ("strong", 48), ("neutral", 4)):
        planned = {name for name, config in configs.items() if config["source"] == condition}
        pack, order = condition_repertoire(metrics, planned, distances, settings["distance"])
        packs[condition] = (pack, order)
        scored = [
            metrics["stability"][name] for name in metrics["configurations"] if name in planned
        ]
        result["condition_diagnostics"][condition] = {
            "planned": len(planned),
            "scored": len(scored),
            "stable_repertoire": len(pack),
            "stable_configurations": sum(item["passes_gate"] for item in scored),
            "mean_repeat_agreement": mean(item["repeat_agreement"] for item in scored)
            if scored
            else None,
        }
        if len(planned) != expected or len(scored) < (36 if expected == 48 else 2):
            reasons.append(f"Insufficient {condition} condition coverage.")

    if len(manifest["scenarios"]) != 30 or settings["repeats"] < 4:
        reasons.append("Calibration requires 30 probes and at least four repetitions.")
    if valid_fraction < 0.95:
        reasons.append("Fewer than 95% of planned responses produced valid decisions.")
    if settings["distance"] < 0.2 or settings["stability"] < 0.8:
        reasons.append("Calibration requires distance >= 0.2 and stability >= 0.8.")
    if reasons:
        return result

    pack, order = packs["weak"]
    rng = np.random.default_rng(settings["seed"])
    stable = set(order)
    counts = [
        len(packing(rng.permutation(order).tolist(), stable, distances, settings["distance"])[0])
        for _ in range(settings["bootstrap"])
    ]
    band = np.percentile(counts, [2.5, 97.5], method="nearest").astype(int).tolist()
    count = len(pack)
    population = calibration.population(count)
    city = closest_city(population, catalog["entries"])
    result.update(
        status="provisional",
        confidence="synthetic-control" if settings["provider"] == "mock" else "exploratory",
        normalized_complexity=calibration.normalized(count),
        equivalent_population=population,
        closest_city=city,
        population_order_sensitivity_95=[calibration.population(value) for value in band],
        weak_repertoire=pack,
    )
    if count > calibration.reference_repertoire:
        reasons.append("Population extrapolates above the upper calibration anchor.")
    if population < min(entry["population"] for entry in catalog["entries"]) or population > max(
        entry["population"] for entry in catalog["entries"]
    ):
        reasons.append("Population lies outside the reference catalog. The city is an endpoint.")
    return result


def capacity_profile(manifest: dict, rows: list[dict]) -> dict:
    raw = analyze(manifest, rows)
    fingerprints = {
        fingerprint
        for row in rows
        if isinstance(fingerprint := row.get("metadata", {}).get("system_fingerprint"), str)
    }
    metadata = raw["model_metadata"]
    return {
        "profile_version": 1,
        "model_version": metadata.get("version") or metadata.get("revision"),
        "observed_system_fingerprints": sorted(fingerprints),
        **raw,
        "city_equivalent": city_equivalent(manifest, raw, city_catalog()),
    }


def profile_text(profile: dict) -> str:
    score = profile["city_equivalent"]
    city = score["closest_city"]
    population = score["equivalent_population"]
    coverage = profile["coverage"]
    metrics = profile["metrics"]
    stability = list(metrics["stability"].values()) if metrics else []
    average = mean(item["repeat_agreement"] for item in stability) if stability else None
    lines = [
        "World-Clocker Model World Capacity Profile",
        f"Model: {profile['model']} (version {profile['model_version'] or 'unreported'})",
        f"Benchmark: {profile['benchmark_version']}",
        f"Equivalent population: {population:,}"
        if population is not None
        else "Equivalent population: uncalibrated",
        (
            f"Closest city: {city['city']}, {city['country']} "
            f"({city['population']:,}, {city['geography']}, {city['year']})"
            if city
            else "Closest city: uncalibrated"
        ),
        f"Score status: {score['status']}",
        f"Confidence: {score['confidence']}",
        f"Behavioral effective rank: {metrics['effective_rank']:.3f}"
        if metrics
        else "Behavioral effective rank: unavailable",
        f"Stable repertoire: {metrics['repertoire_size']}"
        if metrics
        else "Stable repertoire: unavailable",
        f"Stability (mean repeat agreement): {average:.1%}"
        if average is not None
        else "Stability (mean repeat agreement): unavailable",
        f"Coverage: {coverage['valid']:,} valid / {coverage['planned']:,} planned "
        f"({coverage['recorded']:,} recorded)",
        f"Scoring v{score['scoring_version']} / calibration v{score['calibration']['version']} "
        f"/ city catalog v{score['city_catalog_version']}",
    ]
    if city:
        lines.append(f"City source: {city['source']}")
        lines.append(f"Reference boundaries: {score['city_boundary_policy']}")
        weak = score["condition_diagnostics"]["weak"]["stable_repertoire"]
        lines.append(f"Stable weak-prompt repertoire used in score: {weak}")
    if score["population_order_sensitivity_95"] is not None:
        lower, upper = score["population_order_sensitivity_95"]
        lines.append(f"Population order sensitivity (95%): {lower:,} to {upper:,}")
    if metrics:
        lower, upper = metrics["family_bootstrap_95"]["repeat_agreement"]
        lines.append(f"Stability family-bootstrap interval (95%): {lower:.1%} to {upper:.1%}")
    lines.extend(f"Note: {warning}" for warning in score["warnings"])
    lines.append("Equivalent population is a metaphorical complexity index.")
    return "\n".join(lines)
