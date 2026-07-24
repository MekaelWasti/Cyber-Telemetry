import streamlit as st
import pandas as pd
import numpy as np

# Initialize session state for results if not already present
if "feature_extraction_table" not in st.session_state:
    st.session_state.feature_extraction_table = pd.DataFrame(columns=["Method", "Development AP", "Recall@100", "Recall@200", "Signal Strength", "Localization Accuracy"])

if "signal_process_table" not in st.session_state:
    st.session_state.signal_process_table = pd.DataFrame(columns=["Method", "Spectral", "Signal-to-Noise Ratio", "Amplification Factor"])


# Main Page Configuration
st.set_page_config(page_title="AutoSignal", layout="centered")

st.title("AutoSignal: An Agentic Framework for Telemetry Signal Localization")

st.header("Telemetry Dataset Input")

# Dataset Entry Point
dataset_upload_columns = st.columns(2)

# File Selector for Telemetry Dataset
with dataset_upload_columns[0]:
    dataset_table = st.selectbox("Select Telemetry Dataset", ["ACME 4", "OpTC", "AWS"])

# File Uploader for Telemetry Dataset
with dataset_upload_columns[1]:
    file = st.file_uploader("Upload Telemetry Dataset (CSV)", type=["csv"])

# Main Pipeline Entry Point

if "started" not in st.session_state:
    st.session_state.started = False

def start():
    st.session_state.started = True
    
    run_autosignal_pipeline()

def run_autosignal_pipeline():
    # Placeholder for the actual pipeline logic
    st.info("Running AutoSignal pipeline...")

    # Call the individual methods for feature extraction, signal localization, and amplification here

    # Dummy results for demonstration purposes
    st.session_state.feature_extraction_table = pd.DataFrame({
        "Method": ["Random Ranking", "Raw Session Features", "Typed Graph Statistics", "Node2Vec", "GraphSAGE Random", "GraphSAGE Trained"],
        "Development AP": [0.45, 0.50, 0.55, 0.60, 0.65, 0.70],
        "Recall@100": [0.0526, 0.0789, 0.10, 0.12, 0.15, 0.18],
        "Recall@200": [0.10, 0.15, 0.20, 0.25, 0.30, 0.35],
        "Signal Strength": [0.85, 0.90, 0.88, 0.87, 0.86, 0.89],
        "Localization Accuracy": [0.80, 0.88, 0.85, 0.83, 0.82, 0.84],
    })

    st.session_state.signal_process_table = pd.DataFrame({
        "Method": ["Random Ranking", "Raw Session Features", "Typed Graph Statistics", "Node2Vec", "GraphSAGE Random", "GraphSAGE Trained"],
        "Spectral": [0.75, 0.80, 0.78, 0.82, 0.85, 0.88],
        "Signal-to-Noise Ratio": [1.5, 2.0, 1.8, 2.2, 2.5, 2.8],
        "Amplification Factor": [1.2, 1.5, 1.3, 1.6, 1.8, 2.0],
    })

if not st.session_state.started:
    entry_point_button = st.button("Start Feature Extraction", on_click=start, key="start_button", help="Click to start AutoSignal feature extraction pipeline on the selected telemetry dataset.")
else:
    entry_point_button = st.button("AutoSignal Pipeline Running...", key="running_button", disabled=True, help="AutoSignal pipeline is currently running. Please wait for completion.")


# Display Feature Extraction Results in a Table
# Results will be the C0/M0 methods table of results
st.header("Features Extracted from Telemetry Dataset")
autosignal_pipleine_results = st.table(
    st.session_state.feature_extraction_table
)

# st.header("Telemetry Embedding & Signal Visualization")


st.header("Signal Localization & Amplification Results")
autosignal_signal_results = st.table(
    st.session_state.signal_process_table
)