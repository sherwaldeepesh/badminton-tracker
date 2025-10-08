import streamlit as st
import json
import os
from datetime import datetime, date, timedelta
import pytz

st.set_page_config(page_title="🏸 Badminton Match Tracker", layout="centered", page_icon="🏸")

DATA_FILE = "badminton_data.json"
IST = pytz.timezone("Asia/Kolkata")
today = datetime.now(IST).date()

if "refresh_toggle" not in st.session_state:
    st.session_state.refresh_toggle = False

# ---------- File helpers ----------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"date": today.strftime("%Y-%m-%d"), "player_stats": {}, "name_map": {}, "matches": []}
    with open(DATA_FILE, "r") as f:
        d = json.load(f)
    if d.get("date") != today.strftime("%Y-%m-%d"):
        d["date"] = today.strftime("%Y-%m-%d")
        d["player_stats"] = {}
        d["matches"] = []
        save_data(d)
    return d

def save_data(d):
    with open(DATA_FILE, "w") as f:
        json.dump(d, f, indent=2)

data = load_data()

# ---------- Utility ----------
def normalize_name(name: str) -> str:
    return name.strip().upper()

def register_player(name: str):
    norm = normalize_name(name)
    upper_name = norm
    if norm not in data["name_map"]:
        data["name_map"][norm] = upper_name
    if upper_name not in data["player_stats"]:
        data["player_stats"][upper_name] = 0
    save_data(data)
    st.session_state.refresh_toggle = not st.session_state.refresh_toggle
    return upper_name

def add_match(players, remark=""):
    match_id = len(data["matches"]) + 1
    timestamp = datetime.now(IST).strftime("%H:%M")
    players_upper = [normalize_name(p) for p in players]
    data["matches"].append({"id": match_id, "players": players_upper, "time": timestamp, "remark": remark})
    for p in players_upper:
        data["player_stats"][p] = data["player_stats"].get(p, 0) + 1
    save_data(data)
    st.session_state.refresh_toggle = not st.session_state.refresh_toggle

def reset_counters():
    for p in data["player_stats"]:
        data["player_stats"][p] = 0
    data["matches"] = []
    save_data(data)
    st.session_state.refresh_toggle = not st.session_state.refresh_toggle

# ---------- Time range helper ----------
TIME_RANGES = [
    ("5:31", "6:30"),
    ("6:31", "7:00"),
    ("7:01", "7:30"),
    ("7:31", "8:00"),
    ("8:01", "10:00"),
]

def time_in_range(t, start, end):
    fmt = "%H:%M"
    t_dt = datetime.strptime(t, fmt)
    start_dt = datetime.strptime(start, fmt)
    end_dt = datetime.strptime(end, fmt)
    return start_dt <= t_dt <= end_dt

def stats_by_time_range():
    ranges_count = {f"{r[0]}-{r[1]}": {} for r in TIME_RANGES}
    for match in data["matches"]:
        t = match["time"]
        for r in TIME_RANGES:
            if time_in_range(t, r[0], r[1]):
                key = f"{r[0]}-{r[1]}"
                for p in match["players"]:
                    ranges_count[key][p] = ranges_count[key].get(p, 0) + 1
    return ranges_count

def today_matches_count(player):
    count = 0
    for m in data["matches"]:
        if player in m["players"]:
            count += 1
    return count

def shade_color(count, max_count):
    if count == 0:
        return "#2F3640"
    ratio = count / max_count if max_count > 0 else 0
    palette = ["#1B5E20", "#0D47A1", "#B71C1C", "#4A148C", "#E65100"]
    index = min(int(ratio * len(palette)), len(palette)-1)
    return palette[index]

# ---------- Main App ----------
def main():
    st.title("🏸 Badminton Match Tracker")
    st.caption("Players stored in UPPERCASE. Daily counters and matches resettable.")

    # ---- Register new player ----
    st.subheader("Register New Player")
    new_player = st.text_input("Enter player name to register", placeholder="Type player name")
    if st.button("➕ Register Player") and new_player.strip():
        name_registered = register_player(new_player)
        st.success(f"Player '{name_registered}' registered successfully!")

    # ---- Add Match ----
    st.subheader("Add New Match")
    existing_players = sorted(data["player_stats"].keys())
    if len(existing_players) < 4:
        st.warning("At least 4 players must be registered to add a match.")

    if len(existing_players) >= 4:
        col1, col2 = st.columns([1,1])
        p1 = col1.selectbox("Select Player 1", [""] + existing_players, key="sel_1")
        p2 = col1.selectbox("Select Player 2", [""] + existing_players, key="sel_2")
        p3 = col2.selectbox("Select Player 3", [""] + existing_players, key="sel_3")
        p4 = col2.selectbox("Select Player 4", [""] + existing_players, key="sel_4")
        remark = st.text_input("Remark (optional)", placeholder="Add a remark for this match")

        if st.button("➕ Add Match Record"):
            players_selected = [p for p in [p1,p2,p3,p4] if p]
            if len(players_selected) != 4:
                st.warning("Please select exactly 4 players.")
            elif len(set(players_selected)) < 4:
                st.warning("Each player must be unique for the match.")
            else:
                add_match(players_selected, remark)
                st.success("Match added successfully!")

    # ---- Match History (Reverse Chronological) ----
    st.subheader("🕹️ Match History (Latest First)")
    if data["matches"]:
        max_today = max([today_matches_count(p) for p in data["player_stats"]], default=1)

        for m in reversed(data["matches"]):  # latest match at top
            st.markdown(f"**Match #{m['id']} at {m['time']}**")
            if m.get("remark"):
                st.markdown(f"_Remark: {m['remark']}_")

            col1, col2, col3 = st.columns([1,0.2,1])

            # Team 1
            with col1:
                p1, p2 = m["players"][:2]
                c1, c2 = today_matches_count(p1), today_matches_count(p2)
                color1, color2 = shade_color(c1,max_today), shade_color(c2,max_today)
                st.markdown(f"""
                <div style='background-color:{color1}; color:white; padding:8px; border-radius:8px; 
                text-align:center; margin-bottom:5px; display:flex; justify-content:center;'>{p1}</div>
                <div style='background-color:{color2}; color:white; padding:8px; border-radius:8px; 
                text-align:center; display:flex; justify-content:center;'>{p2}</div>
                """, unsafe_allow_html=True)

            # VS separator
            with col2:
                st.markdown("<div style='color:white; text-align:center; margin-top:15px;'>VS</div>", unsafe_allow_html=True)

            # Team 2
            with col3:
                p3, p4 = m["players"][2:]
                c3, c4 = today_matches_count(p3), today_matches_count(p4)
                color3, color4 = shade_color(c3,max_today), shade_color(c4,max_today)
                st.markdown(f"""
                <div style='background-color:{color3}; color:white; padding:8px; border-radius:8px; 
                text-align:center; margin-bottom:5px; display:flex; justify-content:center;'>{p3}</div>
                <div style='background-color:{color4}; color:white; padding:8px; border-radius:8px; 
                text-align:center; display:flex; justify-content:center;'>{p4}</div>
                """, unsafe_allow_html=True)

            st.markdown("<hr style='border:1px solid #555'>", unsafe_allow_html=True)
    else:
        st.info("No matches recorded yet today.")

    # ---------- Player Statistics (Centered) ----------
    st.subheader("📊 Player Statistics")
    if data["player_stats"]:
        table_html = "<table style='width:50%; margin:auto; border-collapse: collapse;'>"
        table_html += "<tr><th style='text-align:center'>Player</th><th style='text-align:center'>Matches Played</th></tr>"
        for p, c in sorted(data["player_stats"].items(), key=lambda x:-x[1]):
            table_html += f"<tr><td style='text-align:center'>{p}</td><td style='text-align:center'>{c}</td></tr>"
        table_html += "</table>"
        st.markdown(table_html, unsafe_allow_html=True)
    else:
        st.info("No player statistics yet.")

    # ---------- Top Active Players Today ----------
    st.subheader("🔥 Top Active Players Today")
    today_counts = {p: today_matches_count(p) for p in data["player_stats"] if today_matches_count(p) > 0}
    if today_counts:
        top_players = sorted(today_counts.items(), key=lambda x: -x[1])[:4]
        max_count = max([c for _, c in top_players])

        st.markdown("<div style='display:flex; justify-content:center; gap:10px; flex-wrap:wrap;'>", unsafe_allow_html=True)
        for p, c in top_players:
            bar_color = shade_color(c, max_count)
            width_px = max(int((c / max_count) * 380), 80)
            st.markdown(f"""
            <div style='background-color:{bar_color}; width:{width_px}px; padding:8px; 
            color:white; border-radius:5px; text-align:center; display:inline-block;'>{p} ({c})</div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No matches recorded today.")

    # ---------- Matches by Time Ranges ----------
    st.subheader("⏱️ Matches by Time Ranges")
    ranges_count = stats_by_time_range()
    for r, counts in ranges_count.items():
        st.markdown(f"**Time Range {r}**")
        if counts:
            table = [{"Player": p, "Matches": c} for p,c in sorted(counts.items(), key=lambda x:-x[1])]
            st.table(table)
        else:
            st.info("No matches in this range.")

    # ---------- Reset Counters & Matches ----------
    st.divider()
    if st.button("🔄 Reset Counters & Match History (Keep Players)"):
        reset_counters()
        st.success("Counters and match history reset, players retained!")

    # ---------- Manage Players (Edit / Remove) moved to bottom ----------
    st.subheader("⚙️ Manage Players")
    all_players = sorted(data["player_stats"].keys())

    if all_players:
        col1, col2 = st.columns(2)

        # ---- Edit Name ----
        with col1:
            player_to_edit = st.selectbox("Select Player to Edit", [""] + all_players, key="edit_player")
            new_name = st.text_input("New Name", key="new_name_input")
            if st.button("✏️ Update Name"):
                if player_to_edit and new_name.strip():
                    norm_new = normalize_name(new_name)
                    # Update player_stats
                    data["player_stats"][norm_new] = data["player_stats"].pop(player_to_edit)
                    # Update name_map
                    data["name_map"].pop(player_to_edit, None)
                    data["name_map"][norm_new] = norm_new
                    # Update matches
                    for m in data["matches"]:
                        m["players"] = [norm_new if p == player_to_edit else p for p in m["players"]]
                    save_data(data)
                    st.success(f"Player '{player_to_edit}' renamed to '{norm_new}'")
                    st.session_state.refresh_toggle = not st.session_state.refresh_toggle

        # ---- Remove Player ----
        with col2:
            player_to_remove = st.selectbox("Select Player to Remove", [""] + all_players, key="remove_player")
            if st.button("🗑️ Remove Player"):
                if player_to_remove:
                    # Remove from stats and name_map
                    data["player_stats"].pop(player_to_remove, None)
                    data["name_map"].pop(player_to_remove, None)
                    # Remove from matches
                    for m in data["matches"]:
                        m["players"] = [p for p in m["players"] if p != player_to_remove]
                    save_data(data)
                    st.success(f"Player '{player_to_remove}' removed")
                    st.session_state.refresh_toggle = not st.session_state.refresh_toggle
    else:
        st.info("No registered players to manage.")

# Run the app
main()
