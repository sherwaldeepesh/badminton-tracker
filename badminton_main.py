import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import os
import json

# =========================
# Configuration
# =========================
DATA_FILE = "badminton_data.json"
PLAYER_FILE = "players.json"
INDIA_TZ = pytz.timezone("Asia/Kolkata")

# =========================
# Utility Functions
# =========================

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def load_players():
    if os.path.exists(PLAYER_FILE):
        with open(PLAYER_FILE, "r") as f:
            return json.load(f)
    return []

def save_players(players):
    with open(PLAYER_FILE, "w") as f:
        json.dump(players, f)

# =========================
# Main App
# =========================

def main():
    st.title("🏸 Badminton Tracker")

    # Load Data
    data = load_data()
    players = load_players()

    menu = ["🏸 Add Match Record", "📜 Match History", "📊 Player Statistics", "🧑‍🤝‍🧑 Manage Players"]
    choice = st.sidebar.selectbox("Navigation", menu)

    # ===================================
    # Add Match Record
    # ===================================
    if choice == "🏸 Add Match Record":
        st.header("Add Match Record")

        if not players:
            st.warning("Please add players in the 'Manage Players' section first.")
            return

        col1, col2 = st.columns(2)
        with col1:
            player1 = st.selectbox("Player 1", players)
        with col2:
            player2 = st.selectbox("Player 2", [p for p in players if p != player1])

        score1 = st.number_input(f"Score for {player1}", min_value=0, step=1)
        score2 = st.number_input(f"Score for {player2}", min_value=0, step=1)

        if st.button("Add Record"):
            now = datetime.now(INDIA_TZ).strftime("%Y-%m-%d %H:%M:%S")
            winner = player1 if score1 > score2 else player2 if score2 > score1 else "Draw"
            new_record = {
                "datetime": now,
                "player1": player1,
                "player2": player2,
                "score1": score1,
                "score2": score2,
                "winner": winner,
            }
            data.append(new_record)
            save_data(data)
            st.success(f"Record added successfully! Winner: {winner}")

    # ===================================
    # Match History
    # ===================================
    elif choice == "📜 Match History":
        st.header("Match History")
        if data:
            df = pd.DataFrame(data)
            df["datetime"] = pd.to_datetime(df["datetime"])
            df = df.sort_values(by="datetime", ascending=False)  # Latest first
            st.dataframe(df.reset_index(drop=True), use_container_width=True)
        else:
            st.info("No match records found yet.")

    # ===================================
    # Player Statistics
    # ===================================
    elif choice == "📊 Player Statistics":
        st.header("Player Statistics")

        if not data:
            st.info("No match records available to calculate statistics.")
            return

        stats = {}
        for record in data:
            for player, score, opponent_score in [
                (record["player1"], record["score1"], record["score2"]),
                (record["player2"], record["score2"], record["score1"]),
            ]:
                if player not in stats:
                    stats[player] = {"Matches": 0, "Wins": 0, "Losses": 0, "Draws": 0, "Points Scored": 0}
                stats[player]["Matches"] += 1
                stats[player]["Points Scored"] += score

                if record["winner"] == "Draw":
                    stats[player]["Draws"] += 1
                elif record["winner"] == player:
                    stats[player]["Wins"] += 1
                else:
                    stats[player]["Losses"] += 1

        stats_df = pd.DataFrame(stats).T
        stats_df["Win %"] = (stats_df["Wins"] / stats_df["Matches"] * 100).round(2)
        st.dataframe(stats_df.style.set_properties(**{
            'text-align': 'center'
        }).set_table_styles([dict(selector='th', props=[('text-align', 'center')])]), use_container_width=True)

    # ===================================
    # Manage Players (Bottom)
    # ===================================
    elif choice == "🧑‍🤝‍🧑 Manage Players":
        st.header("Manage Players")

        st.subheader("Add Player")
        new_player = st.text_input("Enter Player Name")

        if st.button("Add Player"):
            new_player = new_player.strip()
            if new_player and new_player not in players:
                players.append(new_player)
                save_players(players)
                st.success(f"Added player: {new_player}")
            else:
                st.warning("Player name is empty or already exists!")

        st.subheader("Existing Players")
        if players:
            for p in players:
                col1, col2 = st.columns([4, 1])
                col1.write(p)
                if col2.button("❌ Remove", key=p):
                    players.remove(p)
                    save_players(players)
                    st.warning(f"Removed player: {p}")
                    st.experimental_rerun()
        else:
            st.info("No players added yet.")

# =========================
# Run App
# =========================
if __name__ == "__main__":
    main()
