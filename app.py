# app.py
# Main entry point for SupportNova Streamlit web application.
# Handles initialization, custom styling, authentication state, and role navigation.

import streamlit as st
import os
from database.seed import run_seed_if_needed
from security.auth import check_permission

# Set Page Config (Title, Icon, Layout)
st.set_page_config(
    page_title="SupportNova - VoltKart Triage Platform",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for rich, dark glassmorphism design system
CUSTOM_CSS = """
<style>
    /* Main Background & Font Styling */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
        color: #f8fafc;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }

    /* Glassmorphic Container Cards */
    div.css-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }

    /* Gradient Headers */
    .gradient-header {
        background: linear-gradient(90deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.2rem;
        margin-bottom: 0.5rem;
    }

    /* Status Badges */
    .badge-verified {
        background-color: rgba(34, 197, 94, 0.2);
        color: #4ade80;
        border: 1px solid #22c55e;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    .badge-review {
        background-color: rgba(239, 68, 68, 0.2);
        color: #f87171;
        border: 1px solid #ef4444;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    /* Metric Cards */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        color: #38bdf8;
        font-weight: 700;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Run DB seeding on application startup if database is missing or uninitialized
run_seed_if_needed()

# Initialize Session State Variables
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None

def main():
    st.markdown('<h1 class="gradient-header">SupportNova Triage Platform</h1>', unsafe_allow_html=True)
    st.markdown("### Dual-Pipeline Customer Complaint Resolution & Verification Engine for **VoltKart**")

    # Sidebar Navigation & Role Info
    with st.sidebar:
        st.title("🚀 SupportNova")
        if st.session_state.authenticated:
            user = st.session_state.user
            st.success(f"Logged in as: **{user['full_name']}**")
            st.info(f"Role: **{user['role'].upper()}**")
            if st.button("Log Out", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.user = None
                st.rerun()
        else:
            st.warning("🔒 Not Logged In")
            st.caption("Please go to the Login page to access your role workspace.")

    # Home Landing Dashboard Overview
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("🤖 Pipeline 1 (GenAI)")
        st.write("Structured interpretation powered by Groq/Gemini JSON mode. Categorizes issue, extracts sentiment, and drafts customer replies.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("🛡️ Pipeline 2 (Python Matrix)")
        st.write("Independent, zero-AI deterministic rule validation. Enforces mandatory escalations, refund caps, and policy precedence.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("🔍 Comparison Engine")
        st.write("Cross-checks GenAI and Python results. Flags mismatches, prompt injection, and unsupported facts for Manual Review.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Demo Quick Instructions
    st.divider()
    st.markdown("#### 🔑 Quick Demo Credentials")
    st.dataframe(
        [
            {"Role": "Admin", "Username": "admin1", "Password": "admin123", "Capabilities": "Manage rules, documents, and system metrics"},
            {"Role": "Manager", "Username": "manager1", "Password": "manager123", "Capabilities": "Review team analytics and resolution reports"},
            {"Role": "Reviewer", "Username": "reviewer1", "Password": "reviewer123", "Capabilities": "Manual Review queue and override decisions"},
            {"Role": "Agent", "Username": "agent1", "Password": "agent123", "Capabilities": "Agent workspace, AI vs Python comparison view"},
            {"Role": "Customer", "Username": "customer1", "Password": "customer123", "Capabilities": "Submit complaints and track ticket status"}
        ],
        use_container_width=True
    )

if __name__ == "__main__":
    main()
