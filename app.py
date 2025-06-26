import streamlit as st
import pandas as pd

# Set wide layout for horizontal scroll
st.set_page_config(page_title="TUG Rummy", layout="wide")

# Initial session state setup
if "players" not in st.session_state:
    st.session_state.players = ["Alice", "Bob", "Charlie", "David"]

if "scores" not in st.session_state:
    st.session_state.scores = []

# Title
st.title("🏆 TUG Rummy Scoreboard")

# Display Total Scores
st.subheader("📊 Total Scores")
if st.session_state.scores:
    score_df = pd.DataFrame(st.session_state.scores).fillna(0).astype(int)
    total_scores = score_df.sum().to_frame().T
    total_scores.columns = st.session_state.players
    st.dataframe(total_scores.style.set_properties(**{"font-weight": "bold"}), use_container_width=True)

# Editable Previous Rounds Table
st.markdown("---")
st.subheader("📜 Previous Rounds (Editable)")

if st.session_state.scores:
    for round_idx, round_data in enumerate(st.session_state.scores):
        with st.form(f"edit_form_{round_idx}"):
            st.write(f"**Round {round_idx + 1}**")
            cols = st.columns(len(st.session_state.players) + 1)
            updated_scores = {}

            for i, player in enumerate(st.session_state.players):
                updated_scores[player] = cols[i].number_input(
                    f"{player}",
                    min_value=0,
                    value=round_data.get(player, 0),
                    step=1,
                    key=f"edit_{round_idx}_{player}"
                )

            if cols[-1].form_submit_button("Update"):
                st.session_state.scores[round_idx] = updated_scores
                st.success(f"✅ Round {round_idx + 1} updated!")
                st.rerun()

# New Round Entry
st.markdown("---")
st.subheader("✍️ Enter New Round Scores")

with st.form("new_round_form"):
    new_scores = {}
    cols = st.columns(len(st.session_state.players))

    for i, player in enumerate(st.session_state.players):
        key = f"new_input_{player}_{len(st.session_state.scores)}"
        new_scores[player] = cols[i].number_input(
            f"{player}", min_value=0, value=0, step=1, key=key
        )

    if st.form_submit_button("📅 Save This Round"):
        st.session_state.scores.append(new_scores.copy())
        st.success("✅ New round saved!")
        st.rerun()
