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
    return DEFAULT_CONFIG.read_text(encoding="utf-8")


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
    run_button = st.button(
        "Run AutoSignal",
        type="primary",
        width="stretch",
    )
    pipeline_progress = st.empty()

st.subheader("Agent configuration")
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
    embeddings = pd.DataFrame(result["embeddings"])
    score_rows = pd.DataFrame(result["session_scores"])
    sessions = pd.DataFrame(result["sessions"])
    method_keys = embeddings["method_key"].drop_duplicates().tolist()
    method_rows = embeddings.drop_duplicates("method_key")
    method_names = {
        row["method_key"]: display_name(row) for _, row in method_rows.iterrows()
    }
    has_demo_labels = embeddings["label"].ne("unknown").any()

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

with tabs[3]:
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

with tabs[4]:
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
