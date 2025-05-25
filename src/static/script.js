document.addEventListener('DOMContentLoaded', () => {
    const rockButton = document.getElementById('rock');
    const paperButton = document.getElementById('paper');
    const scissorsButton = document.getElementById('scissors');

    const playerChoiceDisplay = document.getElementById('player-choice');
    const computerChoiceDisplay = document.getElementById('computer-choice');
    const resultDisplay = document.getElementById('result');

    const choices = ['rock', 'paper', 'scissors'];

    async function playGame(playerChoice) {
        playerChoiceDisplay.textContent = playerChoice;
        computerChoiceDisplay.textContent = ''; // Clear previous computer choice
        resultDisplay.textContent = 'Thinking...';

        try {
            const response = await fetch('/play', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ choice: playerChoice }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            computerChoiceDisplay.textContent = data.computer_choice;
            resultDisplay.textContent = data.result;

        } catch (error) {
            console.error('Error playing game:', error);
            resultDisplay.textContent = 'Error! Could not get result.';
        }
    }

    rockButton.addEventListener('click', () => playGame('rock'));
    paperButton.addEventListener('click', () => playGame('paper'));
    scissorsButton.addEventListener('click', () => playGame('scissors'));
});
