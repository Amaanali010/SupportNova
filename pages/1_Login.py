# pages/1_Login.py
# Streamlit Login page supporting role-based authentication.

import streamlit as st
from security.auth import authenticate_user

st.set_page_config(page_title="Login - SupportNova", page_icon="🔑", layout="centered")

st.title("🔑 User Login")
st.caption("Sign in with your VoltKart staff or customer credentials.")

if st.session_state.get("authenticated", False):
    user = st.session_state.user
    st.success(f"You are currently logged in as **{user['username']}** ({user['role'].upper()}).")
    if st.button("Log Out", type="primary"):
        st.session_state.authenticated = False
        st.session_state.user = None
        st.rerun()
else:
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign In", use_container_width=True)

        if submitted:
            if not username or not password:
                st.error("Please enter both username and password.")
            else:
                user_info = authenticate_user(username, password)
                if user_info:
                    st.session_state.authenticated = True
                    st.session_state.user = user_info
                    st.success(f"Welcome back, {user_info['full_name']}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

    st.divider()
    st.caption("Need test accounts? Use one of the demo logins below:")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        - **Admin**: `admin1` / `admin123`
        - **Manager**: `manager1` / `manager123`
        - **Reviewer**: `reviewer1` / `reviewer123`
        """)
    with col2:
        st.markdown("""
        - **Agent**: `agent1` / `agent123`
        - **Customer**: `customer1` / `customer123`
        """)
