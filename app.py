import pandas as pd
import streamlit as st

st.set_page_config(page_title="Lead Triage Copilot", layout="wide")
st.title("Lead Triage Copilot")
st.caption("Ranked leads with reasoning. Nothing is sent without your approval.")

CSV = "data/leads_top.csv"


def load():
    if "df" not in st.session_state:
        st.session_state.df = pd.read_csv(CSV)
    return st.session_state.df


df = load()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Leads shown", len(df))
c2.metric("Approved", (df["status"] == "approved").sum())
c3.metric("Rejected", (df["status"] == "rejected").sum())
c4.metric("Pending", (df["status"] == "pending").sum())

st.divider()

for i, row in df.iterrows():
    header = f"#{i+1} — {row['company_name']}  •  score {row['score']}  •  {row['status']}"
    with st.expander(header):
        col_left, col_right = st.columns([3, 2])

        with col_left:
            st.markdown(f"**Industry:** {row['industry']}  |  **Size:** {row['company_size']}")
            st.markdown(f"**Engagement:** {row['engagement_score']}  |  **Stage:** {row['deal_stage']}  |  **Stale:** {row['is_stale']}")
            st.markdown(f"**Notes:** {row['notes']}")
            st.markdown(f"**Past deal value:** {row['past_deal_value']}  |  **Days since contact:** {row['days_since_contact']}")

            st.markdown("---")
            st.markdown("**Why the model ranked it here**")
            st.info(row["reasoning"])

            st.markdown("**Trace**")
            st.caption(f"Cited fields: `{row['cited_fields']}`")
            st.caption(f"Similar past wins: `{row['similar_deal_ids']}`")
            st.caption(f"Model used: `{row['model_used']}`")

        with col_right:
            st.markdown("**Draft outreach message**")
            edited = st.text_area(
                "Edit before approving",
                value=row["draft_message"],
                key=f"draft_{i}",
                height=220,
                label_visibility="collapsed",
            )
            b1, b2, b3 = st.columns(3)
            if b1.button("Approve", key=f"a_{i}", type="primary"):
                st.session_state.df.at[i, "status"] = "approved"
                st.session_state.df.at[i, "draft_message"] = edited
                st.session_state.df.to_csv(CSV, index=False)
                st.rerun()
            if b2.button("Reject", key=f"r_{i}"):
                st.session_state.df.at[i, "status"] = "rejected"
                st.session_state.df.to_csv(CSV, index=False)
                st.rerun()
            if b3.button("Reset", key=f"x_{i}"):
                st.session_state.df.at[i, "status"] = "pending"
                st.session_state.df.to_csv(CSV, index=False)
                st.rerun()

st.divider()
st.caption("The system never sends anything. 'Approved' just marks it ready for a human to send.")