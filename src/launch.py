import random
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='static')

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/play', methods=['POST'])
def play():
    try:
        player_choice = request.json.get('choice')
        if not player_choice or player_choice not in ['rock', 'paper', 'scissors']:
            return jsonify({'error': 'Invalid choice'}), 400

        choices = ['rock', 'paper', 'scissors']
        computer_choice = random.choice(choices)

        result = ''
        if player_choice == computer_choice:
            result = 'Tie'
        elif (player_choice == 'rock' and computer_choice == 'scissors') or \
             (player_choice == 'scissors' and computer_choice == 'paper') or \
             (player_choice == 'paper' and computer_choice == 'rock'):
            result = 'You Win!'
        else:
            result = 'You Lose!'

        return jsonify({
            'player_choice': player_choice,
            'computer_choice': computer_choice,
            'result': result
        })

    except Exception as e:
        app.logger.error(f"Error in /play endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
