document.addEventListener('DOMContentLoaded', () => {
    // UI Elements for Input
    const unitTypeSelect = document.getElementById('unit-type');
    const unitCountInput = document.getElementById('unit-count');
    const deployButton = document.getElementById('deploy-button');

    // UI Elements for Display
    const playerArmyDisplay = document.getElementById('player-army-display');
    const computerArmyDisplay = document.getElementById('computer-army-display');
    const playerStrengthDisplay = document.getElementById('player-strength-display');
    const computerStrengthDisplay = document.getElementById('computer-strength-display');
    const resultDisplay = document.getElementById('result-display');

    deployButton.addEventListener('click', async () => {
        const unitType = unitTypeSelect.value;
        const unitCount = parseInt(unitCountInput.value, 10);

        if (isNaN(unitCount) || unitCount <= 0) {
            resultDisplay.textContent = 'Please enter a valid, positive unit count.';
            playerArmyDisplay.textContent = '';
            computerArmyDisplay.textContent = '';
            playerStrengthDisplay.textContent = '';
            computerStrengthDisplay.textContent = '';
            return;
        }

        playerArmyDisplay.textContent = '---';
        computerArmyDisplay.textContent = '---';
        playerStrengthDisplay.textContent = '---';
        computerStrengthDisplay.textContent = '---';
        resultDisplay.textContent = 'Battling...';

        try {
            const response = await fetch('/play', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    unit_type: unitType,
                    unit_count: unitCount
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                const errorMessage = data.error || `HTTP error! Status: ${response.status}`;
                throw new Error(errorMessage);
            }

            playerArmyDisplay.textContent = `${data.player_army.type} x${data.player_army.count}`;
            computerArmyDisplay.textContent = `${data.computer_army.type} x${data.computer_army.count}`;
            playerStrengthDisplay.textContent = data.player_effective_strength;
            computerStrengthDisplay.textContent = data.computer_effective_strength;
            resultDisplay.textContent = data.result;

        } catch (error) {
            console.error('Error playing game:', error);
            resultDisplay.textContent = `Error: ${error.message}`;
            playerArmyDisplay.textContent = 'Error';
            computerArmyDisplay.textContent = 'Error';
            playerStrengthDisplay.textContent = 'Error';
            computerStrengthDisplay.textContent = 'Error';
        }
    });
});
