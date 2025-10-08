import streamlit as st
import json
import os
from datetime import datetime
import pytz

# ------------------ CONFIGURATION ------------------
IST = pytz.timezone("Asia/Kolkata")
today = datetime.now(IST).date()
DATA_FILE = "badminton_data.json"

st.set_page_config(page_title="Badminton Game Tracker", layout="centered")

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


def get_time_range_label(time_obj):
    t = time_obj.hour * 60 + time_obj.minute
    if 5 * 60 + 31 <= t <= 6 * 60 + 30:
        return "5:31–6:30"
    elif 6 * 60 + 31 <= t <= 7 * 60:
        return "6:31–7:00"
    elif 7 * 60 + 1 <= t <= 7 * 60 + 30:
        return "7:01–7:30"
    elif 7 * 60 + 31 <= t <= 8 * 60:
        return "7:31–8:00"
    elif 8 * 60 + 1 <= t <= 10 * 60:
        return "8:01–10:00"
    else:
        return "Other"


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
    st.title("🏸 Badminton Game Tracker")

    # Load or initialize data
    data = load_data()
    players = list(data["player_stats"].keys())

    # ---------------- MATCH HISTORY ----------------
    st.markdown("## 🎯 Match History (Today)")
    if data["matches"]:
        for match in reversed(data["matches"]):  # latest first
            st.markdown(
                f"🕒 {match['time']} — 👥 {match['p1']} & {match['p2']} vs {match['p3']} & {match['p4']} — 🗒️ Remark: {match['remark']}"
            )
    else:
        st.info("No matches recorded yet today.")

    # ---------------- ADD MATCH ----------------
    st.markdown("## ➕ Add New Match")
    col1, col2, col3, col4 = st.columns(4)
    p1 = col1.selectbox("Player 1", [""] + players, key="p1_sel")
    p2 = col2.selectbox("Player 2", [""] + players, key="p2_sel")
    p3 = col3.selectbox("Player 3", [""] + players, key="p3_sel")
    p4 = col4.selectbox("Player 4", [""] + players, key="p4_sel")
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
                "range": get_time_range_label(now),
            }
            data["matches"].append(match)
            for p in [p1, p2, p3, p4]:
                data["player_stats"][p] = data["player_stats"].get(p, 0) + 1
            save_data(data)
            st.success("Match added successfully!")
            st.session_state.refresh_toggle = not st.session_state.get("refresh_toggle", False)

    # ---------------- PLAYER STATISTICS ----------------
    st.markdown("## 📊 Player Statistics")
    if data["player_stats"]:
        stats_html = "<table><tr><th>Player</th><th>Matches Played</th></tr>"
        for player, count in sorted(data["player_stats"].items(), key=lambda x: x[1], reverse=True):
            stats_html += f"<tr><td>{player}</td><td>{count}</td></tr>"
        stats_html += "</table>"
        st.markdown(stats_html, unsafe_allow_html=True)
    else:
        st.info("No player statistics available yet.")

    # ---------------- TOP ACTIVE PLAYERS ----------------
    st.markdown("## 🔥 Top Active Players Today")
    if data["player_stats"] and any(v > 0 for v in data["player_stats"].values()):
        top_players = sorted(data["player_stats"].items(), key=lambda x: x[1], reverse=True)
        max_count = max(v for v in data["player_stats"].values())
        for p, c in top_players:
            if c == 0:
                continue
            bar = "█" * int((c / max_count) * 20)
            st.markdown(f"**{p}** — {c} matches &nbsp;&nbsp;{bar}")
    else:
        st.info("No matches played yet today.")

    # ---------------- MATCHES BY TIME RANGE ----------------
    st.markdown("## 🕒 Matches by Time Range")
    if data["matches"]:
        ranges = {}
        for m in data["matches"]:
            r = m["range"]
            ranges[r] = ranges.get(r, 0) + 1
        html = "<table><tr><th>Time Range</th><th>Matches</th></tr>"
        for r, c in ranges.items():
            html += f"<tr><td>{r}</td><td>{c}</td></tr>"
        html += "</table>"
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.info("No matches played yet.")

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
    if st.button("🔄 Reset (Clear Matches & Counters)"):
        reset_data()
        st.success("Data reset for the day!")

# ------------------ RUN ------------------
if __name__ == "__main__":
    main()
