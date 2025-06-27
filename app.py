import streamlit as st
import pandas as pd
import os
import json

# ----------------- CONFIG + CSS -----------------
st.set_page_config(page_title="TUG Rummy", layout="centered")
st.markdown("""
    <style>
        .stNumberInput, .stTextInput, .stSelectbox, .stButton {
            padding: 2px !important;
            margin: 2px !important;
        }
        div[data-testid="column"] {
            padding: 0px 2px !important;
        }
        section.main > div {
            padding-top: 0.5rem;
        }
        h1, h2, h3, h4, h5 {
            margin: 0.5rem 0 !important;
        }
        .stForm {
            padding: 0.25rem 0.5rem;
            border: 1px solid #ddd;
            border-radius: 6px;
            margin-bottom: 6px;
        }
        input {
            font-size: 12px !important;
            height: 28px !important;
            padding: 2px !important;
            text-align: center;
        }
        button[kind="formSubmit"] {
            height: 28px !important;
            padding: 0 6px !important;
            font-size: 12px !important;
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
sorted_scores = sorted(set(totals.values()))
min_score = sorted_scores[0] if sorted_scores else None
second_high = sorted_scores[-2] if len(sorted_scores) > 1 else None
max_score = sorted_scores[-1] if sorted_scores else None

labelled = {}
for player, score in totals.items():
    label = player
    if score == min_score:
        label += " 🏆 TUG"
    elif score == max_score:
        label += " 🥇"
    elif score == second_high:
        label += " 🥈"
    labelled[player] = label

score_df = pd.DataFrame([[totals[p] for p in totals]], columns=[labelled[p] for p in totals])
st.dataframe(score_df.style, use_container_width=True)

# ----------------- PREVIOUS ROUNDS (Editable Clean Table) -----------------
st.markdown("---")
st.subheader("📜 Previous Rounds (Editable)")

if st.session_state.scores:
    players = st.session_state.players

    # Header row
    header_cols = st.columns(len(players) + 2)
    header_cols[0].markdown("**Round**")
    for j, player in enumerate(players):
        header_cols[j + 1].markdown(f"**{player}**")
    header_cols[-1].markdown("")

    for i, round_scores in enumerate(st.session_state.scores):
        with st.form(f"round_edit_form_{i}", clear_on_submit=False):
            cols = st.columns(len(players) + 2)
            cols[0].markdown(f"Round {i+1}")
            round_updated = {}
            for j, player in enumerate(players):
                val = round_scores.get(player, 0)
                round_updated[player] = cols[j + 1].text_input(
                    "", value=str(val), key=f"r{i}_{player}",
                    label_visibility="collapsed", placeholder="0"
                )
            update_button = cols[-1].form_submit_button("🔄")
            if update_button and is_admin:
                try:
                    for k in round_updated:
                        round_updated[k] = int(round_updated[k])
                    st.session_state.scores[i] = round_updated
                    save_game()
                    st.success(f"✅ Round {i+1} updated.")
                    st.rerun()
                except ValueError:
                    st.warning("All scores must be valid numbers.")
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
