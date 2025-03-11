from flask import Flask, request, jsonify
from flask_cors import CORS
import random
import math

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# In-memory database for demonstration
players = []
rounds = []
current_round = 0

@app.route('/api/players', methods=['GET', 'POST'])
def handle_players():
    global players
    
    if request.method == 'POST':
        data = request.json
        player_name = data.get('name', '')
        player_rating = data.get('rating', 0)
        
        if not player_name:
            return jsonify({"error": "Player name is required"}), 400
            
        player_id = len(players) + 1
        new_player = {
            "id": player_id,
            "name": player_name,
            "rating": player_rating,
            "score": 0,
            "opponents": []
        }
        
        players.append(new_player)
        return jsonify(new_player), 201
    
    # GET request
    return jsonify(players)

@app.route('/api/players/<int:player_id>', methods=['DELETE'])
def delete_player(player_id):
    global players
    
    for i, player in enumerate(players):
        if player["id"] == player_id:
            players.pop(i)
            return jsonify({"message": "Player deleted successfully"}), 200
    
    return jsonify({"error": "Player not found"}), 404

@app.route('/api/pairings', methods=['POST'])
def generate_pairings():
    global players, rounds, current_round
    
    if len(players) < 2:
        return jsonify({"error": "Need at least 2 players to generate pairings"}), 400
    
    # Sort players by score (descending) and then by rating (descending)
    sorted_players = sorted(players, key=lambda x: (-x["score"], -x["rating"]))
    
    pairings = []
    used_players = set()
    
    # Swiss system pairing algorithm
    for i in range(len(sorted_players)):
        if i in used_players:
            continue
            
        player1 = sorted_players[i]
        opponent_found = False
        
        # Look for an opponent who hasn't played against player1 yet
        for j in range(i + 1, len(sorted_players)):
            if j in used_players:
                continue
                
            player2 = sorted_players[j]
            
            # Check if these players have already played each other
            if player2["id"] not in player1["opponents"]:
                pairings.append({
                    "white": player1,
                    "black": player2,
                    "result": None
                })
                
                used_players.add(i)
                used_players.add(j)
                opponent_found = True
                break
        
        # If no suitable opponent found, pair with the closest eligible player
        if not opponent_found and i not in used_players:
            for j in range(i + 1, len(sorted_players)):
                if j not in used_players:
                    player2 = sorted_players[j]
                    pairings.append({
                        "white": player1,
                        "black": player2,
                        "result": None
                    })
                    
                    used_players.add(i)
                    used_players.add(j)
                    break
    
    # Handle odd number of players (give bye to lowest-ranked player without a bye)
    unpaired_players = [i for i in range(len(sorted_players)) if i not in used_players]
    if unpaired_players:
        bye_player = sorted_players[unpaired_players[0]]
        pairings.append({
            "white": bye_player,
            "black": {"id": None, "name": "BYE"},
            "result": "1-0"  # Bye gets a win
        })
        
        # Update score for the player with a bye
        for player in players:
            if player["id"] == bye_player["id"]:
                player["score"] += 1
    
    current_round += 1
    rounds.append({"round": current_round, "pairings": pairings})
    
    return jsonify({"round": current_round, "pairings": pairings})

@app.route('/api/results', methods=['POST'])
def submit_results():
    global players, rounds
    
    data = request.json
    round_num = data.get('round', current_round)
    pairing_idx = data.get('pairingIndex', 0)
    result = data.get('result', None)
    
    if round_num <= 0 or round_num > len(rounds):
        return jsonify({"error": "Invalid round number"}), 400
        
    if pairing_idx < 0 or pairing_idx >= len(rounds[round_num - 1]["pairings"]):
        return jsonify({"error": "Invalid pairing index"}), 400
        
    if result not in ["1-0", "0-1", "1/2-1/2"]:
        return jsonify({"error": "Invalid result. Must be '1-0', '0-1', or '1/2-1/2'"}), 400
    
    # Update the pairing result
    rounds[round_num - 1]["pairings"][pairing_idx]["result"] = result
    
    # Update player scores and opponents
    pairing = rounds[round_num - 1]["pairings"][pairing_idx]
    white_id = pairing["white"]["id"]
    black_id = pairing["black"]["id"]
    
    # Skip if it's a bye (black_id is None)
    if black_id is not None:
        # Update opponents
        for player in players:
            if player["id"] == white_id:
                player["opponents"].append(black_id)
                if result == "1-0":
                    player["score"] += 1
                elif result == "1/2-1/2":
                    player["score"] += 0.5
            
            if player["id"] == black_id:
                player["opponents"].append(white_id)
                if result == "0-1":
                    player["score"] += 1
                elif result == "1/2-1/2":
                    player["score"] += 0.5
    
    return jsonify({"message": "Result submitted successfully"})

@app.route('/api/standings', methods=['GET'])
def get_standings():
    global players
    
    # Sort players by score (descending) and then by rating (descending)
    standings = sorted(players, key=lambda x: (-x["score"], -x["rating"]))
    
    return jsonify(standings)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
