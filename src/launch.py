import random
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='static')

VALID_UNIT_TYPES = ['infantry', 'archers', 'cavalry']
MAP_SIZE = 5 # 5x5 grid

# --- Helper Function for AI Deployment ---
def deploy_ai_units(units_to_deploy_total_count, unit_type, current_occupied_coords, owner_id="AI"):
    """
    Deploys a given total count of AI units of a specific type onto random empty cells.
    - units_to_deploy_total_count: Integer, total number of units of this type to deploy.
    - unit_type: String, e.g., 'infantry'.
    - current_occupied_coords: List of (x, y) tuples already occupied.
    - owner_id: String, 'AI' or 'P1'.
    Returns:
        - list of deployment dicts: [{'unit_type': ..., 'count': ..., 'x': ..., 'y': ..., 'owner': ...}, ...]
        - updated list of occupied_coords
    """
    ai_deployments = []
    available_cells = []
    for r in range(MAP_SIZE):
        for c in range(MAP_SIZE):
            if (r, c) not in current_occupied_coords:
                available_cells.append((r, c))
    
    random.shuffle(available_cells)

    # For simplicity in this version, AI deploys its total count of a single unit type
    # into as many cells as possible, or up to its total count if cells are limited.
    # A more complex AI might split units, but here we assume 1 unit per cell if possible,
    # or group them if cells are very scarce.
    # For now, let's assume AI tries to spread out, one unit per cell if possible.
    # If it has more units than available cells, it will deploy multiple units on some cells.

    # This simplified AI will deploy 1 unit per chosen cell until units run out or cells run out.
    # More advanced logic would be needed for "stacking" units if units > available_cells.
    # For this iteration, if units_to_deploy_total_count > len(available_cells),
    # it will deploy to all available_cells, with counts distributed.
    
    # Simplified: AI deploys its units into distinct cells if possible.
    # If it has more units than cells, it will put more in some cells.
    # This version will just pick distinct cells for now.
    
    num_deployment_locations = min(units_to_deploy_total_count, len(available_cells))
    
    # Basic distribution:
    # if units_to_deploy_total_count = 7, num_deployment_locations = 3
    # cell1: 3, cell2: 2, cell3: 2
    
    units_remaining_to_assign = units_to_deploy_total_count
    
    for i in range(num_deployment_locations):
        if units_remaining_to_assign <= 0:
            break
            
        cell_coord = available_cells.pop(0) # Get an available cell
        
        # Determine count for this cell
        count_for_this_cell = 1 # Default to 1
        if i == num_deployment_locations - 1: # Last cell gets all remaining
            count_for_this_cell = units_remaining_to_assign
        elif num_deployment_locations > 0 : # Distribute somewhat evenly
             count_for_this_cell = units_remaining_to_assign // (num_deployment_locations - i)
        
        count_for_this_cell = max(1, count_for_this_cell) # Ensure at least 1 if assigning
        count_for_this_cell = min(count_for_this_cell, units_remaining_to_assign) # Don't assign more than available

        ai_deployments.append({
            'owner': owner_id,
            'unit_type': unit_type,
            'count': count_for_this_cell,
            'x': cell_coord[0],
            'y': cell_coord[1]
        })
        current_occupied_coords.append(cell_coord)
        units_remaining_to_assign -= count_for_this_cell
        
    # If units still remain (e.g. no cells were available), they are not deployed.
    # This is a simplification; a real game might handle this differently.

    return ai_deployments, current_occupied_coords


def initialize_map():
    return [[None for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]

def populate_map_from_deployments(deployments_list):
    game_map = initialize_map()
    for dep in deployments_list:
        if 0 <= dep['x'] < MAP_SIZE and 0 <= dep['y'] < MAP_SIZE:
            if game_map[dep['x']][dep['y']] is None:
                game_map[dep['x']][dep['y']] = {'owner': dep['owner'], 'unit_type': dep['unit_type'], 'count': dep['count']}
            else:
                # Handle error or update logic if cell is already occupied (e.g. merging units)
                # For now, this implies an error in deployment list generation or validation
                app.logger.warning(f"Cell {dep['x']},{dep['y']} already occupied during map population. New: {dep}, Existing: {game_map[dep['x']][dep['y']]}")
                # Overwrite for now, assuming validation should prevent this for distinct player deployments
                game_map[dep['x']][dep['y']] = {'owner': dep['owner'], 'unit_type': dep['unit_type'], 'count': dep['count']}

    return game_map

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/submit_round_1', methods=['POST'])
def submit_round_1():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'Invalid request, no JSON data received.'}), 400

        player_r1_deployments_input = data.get('player_deployments')

        # --- R1 Player Deployment Validation ---
        if not isinstance(player_r1_deployments_input, list):
            return jsonify({'error': 'Invalid player_deployments format. Must be a list.'}), 400

        validated_player_r1_deployments = []
        player_r1_total_deployed_count = 0
        player_occupied_cells_r1 = set()

        for dep in player_r1_deployments_input:
            if not isinstance(dep, dict): return jsonify({'error': 'Invalid deployment item (must be dict).'}), 400
            unit_type = dep.get('unit_type')
            unit_count_str = dep.get('unit_count')
            x, y = dep.get('x'), dep.get('y')

            if unit_type not in VALID_UNIT_TYPES: return jsonify({'error': f'Invalid unit_type: {unit_type}.'}), 400
            if not isinstance(x, int) or not isinstance(y, int) or \
               not (0 <= x < MAP_SIZE and 0 <= y < MAP_SIZE):
                return jsonify({'error': f'Invalid coordinates: ({x},{y}). Must be 0-{MAP_SIZE-1}.'}), 400
            if (x,y) in player_occupied_cells_r1: return jsonify({'error': f'Player cannot deploy to the same cell ({x},{y}) twice in R1.'}), 400
            
            try:
                unit_count = int(unit_count_str)
                if unit_count <= 0: return jsonify({'error': 'Unit count must be positive.'}), 400
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid unit_count format.'}), 400
            
            validated_player_r1_deployments.append({'owner': 'P1', 'unit_type': unit_type, 'count': unit_count, 'x': x, 'y': y})
            player_r1_total_deployed_count += unit_count
            player_occupied_cells_r1.add((x,y))

        if player_r1_total_deployed_count > 10: # R1 Budget
            return jsonify({'error': f'Player R1 deployment exceeds budget of 10 (deployed {player_r1_total_deployed_count}).'}), 400
        if player_r1_total_deployed_count < 1: # Must deploy at least 1 unit
             return jsonify({'error': 'Player must deploy at least 1 unit in Round 1.'}), 400


        # --- AI R1 Deployment ---
        # For R1, AI also has a budget of 10. For simplicity, assume it deploys one type of unit.
        ai_r1_total_budget = 10
        ai_r1_chosen_unit_type = random.choice(VALID_UNIT_TYPES)
        
        # AI needs to deploy on cells not occupied by the player
        ai_r1_deployments, _ = deploy_ai_units(
            ai_r1_total_budget, 
            ai_r1_chosen_unit_type, 
            list(player_occupied_cells_r1), # Pass player's cells as occupied
            "AI"
        )
        
        ai_r1_actual_deployed_count = sum(d['count'] for d in ai_r1_deployments)


        # --- Map State Construction R1 ---
        all_r1_deployments = validated_player_r1_deployments + ai_r1_deployments
        current_map_state = populate_map_from_deployments(all_r1_deployments)
        
        # --- Combat Logic (Simplified - based on total counts, not map) ---
        # This part remains the same as before, using total counts for strength calculation
        player_r1_eff_strength = 0
        # Assume single unit type for player for this strength calc, or sum up if multiple types were allowed in validated_player_r1_deployments
        # For now, let's use the first deployment's type for player's overall unit type for combat
        # This is a simplification from previous logic where player chose one type and one count.
        # The new deployment structure means player can deploy multiple types.
        # For FAIRNESS, combat should consider this. Let's calculate strength based on *each* deployed stack.
        
        # Recalculate player_r1_eff_strength based on all their deployed units
        player_r1_total_strength_for_combat = 0
        # For AI combat strength, we need AI's overall chosen type for this round for modifier calculations
        # The current AI deploys one type, so ai_r1_chosen_unit_type is fine.
        # For player, if they deploy multiple types, how does the modifier work?
        # The original combat was one type vs one type.
        # Let's keep it simple: player's "overall" type for R1 is the type of their largest deployed stack.
        # This is a placeholder for potentially more complex combat logic.
        
        # Determine player's primary type for combat (e.g., type of largest deployment)
        # Or, for now, assume player also picks one "main" type for the round for combat calc,
        # even if deployments are varied.
        # The problem description says "The existing R1 combat logic ... should remain UNCHANGED".
        # This implies we still need a single player_r1_unit_type and player_r1_unit_count for that logic.
        # This conflicts with the new deployment input.
        # RESOLUTION: For now, use the *total deployed count* for player for combat,
        # and use the *first unit type in their deployment list* as their "main type" for modifier.
        
        player_r1_combat_unit_type = validated_player_r1_deployments[0]['unit_type'] if validated_player_r1_deployments else VALID_UNIT_TYPES[0]
        player_r1_combat_total_count = player_r1_total_deployed_count

        ai_r1_combat_unit_type = ai_r1_chosen_unit_type
        ai_r1_combat_total_count = ai_r1_actual_deployed_count


        player_modifier = 1.0
        ai_modifier = 1.0
        if (player_r1_combat_unit_type == 'infantry' and ai_r1_combat_unit_type == 'archers') or \
           (player_r1_combat_unit_type == 'archers' and ai_r1_combat_unit_type == 'cavalry') or \
           (player_r1_combat_unit_type == 'cavalry' and ai_r1_combat_unit_type == 'infantry'):
            player_modifier = 1.25
        elif (ai_r1_combat_unit_type == 'infantry' and player_r1_combat_unit_type == 'archers') or \
              (ai_r1_combat_unit_type == 'archers' and player_r1_combat_unit_type == 'cavalry') or \
              (ai_r1_combat_unit_type == 'cavalry' and player_r1_combat_unit_type == 'infantry'):
            ai_modifier = 1.25

        player_r1_eff_strength = float(player_r1_combat_total_count) * player_modifier
        ai_r1_eff_strength = float(ai_r1_combat_total_count) * ai_modifier
        
        r1_winner = "Draw"
        if player_r1_eff_strength > ai_r1_eff_strength: r1_winner = "Player"
        elif ai_r1_eff_strength > player_r1_eff_strength: r1_winner = "AI"

        player_r2_base_recruits = 10 + (10 - player_r1_combat_total_count) # Based on total deployed
        ai_r2_base_recruits = 10 + (10 - ai_r1_combat_total_count)     # Based on total deployed

        strength_diff = abs(player_r1_eff_strength - ai_r1_eff_strength)
        bonus_troops = int(strength_diff)
        player_r2_bonus, ai_r2_bonus = (bonus_troops, 0) if r1_winner == "Player" else (0, bonus_troops) if r1_winner == "AI" else (0,0)
        
        player_total_r2_pool = max(0, player_r2_base_recruits + player_r2_bonus)
        ai_total_r2_pool = max(0, ai_r2_base_recruits + ai_r2_bonus)

        return jsonify({
            'round_1_results': {
                'player_army': {
                    'type': player_r1_combat_unit_type,
                    'count': player_r1_combat_total_count,
                    'strength': player_r1_eff_strength
                },
                'ai_army': {
                    'type': ai_r1_combat_unit_type,
                    'count': ai_r1_combat_total_count,
                    'strength': ai_r1_eff_strength
                },
                'round_winner': r1_winner
            },
            'player_r1_deployments': validated_player_r1_deployments,
            'ai_r1_deployments': ai_r1_deployments,
            'current_map_state': current_map_state,
            'player_r2_data': {'base_recruits': player_r2_base_recruits, 'bonus': player_r2_bonus, 'total_r2_pool': player_total_r2_pool},
            # Pass AI's R1 chosen type and actual deployed count for R2 AI budget reference if needed
            'ai_r1_army_details_for_r2': {'type': ai_r1_combat_unit_type, 'count': ai_r1_combat_total_count}, 
            'ai_r2_data_for_r2': {'base_recruits': ai_r2_base_recruits, 'bonus': ai_r2_bonus, 'total_r2_pool': ai_total_r2_pool}
        })

    except Exception as e:
        app.logger.error(f"Error in /submit_round_1: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({'error': 'An unexpected error occurred on the server.'}), 500


@app.route('/submit_round_2', methods=['POST'])
def submit_round_2():
    try:
        data = request.get_json(silent=True)
        if not data: return jsonify({'error': 'Invalid request, no JSON data received.'}), 400

        # --- Required R1 Data from Client ---
        player_r1_deployments_from_client = data.get('player_r1_deployments')
        ai_r1_deployments_from_client = data.get('ai_r1_deployments')
        ai_r2_data_from_client = data.get('ai_r2_data_for_r2') # For AI's R2 budget
        player_r2_pool_from_client = data.get('player_r2_total_pool') # Player's R2 budget

        if not all([player_r1_deployments_from_client, ai_r1_deployments_from_client, ai_r2_data_from_client, player_r2_pool_from_client is not None]):
            return jsonify({'error': 'Missing R1 deployment data or R2 pool data from client.'}), 400
        
        ai_total_r2_budget = int(ai_r2_data_from_client.get('total_r2_pool', 0))
        player_total_r2_budget = int(player_r2_pool_from_client)


        # --- Player R2 Deployment Input & Validation ---
        player_r2_deployments_input = data.get('player_deployments_r2')
        if not isinstance(player_r2_deployments_input, list):
            return jsonify({'error': 'Invalid player_deployments_r2 format.'}), 400

        validated_player_r2_deployments = []
        player_r2_total_deployed_count = 0
        player_occupied_cells_r2 = set() # For self-collision in R2 deployments

        # Reconstruct occupied cells from R1 to avoid collision
        r1_occupied_coords = set()
        for dep in player_r1_deployments_from_client: r1_occupied_coords.add((dep['x'], dep['y']))
        for dep in ai_r1_deployments_from_client: r1_occupied_coords.add((dep['x'], dep['y']))
        
        for dep in player_r2_deployments_input:
            if not isinstance(dep, dict): return jsonify({'error': 'Invalid R2 deployment item.'}), 400
            unit_type, count_str, x, y = dep.get('unit_type'), dep.get('unit_count'), dep.get('x'), dep.get('y')

            if unit_type not in VALID_UNIT_TYPES: return jsonify({'error': f'R2: Invalid unit_type: {unit_type}.'}), 400
            if not isinstance(x, int) or not isinstance(y, int) or \
               not (0 <= x < MAP_SIZE and 0 <= y < MAP_SIZE):
                return jsonify({'error': f'R2: Invalid coordinates: ({x},{y}).'}), 400
            if (x,y) in player_occupied_cells_r2: return jsonify({'error': f'Player cannot deploy to the same cell ({x},{y}) twice in R2.'}), 400
            if (x,y) in r1_occupied_coords: return jsonify({'error': f'Player R2 cannot deploy to an R1 occupied cell ({x},{y}).'}), 400
            
            try:
                unit_count = int(count_str)
                if unit_count < 0: return jsonify({'error': 'R2 unit count cannot be negative.'}), 400 # Can deploy 0
            except (ValueError, TypeError): return jsonify({'error': 'R2: Invalid unit_count format.'}), 400
            
            validated_player_r2_deployments.append({'owner': 'P1', 'unit_type': unit_type, 'count': unit_count, 'x': x, 'y': y})
            player_r2_total_deployed_count += unit_count
            player_occupied_cells_r2.add((x,y))
        
        if player_r2_total_deployed_count > player_total_r2_budget:
             return jsonify({'error': f'Player R2 deployment ({player_r2_total_deployed_count}) exceeds budget of {player_total_r2_budget}.'}), 400


        # --- AI R2 Deployment ---
        ai_r2_chosen_unit_type = random.choice(VALID_UNIT_TYPES)
        # AI deploys on cells not occupied in R1 or by player's R2 choices
        current_all_occupied_coords = list(r1_occupied_coords.union(player_occupied_cells_r2))
        
        ai_r2_deployments, _ = deploy_ai_units(
            ai_total_r2_budget, 
            ai_r2_chosen_unit_type, 
            current_all_occupied_coords,
            "AI"
        )
        ai_r2_actual_deployed_count = sum(d['count'] for d in ai_r2_deployments)

        # --- Map State Construction R2 ---
        # Combine R1 and R2 deployments
        final_all_deployments = player_r1_deployments_from_client + \
                                ai_r1_deployments_from_client + \
                                validated_player_r2_deployments + \
                                ai_r2_deployments
        final_map_state = populate_map_from_deployments(final_all_deployments)

        # --- R2 Combat Logic (Simplified - based on total R2 counts) ---
        # Similar to R1, use total R2 deployed counts and a "main" type for combat modifiers.
        player_r2_combat_unit_type = validated_player_r2_deployments[0]['unit_type'] if validated_player_r2_deployments and player_r2_total_deployed_count > 0 else VALID_UNIT_TYPES[0]
        player_r2_combat_total_count = player_r2_total_deployed_count

        ai_r2_combat_unit_type = ai_r2_chosen_unit_type
        ai_r2_combat_total_count = ai_r2_actual_deployed_count

        player_modifier = 1.0
        ai_modifier = 1.0
        if player_r2_combat_total_count > 0: # only apply modifier if units exist
            if (player_r2_combat_unit_type == 'infantry' and ai_r2_combat_unit_type == 'archers') or \
               (player_r2_combat_unit_type == 'archers' and ai_r2_combat_unit_type == 'cavalry') or \
               (player_r2_combat_unit_type == 'cavalry' and ai_r2_combat_unit_type == 'infantry'):
                player_modifier = 1.25
        
        if ai_r2_combat_total_count > 0: # only apply modifier if units exist
            if (ai_r2_combat_unit_type == 'infantry' and player_r2_combat_unit_type == 'archers') or \
                  (ai_r2_combat_unit_type == 'archers' and player_r2_combat_unit_type == 'cavalry') or \
                  (ai_r2_combat_unit_type == 'cavalry' and player_r2_combat_unit_type == 'infantry'):
                ai_modifier = 1.25
        
        player_r2_eff_strength = float(player_r2_combat_total_count) * player_modifier
        ai_r2_eff_strength = float(ai_r2_combat_total_count) * ai_modifier

        r2_winner = "Draw"
        if player_r2_eff_strength > ai_r2_eff_strength: r2_winner = "Player"
        elif ai_r2_eff_strength > player_r2_eff_strength: r2_winner = "AI"
        
        game_winner = r2_winner # In this version, R2 winner is game winner

        return jsonify({
            'round_2_results': {
                'player_army_summary_for_combat': {'type': player_r2_combat_unit_type, 'count': player_r2_combat_total_count, 'strength': player_r2_eff_strength},
                'ai_army_summary_for_combat': {'type': ai_r2_combat_unit_type, 'count': ai_r2_combat_total_count, 'strength': ai_r2_eff_strength},
                'round_winner': r2_winner
            },
            'player_r2_deployments': validated_player_r2_deployments,
            'ai_r2_deployments': ai_r2_deployments,
            'final_map_state': final_map_state,
            'game_winner': game_winner
        })

    except Exception as e:
        app.logger.error(f"Error in /submit_round_2: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({'error': 'An unexpected error occurred on the server.'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
