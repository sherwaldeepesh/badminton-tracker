import streamlit as st
import json
import os
from datetime import datetime
import pytz

# ------------------ CONFIGURATION ------------------
IST = pytz.timezone("Asia/Kolkata")
today = datetime.now(IST).date()
DATA_FILE = "badminton_data.json"

st.set_page_config(page_title="Badminton Tracker", layout="centered", page_icon="🏸")

# ------------------ HELPER FUNCTIONS ------------------
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"date": today.strftime("%Y-%m-%d"), "player_stats": {}, "matches": []}

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    # Reset matches & counters for new day but retain player names
    if data.get("date") != today.strftime("%Y-%m-%d"):
        players = list(data.get("player_stats", {}).keys())
        data = {
            "date": today.strftime("%Y-%m-%d"),
            "player_stats": {p: 0 for p in players},
            "matches": [],
        }
        save_data(data)

    return data

def reset_data():
    data = load_data()
    players = list(data.get("player_stats", {}).keys())
    new_data = {
        "date": today.strftime("%Y-%m-%d"),
        "player_stats": {p: 0 for p in players},
        "matches": [],
    }
    save_data(new_data)
    st.session_state.refresh_toggle = not st.session_state.get("refresh_toggle", False)

# ------------------ MAIN APP ------------------
def main():
    st.title("🏸 Badminton Tracker")

    # Load or initialize data
    data = load_data()
    players = list(data["player_stats"].keys())

    # ---------------- ADD MATCH ----------------
    st.markdown("## ➕ Add New Match")
    if not players:
        st.warning("Please add players in the Manage Players section first.")
        return

    col1, col2, col3, col4 = st.columns(4)
    p1 = col1.selectbox("Player 1", [""] + players, key="p1_sel")
    p2 = col2.selectbox("Player 2", [""] + [p for p in players if p != p1], key="p2_sel")
    p3 = col3.selectbox("Player 3", [""] + [p for p in players if p != p1 and p != p2], key="p3_sel")
    p4 = col4.selectbox("Player 4", [""] + [p for p in players if p not in [p1,p2,p3]], key="p4_sel")
    remark = st.text_input("Remark (optional)", key="remark_input")

    if st.button("✅ Add Match"):
        if "" in [p1, p2, p3, p4]:
            st.warning("Please select all 4 players before adding a match.")
        else:
            now = datetime.now(IST)
            match = {
                "time": now.strftime("%H:%M"),
                "p1": p1,
                "p2": p2,
                "p3": p3,
                "p4": p4,
                "remark": remark if remark else "-",
            }
            data["matches"].append(match)
            for p in [p1, p2, p3, p4]:
                data["player_stats"][p] = data["player_stats"].get(p, 0) + 1
            save_data(data)
            st.success("Match added successfully!")
            st.session_state.refresh_toggle = not st.session_state.get("refresh_toggle", False)

    # ---------------- MATCH HISTORY ----------------
    st.markdown("## 📜 Match History")
    if data["matches"]:
        for match in reversed(data["matches"]):  # latest first
            st.markdown(
                f"🕒 {match['time']} — 👥 {match['p1']} & {match['p2']} vs {match['p3']} & {match['p4']} — 🗒️ Remark: {match['remark']}"
            )
    else:
        st.info("No matches recorded yet today.")

    # ---------------- PLAYER STATISTICS ----------------
    st.markdown("## 📊 Player Statistics")
    if data["player_stats"]:
        stats_html = "<table style='width:100%; text-align:center;'><tr><th>Player</th><th>Matches Played</th></tr>"
        for player, count in sorted(data["player_stats"].items(), key=lambda x: x[1], reverse=True):
            stats_html += f"<tr><td>{player}</td><td>{count}</td></tr>"
        stats_html += "</table>"
        st.markdown(stats_html, unsafe_allow_html=True)

        # Top Active Players
        st.markdown("### 🔥 Top Active Players Today")
        top_players = sorted(data["player_stats"].items(), key=lambda x: x[1], reverse=True)
        max_count = max([v for v in data["player_stats"].values()] + [1])
        for p, c in top_players:
            if c == 0:
                continue
            bar = "█" * int((c / max_count) * 20)
            st.markdown(f"**{p}** — {c} matches &nbsp;&nbsp;{bar}")
    else:
        st.info("No player statistics yet.")

    # ---------------- MANAGE PLAYERS ----------------
    st.markdown("## ⚙️ Manage Players")
    new_name = st.text_input("Add New Player (name not case-sensitive)").strip().upper()
    if st.button("Add Player"):
        if not new_name:
            st.warning("Enter a name before adding.")
        elif new_name in data["player_stats"]:
            st.info(f"{new_name} already exists.")
        else:
            data["player_stats"][new_name] = 0
            save_data(data)
            st.success(f"{new_name} added successfully!")
            st.session_state.refresh_toggle = not st.session_state.get("refresh_toggle", False)

    if players:
        remove_name = st.selectbox("Select Player to Remove", [""] + players)
        if st.button("Remove Player"):
            if remove_name:
                data["player_stats"].pop(remove_name, None)
                save_data(data)
                st.success(f"{remove_name} removed successfully!")
                st.session_state.refresh_toggle = not st.session_state.get("refresh_toggle", False)
            else:
                st.warning("Select a player to remove.")

    # ---------------- RESET DATA ----------------
    if st.button("🔄 Reset Matches & Counters"):
        reset_data()
        st.success("Match data and counters reset for today!")

# ------------------ RUN ------------------
if __name__ == "__main__":
    main()
