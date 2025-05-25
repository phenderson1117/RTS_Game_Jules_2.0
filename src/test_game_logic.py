import unittest
import json
import random # Keep random for potential future use or if app uses it globally
from launch import app # Import the Flask app instance

class TestTwoRoundGameLogic(unittest.TestCase):

    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push() # Push an application context
        app.testing = True
        self.client = app.test_client()
        # Seed random for predictable AI choices in tests, if necessary for some tests
        # random.seed(12345)


    def tearDown(self):
        self.app_context.pop() # Pop the application context


    def _get_json_response(self, response):
        try:
            return json.loads(response.data.decode('utf-8'))
        except json.JSONDecodeError:
            self.fail(f"Failed to decode JSON from response. Status: {response.status_code}, Data: {response.data}")

    # --- Tests for /submit_round_1 ---
    def test_submit_round_1_valid_submission(self):
        payload = {'unit_type': 'infantry', 'unit_count': 10}
        response = self.client.post('/submit_round_1', json=payload)
        self.assertEqual(response.status_code, 200)
        data = self._get_json_response(response)

        self.assertIn('round_1_results', data)
        self.assertIn('player_r2_data', data)
        self.assertIn('ai_r1_army_details_for_r2', data)
        self.assertIn('ai_r2_data_for_r2', data)

        r1_res = data['round_1_results']
        self.assertEqual(r1_res['player_army']['type'], 'infantry')
        self.assertEqual(r1_res['player_army']['count'], 10)
        self.assertIn(r1_res['ai_army']['type'], ['infantry', 'archers', 'cavalry'])
        self.assertTrue(1 <= r1_res['ai_army']['count'] <= 10)
        self.assertIn(r1_res['round_winner'], ['Player', 'AI', 'Draw'])

        # Check R2 pool calculations (example structure, actual values depend on random AI)
        player_r2 = data['player_r2_data']
        self.assertIsInstance(player_r2['base_recruits'], int)
        self.assertIsInstance(player_r2['bonus'], int)
        self.assertIsInstance(player_r2['total_r2_pool'], int)
        self.assertEqual(player_r2['base_recruits'], 10 - payload['unit_count']) # 0 in this case
        self.assertTrue(player_r2['total_r2_pool'] >= player_r2['base_recruits'])


    def test_submit_round_1_invalid_unit_type(self):
        payload = {'unit_type': 'dragon', 'unit_count': 5}
        response = self.client.post('/submit_round_1', json=payload)
        self.assertEqual(response.status_code, 400)
        data = self._get_json_response(response)
        self.assertIn('error', data)
        self.assertIn('Invalid unit_type', data['error'])

    def test_submit_round_1_invalid_unit_count_too_high(self):
        payload = {'unit_type': 'archers', 'unit_count': 11}
        response = self.client.post('/submit_round_1', json=payload)
        self.assertEqual(response.status_code, 400)
        data = self._get_json_response(response)
        self.assertIn('error', data)
        self.assertIn("Invalid unit_count for Round 1. Must be an integer between 1 and 10.", data['error'])
        
    def test_submit_round_1_invalid_unit_count_zero(self):
        payload = {'unit_type': 'archers', 'unit_count': 0}
        response = self.client.post('/submit_round_1', json=payload)
        self.assertEqual(response.status_code, 400) # Should fail as count must be 1-10
        data = self._get_json_response(response)
        self.assertIn('error', data)

    def test_submit_round_1_missing_unit_count(self):
        payload = {'unit_type': 'cavalry'}
        response = self.client.post('/submit_round_1', json=payload)
        self.assertEqual(response.status_code, 400)
        data = self._get_json_response(response)
        self.assertIn('error', data)
        self.assertIn('Invalid unit_count', data['error']) # or similar, depending on error message for None

    def test_submit_round_1_no_json_data(self):
        response = self.client.post('/submit_round_1', data="not json")
        self.assertEqual(response.status_code, 400) # Flask usually handles this if not json
        data = self._get_json_response(response)
        self.assertIn('error', data)
        self.assertIn('Invalid request, no JSON data received', data['error'])


    # --- Test specific R1 combat scenarios and R2 pool calculations ---
    def test_r1_player_wins_gets_bonus(self):
        # Mock AI choice or run multiple times if AI is random
        # This requires more control over AI or analyzing the known game logic
        # For simplicity, we'll check structure and player's base recruits.
        # A full test would involve mocking random.choice for AI.
        
        # Player: 10 Infantry, AI: 5 Archers (Player should win big)
        # Player strength: 10 * 1.25 = 12.5
        # AI strength: 5 * 1.0 = 5.0
        # Diff = 7.5. Bonus = floor(7.5) = 7
        # Player R2 Base = 10 - 10 = 0. Player R2 Total = 0 + 7 = 7
        # AI R2 Base = 10 - 5 = 5. AI R2 Total = 5 + 0 = 5
        
        # To make this deterministic, we'd need to patch random.choice and random.randint
        # For now, let's assume the logic inside the endpoint is what we test conceptually.
        pass # Placeholder for more complex scenario testing

    # --- Tests for /submit_round_2 ---
    def test_submit_round_2_valid_submission(self):
        # First, simulate a Round 1 to get necessary AI data for Round 2
        r1_payload = {'unit_type': 'infantry', 'unit_count': 5}
        r1_response = self.client.post('/submit_round_1', json=r1_payload)
        self.assertEqual(r1_response.status_code, 200, "R1 call failed, cannot proceed to R2 test")
        r1_data = self._get_json_response(r1_response)

        ai_r1_details = r1_data['ai_r1_army_details_for_r2']
        ai_r2_pool_data = r1_data['ai_r2_data_for_r2']
        player_r2_pool = r1_data['player_r2_data']['total_r2_pool']

        # Player R2 choices
        player_r2_unit_count = min(player_r2_pool, 5) # Use some or all of the pool, ensure non-negative
        if player_r2_pool == 0 and player_r2_unit_count < 0 : player_r2_unit_count = 0 # Cannot deploy negative

        r2_payload = {
            'unit_type': 'archers',
            'unit_count': player_r2_unit_count,
            'ai_r1_army_details_for_r2': ai_r1_details,
            'ai_r2_data_for_r2': ai_r2_pool_data
        }
        
        response = self.client.post('/submit_round_2', json=r2_payload)
        self.assertEqual(response.status_code, 200, f"R2 call failed. Payload: {r2_payload}, R1 Data: {r1_data}")
        data = self._get_json_response(response)

        self.assertIn('round_2_results', data)
        self.assertIn('game_winner', data)

        r2_res = data['round_2_results']
        self.assertEqual(r2_res['player_army']['type'], 'archers')
        self.assertEqual(r2_res['player_army']['count'], player_r2_unit_count)
        self.assertIn(r2_res['ai_army']['type'], ['infantry', 'archers', 'cavalry'])
        # AI R2 count can be 0 up to its total_r2_pool
        self.assertTrue(0 <= r2_res['ai_army']['count'] <= ai_r2_pool_data['total_r2_pool'])
        self.assertIn(r2_res['round_winner'], ['Player', 'AI', 'Draw'])
        self.assertEqual(data['game_winner'], r2_res['round_winner'])


    def test_submit_round_2_invalid_unit_type(self):
        # Simulate R1 data
        ai_r1_details = {'type': 'infantry', 'count': 5}
        ai_r2_pool_data = {'base_recruits': 5, 'bonus': 0, 'total_r2_pool': 5}
        
        payload = {
            'unit_type': 'wizard', 
            'unit_count': 3,
            'ai_r1_army_details_for_r2': ai_r1_details,
            'ai_r2_data_for_r2': ai_r2_pool_data
        }
        response = self.client.post('/submit_round_2', json=payload)
        self.assertEqual(response.status_code, 400)
        data = self._get_json_response(response)
        self.assertIn('error', data)
        self.assertIn('Invalid unit_type', data['error'])

    def test_submit_round_2_negative_unit_count(self):
        ai_r1_details = {'type': 'infantry', 'count': 5}
        ai_r2_pool_data = {'base_recruits': 5, 'bonus': 0, 'total_r2_pool': 5}
        payload = {
            'unit_type': 'cavalry', 
            'unit_count': -1,
            'ai_r1_army_details_for_r2': ai_r1_details,
            'ai_r2_data_for_r2': ai_r2_pool_data
        }
        response = self.client.post('/submit_round_2', json=payload)
        self.assertEqual(response.status_code, 400)
        data = self._get_json_response(response)
        self.assertIn('error', data)
        self.assertIn("Invalid unit_count for Round 2. Must be a non-negative integer.", data['error'])
        
    def test_submit_round_2_missing_ai_data(self):
        payload = {'unit_type': 'infantry', 'unit_count': 5} # Missing AI data
        response = self.client.post('/submit_round_2', json=payload)
        self.assertEqual(response.status_code, 400)
        data = self._get_json_response(response)
        self.assertIn('error', data)
        self.assertIn('Missing AI R2 data', data['error'])

if __name__ == '__main__':
    unittest.main()
