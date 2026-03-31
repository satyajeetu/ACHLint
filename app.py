from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from html import escape
from typing import Iterable

import streamlit as st

from achlint.copy import ISSUE_TITLE_MAP, UI_COPY, issue_display_message, issue_next_step_copy, issue_summary_copy
from achlint.csv_parser import parse_payment_csv
from achlint.csv_template import get_template_csv
from achlint.models import BuildResult, OriginatorConfig, ValidationIssue, ValidationResult
from achlint.nacha_builder import build_file
from achlint.nacha_validator import validate_ach
from achlint.report_builder import build_exceptions_csv, build_report_pdf


st.set_page_config(page_title="ACHLint", page_icon="🏦", layout="wide", initial_sidebar_state="collapsed")


DEFAULT_CONFIG = {
    "company_name": "ACME PAYROLL",
    "company_identification": "1234567890",
    "immediate_destination_routing": "021000021",
    "immediate_destination_name": "JPMORGAN CHASE",
    "immediate_origin_routing": "011000015",
    "immediate_origin_name": "BANK OF AMERICA",
    "company_entry_description": "PAYROLL",
    "effective_entry_date": date.today() + timedelta(days=1),
    "originating_dfi_identification": "01100001",
    "file_id_modifier": "A",
    "company_discretionary_data": "",
    "company_descriptive_date": "",
    "reference_code": "",
    "trace_number_start": 1,
}


def main() -> None:
    st.session_state.setdefault("page", "Landing")
    st.session_state.setdefault("latest_result", None)
    st.session_state.setdefault("originator_config_values", DEFAULT_CONFIG.copy())
    st.session_state.setdefault("show_tour", True)
    st.session_state.setdefault("generate_step", 1)
    inject_styles()

    page = render_app_shell()

    if page == "Landing":
        render_landing()
    elif page == "Generate":
        render_generate()
    elif page == "Validate":
        render_validate()
    elif page == "Results":
        render_results()
    else:
        render_help()


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto+Flex:opsz,wght@8..144,400;8..144,500;8..144,700;8..144,800&family=Roboto+Mono:wght@500&display=swap');
        :root {
            --md-primary: #6750A4;
            --md-on-primary: #FFFFFF;
            --md-primary-container: #EADDFF;
            --md-on-primary-container: #21005D;
            --md-secondary: #625B71;
            --md-on-secondary: #FFFFFF;
            --md-secondary-container: #E8DEF8;
            --md-on-secondary-container: #1D192B;
            --md-tertiary: #7D5260;
            --md-on-tertiary: #FFFFFF;
            --md-tertiary-container: #FFD8E4;
            --md-on-tertiary-container: #31111D;
            --md-error: #B3261E;
            --md-on-error: #FFFFFF;
            --md-error-container: #F9DEDC;
            --md-on-error-container: #410E0B;
            --md-surface: #FFFBFE;
            --md-on-surface: #1C1B1F;
            --md-surface-variant: #E7E0EC;
            --md-on-surface-variant: #49454F;
            --md-outline: #79747E;
            --md-shadow: 0 18px 44px rgba(0, 0, 0, 0.08);
            --md-radius-lg: 16px;
            --md-radius-md: 12px;
            --md-radius-sm: 8px;
            
            --md-surface-soft: #F3EDF7;
            --md-surface-container: rgba(255, 251, 254, 0.82);
            --md-surface-container-high: rgba(255, 251, 254, 0.94);
            --md-outline-strong: #49454F;
            --md-text: #1C1B1F;
            --md-text-soft: #49454F;
            --md-text-muted: #625B71;

        }
        .stApp {
            background:
                radial-gradient(circle at top right, rgba(103, 80, 164, 0.12), transparent 24%),
                radial-gradient(circle at 10% 20%, rgba(125, 82, 96, 0.22), transparent 18%),
                linear-gradient(180deg, #FFFBFE 0%, #E7E0EC 100%);
            color: var(--md-text);
            font-family: "Roboto Flex", "Inter", sans-serif;
        }
        .block-container {
            padding-top: 1rem;
            padding-bottom: 3.5rem;
            max-width: 1320px;
        }
        section[data-testid="stSidebar"] {
            display: none;
        }
        button[kind="header"] {
            display: none;
        }
        .app-shell {
            background: var(--md-surface-container);
            border: 1px solid var(--md-outline);
            border-radius: 24px;
            padding: 1rem 1.15rem;
            margin-bottom: 1rem;
            box-shadow: var(--md-shadow);
            backdrop-filter: blur(14px);
        }
        .shell-brand {
            font-size: 1.45rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            color: var(--md-text);
        }
        .shell-subtitle {
            color: var(--md-text-soft);
            font-size: 0.92rem;
            line-height: 1.4;
            margin-top: 0.15rem;
        }
        .shell-meta {
            background: linear-gradient(180deg, #f4f8f4 0%, #edf3ef 100%);
            border: 1px solid var(--md-outline);
            border-radius: 16px;
            padding: 0.85rem 1rem;
            color: var(--md-text-soft);
            font-size: 0.9rem;
            line-height: 1.45;
        }
        .shell-meta strong {
            color: var(--md-text);
        }
        .hero-card, .section-card, .metric-card, .trust-card, .artifact-card, .workspace-card {
            background: var(--md-surface-container-high);
            border: 1px solid var(--md-outline);
            border-radius: var(--md-radius-lg);
            box-shadow: var(--md-shadow);
        }
        .hero-card {
            padding: 2.4rem 2.5rem;
            margin-bottom: 1rem;
            position: relative;
            overflow: hidden;
        }
        .hero-card::after, .workspace-card::after {
            content: "";
            position: absolute;
            inset: 0 auto auto 0;
            width: 100%;
            height: 4px;
            background: linear-gradient(90deg, var(--md-primary) 0%, #8ba89c 60%, rgba(139, 168, 156, 0) 100%);
            opacity: 0.95;
        }
        .sales-problem {
            color: var(--md-text-soft);
            font-size: 1rem;
            line-height: 1.6;
            max-width: 48rem;
            margin-bottom: 0.7rem;
        }
        .eyebrow {
            color: var(--md-primary);
            font-size: 0.85rem;
            font-weight: 700;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            margin-bottom: 0.75rem;
        }
        .hero-title {
            font-size: 2.7rem;
            line-height: 1.05;
            letter-spacing: -0.04em;
            color: var(--md-text);
            margin-bottom: 0.8rem;
            font-weight: 800;
        }
        .hero-copy {
            color: var(--md-text-soft);
            font-size: 1.05rem;
            line-height: 1.65;
            max-width: 56rem;
        }
        .hero-minimal-proof {
            color: var(--md-text-muted);
            font-size: 0.9rem;
            line-height: 1.5;
            margin-top: 0.95rem;
        }
        .trust-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.9rem;
            margin: 1rem 0 1.1rem 0;
        }
        .proof-grid {
            display: grid;
            grid-template-columns: 1.15fr 0.85fr;
            gap: 1rem;
            margin-bottom: 1rem;
        }
        .trust-card, .metric-card, .artifact-card {
            padding: 1rem 1.1rem;
        }
        .trust-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.65rem;
            margin: 0.9rem 0 0.25rem 0;
        }
        .trust-pill {
            border-radius: 999px;
            padding: 0.55rem 0.8rem;
            background: var(--md-surface-soft);
            border: 1px solid var(--md-outline);
            color: var(--md-primary);
            font-size: 0.86rem;
            font-weight: 600;
        }
        .trust-title, .metric-label {
            color: var(--md-text);
            font-weight: 700;
            font-size: 0.92rem;
            margin-bottom: 0.2rem;
        }
        .trust-copy, .metric-copy {
            color: var(--md-text-soft);
            font-size: 0.92rem;
            line-height: 1.45;
        }
        .section-card {
            padding: 1.35rem 1.45rem;
            margin-bottom: 1rem;
        }
        .workspace-card {
            padding: 1.4rem 1.45rem;
            margin-bottom: 1rem;
            position: relative;
            overflow: hidden;
        }
        .feature-band {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.85rem;
            margin: 1rem 0;
        }
        .feature-panel {
            border-radius: 18px;
            border: 1px solid var(--md-outline);
            background: linear-gradient(180deg, #fbfcfb 0%, #f2f6f3 100%);
            padding: 1rem 1.05rem;
        }
        .feature-label {
            color: var(--md-text-muted);
            font-size: 0.82rem;
            margin-bottom: 0.35rem;
        }
        .feature-value {
            color: var(--md-text);
            font-size: 1.15rem;
            font-weight: 760;
            letter-spacing: -0.02em;
        }
        .tutorial-card {
            border-radius: 20px;
            border: 1px solid var(--md-outline);
            background: linear-gradient(180deg, #ffffff 0%, #f3f7f4 100%);
            box-shadow: var(--md-shadow);
            padding: 1.2rem 1.25rem;
            margin-bottom: 1rem;
        }
        .tutorial-title {
            color: var(--md-text);
            font-size: 1.08rem;
            font-weight: 760;
            margin-bottom: 0.25rem;
        }
        .tutorial-copy {
            color: var(--md-text-soft);
            font-size: 0.95rem;
            line-height: 1.5;
            margin-bottom: 0.9rem;
        }
        .tutorial-steps {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.75rem;
        }
        .tutorial-step {
            border-radius: 16px;
            border: 1px solid var(--md-outline);
            background: #fbfcfb;
            padding: 0.9rem;
        }
        .tutorial-step-number {
            width: 1.7rem;
            height: 1.7rem;
            border-radius: 999px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: var(--md-primary);
            color: white;
            font-size: 0.78rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        .tutorial-step-title {
            color: var(--md-text);
            font-size: 0.95rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
        }
        .tutorial-step-copy {
            color: var(--md-text-soft);
            font-size: 0.88rem;
            line-height: 1.45;
        }
        .customer-note {
            border-left: 4px solid var(--md-primary);
            padding-left: 0.9rem;
            color: var(--md-text-soft);
            font-size: 0.95rem;
            line-height: 1.55;
            margin: 0.9rem 0 0 0;
        }
        .hero-actions {
            display: grid;
            grid-template-columns: 1.1fr 1fr 1fr;
            gap: 0.8rem;
            margin-top: 1.1rem;
        }
        .landing-secondary {
            margin-top: 0.95rem;
        }
        .hero-subproof {
            display: flex;
            flex-wrap: wrap;
            gap: 0.6rem;
            margin-top: 1rem;
        }
        .hero-proof-pill {
            border-radius: 999px;
            padding: 0.45rem 0.75rem;
            border: 1px solid #dce9e2;
            background: #f3f8f4;
            color: var(--md-primary);
            font-size: 0.84rem;
            font-weight: 600;
        }
        .mini-funnel {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.85rem;
            margin: 1rem 0 0.9rem 0;
        }
        .mini-funnel-card {
            border-radius: 18px;
            border: 1px solid var(--md-outline);
            background: #fbfcfb;
            padding: 1rem;
        }
        .mini-funnel-kicker {
            color: var(--md-primary);
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.35rem;
        }
        .mini-funnel-title {
            color: var(--md-text);
            font-size: 1rem;
            font-weight: 720;
            margin-bottom: 0.2rem;
        }
        .mini-funnel-copy {
            color: var(--md-text-soft);
            font-size: 0.9rem;
            line-height: 1.45;
        }
        .landing-story {
            display: grid;
            grid-template-columns: 1.2fr 0.8fr;
            gap: 1rem;
            margin-top: 1rem;
        }
        .story-panel {
            border-radius: 20px;
            border: 1px solid var(--md-outline);
            background: rgba(255,255,255,0.88);
            padding: 1.25rem 1.35rem;
        }
        .story-title {
            color: var(--md-text);
            font-size: 1.05rem;
            font-weight: 720;
            margin-bottom: 0.45rem;
        }
        .story-copy {
            color: var(--md-text-soft);
            font-size: 0.94rem;
            line-height: 1.6;
        }
        .section-title {
            font-weight: 700;
            color: var(--md-text);
            margin-bottom: 0.25rem;
            font-size: 1.15rem;
        }
        .section-copy {
            color: var(--md-text-soft);
            line-height: 1.55;
            font-size: 0.96rem;
        }
        .step-pill, .status-pill {
            display: inline-block;
            border-radius: 999px;
            padding: 0.36rem 0.78rem;
            font-size: 0.82rem;
            font-weight: 700;
            margin-bottom: 0.8rem;
            border: 1px solid transparent;
        }
        .step-pill {
            background: var(--md-primary-container);
            color: var(--md-on-primary-container);
            border-color: rgba(51, 93, 80, 0.12);
        }
        .progress-strip {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.85rem;
            margin-bottom: 1rem;
        }
        .progress-card {
            border-radius: 18px;
            border: 1px solid var(--md-outline);
            background: #f7fbf8;
            padding: 1rem;
        }
        .progress-number {
            width: 1.8rem;
            height: 1.8rem;
            border-radius: 999px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: var(--md-primary);
            color: white;
            font-size: 0.82rem;
            font-weight: 700;
            margin-bottom: 0.55rem;
        }
        .progress-title {
            color: var(--md-text);
            font-size: 0.96rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }
        .progress-copy {
            color: var(--md-text-soft);
            font-size: 0.9rem;
            line-height: 1.45;
        }
        .wizard-strip {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.85rem;
            margin-bottom: 1rem;
        }
        .wizard-step {
            border-radius: 18px;
            border: 1px solid var(--md-outline);
            background: rgba(255,255,255,0.74);
            padding: 1rem;
        }
        .wizard-step.active {
            border-color: rgba(51, 93, 80, 0.22);
            background: linear-gradient(180deg, #f6fbf8 0%, #ebf3ef 100%);
            box-shadow: inset 0 0 0 1px rgba(51, 93, 80, 0.08);
        }
        .wizard-step.done {
            border-color: rgba(74, 99, 89, 0.18);
            background: #f9fcfa;
        }
        .wizard-step-number {
            width: 1.75rem;
            height: 1.75rem;
            border-radius: 999px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: #dfe8e2;
            color: var(--md-primary);
            font-size: 0.82rem;
            font-weight: 700;
            margin-bottom: 0.45rem;
        }
        .wizard-step.active .wizard-step-number,
        .wizard-step.done .wizard-step-number {
            background: var(--md-primary);
            color: white;
        }
        .wizard-step-title {
            color: var(--md-text);
            font-size: 0.96rem;
            font-weight: 720;
            margin-bottom: 0.2rem;
        }
        .wizard-step-copy {
            color: var(--md-text-soft);
            font-size: 0.88rem;
            line-height: 1.45;
        }
        .status-success {
            background: #d9f2e3;
            color: #165c3a;
            border-color: rgba(22, 92, 58, 0.14);
        }
        .status-warning {
            background: #fff1cf;
            color: #7d5700;
            border-color: rgba(125, 87, 0, 0.16);
        }
        .status-fail {
            background: var(--md-error-container);
            color: #8c1d18;
            border-color: rgba(140, 29, 24, 0.18);
        }
        .summary-strip {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.85rem;
            margin: 0.8rem 0 1rem 0;
        }
        .artifact-title {
            font-size: 1rem;
            font-weight: 700;
            color: var(--md-text);
            margin-bottom: 0.25rem;
        }
        .artifact-copy {
            color: var(--md-text-soft);
            font-size: 0.92rem;
            line-height: 1.45;
        }
        .workspace-title {
            font-size: 1.45rem;
            line-height: 1.15;
            letter-spacing: -0.03em;
            color: var(--md-text);
            margin-bottom: 0.25rem;
            font-weight: 760;
        }
        .workspace-copy {
            color: var(--md-text-soft);
            font-size: 0.97rem;
            line-height: 1.55;
            margin-bottom: 1rem;
        }
        .mini-kpis {
            display: grid;
            grid-template-columns: repeat(3, minmax(0,1fr));
            gap: 0.8rem;
            margin-top: 1rem;
        }
        .mini-kpi {
            padding: 0.9rem 1rem;
            border-radius: 18px;
            background: #f7fbf8;
            border: 1px solid var(--md-outline);
        }
        .mini-kpi-label {
            color: var(--md-text-muted);
            font-size: 0.84rem;
            margin-bottom: 0.2rem;
        }
        .mini-kpi-value {
            color: var(--md-text);
            font-weight: 760;
            font-size: 1.15rem;
        }
        .plain-list {
            margin: 0;
            padding-left: 1rem;
            color: var(--md-text-soft);
            line-height: 1.6;
        }
        .metric-grid, .fact-grid {
            display: grid;
            gap: 0.85rem;
            margin: 0.8rem 0 0;
        }
        .metric-grid {
            grid-template-columns: repeat(4, minmax(0, 1fr));
            margin-bottom: 1rem;
        }
        .fact-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .metric-card, .fact-card {
            padding: 1rem 1.05rem;
            border-radius: 18px;
            background: linear-gradient(180deg, #ffffff 0%, #f4f8f5 100%);
            border: 1px solid var(--md-outline);
            box-shadow: 0 10px 24px rgba(18, 41, 33, 0.04);
        }
        .metric-value, .fact-value {
            color: var(--md-text);
            font-size: 1.2rem;
            font-weight: 800;
            letter-spacing: -0.02em;
        }
        .metric-label, .fact-label {
            color: var(--md-text-muted);
            font-size: 0.82rem;
            margin-bottom: 0.32rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }
        .fact-value {
            font-size: 1rem;
            font-family: "Roboto Mono", ui-monospace, monospace;
            overflow-wrap: anywhere;
        }
        .issue-cluster {
            border-radius: 18px;
            padding: 0.95rem 1rem;
            margin: 0.85rem 0 0.65rem 0;
            border: 1px solid var(--md-outline);
            background: #fff;
        }
        .issue-cluster-title {
            color: var(--md-text);
            font-size: 0.95rem;
            font-weight: 760;
            margin-bottom: 0.2rem;
        }
        .issue-cluster-copy {
            color: var(--md-text-soft);
            font-size: 0.9rem;
            line-height: 1.45;
        }
        .issue-cluster.error {
            background: linear-gradient(180deg, #fff7f6 0%, #fdf0ef 100%);
            border-color: rgba(179, 38, 30, 0.16);
        }
        .issue-cluster.warning {
            background: linear-gradient(180deg, #fff9ef 0%, #fff2da 100%);
            border-color: rgba(125, 87, 0, 0.16);
        }
        .issue-cluster.info {
            background: linear-gradient(180deg, #f5fbf7 0%, #edf6f0 100%);
            border-color: rgba(51, 93, 80, 0.14);
        }
        .stButton > button, .stDownloadButton > button {
            border-radius: 14px;
            font-weight: 700;
            min-height: 2.95rem;
            transition: transform 120ms ease, box-shadow 120ms ease, border-color 120ms ease, background 120ms ease;
        }
        .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
            background: var(--md-primary);
            color: var(--md-on-primary);
            border: 1px solid var(--md-primary);
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.3), 0 1px 3px 1px rgba(0, 0, 0, 0.15);
        }
        .stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover {
            background: #5A4499; /* A slightly darker version of --md-primary */
            color: var(--md-on-primary);
            transform: translateY(-1px);
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.3), 0 2px 6px 2px rgba(0, 0, 0, 0.15);
        }
        .stButton > button[kind="secondary"] {
            border: 1px solid var(--md-outline);
            color: var(--md-primary);
            background: rgba(255,255,255,0.92);
            box-shadow: 0 6px 16px rgba(18, 41, 33, 0.03);
        }
        .stButton > button[kind="secondary"]:hover, .stDownloadButton > button[kind="secondary"]:hover {
            border-color: var(--md-outline-strong);
            background: #f5f8f6;
            transform: translateY(-1px);
        }
        .stButton > button:focus-visible, .stDownloadButton > button:focus-visible,
        div[data-baseweb="input"] input:focus, textarea:focus {
            outline: 3px solid rgba(51, 93, 80, 0.18);
            outline-offset: 2px;
            box-shadow: 0 0 0 1px rgba(51, 93, 80, 0.32);
        }
        div[data-baseweb="input"] input,
        div[data-baseweb="base-input"] input,
        div[data-baseweb="textarea"] textarea {
            background: rgba(255, 255, 255, 0.92);
            border-radius: 14px;
            color: var(--md-text);
        }
        div[data-baseweb="input"] > div,
        div[data-baseweb="base-input"] > div,
        div[data-baseweb="textarea"] > div,
        div[data-baseweb="select"] > div {
            border-radius: 14px !important;
            border-color: var(--md-outline) !important;
            background: rgba(255, 255, 255, 0.92) !important;
            box-shadow: none !important;
        }
        div[data-testid="stDateInput"] > div,
        div[data-testid="stNumberInput"] > div {
            border-radius: 14px;
        }
        div[data-testid="stFileUploaderDropzone"] {
            border-radius: 20px;
            border: 1.5px dashed var(--md-outline);
            background: linear-gradient(180deg, var(--md-surface) 0%, var(--md-surface-soft) 100%);
            padding-top: 1.1rem;
            padding-bottom: 1.1rem;
        }
        div[data-testid="stFileUploaderDropzone"]:hover {
            border-color: var(--md-primary);
            background: linear-gradient(180deg, var(--md-surface-soft) 0%, var(--md-surface-variant) 100%);
        }
        div[data-testid="stDataFrame"] {
            border-radius: 18px;
            overflow: hidden;
            border: 1px solid var(--md-outline);
            background: rgba(255, 255, 255, 0.92);
        }
        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid var(--md-outline);
            padding: 1rem;
            border-radius: 18px;
            box-shadow: 0 12px 30px rgba(20, 46, 40, 0.04);
        }
        div[data-testid="stAlert"] {
            border-radius: 18px;
            border: 1px solid var(--md-outline);
            background: rgba(255, 255, 255, 0.94);
        }
        div[data-testid="stExpander"] {
            border: 1px solid var(--md-outline);
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.78);
        }
        @media (max-width: 900px) {
            .trust-grid, .summary-strip, .progress-strip, .proof-grid, .mini-kpis, .feature-band, .tutorial-steps, .hero-actions, .mini-funnel, .landing-story, .wizard-strip, .metric-grid, .fact-grid {
                grid-template-columns: 1fr;
            }
            .hero-title {
                font-size: 2.1rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_app_shell() -> str:
    brand_col, meta_col = st.columns([1.45, 0.9])
    with brand_col:
        st.markdown(
            """
            <div class="app-shell">
                <div class="shell-brand">ACHLint</div>
                <div class="shell-subtitle">A focused ACH file workspace for spreadsheet-driven payroll and payout operations.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with meta_col:
        st.markdown(
            """
            <div class="app-shell">
                <div class="shell-meta">
                    <strong>Focused scope.</strong> PPD credits only. One batch per file. Validation happens before ACH download so operators can catch issues earlier.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    nav_cols = st.columns(5)
    pages = ["Landing", "Generate", "Validate", "Results", "Help"]
    for col, page_name in zip(nav_cols, pages):
        with col:
            button_type = "primary" if st.session_state.get("page") == page_name else "secondary"
            if st.button(page_name, use_container_width=True, type=button_type):
                st.session_state["page"] = page_name
                st.rerun()
    return st.session_state["page"]


def render_landing() -> None:
    render_onboarding_tour()
    st.markdown(
        f"""
        <div class="hero-card">
            <div class="eyebrow">{UI_COPY["landing_eyebrow"]}</div>
            <div class="sales-problem">{UI_COPY["landing_problem"]}</div>
            <div class="hero-title">{UI_COPY["landing_title"]}</div>
            <div class="hero-copy">
                {UI_COPY["landing_body"]}
            </div>
            <div class="hero-minimal-proof">{UI_COPY["landing_proof"]}</div>
            <div class="customer-note">
                {UI_COPY["landing_note"]}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cta1, cta2, cta3 = st.columns([1.25, 1, 1])
    with cta1:
        if st.button(UI_COPY["cta_primary"], use_container_width=True, type="primary"):
            st.session_state["show_tour"] = False
            st.session_state["page"] = "Generate"
            st.rerun()
    with cta2:
        st.download_button(
            UI_COPY["cta_template"],
            data=get_template_csv(),
            file_name="achlint_template.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with cta3:
        if st.button(UI_COPY["cta_validate"], use_container_width=True):
            st.session_state["page"] = "Validate"
            st.rerun()

    st.markdown(
        """
        <div class="mini-funnel">
            <div class="mini-funnel-card">
                <div class="mini-funnel-kicker">Step 1</div>
                <div class="mini-funnel-title">Bring your spreadsheet</div>
                <div class="mini-funnel-copy">Use the template or your existing payout CSV with the supported columns.</div>
            </div>
            <div class="mini-funnel-card">
                <div class="mini-funnel-kicker">Step 2</div>
                <div class="mini-funnel-title">Fix issues before upload</div>
                <div class="mini-funnel-copy">ACHLint flags blocking errors and explains them in operator-friendly language.</div>
            </div>
            <div class="mini-funnel-card">
                <div class="mini-funnel-kicker">Step 3</div>
                <div class="mini-funnel-title">Download ready-to-use artifacts</div>
                <div class="mini-funnel-copy">Leave with the ACH file, validation report, and exceptions CSV for follow-up.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="landing-story">
            <div class="story-panel">
                <div class="story-title">Why customers use ACHLint</div>
                <div class="story-copy">
                    Most small teams do not need a full treasury platform. They need one thing: a fast, trustworthy way to turn spreadsheet payment data into a file their bank will accept without forcing them to learn NACHA formatting under pressure.
                </div>
            </div>
            <div class="story-panel">
                <div class="story-title">What makes the workflow credible</div>
                <div class="story-copy">
                    ACHLint stays intentionally narrow, validates before download, and explains issues in plain language. That makes the product feel safer than a generic converter or a broad “all ACH” promise.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("See product details", expanded=False):
        st.write("• PPD credits only")
        st.write("• One batch per file")
        st.write("• ACH file, validation PDF, and exceptions CSV output")
        st.write("• Validate mode for existing ACH files")


def render_generate() -> None:
    st.markdown('<div class="eyebrow">Generate Mode</div>', unsafe_allow_html=True)
    render_generate_helper()
    st.markdown(
        """
        <div class="workspace-card">
            <div class="workspace-title">Create a validated ACH file</div>
            <div class="workspace-copy">
                This workspace is designed for the natural operator flow: bring in the spreadsheet, confirm company and bank settings,
                review what blocks the file, then generate artifacts when everything is clean.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    csv_file = st.file_uploader("Payments CSV", type=["csv"], key="generate_csv", label_visibility="collapsed")
    preview_rows, preview_issues = parse_payment_csv(csv_file.getvalue()) if csv_file is not None else ([], [])
    config = build_originator_config_from_session()
    step = st.session_state.get("generate_step", 1)
    render_generate_wizard(step, csv_file is not None, preview_issues)

    nav1, nav2, nav3 = st.columns([1, 1, 1.4])
    with nav1:
        if st.button("Step 1: Upload", use_container_width=True, type="secondary", key="step_1_nav"):
            st.session_state["generate_step"] = 1
            st.rerun()
    with nav2:
        if st.button("Step 2: Settings", use_container_width=True, type="secondary", key="step_2_nav"):
            st.session_state["generate_step"] = 2 if csv_file is not None else 1
            st.rerun()
    with nav3:
        if st.button("Step 3: Review & Generate", use_container_width=True, type="secondary", key="step_3_nav"):
            st.session_state["generate_step"] = 3 if csv_file is not None else 1
            st.rerun()

    if step == 1:
        render_generate_upload_step(csv_file, preview_rows, preview_issues)
    elif step == 2:
        render_generate_settings_step(csv_file)
    else:
        render_generate_review_step(csv_file, preview_rows, preview_issues, config)


def render_validate() -> None:
    st.markdown('<div class="eyebrow">Validate Mode</div>', unsafe_allow_html=True)
    render_validate_helper()
    st.markdown(
        """
        <div class="workspace-card">
            <div class="workspace-title">Inspect an existing ACH file before upload</div>
            <div class="workspace-copy">
                Use this mode when you already have a generated ACH file and want a fast confidence check on record order,
                totals, padding, and MVP support constraints.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    left, right = st.columns([0.95, 1.05])

    with left:
        render_section_card(
            "What ACHLint checks",
            """
            - 94-character fixed-width records
            - File and batch record order
            - Entry counts, entry hash, and totals
            - PPD credits-only constraints for this MVP
            - Padding and block count rules
            """,
        )

    with right:
        st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Upload an ACH file</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-copy">Use this mode to understand what happened in an existing ACH file before you upload it or send it back for correction.</div>',
            unsafe_allow_html=True,
        )
        ach_file = st.file_uploader("Upload .ach file", type=["ach", "txt"], key="validate_ach", label_visibility="collapsed")
        if ach_file is None:
            render_empty_state(
                "No file uploaded yet",
                "Upload an existing ACH/NACHA file to inspect structure, totals, record order, and padding before the next bank upload attempt.",
            )
        elif st.button("Run validation", type="primary", use_container_width=True):
            with st.spinner(UI_COPY["validate_loading"]):
                validation = handle_validate(ach_file.getvalue().decode("ascii", errors="replace"))
            st.session_state["latest_result"] = validation
            st.session_state["page"] = "Results"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def render_results() -> None:
    result = st.session_state.get("latest_result")
    st.markdown('<div class="eyebrow">Results</div>', unsafe_allow_html=True)
    st.markdown("## Your validation outcome")
    if result is None:
        render_empty_state("No results yet", "Run Generate or Validate to see your validation outcome and download artifacts here.")
        return

    badge_class, headline, copy = result_banner(result)
    st.markdown(
        f"""
        <div class="hero-card">
            <div class="status-pill {badge_class}">{result.status.replace('_', ' ').upper()}</div>
            <div class="hero-title" style="font-size:2rem;">{headline}</div>
            <div class="hero-copy">{copy}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    action1, action2 = st.columns(2)
    with action1:
        if st.button("Start a new generation run", use_container_width=True):
            st.session_state["page"] = "Generate"
            st.session_state["generate_step"] = 1
            st.rerun()
    with action2:
        if st.button("Validate another file", use_container_width=True):
            st.session_state["page"] = "Validate"
            st.rerun()

    if isinstance(result, BuildResult):
        readiness = UI_COPY["results_ready"] if result.ach_text else UI_COPY["results_not_ready"]
        st.info(f"Outcome: {readiness}. Review the summary below, then choose the next action.")
    else:
        st.info("Outcome: Validation complete. Review the grouped issues below before the next upload attempt.")

    render_summary_metrics(
        [
            ("Entries", str(result.summary.entries)),
            ("Total credit", f"${result.summary.total_credit_cents / 100:,.2f}"),
            ("Blocking issues", str(result.summary.errors)),
            ("Warnings", str(result.summary.warnings)),
        ]
    )

    render_issue_groups(result.issues, empty_message="No issues were found in this run.")

    st.markdown("### Downloads")
    download_col1, download_col2, download_col3 = st.columns(3)
    with download_col1:
        st.markdown(
            """
            <div class="artifact-card">
                <div class="artifact-title">ACH file</div>
                <div class="artifact-copy">This file is available only when the run passes without blocking issues and is ready for bank upload.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if isinstance(result, BuildResult) and result.ach_text:
            st.download_button(
                "Download payments.ach",
                data=result.ach_text.encode("ascii"),
                file_name="payments.ach",
                mime="text/plain",
                use_container_width=True,
            )
        else:
            st.button("ACH file not available", disabled=True, use_container_width=True)
    with download_col2:
        st.markdown(
            """
            <div class="artifact-card">
                <div class="artifact-title">Validation report</div>
                <div class="artifact-copy">Human-readable PDF with summary totals, issue details, and next-step guidance.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.download_button(
            "Download validation_report.pdf",
            data=result.report_pdf,
            file_name="validation_report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    with download_col3:
        st.markdown(
            """
            <div class="artifact-card">
                <div class="artifact-title">Exceptions CSV</div>
                <div class="artifact-copy">Machine-friendly issue export for remediation and internal review.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.download_button(
            "Download exceptions.csv",
            data=result.exceptions_csv,
            file_name="exceptions.csv",
            mime="text/csv",
            use_container_width=True,
        )


def render_help() -> None:
    st.markdown('<div class="eyebrow">Help</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="workspace-card">
            <div class="workspace-title">Product scope and operator guidance</div>
            <div class="workspace-copy">
                ACHLint is intentionally narrow so operators can trust what it does today instead of navigating a broad,
                ambiguous ACH platform.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        render_section_card(
            "Supported in v1",
            """
            - PPD credits only
            - One batch per file
            - No addenda records
            - CSV-in to ACH-out workflow
            - Existing ACH validator mode
            """,
        )
    with col2:
        render_section_card(
            "Not supported in v1",
            """
            - Debits
            - CCD, CTX, WEB, TEL, IAT
            - Bank integrations or SFTP push
            - Saved recipients or approval workflows
            - Multi-batch authoring
            """,
        )

    st.warning(
        "ACHLint checks structural and formatting issues for the supported ACH file type. Bank-specific policies, cutoffs, and authorization requirements still apply."
    )
    render_section_card(
        "Recommended workflow",
        """
        1. Download the CSV template and prepare your payout rows.
        2. Review all blocking errors before generating the ACH file.
        3. Keep the validation report alongside the uploaded bank file for operational traceability.
        """,
    )
    c1, c2 = st.columns([1, 1.5])
    with c1:
        if st.button("Show getting-started tutorial", use_container_width=True):
            st.session_state["show_tour"] = True
            st.session_state["page"] = "Landing"
            st.rerun()


def render_onboarding_tour() -> None:
    if not st.session_state.get("show_tour", True):
        return

    st.markdown(
        f"""
        <div class="tutorial-card">
            <div class="tutorial-title">{UI_COPY["tour_title"]}</div>
            <div class="tutorial-copy">
                {UI_COPY["tour_body"]}
            </div>
            <div class="tutorial-steps">
                <div class="tutorial-step">
                    <div class="tutorial-step-number">1</div>
                    <div class="tutorial-step-title">Download the template</div>
                    <div class="tutorial-step-copy">Use the provided CSV so your columns match what the validator expects.</div>
                </div>
                <div class="tutorial-step">
                    <div class="tutorial-step-number">2</div>
                    <div class="tutorial-step-title">Use Generate mode</div>
                    <div class="tutorial-step-copy">Upload your CSV, save your originator settings, and review the readiness panel.</div>
                </div>
                <div class="tutorial-step">
                    <div class="tutorial-step-number">3</div>
                    <div class="tutorial-step-title">Download your artifacts</div>
                    <div class="tutorial-step-copy">When errors are cleared, download the ACH file, validation report, and exceptions CSV.</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns([1, 1, 2.2])
    with c1:
        if st.button(UI_COPY["tour_start"], use_container_width=True, type="primary", key="tour_start"):
            st.session_state["show_tour"] = False
            st.session_state["page"] = "Generate"
            st.rerun()
    with c2:
        if st.button(UI_COPY["tour_hide"], use_container_width=True, key="tour_hide"):
            st.session_state["show_tour"] = False
            st.rerun()
    with c3:
        st.caption("You can reopen this guide anytime from the Help page.")


def render_generate_helper() -> None:
    with st.expander("Quick guide: how Generate works", expanded=False):
        st.write("1. Upload the CSV template with your payment rows.")
        st.write("2. Save your settings for this session.")
        st.write("3. Check the Readiness Review panel for blocking errors.")
        st.write("4. Generate artifacts only when blocking issues are cleared.")


def render_validate_helper() -> None:
    with st.expander("Quick guide: how Validate works", expanded=False):
        st.write("1. Upload an existing `.ach` file.")
        st.write("2. Run validation to inspect structure, totals, and padding.")
        st.write("3. Download the report and exceptions CSV if you need to fix the file.")


def render_originator_form() -> OriginatorConfig:
    values = st.session_state["originator_config_values"]
    with st.form("originator_form", clear_on_submit=False):
        st.markdown("#### Company and bank information")
        company_name = st.text_input("Company name", value=values["company_name"])
        company_identification = st.text_input("Company identification", value=values["company_identification"])
        immediate_destination_routing = st.text_input(
            "Immediate destination routing", value=values["immediate_destination_routing"]
        )
        immediate_destination_name = st.text_input(
            "Immediate destination name", value=values["immediate_destination_name"]
        )
        immediate_origin_routing = st.text_input("Immediate origin routing", value=values["immediate_origin_routing"])
        immediate_origin_name = st.text_input("Immediate origin name", value=values["immediate_origin_name"])

        st.markdown("#### Batch details")
        company_entry_description = st.text_input(
            "Company entry description", value=values["company_entry_description"]
        )
        effective_entry_date = st.date_input("Effective entry date", value=values["effective_entry_date"])
        originating_dfi_identification = st.text_input(
            "Originating DFI identification", value=values["originating_dfi_identification"]
        )
        file_id_modifier = st.text_input("File ID modifier", value=values["file_id_modifier"], max_chars=1)

        with st.expander("Optional fields", expanded=False):
            company_discretionary_data = st.text_input(
                "Company discretionary data", value=values["company_discretionary_data"]
            )
            company_descriptive_date = st.text_input(
                "Company descriptive date", value=values["company_descriptive_date"]
            )
            reference_code = st.text_input("Reference code", value=values["reference_code"])
            trace_number_start = st.number_input(
                "Trace number start",
                min_value=1,
                step=1,
                value=int(values["trace_number_start"]),
            )

        saved = st.form_submit_button("Save settings for this session", use_container_width=True)

    if saved:
        st.session_state["originator_config_values"] = {
            "company_name": company_name,
            "company_identification": company_identification,
            "immediate_destination_routing": immediate_destination_routing,
            "immediate_destination_name": immediate_destination_name,
            "immediate_origin_routing": immediate_origin_routing,
            "immediate_origin_name": immediate_origin_name,
            "company_entry_description": company_entry_description,
            "effective_entry_date": effective_entry_date,
            "originating_dfi_identification": originating_dfi_identification,
            "file_id_modifier": file_id_modifier,
            "company_discretionary_data": company_discretionary_data,
            "company_descriptive_date": company_descriptive_date,
            "reference_code": reference_code,
            "trace_number_start": int(trace_number_start),
        }
        st.success(UI_COPY["settings_saved"])
        values = st.session_state["originator_config_values"]
    else:
        company_discretionary_data = values["company_discretionary_data"]
        company_descriptive_date = values["company_descriptive_date"]
        reference_code = values["reference_code"]
        trace_number_start = values["trace_number_start"]

    return OriginatorConfig(
        company_name=company_name,
        company_identification=company_identification,
        immediate_destination_routing=immediate_destination_routing,
        immediate_destination_name=immediate_destination_name,
        immediate_origin_routing=immediate_origin_routing,
        immediate_origin_name=immediate_origin_name,
        company_entry_description=company_entry_description,
        effective_entry_date=effective_entry_date,
        originating_dfi_identification=originating_dfi_identification,
        file_id_modifier=file_id_modifier,
        company_discretionary_data=company_discretionary_data,
        company_descriptive_date=company_descriptive_date,
        reference_code=reference_code,
        trace_number_start=int(trace_number_start),
    )


def build_originator_config_from_session() -> OriginatorConfig:
    values = st.session_state["originator_config_values"]
    return OriginatorConfig(
        company_name=values["company_name"],
        company_identification=values["company_identification"],
        immediate_destination_routing=values["immediate_destination_routing"],
        immediate_destination_name=values["immediate_destination_name"],
        immediate_origin_routing=values["immediate_origin_routing"],
        immediate_origin_name=values["immediate_origin_name"],
        company_entry_description=values["company_entry_description"],
        effective_entry_date=values["effective_entry_date"],
        originating_dfi_identification=values["originating_dfi_identification"],
        file_id_modifier=values["file_id_modifier"],
        company_discretionary_data=values["company_discretionary_data"],
        company_descriptive_date=values["company_descriptive_date"],
        reference_code=values["reference_code"],
        trace_number_start=int(values["trace_number_start"]),
    )


def render_generate_wizard(step: int, has_csv: bool, preview_issues: list[ValidationIssue]) -> None:
    step1_class = "active" if step == 1 else ("done" if has_csv else "")
    step2_class = "active" if step == 2 else ("done" if step > 2 else "")
    ready_for_review = has_csv
    step3_class = "active" if step == 3 else ("done" if ready_for_review and not count_issues(preview_issues, "error") else "")
    st.markdown(
        f"""
        <div class="wizard-strip">
            <div class="wizard-step {step1_class}">
                <div class="wizard-step-number">1</div>
                <div class="wizard-step-title">Upload CSV</div>
                <div class="wizard-step-copy">Bring in your payout spreadsheet and confirm the file shape.</div>
            </div>
            <div class="wizard-step {step2_class}">
                <div class="wizard-step-number">2</div>
                <div class="wizard-step-title">Confirm settings</div>
                <div class="wizard-step-copy">Review the originator and bank fields used in the ACH headers.</div>
            </div>
            <div class="wizard-step {step3_class}">
                <div class="wizard-step-number">3</div>
                <div class="wizard-step-title">Review and generate</div>
                <div class="wizard-step-copy">Check readiness, then generate only when blocking issues are cleared.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_generate_upload_step(csv_file, preview_rows: list, preview_issues: list[ValidationIssue]) -> None:
    left, right = st.columns([1, 1])
    with left:
        st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
        st.markdown('<div class="step-pill">Step 1</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Upload your payment CSV</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-copy">Start with the ACHLint template if you want the clearest path on your first run.</div>',
            unsafe_allow_html=True,
        )
        st.download_button(
            "Download template",
            data=get_template_csv(),
            file_name="achlint_template.csv",
            mime="text/csv",
            use_container_width=True,
            key="download_template_step1",
        )
        if csv_file is None:
            render_empty_state("Upload required", "Use the uploader above to bring in your payment CSV. Once the file is in place, you can continue to settings.")
        else:
            st.success("Your CSV is in place. Review the preview on the right, then continue to settings.")
            if st.button("Continue to settings", type="primary", use_container_width=True, key="continue_step2"):
                st.session_state["generate_step"] = 2
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">CSV preview</div>', unsafe_allow_html=True)
        if csv_file is None:
            render_empty_state("No preview yet", "Once you upload a CSV, ACHLint will show row counts, totals, and any blocking issues here.")
        else:
            render_summary_metrics(
                [
                    ("Rows parsed", str(len(preview_rows))),
                    ("Total credit", f"${sum(float(row.amount) for row in preview_rows):,.2f}"),
                    ("Blocking issues", str(count_issues(preview_issues, "error"))),
                    ("Warnings", str(count_issues(preview_issues, "warning"))),
                ]
            )
            if preview_rows:
                st.dataframe(
                    [
                        {
                            "Row": row.row_number,
                            "Recipient": row.name,
                            "Routing": row.routing_number,
                            "Account": f"...{row.account_number[-4:]}",
                            "Type": row.account_type.title(),
                            "Amount": f"${row.amount:.2f}",
                        }
                        for row in preview_rows[:15]
                    ],
                    use_container_width=True,
                    hide_index=True,
                )
            render_issue_groups(preview_issues, empty_message="Your CSV preview looks clean so far. You can continue to settings.")
        st.markdown("</div>", unsafe_allow_html=True)


def render_generate_settings_step(csv_file) -> None:
    if csv_file is None:
        render_empty_state("Upload required first", "Start with Step 1 so ACHLint has a payment CSV to work from before you review settings.")
        if st.button("Go to upload step", use_container_width=True, key="back_to_upload_from_settings"):
            st.session_state["generate_step"] = 1
            st.rerun()
        return

    left, right = st.columns([1.08, 0.92])
    with left:
        st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
        st.markdown('<div class="step-pill">Step 2</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Originator settings</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-copy">These values are used in the ACH file header and batch header. Save them for this session, then move to review.</div>',
            unsafe_allow_html=True,
        )
        render_originator_form()
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        config = build_originator_config_from_session()
        st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Current session settings</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-copy">This supporting pane keeps the current ACH header inputs visible while you work, so you do not need to mentally carry the configuration between steps.</div>',
            unsafe_allow_html=True,
        )
        render_fact_grid(
            [
                ("Company", config.company_name),
                ("Entry description", config.company_entry_description),
                ("Effective date", config.effective_entry_date.isoformat()),
                ("Destination routing", config.immediate_destination_routing),
                ("Origin routing", config.immediate_origin_routing),
                ("Trace start", str(config.trace_number_start)),
            ]
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Back to upload", use_container_width=True, key="settings_back_upload"):
                st.session_state["generate_step"] = 1
                st.rerun()
        with c2:
            if st.button("Continue to review", type="primary", use_container_width=True, key="settings_continue_review"):
                st.session_state["generate_step"] = 3
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def render_generate_review_step(csv_file, preview_rows: list, preview_issues: list[ValidationIssue], config: OriginatorConfig) -> None:
    if csv_file is None:
        render_empty_state("Upload required first", "Step 3 works after you upload a CSV and confirm your settings for this session.")
        if st.button("Go to upload step", use_container_width=True, key="back_to_upload_from_review"):
            st.session_state["generate_step"] = 1
            st.rerun()
        return

    left, right = st.columns([1, 1])
    with left:
        st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
        st.markdown('<div class="step-pill">Step 3</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Readiness review</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-copy">This is the final check before generation. If blocking issues remain, fix them before you generate.</div>',
            unsafe_allow_html=True,
        )
        render_summary_metrics(
            [
                ("Rows parsed", str(len(preview_rows))),
                ("Total credit", f"${sum(float(row.amount) for row in preview_rows):,.2f}"),
                ("Blocking issues", str(count_issues(preview_issues, "error"))),
                ("Warnings", str(count_issues(preview_issues, "warning"))),
            ]
        )
        render_issue_groups(preview_issues, empty_message="Your CSV is ready for generation. You can generate artifacts when you are ready.")
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Generation summary</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-copy">Use this panel as the final preflight check. It surfaces the exact identifiers and totals that will shape the file you generate.</div>',
            unsafe_allow_html=True,
        )
        render_fact_grid(
            [
                ("Company", config.company_name),
                ("Effective date", config.effective_entry_date.isoformat()),
                ("Originating DFI", config.originating_dfi_identification),
                ("Destination routing", config.immediate_destination_routing),
                ("Entries", str(len(preview_rows))),
                ("Projected total", f"${sum(float(row.amount) for row in preview_rows):,.2f}"),
            ]
        )
        generate_disabled = csv_file is None
        if st.button("Back to settings", use_container_width=True, key="review_back_settings"):
            st.session_state["generate_step"] = 2
            st.rerun()
        if st.button("Generate ACH artifacts", type="primary", use_container_width=True, disabled=generate_disabled, key="generate_final"):
            with st.spinner(UI_COPY["generate_loading"]):
                result = handle_generate(csv_file.getvalue(), config)
            st.session_state["latest_result"] = result
            st.session_state["page"] = "Results"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def handle_generate(csv_content: bytes, config: OriginatorConfig) -> BuildResult:
    rows, csv_issues = parse_payment_csv(csv_content)
    build_result = build_file(config, rows)
    issues = csv_issues + build_result.issues
    build_result.issues = issues
    build_result.summary.errors = count_issues(issues, "error")
    build_result.summary.warnings = count_issues(issues, "warning")
    if build_result.ach_text:
        validator_result = validate_ach(build_result.ach_text)
        issues.extend(validator_result.issues)
        build_result.summary.errors = count_issues(issues, "error")
        build_result.summary.warnings = count_issues(issues, "warning")
        build_result.status = "failed" if build_result.summary.errors else "success"
        if build_result.status == "failed":
            build_result.ach_text = ""
    build_result.exceptions_csv = build_exceptions_csv(issues)
    build_result.report_pdf = build_report_pdf(
        title="ACHLint Validation Report",
        status="Pass" if build_result.status == "success" else "Fail",
        summary=build_result.summary,
        issues=issues,
    )
    return build_result


def handle_validate(ach_content: str) -> ValidationResult:
    validation = validate_ach(ach_content)
    validation.exceptions_csv = build_exceptions_csv(validation.issues)
    validation.report_pdf = build_report_pdf(
        title="ACHLint ACH Validation Report",
        status=validation.status.replace("_", " ").title(),
        summary=validation.summary,
        issues=validation.issues,
    )
    return validation


def render_section_card(title: str, copy: str) -> None:
    st.markdown(
        f"""
        <div class="section-card">
            <div class="section-title">{title}</div>
            <div class="section-copy">{copy.replace(chr(10), "<br/>")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state(title: str, copy: str) -> None:
    st.markdown(
        f"""
        <div class="section-card">
            <div class="section-title">{title}</div>
            <div class="section-copy">{copy}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_summary_metrics(items: list[tuple[str, str]]) -> None:
    cards = "".join(
        f"""
        <div class="metric-card">
            <div class="metric-label">{escape(label)}</div>
            <div class="metric-value">{escape(value)}</div>
        </div>
        """
        for label, value in items
    )
    st.markdown(f'<div class="metric-grid">{cards}</div>', unsafe_allow_html=True)


def render_fact_grid(items: list[tuple[str, str]]) -> None:
    cards = "".join(
        f"""
        <div class="fact-card">
            <div class="fact-label">{escape(label)}</div>
            <div class="fact-value">{escape(value)}</div>
        </div>
        """
        for label, value in items
    )
    st.markdown(f'<div class="fact-grid">{cards}</div>', unsafe_allow_html=True)


def render_issue_groups(issues: Iterable[ValidationIssue], *, empty_message: str) -> None:
    issues = list(issues)
    if not issues:
        render_empty_state("Ready for the next step", empty_message)
        return

    grouped: dict[str, list[ValidationIssue]] = defaultdict(list)
    for issue in issues:
        grouped[issue.severity].append(issue)

    if grouped.get("error"):
        st.markdown(
            f"""
            <div class="issue-cluster error">
                <div class="issue-cluster-title">Blocking issues</div>
                <div class="issue-cluster-copy">{escape(issue_summary_copy("error", len(grouped["error"])))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.dataframe([issue_to_row(issue) for issue in grouped["error"]], use_container_width=True, hide_index=True)
    if grouped.get("warning"):
        st.markdown(
            f"""
            <div class="issue-cluster warning">
                <div class="issue-cluster-title">Warnings to review</div>
                <div class="issue-cluster-copy">{escape(issue_summary_copy("warning", len(grouped["warning"])))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.dataframe([issue_to_row(issue) for issue in grouped["warning"]], use_container_width=True, hide_index=True)
    if grouped.get("info"):
        st.markdown(
            f"""
            <div class="issue-cluster info">
                <div class="issue-cluster-title">Informational notes</div>
                <div class="issue-cluster-copy">{escape(issue_summary_copy("info", len(grouped["info"])))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.dataframe([issue_to_row(issue) for issue in grouped["info"]], use_container_width=True, hide_index=True)


def issue_to_row(issue: ValidationIssue) -> dict[str, object]:
    location = []
    if issue.row_number:
        location.append(f"Row {issue.row_number}")
    if issue.line_number:
        location.append(f"Line {issue.line_number}")
    return {
        "Severity": ISSUE_TITLE_MAP.get(issue.severity, issue.severity.title()),
        "Code": issue.code,
        "Location": " / ".join(location),
        "Field": issue.field or "",
        "What happened": issue_display_message(issue),
        "Next step": issue_next_step_copy(issue),
        "Original value": issue.original_value or "",
    }


def count_issues(issues: Iterable[ValidationIssue], severity: str) -> int:
    return sum(1 for issue in issues if issue.severity == severity)


def result_banner(result: BuildResult | ValidationResult) -> tuple[str, str, str]:
    if result.status == "success" or result.status == "pass":
        return (
            "status-success",
            UI_COPY["results_pass_title"],
            UI_COPY["results_pass_body"],
        )
    if result.status == "pass_with_warnings":
        return (
            "status-warning",
            UI_COPY["results_warning_title"],
            UI_COPY["results_warning_body"],
        )
    return (
        "status-fail",
        UI_COPY["results_fail_title"],
        UI_COPY["results_fail_body"],
    )


if __name__ == "__main__":
    main()
