import unittest
import json
from launch import app # Import the Flask app instance

class TestGameLogic(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_play_endpoint_valid_choices(self):
        # Test a few valid scenarios
        test_cases = [
            {'choice': 'rock', 'expected_keys': ['player_choice', 'computer_choice', 'result']},
            {'choice': 'paper', 'expected_keys': ['player_choice', 'computer_choice', 'result']},
            {'choice': 'scissors', 'expected_keys': ['player_choice', 'computer_choice', 'result']},
        ]

        for case in test_cases:
            with self.subTest(case=case):
                response = self.app.post('/play',
                                         data=json.dumps({'choice': case['choice']}),
                                         content_type='application/json')
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.data.decode())
                for key in case['expected_keys']:
                    self.assertIn(key, data)
                self.assertEqual(data['player_choice'], case['choice'])

    def test_play_endpoint_invalid_choice(self):
        response = self.app.post('/play',
                                 data=json.dumps({'choice': 'lizard'}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Invalid choice')

    def test_play_endpoint_missing_choice(self):
        response = self.app.post('/play',
                                 data=json.dumps({}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 400) # Or as per your error handling for missing key
        data = json.loads(response.data.decode())
        self.assertIn('error', data)

    def test_game_logic_win_lose_tie(self):
        # This test is more conceptual for the logic within the endpoint,
        # as true randomness makes specific outcomes hard to test directly without mocking.
        # However, we can check if the result is one of the expected outcomes.
        # For more robust testing of game rules, you'd typically extract the core game logic
        # into a separate function and test that function directly with all combinations.

        # Here, we'll just ensure the response structure is correct and result is valid.
        for _ in range(10): # Run a few times to get different computer choices
            player_choice = random.choice(['rock', 'paper', 'scissors'])
            response = self.app.post('/play',
                                     data=json.dumps({'choice': player_choice}),
                                     content_type='application/json')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data.decode())
            self.assertIn(data['result'], ['You Win!', 'You Lose!', 'Tie'])
            self.assertEqual(data['player_choice'], player_choice)
            self.assertIn(data['computer_choice'], ['rock', 'paper', 'scissors'])

if __name__ == '__main__':
    # Need to import random for the test_game_logic_win_lose_tie to run directly
    import random
    unittest.main()
