from collections import Counter, defaultdict
from itertools import combinations

import numpy as np


def entropy(probabilities: np.ndarray) -> np.ndarray:
    safe = np.where(probabilities > 0, probabilities, 1)
    return -(probabilities * np.log2(safe)).sum(axis=-1)


def spectrum(matrix: np.ndarray) -> tuple[list[float], float, float]:
    if len(matrix) < 2:
        return [], 0.0, 0.0
    centered = matrix - matrix.mean(axis=0)
    values = np.linalg.svd(centered, compute_uv=False) ** 2 / (len(matrix) - 1)
    total = values.sum()
    if total == 0:
        return values.tolist(), 0.0, 0.0
    weights = values / total
    return values.tolist(), float(2 ** entropy(weights)), float(1 / np.sum(weights**2))


def packing(order: list[str], stable: set[str], distances: dict, epsilon: float) -> tuple:
    accepted = []
    curve = []
    for candidate in order:
        if candidate in stable and all(
            distances[tuple(sorted((candidate, other)))] >= epsilon for other in accepted
        ):
            accepted.append(candidate)
        curve.append(len(accepted))
    return accepted, curve


def analyze(manifest: dict, rows: list[dict]) -> dict:
    settings = manifest["settings"]
    probes = manifest["scenarios"]
    families = sorted({probe["family"] for probe in probes.values()})
    discovery = [
        i for i, family in enumerate(families) if probes[f"{family}-base"]["split"] == "discovery"
    ]
    heldout = [i for i in range(len(families)) if i not in discovery]
    configs = sorted(manifest["configurations"])
    data = defaultdict(list)
    for row in rows:
        if row["decision"] is not None:
            data[row["configuration"], row["scenario"]].append((row["repeat"], row["decision"]))
    primary_probes = [
        probe for probe, item in probes.items() if item["variant"] != "counterfactual"
    ]
    usable = [
        config
        for config in configs
        if all(len(data[config, probe]) == settings["repeats"] for probe in primary_probes)
    ]
    errors = Counter(row["error"]["kind"] for row in rows if row["error"])
    output = {
        "metric_version": 1,
        "run_id": manifest["run_id"],
        "model": manifest["model"],
        "plan_hash": manifest["plan_hash"],
        "benchmark_version": manifest["benchmark_version"],
        "model_metadata": manifest["model_metadata"],
        "scenario_hash": manifest["scenario_hash"],
        "generator_hash": manifest["generator_hash"],
        "inference_settings": {
            key: settings[key]
            for key in (
                "provider",
                "repeats",
                "seed",
                "temperature",
                "top_p",
                "max_tokens",
                "send_seed",
            )
        },
        "distance_threshold": settings["distance"],
        "stability_threshold": settings["stability"],
        "coverage": {
            "planned": len(manifest["plan"]),
            "recorded": len(rows),
            "valid": sum(len(values) for values in data.values()),
            "errors": dict(errors),
            "excluded_configurations": sorted(set(configs) - set(usable)),
            "parse_failure_rate": errors["parse"] / len(rows) if rows else None,
        },
    }
    if not usable:
        return dict(output, metrics=None)
    trials = np.array(
        [
            [
                [
                    [action for _, action in sorted(data[config, f"{family}-{variant}"])]
                    for variant in ("base", "paraphrase")
                ]
                for family in families
            ]
            for config in usable
        ]
    )
    ordinary = trials.mean(axis=-1)
    # Each base and paraphrase is weighted equally within its scenario family.
    feature = ordinary.reshape(len(usable), -1)
    eigenvalues, rank, ratio = spectrum(feature)
    within = entropy(np.stack([1 - feature, feature], axis=-1)).mean()
    per_probe = feature.mean(axis=0)
    pooled = entropy(np.stack([1 - per_probe, per_probe], axis=-1)).mean()
    overall = per_probe.mean()
    total_entropy = entropy(np.array([1 - overall, overall]))
    repeats = settings["repeats"]
    repeat_agreement = ((ordinary**2 + (1 - ordinary) ** 2) * repeats - 1) / (repeats - 1)
    paraphrase = ordinary[:, :, 0] * ordinary[:, :, 1] + (
        (1 - ordinary[:, :, 0]) * (1 - ordinary[:, :, 1])
    )
    stable = {
        config
        for i, config in enumerate(usable)
        if min(
            repeat_agreement[i, discovery].mean(),
            repeat_agreement[i, heldout].mean(),
            paraphrase[i, discovery].mean(),
            paraphrase[i, heldout].mean(),
        )
        >= settings["stability"]
    }
    distances = {}
    pairwise = []
    # Use both splits and require a consistent directional difference in each repeat half.
    halves = [trials[:, :, :, : repeats // 2], trials[:, :, :, repeats // 2 :]]
    first, second = [half.mean(axis=-1) for half in halves]
    for i, j in combinations(range(len(usable)), 2):
        a, b = first[i] - first[j], second[i] - second[j]
        replicated = np.where(a * b > 0, np.minimum(abs(a), abs(b)), 0)
        in_sample = float(replicated[discovery].mean())
        out_sample = float(replicated[heldout].mean())
        pair = (usable[i], usable[j])
        distances[pair] = min(in_sample, out_sample)
        pairwise.append(
            {
                "left": pair[0],
                "right": pair[1],
                "mean_total_variation": float(abs(ordinary[i] - ordinary[j]).mean()),
                "replicated_discovery": in_sample,
                "replicated_heldout": out_sample,
            }
        )

    counterfactuals = {}
    for i, config in enumerate(usable):
        shifts = []
        for j, family in enumerate(families):
            cell = data[config, f"{family}-counterfactual"]
            if len(cell) == repeats:
                probability = sum(action for _, action in cell) / repeats
                shifts.append(abs(ordinary[i, j, 0] - probability))
        counterfactuals[config] = {
            "counterfactual_mean_absolute_shift": float(np.mean(shifts)) if shifts else None,
            "counterfactual_families_scored": len(shifts),
        }

    rng = np.random.default_rng(settings["seed"])
    accepted, curve = packing(usable, stable, distances, settings["distance"])
    order_curves = []
    ranks = []
    agreements = []
    for _ in range(settings["bootstrap"]):
        order = rng.permutation(usable).tolist()
        order_curves.append(packing(order, stable, distances, settings["distance"])[1])
        sampled = np.concatenate(
            [
                rng.choice(discovery, len(discovery)),
                rng.choice(heldout, len(heldout)),
            ]
        )
        ranks.append(spectrum(ordinary[:, sampled].reshape(len(usable), -1))[1])
        agreements.append(float(repeat_agreement[:, sampled].mean()))

    def interval(values: list) -> list:
        return np.percentile(values, [2.5, 97.5], axis=0).T.tolist()

    return dict(
        output,
        metrics={
            "configurations": usable,
            "feature_order": [
                f"{family}-{variant}" for family in families for variant in ("base", "paraphrase")
            ],
            "choice_probabilities": feature.tolist(),
            "covariance_eigenvalues": eigenvalues,
            "effective_rank": rank,
            "participation_ratio": ratio,
            "entropy_bits": {
                "within_configuration_given_probe": float(within),
                "configuration_information_given_probe": float(pooled - within),
                "probe_information": float(total_entropy - pooled),
            },
            "stability": {
                config: {
                    "repeat_agreement": float(repeat_agreement[i].mean()),
                    "paraphrase_agreement": float(paraphrase[i].mean()),
                    **counterfactuals[config],
                    "passes_gate": config in stable,
                }
                for i, config in enumerate(usable)
            },
            "distances": pairwise,
            "repertoire": accepted,
            "repertoire_size": len(accepted),
            "saturation": {
                "candidates": list(range(1, len(usable) + 1)),
                "discovered": curve,
                "marginal_novelty": np.diff([0, *curve]).tolist(),
                "order_sensitivity_95": interval(order_curves),
            },
            "family_bootstrap_95": {
                "effective_rank": interval(ranks),
                "repeat_agreement": interval(agreements),
            },
        },
    )
