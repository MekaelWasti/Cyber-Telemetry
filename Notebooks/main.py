r"""AutoSignal analyst dashboard.

Run from the repository root with:
    C:\Python314\python.exe -m streamlit run Notebooks/main.py
"""

from __future__ import annotations

import io
import json
import sys
from html import escape
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
sys.path.insert(0, str(HERE))

from autosignal_engine import (
    ConfigValidationError,
    dataframe_profile,
    load_df_slice,
    run_autosignal,
)


DEFAULT_DATASET = REPO_ROOT / "Data" / "train-process_uber_summary.parquet"
DEFAULT_CONFIG = HERE / "sample_agent_config.json"
DEMO_LABEL_COLORS = {
    "benign": "#2563EB",
    "malicious": "#DC2626",
    "unknown": "#64748B",
}
DATAMAP_RESIZE_HANDLE = """
<div
  id="autosignal-resize-handle"
  title="Drag to resize the map"
  aria-label="Drag to resize the map"
></div>
"""
DATAMAP_RESIZE_CSS = """
#autosignal-resize-handle {
  position: fixed;
  right: 7px;
  bottom: 7px;
  width: 22px;
  height: 22px;
  z-index: 10000;
  cursor: nwse-resize;
  border-right: 4px solid #334155;
  border-bottom: 4px solid #334155;
  border-radius: 2px;
  box-sizing: border-box;
}
#autosignal-resize-handle:hover {
  border-color: #2563eb;
}
"""
DATAMAP_RESIZE_JS = """
(() => {
  const handle = document.getElementById("autosignal-resize-handle");
  const frame = window.frameElement;
  if (!handle || !frame) return;

  let startX = 0;
  let startY = 0;
  let startWidth = 0;
  let startHeight = 0;

  handle.addEventListener("pointerdown", (event) => {
    const bounds = frame.getBoundingClientRect();
    startX = event.clientX;
    startY = event.clientY;
    startWidth = bounds.width;
    startHeight = bounds.height;
    handle.setPointerCapture(event.pointerId);
    document.body.style.userSelect = "none";
    event.preventDefault();
  });

  handle.addEventListener("pointermove", (event) => {
    if (!handle.hasPointerCapture(event.pointerId)) return;
    const parentWidth = frame.parentElement?.getBoundingClientRect().width
      ?? startWidth;
    const width = Math.max(
      480,
      Math.min(parentWidth, startWidth + event.clientX - startX),
    );
    const height = Math.max(
      420,
      Math.min(1200, startHeight + event.clientY - startY),
    );
    frame.style.setProperty("width", `${width}px`, "important");
    frame.style.setProperty("height", `${height}px`, "important");
    window.dispatchEvent(new Event("resize"));
  });

  const finishResize = (event) => {
    if (handle.hasPointerCapture(event.pointerId)) {
      handle.releasePointerCapture(event.pointerId);
    }
    document.body.style.userSelect = "";
  };
  handle.addEventListener("pointerup", finishResize);
  handle.addEventListener("pointercancel", finishResize);
})();
"""


st.set_page_config(
    page_title="AutoSignal",
    page_icon="◉",
    layout="wide",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body {
        font-family: 'Inter', sans-serif;
    }

    [data-testid="stAppViewContainer"] :not([data-testid*="Icon"]):not([class*="material-symbols"]):not(svg):not(svg *),
    [data-testid="stSidebar"] :not([data-testid*="Icon"]):not([class*="material-symbols"]):not(svg):not(svg *) {
        font-family: 'Inter', sans-serif !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_bundled_dataset(path: str, rows: int) -> pd.DataFrame:
    return load_df_slice(path, rows)


@st.cache_data(show_spinner=False)
def load_uploaded_dataset(
    content: bytes,
    filename: str,
    rows: int,
) -> pd.DataFrame:
    suffix = Path(filename).suffix.lower()
    buffer = io.BytesIO(content)
    if suffix == ".csv":
        df = pd.read_csv(buffer, low_memory=False)
    elif suffix in {".parquet", ".pq"}:
        df = pd.read_parquet(buffer)
    else:
        raise ValueError("Upload a CSV or Parquet dataset.")
    if rows and len(df) > rows:
        df = df.tail(rows)
    return df.reset_index(drop=True)


def default_config_text() -> str:
    # return (DEFAULT_CONFIG.read_text(encoding="utf-8"))
    return json.dumps(json.loads(DEFAULT_CONFIG.read_text(encoding="utf-8"))[0])


def display_name(row: pd.Series) -> str:
    hypothesis = row.get("hypothesis")
    seed = row.get("seed")
    name = str(row["method"])
    if hypothesis:
        name += f" · {hypothesis}"
    if pd.notna(seed):
        name += f" · seed {int(seed)}"
    return name


def score_colors(scores: pd.Series) -> np.ndarray:
    """Map anomaly scores to readable colors without using ground truth."""
    from matplotlib.colors import LinearSegmentedColormap, to_hex

    values = scores.to_numpy(dtype=float)
    low = float(np.nanmin(values))
    high = float(np.nanmax(values))
    scaled = np.zeros(len(values)) if high == low else (values - low) / (high - low)
    palette = LinearSegmentedColormap.from_list(
        "autosignal",
        ["#1D4ED8", "#0891B2", "#D97706", "#DC2626"],
    )
    return np.asarray([to_hex(palette(value)) for value in scaled])


def hover_text(plot_data: pd.DataFrame, show_labels: bool) -> np.ndarray:
    """Build compact analyst hover cards for the interactive map."""
    cards = []
    for row in plot_data.itertuples(index=False):
        lines = [
            f"<b>Session {int(row.session_id)}</b>",
            f"Anomaly score: {float(row.score):.4f}",
            f"Rows: {int(row.rows)}",
            f"Start: {escape(str(row.start_time))}",
            f"End: {escape(str(row.end_time))}",
        ]
        if show_labels:
            lines.append(f"Demo label: {escape(str(row.label))}")
        cards.append("<br>".join(lines))
    return np.asarray(cards)


def signal_hover_text(
    plot_data: pd.DataFrame,
    channel_label: str,
    show_labels: bool,
) -> np.ndarray:
    """Build hover cards that explain the graph-relative score channels."""
    cards = []
    for row in plot_data.itertuples(index=False):
        lines = [
            f"<b>Session {int(row.session_id)}</b>",
            f"{escape(channel_label)}: {float(row.displayed_score):.4f}",
            f"Intrinsic s: {float(row.intrinsic):.4f}",
            f"Neighbor Ps: {float(row.neighbor_support):.4f}",
            f"Two-hop P²s: {float(row.second_hop_support):.4f}",
            f"Residual s − Ps: {float(row.local_contrast):.4f}",
            f"Pocket Ps − P²s: {float(row.pocket):.4f}",
            f"Matched score: {float(row.matched_score):.4f}",
            (
                f"Ranks: {int(row.intrinsic_rank)} → "
                f"{int(row.matched_rank)} "
                f"({float(row.rank_gain):+0.0f})"
            ),
            f"Rows: {int(row.rows)}",
            f"Start: {escape(str(row.start_time))}",
            f"End: {escape(str(row.end_time))}",
        ]
        if show_labels:
            lines.append(f"Development label: {escape(str(row.label))}")
        cards.append("<br>".join(lines))
    return np.asarray(cards)


@st.cache_data(show_spinner=False)
def interactive_datamap_html(
    coordinates: np.ndarray,
    hover_cards: np.ndarray,
    marker_colors: np.ndarray,
    labels: np.ndarray | None,
    title: str,
) -> str:
    """Create the self-contained HTML used by the Streamlit component."""
    import datamapplot

    label_layers = () if labels is None else (labels,)
    figure = datamapplot.create_interactive_plot(
        coordinates,
        *label_layers,
        hover_text=hover_cards,
        marker_color_array=None if labels is not None else marker_colors,
        marker_alpha_array=np.full(len(coordinates), 255, dtype=np.uint8),
        label_color_map=DEMO_LABEL_COLORS if labels is not None else None,
        title=escape(title),
        darkmode=False,
        background_color="#F8FAFC",
        point_radius_min_pixels=2.5,
        point_radius_max_pixels=18,
        point_hover_color="#111827",
        custom_html=DATAMAP_RESIZE_HANDLE,
        custom_css=DATAMAP_RESIZE_CSS,
        custom_js=DATAMAP_RESIZE_JS,
        inline_data=True,
        width="100%",
        height=720,
    )
    return str(figure)


def static_datamap(
    coordinates: np.ndarray,
    marker_colors: np.ndarray,
    labels: np.ndarray | None,
    title: str,
):
    """Create the static counterpart of the selected interactive map."""
    import datamapplot

    figure, _ = datamapplot.create_plot(
        coordinates,
        labels=labels,
        marker_color_array=None if labels is not None else marker_colors,
        label_color_map=DEMO_LABEL_COLORS if labels is not None else None,
        title=title,
        darkmode=False,
        point_size=4,
        alpha=0.95,
        force_matplotlib=True,
        use_system_fonts=True,
    )
    return figure


st.title("AutoSignal")
st.caption(
    "Agent-guided schema adaptation and representation-level telemetry "
    "signal localization"
)

with st.sidebar:
    st.header("Run configuration")
    source = st.radio(
        "Dataset source",
        ["Bundled ACME development data", "Upload dataset"],
    )
    upload = None
    if source == "Upload dataset":
        upload = st.file_uploader(
            "Telemetry dataset",
            type=["csv", "parquet", "pq"],
        )

    rows = st.slider(
        "Rows in development slice",
        min_value=300,
        max_value=5_000,
        value=1_000,
        step=100,
        help="A focused slice keeps the interactive baseline run responsive.",
    )
    k = st.slider("k for anomaly scoring", 3, 30, 15)
    graph_epochs = st.slider(
        "GraphSAGE epochs",
        min_value=1,
        max_value=8,
        value=4,
    )
    signal_permutations = st.select_slider(
        "Signal-null permutations",
        options=[99, 199, 499, 999],
        value=199,
        help=(
            "Permutation count used by each representation's label-blind "
            "signal-regime diagnosis. Use 999 for a final development run."
        ),
    )
    run_button = st.button(
        "Run AutoSignal",
        type="primary",
        width="stretch",
    )
    pipeline_progress = st.empty()

st.subheader("Agent configuration")
config_textfield = st.text_area(
    "Optional JSON configuration snippet",
)
config_upload = st.file_uploader(
    "Optional JSON configuration file",
    type=["json"],
    key="config_upload",
)
initial_config = (
    config_upload.getvalue().decode("utf-8")
    if config_upload is not None
    else default_config_text()
)
config_text = st.text_area(
    "Validated agent output",
    value=initial_config,
    height=320,
    help=(
        "Paste the schema agent's JSON here. AutoSignal validates every "
        "column and relation before execution."
    ),
)

if run_button:
    progress_bar = pipeline_progress.progress(
        0.0,
        text="Preparing AutoSignal...",
    )

    def update_pipeline_progress(progress: float, message: str) -> None:
        percent = round(progress * 100)
        progress_bar.progress(
            progress,
            text=f"{message} — {percent}%",
        )

    try:
        agent_config = json.loads(config_text)
        if source == "Bundled ACME development data":
            dataset = load_bundled_dataset(str(DEFAULT_DATASET), rows)
            dataset_name = DEFAULT_DATASET.name
        else:
            if upload is None:
                raise ValueError("Choose a dataset file before running.")
            dataset = load_uploaded_dataset(
                upload.getvalue(),
                upload.name,
                rows,
            )
            dataset_name = upload.name

        result = run_autosignal(
            dataset,
            agent_config,
            k=k,
            seeds=(42,),
            graph_epochs=graph_epochs,
            signal_permutations=signal_permutations,
            progress_callback=update_pipeline_progress,
        )
        st.session_state["autosignal_result"] = result
        st.session_state["autosignal_preview"] = dataset.head(20)
        st.session_state["autosignal_profile"] = dataframe_profile(dataset)
        st.session_state["autosignal_dataset_name"] = dataset_name
        st.success("AutoSignal completed successfully.")
    except json.JSONDecodeError as error:
        pipeline_progress.empty()
        st.error(f"The agent configuration is not valid JSON: {error}")
    except ConfigValidationError as error:
        pipeline_progress.empty()
        st.error("Configuration validation failed.")
        st.code(str(error))
    except Exception as error:
        pipeline_progress.empty()
        st.exception(error)


result = st.session_state.get("autosignal_result")
if result is None:
    st.info(
        "Run the bundled development slice or upload a dataset to populate "
        "the analysis views."
    )
    st.stop()


run_manifest = result["run_manifest"]
session_manifest = result["session_manifest"]
graph_manifest = result.get("graph_manifest") or {}
method_results = pd.DataFrame(result["method_results"])
completed_results = method_results[method_results["status"].eq("completed")].copy()
failed_results = method_results[method_results["status"].ne("completed")].copy()
completed_results["display_name"] = completed_results.apply(display_name, axis=1)
embeddings = pd.DataFrame(result["embeddings"])
score_rows = pd.DataFrame(result["session_scores"])
sessions = pd.DataFrame(result["sessions"])
method_keys = embeddings["method_key"].drop_duplicates().tolist()
method_rows = embeddings.drop_duplicates("method_key")
method_names = {
    row["method_key"]: display_name(row) for _, row in method_rows.iterrows()
}
has_demo_labels = embeddings["label"].ne("unknown").any()
signal_results = pd.DataFrame(result.get("signal_results", []))
signal_scores = pd.DataFrame(result.get("signal_scores", []))

st.subheader(st.session_state.get("autosignal_dataset_name", "Telemetry dataset"))
summary_columns = st.columns(5)
summary_columns[0].metric("Rows", f"{run_manifest['rows']:,}")
summary_columns[1].metric("Sessions", f"{run_manifest['sessions']:,}")
summary_columns[2].metric(
    "Graph nodes",
    f"{sum(graph_manifest.get('node_counts', {}).values()):,}",
)
summary_columns[3].metric(
    "Graph edges",
    f"{graph_manifest.get('total_forward_edges', 0):,}",
)
summary_columns[4].metric(
    "Completed methods",
    f"{len(completed_results):,}",
)

tabs = st.tabs(
    [
        "Method comparison",
        "Representations",
        "Signal diagnosis",
        "Top sessions",
        "Configuration",
        "Diagnostics",
    ]
)

with tabs[0]:
    st.subheader("Representation-family comparison")
    metric_columns = [
        "display_name",
        "method",
        "hypothesis",
        "seed",
        "average_precision",
        "reviews_to_first_malicious",
        "recall_at_25",
        "recall_at_100",
        "recall_at_250",
        "status",
    ]
    available_columns = [
        column for column in metric_columns if column in completed_results
    ]
    st.dataframe(
        completed_results[available_columns],
        width="stretch",
        hide_index=True,
    )

    chart_values = completed_results[
        ["display_name", "average_precision", "recall_at_100"]
    ].dropna(subset=["average_precision"])
    if not chart_values.empty:
        st.caption(
            "Development labels are used only for evaluation; larger values are better."
        )
        st.bar_chart(
            chart_values.set_index("display_name"),
            horizontal=True,
            height=max(360, 34 * len(chart_values)),
        )

    if not failed_results.empty:
        with st.expander("Failed or skipped methods", expanded=True):
            st.dataframe(failed_results, width="stretch", hide_index=True)

with tabs[1]:
    st.subheader("Session representation")
    map_controls = st.columns([2, 1, 1])
    with map_controls[0]:
        selected_method_key = st.selectbox(
            "Representation",
            method_keys,
            format_func=lambda key: method_names[key],
            key="embedding_method",
        )
    with map_controls[1]:
        map_view = st.radio(
            "View",
            ["Interactive", "Static"],
            horizontal=True,
            key="embedding_view",
        )
    with map_controls[2]:
        show_demo_labels = st.toggle(
            "Show demo labels",
            value=False,
            disabled=not has_demo_labels,
            help="Reveals evaluation labels only when the dataset provides them.",
        )

    selected_embedding = embeddings[
        embeddings["method_key"].eq(selected_method_key)
    ].copy()
    plot_data = (
        selected_embedding.merge(
            score_rows[
                score_rows["method_key"].eq(selected_method_key)
            ][["session_id", "score"]],
            on="session_id",
            how="left",
        )
        .merge(
            sessions.drop(columns=["label"], errors="ignore"),
            on="session_id",
            how="left",
        )
        .sort_values("session_id")
        .reset_index(drop=True)
    )
    coordinates = plot_data[["x", "y"]].to_numpy(dtype=float)
    marker_colors = score_colors(plot_data["score"])
    labels = (
        plot_data["label"].astype(str).to_numpy()
        if show_demo_labels
        else None
    )
    plot_title = method_names[selected_method_key]

    if map_view == "Interactive":
        with st.spinner("Building interactive session map..."):
            map_html = interactive_datamap_html(
                coordinates,
                hover_text(plot_data, show_demo_labels),
                marker_colors,
                labels,
                plot_title,
            )
        st.iframe(map_html, width="stretch", height=760)
    else:
        from matplotlib import pyplot as plt

        static_figure = static_datamap(
            coordinates,
            marker_colors,
            labels,
            plot_title,
        )
        st.pyplot(static_figure, width="stretch")
        plt.close(static_figure)

    st.caption(
        "UMAP projects the selected method's session representation. With demo "
        "labels hidden, color intensity reflects that method's anomaly score; "
        "coordinates are visualization artifacts, not scores."
    )

with tabs[2]:
    st.subheader("Signal-regime diagnosis")
    st.caption(
        "Choose any completed representation or feature hypothesis. The picker "
        "tests score organization on that representation's full session matrix—not "
        "its 2D visualization—and never uses labels to select a regime."
    )
    st.info(
        "Cross-method browsing is exploratory. Family-wise p-values correct the "
        "three regime hypotheses within the selected representation, not the act "
        "of searching across many representations. For a confirmatory run, freeze "
        "one representation first and count only its matched transform as the "
        "single amplification test."
    )
    signal_config = result.get("signal_config", {})
    if signal_config:
        st.caption(
            "Run settings: "
            f"k={signal_config.get('k')} · "
            f"{signal_config.get('n_permutations')} permutations · "
            f"top {100 * float(signal_config.get('tail_fraction', 0.05)):.0f}% "
            f"tail · α={float(signal_config.get('alpha', 0.05)):.2f}"
        )

    if signal_results.empty or signal_scores.empty:
        st.warning(
            "This result payload has no signal artifacts. Run AutoSignal again "
            "to populate the signal-analysis views."
        )
    else:
        available_signal_results = signal_results[
            signal_results["status"].eq("completed")
        ].copy()
        unavailable_signal_results = signal_results[
            signal_results["status"].ne("completed")
        ].copy()

        if available_signal_results.empty:
            st.warning("No completed representation supports signal diagnosis.")
            if not unavailable_signal_results.empty:
                st.dataframe(
                    unavailable_signal_results,
                    width="stretch",
                    hide_index=True,
                )
        else:
            signal_method_keys = (
                available_signal_results["method_key"].drop_duplicates().tolist()
            )
            selected_signal_key = st.selectbox(
                "Method and feature representation",
                signal_method_keys,
                format_func=lambda key: method_names.get(key, key),
                key="signal_method",
            )
            signal_record = available_signal_results[
                available_signal_results["method_key"].eq(selected_signal_key)
            ].iloc[0]
            selected_hypothesis = signal_record.get("hypothesis")
            if pd.notna(selected_hypothesis):
                feature_set = next(
                    (
                        item
                        for item in result["config"]["feature_sets"]
                        if item["name"] == selected_hypothesis
                    ),
                    None,
                )
                if feature_set is not None:
                    st.caption(
                        f"Feature set: **{feature_set['name']}** · "
                        + ", ".join(feature_set["columns"])
                    )
            else:
                st.caption(
                    "Topology-wide representation: this method uses the configured "
                    "graph relations rather than one individual feature hypothesis."
                )
            evidence = pd.DataFrame(signal_record["evidence"])
            regime = str(signal_record["regime"])
            passing_evidence = evidence[evidence["passes"].astype(bool)]
            winner_evidence = evidence[evidence["regime"].eq(regime)]

            headline = st.columns([2, 1, 1, 1])
            headline[0].metric("Dominant regime", regime)
            headline[1].metric(
                "Winner effect z",
                (
                    f"{float(winner_evidence.iloc[0]['effect_z']):.2f}"
                    if not winner_evidence.empty
                    else "—"
                ),
            )
            headline[2].metric(
                "Family-wise p",
                (
                    f"{float(winner_evidence.iloc[0]['familywise_p']):.4f}"
                    if not winner_evidence.empty
                    else "—"
                ),
            )
            headline[3].metric(
                "Passing regimes",
                f"{len(passing_evidence)} / 3",
            )

            regime_explanations = {
                "Neighborhood-supported": (
                    "High intrinsic scores tend to have high-scoring immediate "
                    "neighbors."
                ),
                "Locally Contrastive": (
                    "High intrinsic scores stand above comparatively normal "
                    "immediate neighbors."
                ),
                "Intermediate-scale": (
                    "Strong one-hop score pockets dilute at the second hop."
                ),
                "No useful organization": (
                    "None of the graph-relative hypotheses beat the permutation "
                    "null after correction."
                ),
            }
            st.write(regime_explanations.get(regime, ""))
            if len(passing_evidence) > 1:
                secondary = passing_evidence[
                    ~passing_evidence["regime"].eq(regime)
                ]["regime"].tolist()
                st.caption(
                    "Secondary passing structure: " + ", ".join(secondary)
                )

            evidence_columns = [
                "regime",
                "observed_statistic",
                "null_mean",
                "null_std",
                "effect_z",
                "raw_p",
                "familywise_p",
                "passes",
            ]
            st.dataframe(
                evidence[evidence_columns].style.format(
                    {
                        "observed_statistic": "{:.3f}",
                        "null_mean": "{:.3f}",
                        "null_std": "{:.3f}",
                        "effect_z": "{:.2f}",
                        "raw_p": "{:.4f}",
                        "familywise_p": "{:.4f}",
                    }
                ),
                width="stretch",
                hide_index=True,
            )

            selected_signal_scores = signal_scores[
                signal_scores["method_key"].eq(selected_signal_key)
            ].copy()
            selected_signal_embedding = embeddings[
                embeddings["method_key"].eq(selected_signal_key)
            ][["session_id", "x", "y"]].copy()
            signal_plot_data = (
                selected_signal_embedding.merge(
                    selected_signal_scores,
                    on="session_id",
                    how="inner",
                    validate="one_to_one",
                )
                .merge(
                    sessions.drop(columns=["label"], errors="ignore"),
                    on="session_id",
                    how="left",
                    validate="one_to_one",
                )
                .sort_values("session_id")
                .reset_index(drop=True)
            )

            channel_labels = {
                "intrinsic": "Intrinsic s",
                "neighbor_support": "Neighbor Ps",
                "second_hop_support": "Two-hop P²s",
                "local_contrast": "Residual s − Ps",
                "local_contrast_magnitude": "Residual magnitude |s − Ps|",
                "pocket": "Pocket Ps − P²s",
                "supported_candidate": "Supported ½s + ½Ps",
                "matched_score": f"Matched transform · {regime}",
            }
            map_controls = st.columns([2, 1, 1])
            with map_controls[0]:
                selected_channel = st.selectbox(
                    "Color map by",
                    list(channel_labels),
                    index=list(channel_labels).index("matched_score"),
                    format_func=lambda key: channel_labels[key],
                    key="signal_channel",
                )
            with map_controls[1]:
                signal_map_view = st.radio(
                    "View",
                    ["Interactive", "Static"],
                    horizontal=True,
                    key="signal_map_view",
                )
            with map_controls[2]:
                reveal_signal_labels = st.toggle(
                    "Reveal development labels",
                    value=False,
                    disabled=not has_demo_labels,
                    help=(
                        "Labels appear only in hover cards and validation tables; "
                        "they never affect the regime picker."
                    ),
                )

            signal_plot_data["displayed_score"] = signal_plot_data[
                selected_channel
            ]
            signal_color_percentiles = signal_plot_data[
                "displayed_score"
            ].rank(pct=True, method="average")
            signal_marker_colors = score_colors(signal_color_percentiles)
            signal_coordinates = signal_plot_data[["x", "y"]].to_numpy(float)
            signal_title = (
                f"{method_names.get(selected_signal_key, selected_signal_key)}"
                f" · {channel_labels[selected_channel]}"
            )

            if signal_map_view == "Interactive":
                with st.spinner("Building interactive signal map..."):
                    signal_map_html = interactive_datamap_html(
                        signal_coordinates,
                        signal_hover_text(
                            signal_plot_data,
                            channel_labels[selected_channel],
                            reveal_signal_labels,
                        ),
                        signal_marker_colors,
                        None,
                        signal_title,
                    )
                st.iframe(signal_map_html, width="stretch", height=760)
            else:
                from matplotlib import pyplot as plt

                signal_figure = static_datamap(
                    signal_coordinates,
                    signal_marker_colors,
                    None,
                    signal_title,
                )
                st.pyplot(signal_figure, width="stretch")
                plt.close(signal_figure)

            st.caption(
                "Color represents within-channel percentile so s, Ps, P²s, and "
                "their differences remain visually comparable. Hover values retain "
                "their original units."
            )

            evaluation_value = signal_record.get("evaluation")
            if isinstance(evaluation_value, dict):
                evaluation_rows = [
                    {"ranking": name, **metrics}
                    for name, metrics in evaluation_value.items()
                    if name in {"intrinsic", "matched"}
                    and isinstance(metrics, dict)
                ]
            else:
                evaluation_rows = evaluation_value or []
            evaluation = pd.DataFrame(evaluation_rows)

            st.subheader("Matched amplification check")
            if evaluation.empty:
                st.info(
                    "No development labels are available. The structural diagnosis "
                    "and rankings remain usable, but amplification cannot be "
                    "validated against malicious-session discovery."
                )
            else:
                metric_order = [
                    "ranking",
                    "average_precision",
                    "reviews_to_first_malicious",
                    "found_at_25",
                    "recall_at_25",
                    "found_at_100",
                    "recall_at_100",
                    "found_at_250",
                    "recall_at_250",
                ]
                evaluation_columns = [
                    column for column in metric_order if column in evaluation
                ]
                st.dataframe(
                    evaluation[evaluation_columns],
                    width="stretch",
                    hide_index=True,
                )
                evaluation_by_name = evaluation.set_index("ranking")
                if regime == "No useful organization":
                    st.info(
                        "No transform was applied; the matched ranking is the "
                        "original intrinsic ranking."
                    )
                elif {"intrinsic", "matched"} <= set(evaluation_by_name.index):
                    intrinsic_eval = evaluation_by_name.loc["intrinsic"]
                    matched_eval = evaluation_by_name.loc["matched"]
                    comparison_values = [
                        intrinsic_eval.get("average_precision"),
                        matched_eval.get("average_precision"),
                        intrinsic_eval.get("reviews_to_first_malicious"),
                        matched_eval.get("reviews_to_first_malicious"),
                    ]
                    if not all(pd.notna(value) for value in comparison_values):
                        st.info(
                            "The dataset does not contain enough positive-label "
                            "evidence to accept or reject the matched ranking."
                        )
                    else:
                        ap_improved = (
                            float(matched_eval["average_precision"])
                            > float(intrinsic_eval["average_precision"])
                        )
                        first_not_worse = (
                            float(
                                matched_eval[
                                    "reviews_to_first_malicious"
                                ]
                            )
                            <= float(
                                intrinsic_eval[
                                    "reviews_to_first_malicious"
                                ]
                            )
                        )
                        if ap_improved and first_not_worse:
                            st.success(
                                "Development evidence supports the one matched "
                                "amplification test. Freeze it before any new "
                                "holdout."
                            )
                        else:
                            st.warning(
                                "The matched transform did not improve the "
                                "development triage ranking. Keep the intrinsic "
                                "score for analyst prioritization; retain the "
                                "regime as structural context."
                            )

            ranking_view = signal_plot_data.copy()
            ranking_view["intrinsic_priority"] = (
                len(ranking_view) + 1 - ranking_view["intrinsic_rank"]
            )
            ranking_view["matched_priority"] = (
                len(ranking_view) + 1 - ranking_view["matched_rank"]
            )
            rank_left, rank_right = st.columns([1, 1])
            with rank_left:
                st.subheader("Original versus matched priority")
                scatter_kwargs = {
                    "data": ranking_view,
                    "x": "intrinsic_priority",
                    "y": "matched_priority",
                    "size": 28,
                    "height": 480,
                }
                if reveal_signal_labels:
                    scatter_kwargs["color"] = "label"
                st.scatter_chart(**scatter_kwargs)
                st.caption(
                    "Higher is better on both axes. Points far above the implied "
                    "diagonal were promoted by graph context."
                )
            with rank_right:
                st.subheader("Top matched sessions")
                top_limit = min(100, len(ranking_view))
                if top_limit >= 10:
                    top_n = st.slider(
                        "Sessions to display",
                        min_value=10,
                        max_value=top_limit,
                        value=min(25, top_limit),
                        key="signal_top_n",
                    )
                else:
                    top_n = top_limit
                top_columns = [
                    "matched_rank",
                    "session_id",
                    "intrinsic",
                    "matched_score",
                    "intrinsic_rank",
                    "rank_gain",
                    "rows",
                    "start_time",
                    "end_time",
                ]
                if reveal_signal_labels:
                    top_columns.insert(6, "label")
                st.dataframe(
                    ranking_view.sort_values("matched_rank")[top_columns].head(
                        top_n
                    ),
                    width="stretch",
                    hide_index=True,
                )

            safe_signal_filename = "".join(
                character
                if character.isalnum() or character in {"-", "_"}
                else "_"
                for character in selected_signal_key
            )
            signal_download = ranking_view.copy()
            if not reveal_signal_labels:
                signal_download = signal_download.drop(
                    columns=["label"],
                    errors="ignore",
                )
            st.download_button(
                "Download selected signal analysis",
                data=signal_download.to_csv(index=False),
                file_name=safe_signal_filename + "_signal_analysis.csv",
                mime="text/csv",
            )

        if not unavailable_signal_results.empty:
            with st.expander("Unavailable signal diagnoses"):
                st.dataframe(
                    unavailable_signal_results,
                    width="stretch",
                    hide_index=True,
                )

with tabs[3]:
    st.subheader("Highest-ranked sessions")
    score_method_keys = score_rows["method_key"].drop_duplicates().tolist()
    selected_score_key = st.selectbox(
        "Ranking method",
        score_method_keys,
        key="score_method",
    )
    ranked = (
        score_rows[score_rows["method_key"].eq(selected_score_key)]
        .merge(sessions, on=["session_id", "label"], how="left")
        .sort_values("score", ascending=False)
        .reset_index(drop=True)
    )
    ranked.insert(0, "rank", np.arange(1, len(ranked) + 1))
    st.dataframe(
        ranked[
            [
                "rank",
                "session_id",
                "score",
                "label",
                "rows",
                "start_time",
                "end_time",
            ]
        ].head(100),
        width="stretch",
        hide_index=True,
    )

with tabs[4]:
    config = result["config"]
    st.subheader("Feature hypotheses")
    for feature_set in config["feature_sets"]:
        with st.expander(feature_set["name"], expanded=True):
            st.write(feature_set.get("rationale", ""))
            st.code(", ".join(feature_set["columns"]))

    st.subheader("Typed graph relations")
    st.dataframe(
        pd.DataFrame(config["graph_relations"]),
        width="stretch",
        hide_index=True,
    )
    st.subheader("Dataset preview")
    st.dataframe(
        st.session_state["autosignal_preview"],
        width="stretch",
        hide_index=True,
    )

with tabs[5]:
    left, right = st.columns(2)
    with left:
        st.subheader("Session manifest")
        st.json(session_manifest)
        st.subheader("Graph manifest")
        st.json(graph_manifest)
    with right:
        st.subheader("Feature preprocessing")
        st.json(result.get("feature_diagnostics", {}))
        st.subheader("Dataset profile")
        st.json(st.session_state.get("autosignal_profile", {}), expanded=False)

    export = json.dumps(result, indent=2)
    st.download_button(
        "Download result payload",
        data=export,
        file_name="autosignal_result.json",
        mime="application/json",
    )
