document.addEventListener('DOMContentLoaded', () => {
    // --- Round 1 UI Elements ---
    const r1Section = document.getElementById('round-1-section');
    const r1UnitTypeSelect = document.getElementById('r1-unit-type');
    const r1UnitCountInput = document.getElementById('r1-unit-count');
    const deployR1Button = document.getElementById('deploy-r1-button');

    // --- Round 1 Results UI Elements ---
    const r1ResultsSection = document.getElementById('round-1-results-section');
    const playerR1ArmyDisplay = document.getElementById('player-r1-army-display');
    const playerR1StrengthDisplay = document.getElementById('player-r1-strength-display');
    const computerR1ArmyDisplay = document.getElementById('computer-r1-army-display');
    const computerR1StrengthDisplay = document.getElementById('computer-r1-strength-display');
    const r1WinnerDisplay = document.getElementById('r1-winner-display');
    const playerR2PoolDisplay = document.getElementById('player-r2-pool-display');

    // --- Round 2 UI Elements ---
    const r2Section = document.getElementById('round-2-section');
    const r2UnitTypeSelect = document.getElementById('r2-unit-type');
    const r2UnitCountInput = document.getElementById('r2-unit-count');
    const deployR2Button = document.getElementById('deploy-r2-button');
    const r2MaxUnitsLabel = document.getElementById('r2-max-units-label');

    // --- Round 2 Results UI Elements ---
    const r2ResultsSection = document.getElementById('round-2-results-section');
    const playerR2ArmyDisplay = document.getElementById('player-r2-army-display');
    const playerR2StrengthDisplay = document.getElementById('player-r2-strength-display');
    const computerR2ArmyDisplay = document.getElementById('computer-r2-army-display');
    const computerR2StrengthDisplay = document.getElementById('computer-r2-strength-display');
    const r2WinnerDisplay = document.getElementById('r2-winner-display');
    const gameWinnerDisplay = document.getElementById('game-winner-display');
    
    // --- General Message UI Element ---
    const generalMessageDisplay = document.getElementById('general-message-display');

    // --- Game State Variables ---
    let playerR2TotalPool = 0;
    let aiR1ArmyDetailsForR2 = null; // To store AI's R1 army details
    let aiR2DataForR2 = null;      // To store AI's R2 pool data

    function showMessage(message, isError = false) {
        generalMessageDisplay.textContent = message;
        generalMessageDisplay.style.color = isError ? 'red' : 'black';
    }
    
    function resetGameDisplay() {
        r1ResultsSection.style.display = 'none';
        r2Section.style.display = 'none';
        r2ResultsSection.style.display = 'none';
        
        r1UnitCountInput.value = "10"; // Reset R1 count
        r1Section.style.display = 'block'; // Show R1 section
        deployR1Button.disabled = false;

        showMessage(""); // Clear any previous messages
    }

    // --- Event Listener for Round 1 Deployment ---
    deployR1Button.addEventListener('click', async () => {
        const unitType = r1UnitTypeSelect.value;
        const unitCount = parseInt(r1UnitCountInput.value, 10);

        if (isNaN(unitCount) || unitCount < 1 || unitCount > 10) {
            showMessage('R1: Please enter a unit count between 1 and 10.', true);
            return;
        }
        
        showMessage('R1: Deploying units...');
        deployR1Button.disabled = true;

        try {
            const response = await fetch('/submit_round_1', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ unit_type: unitType, unit_count: unitCount }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP error! Status: ${response.status}`);
            }

            // Display R1 Results
            const r1res = data.round_1_results;
            playerR1ArmyDisplay.textContent = `${r1res.player_army.type} x${r1res.player_army.count}`;
            playerR1StrengthDisplay.textContent = r1res.player_army.strength;
            computerR1ArmyDisplay.textContent = `${r1res.ai_army.type} x${r1res.ai_army.count}`;
            computerR1StrengthDisplay.textContent = r1res.ai_army.strength;
            r1WinnerDisplay.textContent = r1res.round_winner;

            // Store R2 data for player and AI
            playerR2TotalPool = data.player_r2_data.total_r2_pool;
            aiR1ArmyDetailsForR2 = data.ai_r1_army_details_for_r2; // Store this
            aiR2DataForR2 = data.ai_r2_data_for_r2;             // Store this

            playerR2PoolDisplay.textContent = playerR2TotalPool;
            r2MaxUnitsLabel.textContent = playerR2TotalPool;
            r2UnitCountInput.max = playerR2TotalPool; // Set max for input validation
            r2UnitCountInput.value = Math.min(10, playerR2TotalPool); // Default R2 count

            r1ResultsSection.style.display = 'block';
            if (playerR2TotalPool >= 0) { // Allow R2 even if pool is 0 (player might choose to send 0 troops)
                 r2Section.style.display = 'block';
                 deployR2Button.disabled = false;
            } else { // Should not happen with current backend logic
                 showMessage('No units available for Round 2. Game Over.', true);
                 // Consider adding a reset button or similar
            }
            r1Section.style.display = 'none'; // Hide R1 deployment
            showMessage('R1 complete. Proceed to Round 2 deployment.');

        } catch (error) {
            console.error('Error in Round 1:', error);
            showMessage(`R1 Error: ${error.message}`, true);
            deployR1Button.disabled = false; // Re-enable on error
        }
    });

    // --- Event Listener for Round 2 Deployment ---
    deployR2Button.addEventListener('click', async () => {
        const unitType = r2UnitTypeSelect.value;
        const unitCount = parseInt(r2UnitCountInput.value, 10);

        if (isNaN(unitCount) || unitCount < 0 || unitCount > playerR2TotalPool) {
            showMessage(`R2: Please enter a unit count between 0 and ${playerR2TotalPool}.`, true);
            return;
        }

        showMessage('R2: Deploying units...');
        deployR2Button.disabled = true;

        try {
            const response = await fetch('/submit_round_2', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    unit_type: unitType,
                    unit_count: unitCount,
                    ai_r1_army_details_for_r2: aiR1ArmyDetailsForR2, // Send AI's R1 details back
                    ai_r2_data_for_r2: aiR2DataForR2                 // Send AI's R2 pool back
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP error! Status: ${response.status}`);
            }

            // Display R2 Results
            const r2res = data.round_2_results;
            playerR2ArmyDisplay.textContent = `${r2res.player_army.type} x${r2res.player_army.count}`;
            playerR2StrengthDisplay.textContent = r2res.player_army.strength;
            computerR2ArmyDisplay.textContent = `${r2res.ai_army.type} x${r2res.ai_army.count}`;
            computerR2StrengthDisplay.textContent = r2res.ai_army.strength;
            r2WinnerDisplay.textContent = r2res.round_winner;
            gameWinnerDisplay.textContent = data.game_winner;

            r2ResultsSection.style.display = 'block';
            r2Section.style.display = 'none'; // Hide R2 deployment
            showMessage('Game Over! Refresh to play again.'); 
            // Consider adding a more explicit reset button that calls resetGameDisplay()

        } catch (error) {
            console.error('Error in Round 2:', error);
            showMessage(`R2 Error: ${error.message}`, true);
            deployR2Button.disabled = false; // Re-enable on error
        }
    });
    
    // Initialize game display
    resetGameDisplay();
});
