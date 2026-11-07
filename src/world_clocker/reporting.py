import json
from pathlib import Path


def render(reports: list[dict], manifests: list[dict], destination: Path) -> None:
    try:
        import matplotlib
    except ImportError as exc:
        raise ValueError("Install world-clocker[plots] to generate static reports") from exc

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    conditions = {
        (
            item["plan_hash"],
            item["scenario_hash"],
            item["generator_hash"],
            item["settings"]["distance"],
            item["settings"]["stability"],
            item["settings"]["temperature"],
            item["settings"]["top_p"],
            item["settings"]["max_tokens"],
            item["settings"]["send_seed"],
        )
        for item in manifests
    }
    if len(conditions) != 1:
        raise ValueError("Comparison requires matching plans, sampling controls and thresholds")
    if any(
        not report["metrics"]
        or report["coverage"]["recorded"] != report["coverage"]["planned"]
        or report["coverage"]["excluded_configurations"]
        for report in reports
    ):
        raise ValueError(
            "Plots require finished runs with valid base and paraphrase cells for every prompt."
        )
    destination.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(13, 4), layout="constrained")
    agreements = []
    colors = []
    for report in reports:
        metrics = report["metrics"]
        label = f"{report['model']} ({report['run_id'][:6]})"
        eigenvalues = metrics["covariance_eigenvalues"]
        axes[0].plot(range(1, len(eigenvalues) + 1), eigenvalues, marker=".", label=label)
        saturation = metrics["saturation"]
        x = saturation["candidates"]
        (line,) = axes[1].step(x, saturation["discovered"], where="post", label=label)
        lower, upper = zip(*saturation["order_sensitivity_95"], strict=True)
        axes[1].fill_between(x, lower, upper, step="post", color=line.get_color(), alpha=0.15)
        agreements.append([item["repeat_agreement"] for item in metrics["stability"].values()])
        colors.append(line.get_color())
    axes[2].hist(agreements, bins=[i / 10 for i in range(11)], color=colors, rwidth=0.85)
    axes[0].set(xlabel="Component", ylabel="Covariance eigenvalue", title="Behavioral spectrum")
    axes[1].set(xlabel="Candidates considered", ylabel="Repertoire size", title="Discovery")
    axes[2].set(xlabel="Repeat agreement", ylabel="Configurations", title="Stability")
    axes[0].legend()
    fig.savefig(destination / "behavior.png", dpi=160)
    plt.close(fig)
    (destination / "profile.json").write_text(
        json.dumps(reports, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
