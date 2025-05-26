import unittest
import json
from launch import app # Assuming app is your Flask application instance

class TestMapBasedGameLogic(unittest.TestCase):

    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()
        app.testing = True
        self.client = app.test_client()

    def tearDown(self):
        self.app_context.pop()

    def _get_json_response(self, response):
        try:
            return json.loads(response.data.decode('utf-8'))
        except json.JSONDecodeError:
            self.fail(f"FAIL: Response is not valid JSON. Status: {response.status_code}, Data: {response.data[:200]}") # Show partial data

    # --- /submit_round_1 Tests ---
    def test_r1_valid_submission(self):
        payload = {
            "player_deployments": [
                {"unit_type": "infantry", "unit_count": 5, "x": 0, "y": 0},
                {"unit_type": "archers", "unit_count": 5, "x": 0, "y": 1}
            ]
        } # Total 10 units
        response = self.client.post('/submit_round_1', json=payload)
        data = self._get_json_response(response)
        self.assertEqual(response.status_code, 200, f"R1 valid submission failed. Data: {data}")
        
        self.assertIn('round_1_results', data)
        self.assertIn('player_r2_data', data)
        self.assertIn('ai_r1_deployments', data) # Check for AI R1 deployments
        self.assertIn('player_r1_deployments', data) # Check for player R1 deployments returned
        self.assertIn('current_map_state', data)
        self.assertEqual(len(data['current_map_state']), 5) # 5 rows
        self.assertEqual(len(data['current_map_state'][0]), 5) # 5 columns

        # Check if player's deployments are on the map
        map_state = data['current_map_state']
        # Payload: {"unit_type": "infantry", "unit_count": 5, "x": 0, "y": 0}
        # Map access map[y][x] -> map_state[0][0]
        cell_0_0 = map_state[0][0] 
        self.assertIsNotNone(cell_0_0)
        if cell_0_0: 
            self.assertEqual(cell_0_0.get('owner'), 'P1')
            self.assertEqual(cell_0_0.get('unit_type'), 'infantry')
            self.assertEqual(cell_0_0.get('count'), 5)
        
        # Payload: {'unit_type': 'archers', 'unit_count': 5, 'x': 0, 'y': 1}
        # Map access map[y][x] -> map_state[1][0]
        cell_1_0_map = map_state[1][0] 
        self.assertIsNotNone(cell_1_0_map)
        if cell_1_0_map:
            self.assertEqual(cell_1_0_map.get('owner'), 'P1')
            self.assertEqual(cell_1_0_map.get('unit_type'), 'archers')
            self.assertEqual(cell_1_0_map.get('count'), 5)


    def test_r1_invalid_total_unit_count_too_high(self):
        payload = {
            "player_deployments": [
                {"unit_type": "infantry", "unit_count": 6, "x": 0, "y": 0},
                {"unit_type": "archers", "unit_count": 5, "x": 0, "y": 1}
            ]
        } # Total 11 units
        response = self.client.post('/submit_round_1', json=payload)
        self.assertEqual(response.status_code, 400)
        data = self._get_json_response(response)
        self.assertIn('error', data)
        # Based on current backend, error is "Player R1 deployment exceeds budget of 10"
        self.assertIn("exceeds budget of 10", data['error']) 

    def test_r1_invalid_total_unit_count_too_low(self):
        payload = {
            "player_deployments": [
                {"unit_type": "infantry", "unit_count": 4, "x": 0, "y": 0}
            ]
        } # Total 4 units
        response = self.client.post('/submit_round_1', json=payload)
        self.assertEqual(response.status_code, 400)
        data = self._get_json_response(response)
        self.assertIn('error', data)
        # Based on current backend, error is "Player must deploy at least 1 unit in Round 1."
        # Or if total is >0 but <10: "Player R1 deployment must be exactly 10 units total."
        # The backend currently has "Player R1 deployment exceeds budget of 10" or "Player must deploy at least 1 unit"
        # Let's adjust this test to expect the "at least 1 unit" if the total is less than 1,
        # and a different message if it's between 1 and 9.
        # For now, the backend logic implies any non-10 count (that is >0) might pass initial checks then fail a specific "total must be 10" if that's a rule.
        # The current backend doesn't enforce "exactly 10", only "not > 10" and "not < 1".
        # This test should reflect the actual backend validation for counts.
        # If the backend was changed to "must be exactly 10", this test would be:
        # self.assertIn("Total deployed unit count for Round 1 must be exactly 10.", data['error'])
        # Current backend: "Player R1 deployment exceeds budget of 10 (deployed {player_r1_total_deployed_count})."
        # Or: "Player must deploy at least 1 unit in Round 1."
        # Let's assume for this test, a count of 4 is valid for deployment but might fail a game rule not explicitly a 400 error for schema.
        # The subtask description of tests included "Total deployed unit count for Round 1 must be exactly 10."
        # This implies the backend *should* have this rule.
        # The current backend has:
        # if player_r1_total_deployed_count > 10: return jsonify({'error': f'Player R1 deployment exceeds budget of 10 (deployed {player_r1_total_deployed_count}).'}), 400
        # if player_r1_total_deployed_count < 1: return jsonify({'error': 'Player must deploy at least 1 unit in Round 1.'}), 400
        # So there's no "must be exactly 10" error, only upper/lower bounds.
        # The test should reflect this.
        # For a count of 4, it should be successful (status 200), as it's >=1 and <=10.
        # The test in the prompt seems to expect a stricter rule.
        # I will keep the test as per the prompt for now, assuming backend should enforce "exactly 10".
        self.assertIn("Player R1 deployment must be exactly 10 units total.", data.get('error', 'Error message not found or not as expected'))


    def test_r1_invalid_coordinates_out_of_bounds(self):
        payload = {
            "player_deployments": [
                {"unit_type": "infantry", "unit_count": 10, "x": 0, "y": 5} # y is out of bounds
            ]
        }
        response = self.client.post('/submit_round_1', json=payload)
        self.assertEqual(response.status_code, 400)
        data = self._get_json_response(response)
        self.assertIn('error', data)
        self.assertIn("Invalid coordinates", data['error']) 

    def test_r1_overlapping_player_deployments(self):
        payload = {
            "player_deployments": [
                {"unit_type": "infantry", "unit_count": 5, "x": 0, "y": 0},
                {"unit_type": "archers", "unit_count": 5, "x": 0, "y": 0} # Overlap
            ]
        }
        response = self.client.post('/submit_round_1', json=payload)
        self.assertEqual(response.status_code, 400)
        data = self._get_json_response(response)
        self.assertIn('error', data)
        self.assertIn("Player cannot deploy to the same cell (0,0) twice in R1.", data['error'])


    # --- /submit_round_2 Tests ---
    def test_r2_valid_submission(self):
        # Step 1: Successful Round 1
        r1_payload = {
            "player_deployments": [{"unit_type": "infantry", "unit_count": 10, "x": 0, "y": 0}]
        }
        r1_response = self.client.post('/submit_round_1', json=r1_payload)
        self.assertEqual(r1_response.status_code, 200, f"R1 call failed for R2 test setup. Data: {self._get_json_response(r1_response)}")
        r1_data = self._get_json_response(r1_response)

        player_r1_deployments_from_r1 = r1_data['player_r1_deployments']
        ai_r1_deployments_from_r1 = r1_data['ai_r1_deployments']
        ai_r2_data_for_r2_from_r1 = r1_data['ai_r2_data_for_r2']
        player_r2_pool = r1_data['player_r2_data']['total_r2_pool']

        # Step 2: Round 2 submission
        player_r2_deployments_list = []
        # Ensure player_r2_pool is an int before comparison
        if isinstance(player_r2_pool, int) and player_r2_pool > 0:
            player_r2_deployments_list.append(
                {"unit_type": "cavalry", "unit_count": player_r2_pool, "x": 1, "y": 1} 
            )
        
        r2_payload = {
            "player_deployments_r2": player_r2_deployments_list,
            "player_r1_deployments": player_r1_deployments_from_r1,
            "ai_r1_deployments": ai_r1_deployments_from_r1,
            "ai_r2_data_for_r2": ai_r2_data_for_r2_from_r1,
            "player_r2_total_pool": player_r2_pool # Added this field as per backend expectation
        }

        r2_response = self.client.post('/submit_round_2', json=r2_payload)
        data = self._get_json_response(r2_response)
        self.assertEqual(r2_response.status_code, 200, f"R2 valid submission failed. Data: {data}")

        self.assertIn('round_2_results', data)
        self.assertIn('game_winner', data)
        self.assertIn('final_map_state', data)
        self.assertEqual(len(data['final_map_state']), 5)
        self.assertEqual(len(data['final_map_state'][0]), 5)

        if player_r2_deployments_list:
            map_state_r2 = data['final_map_state']
            cell_1_1_r2 = map_state_r2[1][1] # y=1, x=1
            self.assertIsNotNone(cell_1_1_r2, "Player R2 deployment not found on map where expected.")
            if cell_1_1_r2:
                self.assertEqual(cell_1_1_r2.get('owner'), 'P1')
                self.assertEqual(cell_1_1_r2.get('unit_type'), player_r2_deployments_list[0]['unit_type'])
                self.assertEqual(cell_1_1_r2.get('count'), player_r2_deployments_list[0]['unit_count'])
        
        map_state_r2 = data['final_map_state']
        cell_0_0_r1_in_r2 = map_state_r2[0][0] # y=0, x=0
        self.assertIsNotNone(cell_0_0_r1_in_r2, "Player R1 deployment not found on R2 map.")
        if cell_0_0_r1_in_r2:
             self.assertEqual(cell_0_0_r1_in_r2.get('owner'), 'P1')

    def test_r2_invalid_total_unit_count(self):
        r1_payload = {"player_deployments": [{"unit_type": "infantry", "unit_count": 10, "x": 0, "y": 0}]}
        r1_response = self.client.post('/submit_round_1', json=r1_payload)
        r1_data = self._get_json_response(r1_response)

        player_r2_pool = r1_data['player_r2_data']['total_r2_pool']
        
        r2_payload = {
            "player_deployments_r2": [
                {"unit_type": "archers", "unit_count": player_r2_pool + 1, "x": 1, "y": 0}
            ],
            "player_r1_deployments": r1_data['player_r1_deployments'],
            "ai_r1_deployments": r1_data['ai_r1_deployments'],
            "ai_r2_data_for_r2": r1_data['ai_r2_data_for_r2'],
            "player_r2_total_pool": player_r2_pool
        }
        response = self.client.post('/submit_round_2', json=r2_payload)
        self.assertEqual(response.status_code, 400)
        data = self._get_json_response(response)
        self.assertIn('error', data)
        self.assertIn("exceeds budget", data['error']) # Generic check based on backend

    def test_r2_missing_r1_deployment_data(self):
        r1_payload = {"player_deployments": [{"unit_type": "infantry", "unit_count": 10, "x": 0, "y": 0}]}
        r1_response = self.client.post('/submit_round_1', json=r1_payload)
        r1_data = self._get_json_response(r1_response)
        
        r2_payload = {
            "player_deployments_r2": [{"unit_type": "cavalry", "unit_count": 5, "x": 1, "y": 1}],
            "ai_r2_data_for_r2": r1_data['ai_r2_data_for_r2'],
            "player_r2_total_pool": r1_data['player_r2_data']['total_r2_pool']
            # Missing player_r1_deployments, ai_r1_deployments
        }
        response = self.client.post('/submit_round_2', json=r2_payload)
        self.assertEqual(response.status_code, 400)
        data = self._get_json_response(response)
        self.assertIn('error', data)
        self.assertIn("Missing R1 deployment data", data['error'])

if __name__ == '__main__':
    unittest.main()

```
