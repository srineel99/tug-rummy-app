import streamlit as st
import pandas as pd
import os
import json

st.set_page_config(page_title="TUG Rummy", layout="centered")

# Compact styling
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
AUTH_FILE = ".auth_state.json"
ADMIN_USER = "admin"
ADMIN_PASS = "password"

# ----------------- Authentication -----------------
def save_auth():
    with open(AUTH_FILE, "w") as f:
        json.dump({"authenticated": True}, f)

def load_auth():
    if os.path.exists(AUTH_FILE):
        try:
            with open(AUTH_FILE, "r") as f:
                return json.load(f).get("authenticated", False)
        except:
            return False
    return False

def clear_auth():
    if os.path.exists(AUTH_FILE):
        os.remove(AUTH_FILE)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = load_auth()

if not st.session_state.authenticated:
    with st.form("login_form"):
        st.markdown("### 🔐 Admin Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login = st.form_submit_button("🔓 Login")
    if login:
        if username == ADMIN_USER and password == ADMIN_PASS:
            st.session_state.authenticated = True
            save_auth()
            st.success("✅ Login successful!")
            st.rerun()
        else:
            st.error("❌ Invalid credentials")
    st.stop()

is_admin = st.session_state.authenticated

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
    clear_auth()
    st.session_state.clear()
    st.rerun()

if 'player_setup_done' not in st.session_state:
    st.session_state.player_setup_done = False
    load_game()

if not st.session_state.player_setup_done:
    if is_admin:
        st.subheader("👥 Setup Players")
        with st.form("player_setup_form"):
            num_players = st.number_input("Number of Players", min_value=2, max_value=15, value=4)
            player_names = [st.text_input(f"Player {i+1} Name", key=f"player_{i}") for i in range(int(num_players))]
            submitted = st.form_submit_button("✅ Start Game")
        if submitted and all(name.strip() for name in player_names):
            st.session_state.players = player_names
            st.session_state.scores = []
            st.session_state.reset_inputs = True
            st.session_state.player_setup_done = True
            save_game()
            st.rerun()
        elif submitted:
            st.warning("Please enter all player names.")
    else:
        st.info("Waiting for admin to start the game.")
    st.stop()

# ----------------- TOTAL SCORES -----------------
def get_total_scores():
    totals = {p: 0 for p in st.session_state.players}
    for round_scores in st.session_state.scores:
        for p, score in round_scores.items():
            totals[p] += score
    return totals

st.subheader("🏆 Total Scores")
totals = get_total_scores()
score_df = pd.DataFrame([[totals[p] for p in st.session_state.players]], columns=st.session_state.players)
st.dataframe(score_df.style, use_container_width=True)

# ----------------- PREVIOUS ROUNDS (Grid Edit) -----------------
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
                row_data = {}
                for player in st.session_state.players:
                    value = row.get(player, "")
                    if isinstance(value, (int, float, str)) and str(value).strip().isdigit():
                        row_data[player] = int(value)
                    else:
                        raise ValueError("Invalid score")
                updated_scores.append(row_data)
            st.session_state.scores = updated_scores
            save_game()
            st.success("✅ Scores updated successfully!")
            st.rerun()
        except:
            st.error("❌ Please enter valid numbers only.")
else:
    st.info("No rounds yet.")

# ----------------- ENTER NEW ROUND SCORES -----------------
st.markdown("---")
st.subheader("✍️ Enter New Round Scores")

if 'reset_inputs' not in st.session_state:
    st.session_state.reset_inputs = False

if is_admin:
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
else:
    st.info("Only admin can enter scores.")

st.session_state.reset_inputs = False

# ----------------- ADD / REMOVE PLAYER -----------------
st.markdown("---")
st.subheader("⚙️ Add / Remove Player")

if is_admin:
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
else:
    st.info("Only admin can modify players.")

# ----------------- END GAME -----------------
st.markdown("---")
st.subheader("🎮 End Game")
if is_admin and st.button("🛑 Game Complete"):
    st.session_state.game_reset = True
    st.rerun()
