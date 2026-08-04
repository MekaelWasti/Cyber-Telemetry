"""Create presentation-ready figures from the frozen Phase 5 analysis outputs."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results" / "analysis_v1"
FIGURES = RESULTS / "figures"

DATASET_LABELS = {
    "acme_process_telemetry": "ACME",
    "cic_ids_2017_ml_csv": "CIC-IDS2017",
    "unsw_nb15_raw": "UNSW-NB15",
}
COLORS = {
    "Recommend": "#2A9D8F",
    "Explore": "#E9C46A",
    "Abstain": "#8D99AE",
    "ACME": "#277DA1",
    "CIC-IDS2017": "#F9844A",
    "UNSW-NB15": "#43AA8B",
}


def setup_style() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": 220,
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titleweight": "bold",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": False,
        }
    )


def save(fig: plt.Figure, name: str) -> None:
    fig.tight_layout()
    fig.savefig(FIGURES / f"{name}.png", bbox_inches="tight", facecolor="white")
    fig.savefig(FIGURES / f"{name}.svg", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def intrinsic_selection(outcomes: pd.DataFrame) -> pd.DataFrame:
    return outcomes[
        (outcomes["score_kind"] == "intrinsic")
        & (outcomes["partition_id"].str.endswith("_selection"))
    ].copy()


def all_selection(outcomes: pd.DataFrame) -> pd.DataFrame:
    return outcomes[outcomes["partition_id"].str.endswith("_selection")].copy()


def outcome_counts(frame: pd.DataFrame) -> pd.DataFrame:
    counts = (
        frame.groupby(["dataset_id", "outcome"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=["Recommend", "Explore", "Abstain"], fill_value=0)
    )
    counts.index = counts.index.map(DATASET_LABELS)
    return counts.reindex(["ACME", "CIC-IDS2017", "UNSW-NB15"])


def plot_outcomes(counts: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    left = np.zeros(len(counts))
    for outcome in counts.columns:
        values = counts[outcome].to_numpy()
        ax.barh(
            counts.index,
            values,
            left=left,
            color=COLORS[outcome],
            label=outcome,
            height=0.58,
        )
        for y, (start, value) in enumerate(zip(left, values)):
            if value:
                ax.text(start + value / 2, y, str(int(value)), ha="center", va="center", fontweight="bold")
        left += values
    ax.set_xlabel("Number of intrinsic selection configurations (27 per dataset)")
    ax.set_title("No configuration cleared every recommendation gate", pad=48)
    ax.legend(ncol=3, frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.01))
    ax.set_xlim(0, 27)
    ax.invert_yaxis()
    save(fig, "01_outcome_counts")


def best_rows(frame: pd.DataFrame) -> pd.DataFrame:
    idx = frame.groupby("dataset_id")["median_average_precision"].idxmax()
    best = frame.loc[idx].copy()
    best["dataset"] = best["dataset_id"].map(DATASET_LABELS)
    best["method"] = best["representation"].str.replace("_", " ").str.title()
    best["scorer_label"] = best["scorer"].str.replace("_", " ").str.title()
    return best.set_index("dataset").reindex(["ACME", "CIC-IDS2017", "UNSW-NB15"]).reset_index()


def plot_best(best: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.8))
    colors = [COLORS[name] for name in best["dataset"]]
    ap = best["median_average_precision"].to_numpy()
    lift = best["precision_lift_at_100"].to_numpy()
    axes[0].bar(best["dataset"], ap, color=colors, width=0.62)
    axes[0].set_ylabel("Average precision")
    axes[0].set_title("Best global ranking result")
    axes[0].set_ylim(0, max(ap) * 1.18)
    for x, value in enumerate(ap):
        axes[0].text(x, value + max(ap) * 0.025, f"{value:.3f}", ha="center", fontweight="bold")
    axes[1].bar(best["dataset"], lift, color=colors, width=0.62)
    axes[1].axhline(2.0, color="#C23B22", linestyle="--", linewidth=1.5, label="2× utility threshold")
    axes[1].set_ylabel("Precision@100 lift over prevalence")
    axes[1].set_title("Top-100 analyst utility")
    axes[1].set_ylim(0, max(6.2, max(lift) * 1.15))
    axes[1].legend(frameon=False)
    for x, value in enumerate(lift):
        axes[1].text(x, value + 0.13, f"{value:.2f}×", ha="center", fontweight="bold")
    fig.suptitle("The strongest configuration changed with the dataset", fontsize=14, fontweight="bold", y=1.04)
    save(fig, "02_best_by_dataset")


def portability_long(portability: pd.DataFrame) -> pd.DataFrame:
    readable = {
        "dominant_trained_vs_untrained": "DOMINANT trained − untrained",
        "graphsage_observed_vs_permuted": "GraphSAGE observed − permuted",
        "graphsage_trained_knn_vs_raw_knn": "GraphSAGE kNN − raw kNN",
        "graphsage_trained_vs_random": "GraphSAGE trained − random",
        "matched_vs_intrinsic": "Signal transform − intrinsic",
        "node2vec_observed_vs_permuted": "Node2Vec observed − permuted",
        "raw_hdbscan_vs_raw_knn": "Raw HDBSCAN − raw kNN",
        "raw_isolation_forest_vs_raw_knn": "Raw Isolation Forest − raw kNN",
    }
    rows = []
    for record in portability.to_dict("records"):
        for item in json.loads(record["dataset_directions"]):
            rows.append(
                {
                    "comparison": readable[record["comparison_family"]],
                    "dataset": DATASET_LABELS[item["dataset_id"]],
                    "delta_ap": item["median_delta_ap"],
                }
            )
    return pd.DataFrame(rows)


def plot_comparisons(long: pd.DataFrame) -> None:
    order = list(dict.fromkeys(long["comparison"]))
    datasets = ["ACME", "CIC-IDS2017", "UNSW-NB15"]
    pivot = long.pivot(index="comparison", columns="dataset", values="delta_ap").reindex(index=order, columns=datasets)
    values = pivot.to_numpy()
    limit = max(abs(values.min()), abs(values.max()))
    fig, ax = plt.subplots(figsize=(9.5, 6.2))
    image = ax.imshow(values, cmap="RdBu", vmin=-limit, vmax=limit, aspect="auto")
    ax.set_xticks(range(len(datasets)), datasets)
    ax.set_yticks(range(len(order)), order)
    ax.set_title("Method advantage was context-dependent\nMedian difference in average precision; blue favors candidate")
    for y in range(values.shape[0]):
        for x in range(values.shape[1]):
            value = values[y, x]
            ax.text(x, y, f"{value:+.3f}", ha="center", va="center", color="white" if abs(value) > limit * 0.48 else "#202124", fontsize=9)
    cbar = fig.colorbar(image, ax=ax, shrink=0.82)
    cbar.set_label("Candidate AP − reference AP")
    save(fig, "03_method_control_deltas")


def plot_ap_vs_recall(frame: pd.DataFrame, best: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8.2, 5.6))
    for dataset, group in frame.groupby(frame["dataset_id"].map(DATASET_LABELS)):
        ax.scatter(
            group["median_average_precision"],
            group["median_recall_at_100"],
            s=45,
            alpha=0.62,
            color=COLORS[dataset],
            label=dataset,
            edgecolor="white",
            linewidth=0.4,
        )
    for row in best.itertuples():
        ax.scatter(row.median_average_precision, row.median_recall_at_100, s=150, marker="*", color=COLORS[row.dataset], edgecolor="#202124", linewidth=0.8)
        ax.annotate(row.dataset, (row.median_average_precision, row.median_recall_at_100), xytext=(6, 6), textcoords="offset points", fontsize=9, fontweight="bold")
    ax.set_xlabel("Average precision across the full ranking")
    ax.set_ylabel("Recall within first 100 reviews")
    ax.set_title("A strong global score did not guarantee useful top-ranked alerts")
    ax.set_xlim(left=-0.01)
    ax.set_ylim(-0.03, 1.03)
    ax.legend(frameon=False)
    save(fig, "04_ap_vs_recall100")


def write_tables(counts: pd.DataFrame, best: pd.DataFrame, long: pd.DataFrame) -> None:
    counts.to_csv(FIGURES / "table_outcome_counts.csv")
    best_table = best[
        [
            "dataset",
            "score_kind",
            "representation",
            "scorer",
            "hypothesis",
            "outcome",
            "median_average_precision",
            "median_recall_at_100",
            "median_precision_at_100",
            "prevalence",
            "precision_lift_at_100",
        ]
    ]
    best_table.to_csv(FIGURES / "table_best_by_dataset.csv", index=False)
    long.to_csv(FIGURES / "table_method_control_deltas.csv", index=False)

    lines = [
        "# Presentation-ready result tables",
        "",
        "Outcome counts cover intrinsic selection configurations. The best rows consider both intrinsic and matched scores, consistent with the Phase 5 report. No configuration reached `Recommend`; the best rows are `Explore`, not confirmed winners.",
        "",
        "## Outcome counts",
        "",
        "| Dataset | Recommend | Explore | Abstain |",
        "|---|---:|---:|---:|",
    ]
    for dataset, row in counts.iterrows():
        lines.append(f"| {dataset} | {row['Recommend']} | {row['Explore']} | {row['Abstain']} |")
    lines.extend(
        [
            "",
            "## Highest-AP selection configuration",
            "",
            "| Dataset | Score | Representation + scorer | Hypothesis | AP | Recall@100 | Precision@100 | Prevalence | Lift@100 | Status |",
            "|---|---|---|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in best.itertuples():
        method = f"{row.representation.replace('_', ' ')} + {row.scorer.replace('_', ' ')}"
        lines.append(
            f"| {row.dataset} | {row.score_kind} | {method} | {row.hypothesis} | {row.median_average_precision:.4f} | "
            f"{row.median_recall_at_100:.4f} | {row.median_precision_at_100:.4f} | "
            f"{row.prevalence:.4f} | {row.precision_lift_at_100:.2f}x | {row.outcome} |"
        )
    lines.extend(
        [
            "",
            "## Reading note",
            "",
            "The stars in Figure 4 identify the highest-AP configuration for each dataset. CIC-IDS2017 and UNSW-NB15 illustrate the central evaluation lesson: their highest-AP configurations retrieved no malicious items in the first 100 reviews.",
            "",
        ]
    )
    (FIGURES / "RESULT_TABLES.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    setup_style()
    FIGURES.mkdir(parents=True, exist_ok=True)
    outcomes = pd.read_csv(RESULTS / "outcomes.csv")
    portability = pd.read_csv(RESULTS / "portability_summary.csv")
    intrinsic = intrinsic_selection(outcomes)
    selection = all_selection(outcomes)
    counts = outcome_counts(intrinsic)
    best = best_rows(selection)
    long = portability_long(portability)
    plot_outcomes(counts)
    plot_best(best)
    plot_comparisons(long)
    plot_ap_vs_recall(selection, best)
    write_tables(counts, best, long)
    print(f"Wrote figures and tables to {FIGURES}")


if __name__ == "__main__":
    main()
