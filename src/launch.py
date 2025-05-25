import random
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='static')

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/play', methods=['POST'])
def play():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request, no JSON data received.'}), 400

        player_unit_type = data.get('unit_type')
        player_unit_count_str = data.get('unit_count') # Keep as string for now for validation

        # Validate player_unit_type
        valid_unit_types = ['infantry', 'archers', 'cavalry']
        if not player_unit_type or player_unit_type not in valid_unit_types:
            return jsonify({'error': f'Invalid unit_type. Must be one of {valid_unit_types}.'}), 400

        # Validate player_unit_count
        try:
            player_unit_count = int(player_unit_count_str)
            if player_unit_count <= 0:
                raise ValueError("Unit count must be positive.")
        except (ValueError, TypeError): # Catches if conversion to int fails or if it's None
            return jsonify({'error': 'Invalid unit_count. Must be a positive integer.'}), 400

        # AI's Choice
        computer_unit_type = random.choice(valid_unit_types)
        computer_unit_count = random.randint(5, 15) # Example range

        # Combat Logic
        player_modifier = 1.0
        computer_modifier = 1.0

        # Type advantages: Infantry > Archers > Cavalry > Infantry
        if (player_unit_type == 'infantry' and computer_unit_type == 'archers') or \
           (player_unit_type == 'archers' and computer_unit_type == 'cavalry') or \
           (player_unit_type == 'cavalry' and computer_unit_type == 'infantry'):
            player_modifier = 1.25
        elif (computer_unit_type == 'infantry' and player_unit_type == 'archers') or \
              (computer_unit_type == 'archers' and player_unit_type == 'cavalry') or \
              (computer_unit_type == 'cavalry' and player_unit_type == 'infantry'):
            computer_modifier = 1.25

        player_effective_strength = float(player_unit_count) * player_modifier
        computer_effective_strength = float(computer_unit_count) * computer_modifier

        # Determine Winner
        if player_effective_strength > computer_effective_strength:
            result = 'You Win!'
        elif computer_effective_strength > player_effective_strength:
            result = 'You Lose!'
        else:
            result = 'Draw'

        return jsonify({
            'player_army': {'type': player_unit_type, 'count': player_unit_count},
            'computer_army': {'type': computer_unit_type, 'count': computer_unit_count},
            'player_effective_strength': player_effective_strength,
            'computer_effective_strength': computer_effective_strength,
            'result': result
        })

    except Exception as e:
        # Log the exception for debugging
        app.logger.error(f"Error in /play endpoint: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred on the server.'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
