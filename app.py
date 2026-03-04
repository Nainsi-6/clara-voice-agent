"""
Streamlit UI: Visual dashboard for Clara automation pipeline.
Shows account status, v1 -> v2 diffs, and changelogs.
"""

import streamlit as st
import json
from pathlib import Path
from datetime import datetime
from pipeline import PipelineOrchestrator

# Page config
st.set_page_config(
    page_title="Clara Automation Pipeline",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 Clara Automation Pipeline Dashboard")
st.markdown("Processing demo calls → v1 agents → onboarding updates → v2 agents")

# Initialize session state
if "pipeline" not in st.session_state:
    st.session_state.pipeline = PipelineOrchestrator()

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select View:", [
    "Overview",
    "Account Status",
    "Version Diff Viewer",
    "Changelog Browser",
    "Manual Processing",
])

# Load all accounts
def get_all_accounts():
    accounts_dir = Path(st.session_state.pipeline.base_output_dir) / "accounts"
    if not accounts_dir.exists():
        return []
    return [d.name for d in accounts_dir.iterdir() if d.is_dir()]

# OVERVIEW PAGE
if page == "Overview":
    st.header("Pipeline Overview")
    
    accounts = get_all_accounts()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Accounts", len(accounts))
    
    with col2:
        v1_count = sum(1 for acc in accounts 
                      if (Path(st.session_state.pipeline.base_output_dir) / "accounts" / acc / "v1").exists())
        st.metric("v1 Created", v1_count)
    
    with col3:
        v2_count = sum(1 for acc in accounts 
                      if (Path(st.session_state.pipeline.base_output_dir) / "accounts" / acc / "v2").exists())
        st.metric("v2 Created", v2_count)
    
    st.markdown("---")
    
    if accounts:
        st.subheader("Account Status Overview")
        
        for account_id in sorted(accounts):
            status = st.session_state.pipeline.get_account_status(account_id)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.write(f"**{account_id}**")
                if status.get("v1_company"):
                    st.caption(status["v1_company"])
            
            with col2:
                if status["v1_exists"]:
                    st.success("✓ v1")
                else:
                    st.error("✗ v1")
            
            with col3:
                if status["v2_exists"]:
                    st.success("✓ v2")
                else:
                    st.warning("- v2")
            
            with col4:
                if status["changelog_exists"]:
                    st.info(f"🔄 {status.get('changes_count', 0)} changes")
                else:
                    st.caption("-")
    else:
        st.info("No accounts processed yet. Use Manual Processing to get started.")

# ACCOUNT STATUS PAGE
elif page == "Account Status":
    st.header("Account Status Details")
    
    accounts = get_all_accounts()
    if not accounts:
        st.warning("No accounts found")
    else:
        selected_account = st.selectbox("Select Account:", sorted(accounts))
        
        status = st.session_state.pipeline.get_account_status(selected_account)
        
        st.json(status)
        
        # Show v1 details
        if status["v1_exists"]:
            st.subheader("v1 Account Memo")
            v1_memo_path = Path(st.session_state.pipeline.base_output_dir) / "accounts" / selected_account / "v1" / "account_memo.json"
            with open(v1_memo_path) as f:
                v1_data = json.load(f)
            
            st.json(v1_data)
            
            # Show system prompt
            prompt_path = Path(st.session_state.pipeline.base_output_dir) / "accounts" / selected_account / "v1" / "system_prompt.txt"
            if prompt_path.exists():
                with open(prompt_path) as f:
                    prompt = f.read()
                st.subheader("System Prompt v1")
                st.text_area("Prompt:", prompt, height=300)
        
        # Show v2 details
        if status["v2_exists"]:
            st.subheader("v2 Account Memo")
            v2_memo_path = Path(st.session_state.pipeline.base_output_dir) / "accounts" / selected_account / "v2" / "account_memo.json"
            with open(v2_memo_path) as f:
                v2_data = json.load(f)
            
            st.json(v2_data)
            
            # Show system prompt
            prompt_path = Path(st.session_state.pipeline.base_output_dir) / "accounts" / selected_account / "v2" / "system_prompt.txt"
            if prompt_path.exists():
                with open(prompt_path) as f:
                    prompt = f.read()
                st.subheader("System Prompt v2")
                st.text_area("Prompt:", prompt, height=300)

# VERSION DIFF VIEWER
elif page == "Version Diff Viewer":
    st.header("v1 → v2 Diff Viewer")
    
    accounts = get_all_accounts()
    if not accounts:
        st.warning("No accounts with versions found")
    else:
        selected_account = st.selectbox("Select Account:", sorted(accounts))
        status = st.session_state.pipeline.get_account_status(selected_account)
        
        if status["v1_exists"] and status["v2_exists"]:
            # Load both memos
            v1_path = Path(st.session_state.pipeline.base_output_dir) / "accounts" / selected_account / "v1" / "account_memo.json"
            v2_path = Path(st.session_state.pipeline.base_output_dir) / "accounts" / selected_account / "v2" / "account_memo.json"
            
            with open(v1_path) as f:
                v1_data = json.load(f)
            with open(v2_path) as f:
                v2_data = json.load(f)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("v1 (Demo)")
                st.json(v1_data)
            
            with col2:
                st.subheader("v2 (After Onboarding)")
                st.json(v2_data)
        else:
            st.info("Both v1 and v2 must exist to compare")

# CHANGELOG BROWSER
elif page == "Changelog Browser":
    st.header("Changelog Browser")
    
    accounts = get_all_accounts()
    if not accounts:
        st.warning("No accounts found")
    else:
        selected_account = st.selectbox("Select Account:", sorted(accounts))
        
        changelog_path = Path(st.session_state.pipeline.base_output_dir) / "accounts" / selected_account / "changelog.json"
        changelog_text_path = Path(st.session_state.pipeline.base_output_dir) / "accounts" / selected_account / "changelog.txt"
        
        if changelog_path.exists():
            st.subheader("Changelog (JSON)")
            with open(changelog_path) as f:
                changelog = json.load(f)
            st.json(changelog)
            
            if changelog_text_path.exists():
                st.subheader("Changelog (Human Readable)")
                with open(changelog_text_path) as f:
                    text = f.read()
                st.text(text)
        else:
            st.info("No changelog found for this account")

# MANUAL PROCESSING
elif page == "Manual Processing":
    st.header("Manual Processing")
    
    tab1, tab2 = st.tabs(["Process Demo", "Process Onboarding"])
    
    with tab1:
        st.subheader("Process Demo Call")
        
        account_id = st.text_input("Account ID:", "acc_001")
        company_name = st.text_input("Company Name (optional):")
        transcript = st.text_area("Demo Transcript:", height=300)
        
        if st.button("Process Demo", key="demo_process"):
            try:
                with st.spinner("Processing demo call..."):
                    acc_id, summary = st.session_state.pipeline.process_demo_call(
                        transcript,
                        account_id,
                        company_name or None
                    )
                st.success(f"✓ Demo processed: {acc_id}")
                st.json(summary)
            except Exception as e:
                st.error(f"✗ Error: {str(e)}")
    
    with tab2:
        st.subheader("Process Onboarding Call")
        
        accounts = get_all_accounts()
        if not accounts:
            st.warning("No accounts found. Process a demo call first.")
        else:
            account_id = st.selectbox("Select Account:", sorted(accounts))
            transcript = st.text_area("Onboarding Transcript:", height=300, key="onboarding_transcript")
            
            if st.button("Process Onboarding", key="onboarding_process"):
                try:
                    with st.spinner("Processing onboarding call..."):
                        acc_id, summary = st.session_state.pipeline.process_onboarding_call(
                            transcript,
                            account_id
                        )
                    st.success(f"✓ Onboarding processed: {acc_id}")
                    st.json(summary)
                except Exception as e:
                    st.error(f"✗ Error: {str(e)}")

st.markdown("---")
st.caption("Clara Automation Pipeline | Zero-Cost Onboarding Automation")
