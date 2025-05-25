import random
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='static')

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

# @app.route('/play', methods=['POST'])
# def play():
#     try:
#         data = request.get_json()
#         if not data:
#             return jsonify({'error': 'Invalid request, no JSON data received.'}), 400
# 
#         player_unit_type = data.get('unit_type')
#         player_unit_count_str = data.get('unit_count') # Keep as string for now for validation
# 
#         # Validate player_unit_type
#         valid_unit_types = ['infantry', 'archers', 'cavalry']
#         if not player_unit_type or player_unit_type not in valid_unit_types:
#             return jsonify({'error': f'Invalid unit_type. Must be one of {valid_unit_types}.'}), 400
# 
#         # Validate player_unit_count
#         try:
#             player_unit_count = int(player_unit_count_str)
#             if player_unit_count <= 0:
#                 raise ValueError("Unit count must be positive.")
#         except (ValueError, TypeError): # Catches if conversion to int fails or if it's None
#             return jsonify({'error': 'Invalid unit_count. Must be a positive integer.'}), 400
# 
#         # AI's Choice
#         computer_unit_type = random.choice(valid_unit_types)
#         computer_unit_count = random.randint(5, 15) # Example range
# 
#         # Combat Logic
#         player_modifier = 1.0
#         computer_modifier = 1.0
# 
#         # Type advantages: Infantry > Archers > Cavalry > Infantry
#         if (player_unit_type == 'infantry' and computer_unit_type == 'archers') or \
#            (player_unit_type == 'archers' and computer_unit_type == 'cavalry') or \
#            (player_unit_type == 'cavalry' and computer_unit_type == 'infantry'):
#             player_modifier = 1.25
#         elif (computer_unit_type == 'infantry' and player_unit_type == 'archers') or \
#               (computer_unit_type == 'archers' and player_unit_type == 'cavalry') or \
#               (computer_unit_type == 'cavalry' and player_unit_type == 'infantry'):
#             computer_modifier = 1.25
# 
#         player_effective_strength = float(player_unit_count) * player_modifier
#         computer_effective_strength = float(computer_unit_count) * computer_modifier
# 
#         # Determine Winner
#         if player_effective_strength > computer_effective_strength:
#             result = 'You Win!'
#         elif computer_effective_strength > player_effective_strength:
#             result = 'You Lose!'
#         else:
#             result = 'Draw'
# 
#         return jsonify({
#             'player_army': {'type': player_unit_type, 'count': player_unit_count},
#             'computer_army': {'type': computer_unit_type, 'count': computer_unit_count},
#             'player_effective_strength': player_effective_strength,
#             'computer_effective_strength': computer_effective_strength,
#             'result': result
#         })
# 
#     except Exception as e:
#         # Log the exception for debugging
#         app.logger.error(f"Error in /play endpoint: {str(e)}")
#         return jsonify({'error': 'An unexpected error occurred on the server.'}), 500

@app.route('/submit_round_1', methods=['POST'])
def submit_round_1():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'Invalid request, no JSON data received.'}), 400

        player_r1_unit_type = data.get('unit_type')
        player_r1_unit_count_str = data.get('unit_count')

        valid_unit_types = ['infantry', 'archers', 'cavalry']
        if not player_r1_unit_type or player_r1_unit_type not in valid_unit_types:
            return jsonify({'error': f'Invalid unit_type. Must be one of {valid_unit_types}.'}), 400

        try:
            player_r1_unit_count = int(player_r1_unit_count_str)
            if not (1 <= player_r1_unit_count <= 10): # R1 budget is 10
                raise ValueError("Unit count for Round 1 must be between 1 and 10.")
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid unit_count for Round 1. Must be an integer between 1 and 10.'}), 400

        # AI's R1 Choice
        ai_r1_unit_type = random.choice(valid_unit_types)
        ai_r1_unit_count = random.randint(1, 10) # AI R1 budget is 10

        # R1 Combat Logic
        player_modifier = 1.0
        ai_modifier = 1.0
        # Infantry > Archers > Cavalry > Infantry
        if (player_r1_unit_type == 'infantry' and ai_r1_unit_type == 'archers') or \
           (player_r1_unit_type == 'archers' and ai_r1_unit_type == 'cavalry') or \
           (player_r1_unit_type == 'cavalry' and ai_r1_unit_type == 'infantry'):
            player_modifier = 1.25
        elif (ai_r1_unit_type == 'infantry' and player_r1_unit_type == 'archers') or \
              (ai_r1_unit_type == 'archers' and player_r1_unit_type == 'cavalry') or \
              (ai_r1_unit_type == 'cavalry' and player_r1_unit_type == 'infantry'):
            ai_modifier = 1.25

        player_r1_eff_strength = float(player_r1_unit_count) * player_modifier
        ai_r1_eff_strength = float(ai_r1_unit_count) * ai_modifier

        r1_winner = "Draw"
        if player_r1_eff_strength > ai_r1_eff_strength:
            r1_winner = "Player"
        elif ai_r1_eff_strength > player_r1_eff_strength:
            r1_winner = "AI"

        # Calculate R2 Pools
        player_r2_base_recruits = 10 + (10 - player_r1_unit_count)
        ai_r2_base_recruits = 10 + (10 - ai_r1_unit_count)
        
        strength_diff = abs(player_r1_eff_strength - ai_r1_eff_strength)
        bonus_troops = int(strength_diff) # round down (floor)

        player_r2_bonus = 0 # Default to 0
        ai_r2_bonus = 0 # Default to 0
        
        if r1_winner == "Player":
            player_r2_bonus = bonus_troops
        elif r1_winner == "AI":
            ai_r2_bonus = bonus_troops
        # If R1 winner is "Draw", bonus remains 0 for both

        player_total_r2_pool = player_r2_base_recruits + player_r2_bonus
        ai_total_r2_pool = ai_r2_base_recruits + ai_r2_bonus
        
        player_total_r2_pool = max(0, player_total_r2_pool)
        ai_total_r2_pool = max(0, ai_total_r2_pool)


        return jsonify({
            'round_1_results': {
                'player_army': {'type': player_r1_unit_type, 'count': player_r1_unit_count, 'strength': player_r1_eff_strength},
                'ai_army': {'type': ai_r1_unit_type, 'count': ai_r1_unit_count, 'strength': ai_r1_eff_strength},
                'round_winner': r1_winner
            },
            'player_r2_data': {'base_recruits': player_r2_base_recruits, 'bonus': player_r2_bonus, 'total_r2_pool': player_total_r2_pool},
            'ai_r1_army_details_for_r2': {'type': ai_r1_unit_type, 'count': ai_r1_unit_count}, 
            'ai_r2_data_for_r2': {'base_recruits': ai_r2_base_recruits, 'bonus': ai_r2_bonus, 'total_r2_pool': ai_total_r2_pool}
        })

    except Exception as e:
        app.logger.error(f"Error in /submit_round_1: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred on the server.'}), 500

@app.route('/submit_round_2', methods=['POST'])
def submit_round_2():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'Invalid request, no JSON data received.'}), 400

        player_r2_unit_type = data.get('unit_type')
        player_r2_unit_count_str = data.get('unit_count')
        # ai_r1_army_details = data.get('ai_r1_army_details_for_r2') 
        ai_r2_data_from_client = data.get('ai_r2_data_for_r2')

        if not ai_r2_data_from_client or 'total_r2_pool' not in ai_r2_data_from_client:
             return jsonify({'error': 'Missing AI R2 data from client.'}), 400
        
        ai_total_r2_pool = int(ai_r2_data_from_client.get('total_r2_pool', 0))

        valid_unit_types = ['infantry', 'archers', 'cavalry']
        if not player_r2_unit_type or player_r2_unit_type not in valid_unit_types:
            return jsonify({'error': f'Invalid unit_type for Round 2. Must be one of {valid_unit_types}.'}), 400

        try:
            player_r2_unit_count = int(player_r2_unit_count_str)
            if player_r2_unit_count < 0: 
                 raise ValueError("Unit count for Round 2 cannot be negative.")
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid unit_count for Round 2. Must be a non-negative integer.'}), 400

        # AI's R2 Choice
        ai_r2_unit_type = random.choice(valid_unit_types)
        ai_r2_unit_count = 0
        if ai_total_r2_pool > 0:
             ai_r2_unit_count = random.randint(0, ai_total_r2_pool) 
        elif ai_total_r2_pool == 0: 
             ai_r2_unit_count = 0


        # R2 Combat Logic (same as R1)
        player_modifier = 1.0
        ai_modifier = 1.0
        if (player_r2_unit_type == 'infantry' and ai_r2_unit_type == 'archers') or \
           (player_r2_unit_type == 'archers' and ai_r2_unit_type == 'cavalry') or \
           (player_r2_unit_type == 'cavalry' and ai_r2_unit_type == 'infantry'):
            player_modifier = 1.25
        elif (ai_r2_unit_type == 'infantry' and player_r2_unit_type == 'archers') or \
              (ai_r2_unit_type == 'archers' and player_r2_unit_type == 'cavalry') or \
              (ai_r2_unit_type == 'cavalry' and player_r2_unit_type == 'infantry'):
            ai_modifier = 1.25
        
        player_r2_eff_strength = 0.0
        if player_r2_unit_count > 0:
            player_r2_eff_strength = float(player_r2_unit_count) * player_modifier
        
        ai_r2_eff_strength = 0.0
        if ai_r2_unit_count > 0:
            ai_r2_eff_strength = float(ai_r2_unit_count) * ai_modifier


        r2_winner = "Draw"
        if player_r2_eff_strength > ai_r2_eff_strength:
            r2_winner = "Player"
        elif ai_r2_eff_strength > player_r2_eff_strength:
            r2_winner = "AI"
        
        game_winner = r2_winner

        return jsonify({
            'round_2_results': {
                'player_army': {'type': player_r2_unit_type, 'count': player_r2_unit_count, 'strength': player_r2_eff_strength},
                'ai_army': {'type': ai_r2_unit_type, 'count': ai_r2_unit_count, 'strength': ai_r2_eff_strength},
                'round_winner': r2_winner
            },
            'game_winner': game_winner
        })

    except Exception as e:
        app.logger.error(f"Error in /submit_round_2: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred on the server.'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
