# Full updated Streamlit app with dual-login (admin with password, players with name-only)
import streamlit as st
import pandas as pd
import os
import json

st.set_page_config(page_title="TUG Rummy", layout="centered")

# Compact UI styling for mobile
st.markdown("""
    <style>
        .stDataFrame div {
            font-size: 13px !important;
        }
        button[kind="formSubmit"] {
            height: 30px !important;
            padding: 0 8px !important;
            font-size: 14px !important;
        }
        .stForm {
            padding: 0.5rem;
            margin-bottom: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='color:#aa0000;'>🃏 <b>TUG Rummy Team</b></h1>", unsafe_allow_html=True)

SAVE_FILE = "rummy_game_state.json"
ADMIN_USER = "admin"
ADMIN_PASS = "password"

# ----------------- Authentication -----------------
def load_auth():
    return st.session_state.get("authenticated", False)

def save_auth():
    st.session_state["authenticated"] = True

def save_guest(name):
    st.session_state["guest_user"] = name
    st.session_state["authenticated"] = False

if "authenticated" not in st.session_state and "guest_user" not in st.session_state:
    with st.form("login_choice"):
        st.markdown("### 🔐 Login")
        login_type = st.radio("Select login type:", ["Admin", "Player"])
        if login_type == "Admin":
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
        else:
            player_name = st.text_input("Your Name")
        submit = st.form_submit_button("➡️ Continue")

    if submit:
        if login_type == "Admin":
            if username == ADMIN_USER and password == ADMIN_PASS:
                save_auth()
                st.success("✅ Admin login successful!")
                st.rerun()
            else:
                st.error("❌ Invalid admin credentials.")
        else:
            if player_name.strip():
                save_guest(player_name.strip())
                st.success(f"👋 Welcome, {player_name.strip()}!")
                st.rerun()
            else:
                st.warning("Please enter your name to continue.")
    st.stop()

is_admin = st.session_state.get("authenticated", False)
is_guest = "guest_user" in st.session_state and not is_admin

# ----------------- Load & Save -----------------
def load_game():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)
        st.session_state.players = data.get("players", [])
        st.session_state.scores = data.get("scores", [])
        st.session_state.player_setup_done = True
        st.session_state.reset_inputs = True

def save_game():
    with open(SAVE_FILE, "w") as f:
        json.dump({
            "players": st.session_state.players,
            "scores": st.session_state.scores
        }, f)

if 'game_reset' in st.session_state and st.session_state.game_reset:
    if os.path.exists(SAVE_FILE):
        os.remove(SAVE_FILE)
    st.session_state.clear()
    st.rerun()

if 'player_setup_done' not in st.session_state:
    st.session_state.player_setup_done = False
    load_game()

# ----------------- Player Setup (Admin Only) -----------------
if not st.session_state.player_setup_done:
    if is_admin:
        st.subheader("👥 Setup Players")
        if 'player_names' not in st.session_state:
            st.session_state.player_names = ["", "", "", ""]  # Default 4 players

        with st.form("player_setup_form"):
            for i, name in enumerate(st.session_state.player_names):
                st.session_state.player_names[i] = st.text_input(f"Player {i+1} Name", value=name, key=f"player_{i}")

            col1, col2 = st.columns(2)
            with col1:
                if len(st.session_state.player_names) < 15:
                    if st.form_submit_button("➕ Add Player"):
                        st.session_state.player_names.append("")
                        st.rerun()

            with col2:
                if st.form_submit_button("✅ Start Game"):
                    cleaned = [name.strip() for name in st.session_state.player_names if name.strip()]
                    if len(cleaned) >= 2:
                        st.session_state.players = cleaned
                        st.session_state.scores = []
                        st.session_state.reset_inputs = True
                        st.session_state.player_setup_done = True
                        save_game()
                        st.rerun()
                    else:
                        st.warning("Please enter at least 2 player names.")
    else:
        st.info("Waiting for admin to start the game.")
    st.stop()

# ----------------- TOTAL SCORES HELPER -----------------
def get_total_scores():
    totals = {p: 0 for p in st.session_state.players}
    for round_scores in st.session_state.scores:
        for p, score in round_scores.items():
            totals[p] += score
    return totals

# ----------------- TOTAL SCORES -----------------
st.subheader("🏆 Total Scores")
totals = get_total_scores()

sorted_unique = sorted(set(totals.values()))
min_score = sorted_unique[0] if sorted_unique else None
second_high = sorted_unique[-2] if len(sorted_unique) > 1 else None
max_score = sorted_unique[-1] if sorted_unique else None

unique_labels = []
name_counts = {}
for name in st.session_state.players:
    score = totals[name]
    label = name
    if score == min_score:
        label += " 🏆TUG"
    count = name_counts.get(label, 0)
    if count:
        label = f"{label} ({count+1})"
    name_counts[label] = count + 1
    unique_labels.append(label)

score_df = pd.DataFrame([[totals[p] for p in st.session_state.players]], columns=unique_labels)

def highlight(val):
    if val == min_score:
        return 'background-color: lightgreen; font-weight: bold'
    elif val == second_high:
        return 'background-color: orange; font-weight: bold'
    elif val == max_score:
        return 'background-color: red; color: white; font-weight: bold'
    return ''

try:
    styled_df = score_df.style.applymap(highlight)
    st.dataframe(styled_df, use_container_width=True)
except:
    st.dataframe(score_df, use_container_width=True)

# ----------------- GUEST MODE -----------------
if is_guest:
    st.markdown("🔒 You are in view-only mode. Only admin can manage scores.")
    st.stop()

# ----------------- PREVIOUS ROUNDS TABLE -----------------
st.markdown("---")
st.subheader("📜 Previous Rounds (Editable Table)")

if st.session_state.scores:
    df_rounds = pd.DataFrame(st.session_state.scores)
    df_rounds.index = [f"{i+1}" for i in range(len(df_rounds))]
    df_rounds.insert(0, "Round No", df_rounds.index)
    st.markdown("Edit scores below and press **Update Table** to save:")
    edited_df = st.data_editor(df_rounds, use_container_width=True, hide_index=True, num_rows="fixed")
    if st.button("✅ Update Table"):
        try:
            updated_scores = []
            for _, row in edited_df.iterrows():
                row_data = {player: int(float(row.get(player))) for player in st.session_state.players}
                updated_scores.append(row_data)
            st.session_state.scores = updated_scores
            save_game()
            st.success("✅ Scores updated successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Invalid input: {e}")
else:
    st.info("No rounds yet.")

# ----------------- ENTER NEW ROUND SCORES -----------------
st.markdown("---")
st.subheader("✍️ Enter New Round Scores")

if 'reset_inputs' not in st.session_state:
    st.session_state.reset_inputs = False

with st.form("new_round_form"):
    new_scores = {}
    for player in st.session_state.players:
        key = f"new_round_{player}"
        default = 0 if st.session_state.reset_inputs else st.session_state.get(key, 0)
        new_scores[player] = st.number_input(f"{player}", min_value=0, value=default, step=1, key=key)
    if st.form_submit_button("📅 Save This Round"):
        st.session_state.scores.append(new_scores.copy())
        st.session_state.reset_inputs = True
        save_game()
        st.rerun()

st.session_state.reset_inputs = False

# ----------------- ADD / REMOVE PLAYER -----------------
st.markdown("---")
st.subheader("⚙️ Add / Remove Player")

remove_player = st.selectbox("❌ Remove Player", options=st.session_state.players)
if st.button("❌ Confirm Remove"):
    st.session_state.players.remove(remove_player)
    for round_score in st.session_state.scores:
        round_score.pop(remove_player, None)
    save_game()
    st.success(f"Removed player: {remove_player}")
    st.rerun()

if len(st.session_state.players) < 15:
    new_player = st.text_input("➕ Add Player (max 15)")
    if st.button("✅ Confirm Add") and new_player and new_player not in st.session_state.players:
        st.session_state.players.append(new_player)
        for round_score in st.session_state.scores:
            round_score[new_player] = 0
        save_game()
        st.success(f"Added player: {new_player}")
        st.rerun()
else:
    st.warning("Maximum 15 players reached.")

# ----------------- END GAME -----------------
st.markdown("---")
st.subheader("🎮 End Game")
if st.button("🛑 Game Complete"):
    st.session_state.game_reset = True
    st.rerun()
