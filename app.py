import streamlit as st
import pandas as pd
import os
import json

st.set_page_config(page_title="TUG Rummy", layout="centered")
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

# ----------------- Load from Disk -----------------
def load_game():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)
        st.session_state.players = data.get("players", [])
        st.session_state.scores = data.get("scores", [])
        st.session_state.player_setup_done = True
        st.session_state.reset_inputs = True

# ----------------- Save to Disk -----------------
def save_game():
    with open(SAVE_FILE, "w") as f:
        json.dump({
            "players": st.session_state.players,
            "scores": st.session_state.scores
        }, f)

# ----------------- Safe Reset -----------------
if 'game_reset' in st.session_state and st.session_state.game_reset:
    if os.path.exists(SAVE_FILE):
        os.remove(SAVE_FILE)
    clear_auth()
    st.session_state.clear()
    st.rerun()

# ----------------- Player Setup -----------------
if 'player_setup_done' not in st.session_state:
    st.session_state.player_setup_done = False
    load_game()

if not st.session_state.player_setup_done:
    if is_admin:
        st.subheader("👥 Setup Players")
        with st.form("player_setup_form"):
            num_players = st.number_input("Number of Players", min_value=2, max_value=15, value=4, key="num_players")
            player_names = [st.text_input(f"Player {i+1} Name", key=f"player_{i}") for i in range(int(st.session_state.num_players))]
            submitted = st.form_submit_button("✅ Start Game")

        if submitted:
            if all(name.strip() for name in player_names):
                st.session_state.players = player_names
                st.session_state.scores = []
                st.session_state.reset_inputs = True
                st.session_state.player_setup_done = True
                save_game()
                st.rerun()
            else:
                st.warning("Please enter all player names.")
    else:
        st.info("Waiting for admin to start the game.")
    st.stop()

# ----------------- Score Totals -----------------
def get_total_scores():
    totals = {p: 0 for p in st.session_state.players}
    for round_scores in st.session_state.scores:
        for p, score in round_scores.items():
            totals[p] += score
    return totals

# ----------------- 1. TOTAL SCORES -----------------
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

def highlight(val):
    if val == min_score:
        return 'background-color: lightgreen; font-weight: bold'
    elif val == second_high:
        return 'background-color: orange; font-weight: bold'
    elif val == max_score:
        return 'background-color: red; color: white; font-weight: bold'
    return ''

st.dataframe(score_df.style.applymap(highlight), use_container_width=True)

# ----------------- 2. PREVIOUS ROUNDS -----------------
st.markdown("---")
st.subheader("📜 Previous Rounds (Editable)")
if st.session_state.scores:
    round_data = []
    for i, round_scores in enumerate(st.session_state.scores):
        row = {"Round": f"Round {i+1}"}
        for player in st.session_state.players:
            key = f"edit_r{i}_{player}"
            row[player] = st.number_input(
                label=f"{player} (R{i+1})",
                value=round_scores.get(player, 0),
                min_value=0,
                step=1,
                key=key,
                label_visibility="collapsed",
                disabled=not is_admin
            )
        round_data.append(row)

    df = pd.DataFrame(round_data)
    st.dataframe(df.set_index("Round"), use_container_width=True, hide_index=False)

    for i in range(len(st.session_state.scores)):
        if is_admin and st.button(f"🔄 Update Round {i+1}", key=f"update_{i}"):
            for player in st.session_state.players:
                key = f"edit_r{i}_{player}"
                st.session_state.scores[i][player] = st.session_state[key]
            save_game()
            st.success(f"✅ Round {i+1} updated!")
            st.rerun()

# ----------------- 3. ENTER NEW ROUND SCORES -----------------
st.markdown("---")
st.subheader("✍️ Enter New Round Scores")
if 'reset_inputs' not in st.session_state:
    st.session_state.reset_inputs = False

if is_admin:
    new_scores = {}
    with st.form("new_round_form"):
        for player in st.session_state.players:
            value = 0 if st.session_state.reset_inputs else st.session_state.get(f"new_round_{player}", 0)
            new_scores[player] = st.number_input(f"{player}", min_value=0, step=1, value=value, key=f"new_round_{player}")
        if st.form_submit_button("📅 Save This Round"):
            st.session_state.scores.append(new_scores.copy())
            for player in st.session_state.players:
                st.session_state[f"new_round_{player}"] = 0
            st.session_state.reset_inputs = True
            save_game()
            st.rerun()
else:
    st.info("Only admin can enter scores.")

st.session_state.reset_inputs = False

# ----------------- 4. ADD / REMOVE PLAYER -----------------
st.markdown("---")
st.subheader("⚙️ Add / Remove Player")
if is_admin:
    remove_player = st.selectbox("❌ Remove Player", options=st.session_state.players)
    if st.button("❌ Confirm Remove"):
        st.session_state.players.remove(remove_player)
        for i in range(len(st.session_state.scores)):
            if remove_player in st.session_state.scores[i]:
                del st.session_state.scores[i][remove_player]
        save_game()
        st.success(f"Removed player: {remove_player}")
        st.rerun()

    if len(st.session_state.players) < 15:
        new_player = st.text_input("➕ Add Player (max 15)")
        if st.button("✅ Confirm Add"):
            if new_player and new_player not in st.session_state.players:
                st.session_state.players.append(new_player)
                for round_score in st.session_state.scores:
                    round_score[new_player] = 0
                save_game()
                st.success(f"Added new player: {new_player}")
                st.rerun()
    else:
        st.warning("Maximum 15 players reached.")
else:
    st.info("Only admin can modify players.")

# ----------------- 5. END GAME -----------------
st.markdown("---")
st.subheader("🎮 End Game")
if is_admin and st.button("🛑 Game Complete"):
    st.session_state.game_reset = True
    st.rerun()
