document.addEventListener('DOMContentLoaded', () => {
    // --- Map Grid Elements ---
    const mapGridTable = document.getElementById('map-grid');

    // --- Round 1 UI Elements ---
    const r1Section = document.getElementById('round-1-section'); // Main section
    const r1BatchUnitTypeSelect = document.getElementById('r1-batch-unit-type');
    const r1BatchUnitCountInput = document.getElementById('r1-batch-unit-count');
    const r1BatchXInput = document.getElementById('r1-batch-x');
    const r1BatchYInput = document.getElementById('r1-batch-y');
    const r1AddBatchButton = document.getElementById('r1-add-batch-button');
    const r1TotalDeployedCountSpan = document.getElementById('r1-total-deployed-count');
    const r1DeploymentListUl = document.getElementById('r1-deployment-list');
    const r1FinalizeButton = document.getElementById('r1-finalize-deployments-button');

    // --- Round 1 Results UI Elements ---
    const r1ResultsSection = document.getElementById('round-1-results-section');
    const playerR1ArmyDisplay = document.getElementById('player-r1-army-display');
    const playerR1StrengthDisplay = document.getElementById('player-r1-strength-display');
    const computerR1ArmyDisplay = document.getElementById('computer-r1-army-display');
    const computerR1StrengthDisplay = document.getElementById('computer-r1-strength-display');
    const r1WinnerDisplay = document.getElementById('r1-winner-display');
    const playerR2PoolDisplay = document.getElementById('player-r2-pool-display');

    // --- Round 2 UI Elements ---
    const r2Section = document.getElementById('round-2-section'); // Main section
    const r2BatchUnitTypeSelect = document.getElementById('r2-batch-unit-type');
    const r2BatchUnitCountInput = document.getElementById('r2-batch-unit-count');
    const r2BatchXInput = document.getElementById('r2-batch-x');
    const r2BatchYInput = document.getElementById('r2-batch-y');
    const r2AddBatchButton = document.getElementById('r2-add-batch-button');
    const r2TotalDeployedCountSpan = document.getElementById('r2-total-deployed-count');
    const r2DeploymentListUl = document.getElementById('r2-deployment-list');
    const r2FinalizeButton = document.getElementById('r2-finalize-deployments-button');
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
    let currentRound = 1;
    let r1Deployments = [];
    let r1CurrentTotalUnits = 0;
    const R1_MAX_UNITS = 10;

    let r2Deployments = [];
    let r2CurrentTotalUnits = 0;
    let R2_MAX_UNITS = 0; // Will be set after R1

    // Variables to store data from R1 response for R2 request
    let aiR1ArmyDetailsForR2 = null;
    let aiR2DataForR2 = null;
    let playerR1DeploymentsForR2 = null; // Player's R1 deployments also need to be sent for map reconstruction

    // --- Utility Functions ---
    function showMessage(message, isError = false) {
        generalMessageDisplay.textContent = message;
        generalMessageDisplay.style.color = isError ? 'red' : 'black';
    }

    function createMapGrid() {
        mapGridTable.innerHTML = ''; // Clear existing grid
        for (let y = 0; y < 5; y++) {
            const row = mapGridTable.insertRow();
            for (let x = 0; x < 5; x++) {
                const cell = row.insertCell();
                cell.id = `cell-${y}-${x}`; // Corrected ID format
                cell.textContent = '-'; // Placeholder for empty
            }
        }
    }

    function renderMap(mapState) { // mapState is the 2D list from backend
        if (!mapState) return;
        for (let y = 0; y < 5; y++) {
            for (let x = 0; x < 5; x++) {
                const cellId = `cell-${y}-${x}`; // Corrected ID format
                const cell = document.getElementById(cellId);
                if (cell) {
                    const cellData = mapState[y][x];
                    if (cellData) {
                        cell.textContent = `${cellData.owner === 'P1' ? 'P' : 'AI'}:${cellData.unit_type.substring(0,3)}:${cellData.count}`;
                    } else {
                        cell.textContent = '-';
                    }
                }
            }
        }
    }

    function addDeploymentToList(round, type, count, x, y, listElement, totalCountSpan, currentTotal, maxUnits) {
        if (currentTotal + count > maxUnits) {
            showMessage(`Cannot add batch. Exceeds max units for Round ${round} (${currentTotal + count}/${maxUnits}).`, true);
            return false;
        }
        const listItem = document.createElement('li');
        listItem.textContent = `${count}x ${type} at (${x},${y})`;
        listElement.appendChild(listItem);
        
        if (round === 1) {
            r1Deployments.push({ unit_type: type, unit_count: count, x: parseInt(x), y: parseInt(y) });
            r1CurrentTotalUnits += count;
            totalCountSpan.textContent = r1CurrentTotalUnits;
        } else {
            r2Deployments.push({ unit_type: type, unit_count: count, x: parseInt(x), y: parseInt(y) });
            r2CurrentTotalUnits += count;
            totalCountSpan.textContent = r2CurrentTotalUnits;
        }
        return true;
    }
    
    function resetDeploymentInputs(typeSelect, countInput, xInput, yInput) {
        typeSelect.value = 'infantry'; // Default
        countInput.value = "1";
        xInput.value = "";
        yInput.value = "";
    }

    // --- Event Listeners ---
    r1AddBatchButton.addEventListener('click', () => {
        const type = r1BatchUnitTypeSelect.value;
        const count = parseInt(r1BatchUnitCountInput.value);
        const x = r1BatchXInput.value;
        const y = r1BatchYInput.value;

        if (isNaN(count) || count <= 0) { showMessage("R1 Batch: Count must be positive.", true); return; }
        if (x === "" || y === "") { showMessage("R1 Batch: X and Y coordinates are required.", true); return; }
        if (parseInt(x) < 0 || parseInt(x) > 4 || parseInt(y) < 0 || parseInt(y) > 4) { showMessage("R1 Batch: Coordinates must be 0-4.", true); return; }

        if (addDeploymentToList(1, type, count, x, y, r1DeploymentListUl, r1TotalDeployedCountSpan, r1CurrentTotalUnits, R1_MAX_UNITS)) {
            resetDeploymentInputs(r1BatchUnitTypeSelect, r1BatchUnitCountInput, r1BatchXInput, r1BatchYInput);
            showMessage("R1 Batch added. Add more or finalize.", false);
        }
    });

    r1FinalizeButton.addEventListener('click', async () => {
        if (r1Deployments.length === 0) {
            showMessage("R1: No units deployed. Please add at least one batch.", true);
            return;
        }
        if (r1CurrentTotalUnits !== R1_MAX_UNITS) {
            showMessage(`R1: Must deploy exactly ${R1_MAX_UNITS} units. Currently ${r1CurrentTotalUnits}.`, true);
            return;
        }

        showMessage('R1: Finalizing deployments...');
        r1FinalizeButton.disabled = true;
        r1AddBatchButton.disabled = true;

        try {
            const response = await fetch('/submit_round_1', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ player_deployments: r1Deployments }), // Sending the list of deployments
            });
            const data = await response.json();

            // --- Start of new defensive checks ---
            if (!data) {
                console.error("R1 Finalize Error: Received no data from server.", response);
                showMessage("R1 Error: No data received from server.", true);
                r1FinalizeButton.disabled = false;
                r1AddBatchButton.disabled = false;
                return;
            }

            console.log("R1 Finalize Data Received:", JSON.stringify(data, null, 2)); // Log the whole data object

            if (!data.round_1_results || 
                !data.round_1_results.player_army || 
                typeof data.round_1_results.player_army.count === 'undefined' ||
                !data.round_1_results.ai_army || 
                typeof data.round_1_results.ai_army.count === 'undefined' ||
                !data.player_r2_data || 
                typeof data.player_r2_data.total_r2_pool === 'undefined' ||
                !data.ai_r1_army_details_for_r2 ||
                !data.ai_r2_data_for_r2 ||
                !data.current_map_state || // Also check for map state as it's crucial
                !data.player_r1_deployments ||
                !data.ai_r1_deployments) {
                
                console.error("R1 Finalize Error: Malformed data received from server. One or more expected fields are missing.", data);
                showMessage("R1 Error: Server response was incomplete or malformed. Cannot proceed.", true);
                
                // Log which specific parts are problematic
                if (!data.round_1_results) console.error("Missing: data.round_1_results");
                else {
                    if (!data.round_1_results.player_army) console.error("Missing: data.round_1_results.player_army");
                    else if (typeof data.round_1_results.player_army.count === 'undefined') console.error("Missing: data.round_1_results.player_army.count");
                    if (!data.round_1_results.ai_army) console.error("Missing: data.round_1_results.ai_army");
                    else if (typeof data.round_1_results.ai_army.count === 'undefined') console.error("Missing: data.round_1_results.ai_army.count");
                }
                if (!data.player_r2_data) console.error("Missing: data.player_r2_data");
                else if (typeof data.player_r2_data.total_r2_pool === 'undefined') console.error("Missing: data.player_r2_data.total_r2_pool");
                if (!data.ai_r1_army_details_for_r2) console.error("Missing: data.ai_r1_army_details_for_r2");
                if (!data.ai_r2_data_for_r2) console.error("Missing: data.ai_r2_data_for_r2");
                if (!data.current_map_state) console.error("Missing: data.current_map_state");
                if (!data.player_r1_deployments) console.error("Missing: data.player_r1_deployments");
                if (!data.ai_r1_deployments) console.error("Missing: data.ai_r1_deployments");

                r1FinalizeButton.disabled = false;
                r1AddBatchButton.disabled = false;
                return;
            }
            // --- End of new defensive checks ---

            if (!response.ok) { throw new Error(data.error || `HTTP error! Status: ${response.status}`); }

            const r1res = data.round_1_results;
            playerR1ArmyDisplay.textContent = `Total ${r1res.player_army.count} units`; // Simplified display
            playerR1StrengthDisplay.textContent = r1res.player_army.strength;
            computerR1ArmyDisplay.textContent = `Total ${r1res.ai_army.count} units`; // Simplified display
            computerR1StrengthDisplay.textContent = r1res.ai_army.strength;
            r1WinnerDisplay.textContent = r1res.round_winner;
            renderMap(data.current_map_state); // Render R1 map

            R2_MAX_UNITS = data.player_r2_data.total_r2_pool;
            aiR1ArmyDetailsForR2 = data.ai_r1_army_details_for_r2; // Store for R2
            aiR2DataForR2 = data.ai_r2_data_for_r2;                 // Store for R2
            playerR1DeploymentsForR2 = r1Deployments; // Store player's R1 deployments

            playerR2PoolDisplay.textContent = R2_MAX_UNITS;
            r2MaxUnitsLabel.textContent = R2_MAX_UNITS;
            
            // Ensure r2UnitCountInput is correctly defined and accessed
            if (r2UnitCountInput) { // Check if the element was found
                r2UnitCountInput.max = R2_MAX_UNITS; 
                r2UnitCountInput.value = Math.min(10, R2_MAX_UNITS); // Default R2 count
            } else {
                console.error("Error: r2-unit-count element not found in HTML!");
                showMessage("Critical UI Error: R2 count input missing.", true);
            }

            r1ResultsSection.style.display = 'block';
            // Check R2_MAX_UNITS before displaying R2 section and enabling buttons
            if (R2_MAX_UNITS >= 0) { // Player might have 0 units but can still proceed to R2 (to deploy 0)
                 r2Section.style.display = 'block';
                 if(r2FinalizeButton) r2FinalizeButton.disabled = false; 
                 if(r2AddBatchButton) r2AddBatchButton.disabled = false;
            } else { 
                 // This case should ideally not be reached if backend logic is correct (pool shouldn't be negative)
                 showMessage('Error in R2 pool calculation or no units available. Game Over.', true);
            }
            
            r1Section.style.display = 'none';
            showMessage('R1 complete. Proceed to Round 2 deployment.');

        } catch (error) {
            console.error('Error in Round 1 Finalize:', error);
            showMessage(`R1 Finalize Error: ${error.message}`, true);
            r1FinalizeButton.disabled = false;
            r1AddBatchButton.disabled = false;
        }
    });
    
    // Placeholder for r2AddBatchButton (similar to r1)
    r2AddBatchButton.addEventListener('click', () => {
        const type = r2BatchUnitTypeSelect.value;
        const count = parseInt(r2BatchUnitCountInput.value);
        const x = r2BatchXInput.value;
        const y = r2BatchYInput.value;

        if (isNaN(count) || count < 0 ) { showMessage("R2 Batch: Count must be non-negative.", true); return; }
         if (count === 0 && R2_MAX_UNITS > 0) { /* Allow deploying 0 if desired */ }
         else if (count <= 0 && R2_MAX_UNITS == 0) { /* Also allow if pool is 0 */ }
         else if (count <=0) { showMessage("R2 Batch: Count must be positive if deploying units.", true); return; }


        if (x === "" || y === "") { showMessage("R2 Batch: X and Y coordinates are required.", true); return; }
        if (parseInt(x) < 0 || parseInt(x) > 4 || parseInt(y) < 0 || parseInt(y) > 4) { showMessage("R2 Batch: Coordinates must be 0-4.", true); return; }
        
        // Note: r2CurrentTotalUnits and R2_MAX_UNITS are used here
        if (addDeploymentToList(2, type, count, x, y, r2DeploymentListUl, r2TotalDeployedCountSpan, r2CurrentTotalUnits, R2_MAX_UNITS)) {
            resetDeploymentInputs(r2BatchUnitTypeSelect, r2BatchUnitCountInput, r2BatchXInput, r2BatchYInput);
            showMessage("R2 Batch added. Add more or finalize.", false);
        }
    });

    // Placeholder for r2FinalizeButton (similar to r1 but calls /submit_round_2)
    r2FinalizeButton.addEventListener('click', async () => {
        // Validation: ensure r2CurrentTotalUnits matches R2_MAX_UNITS
        if (r2CurrentTotalUnits !== R2_MAX_UNITS) {
             showMessage(`R2: Must deploy exactly ${R2_MAX_UNITS} units. Currently ${r2CurrentTotalUnits}.`, true);
             return;
        }
        // Allow finalizing with 0 units if R2_MAX_UNITS is 0.
        if (R2_MAX_UNITS === 0 && r2Deployments.length > 0) { // Should not happen if count validation is good
            showMessage(`R2: Cannot deploy units if R2 pool is 0.`, true);
            return;
        }
        if (R2_MAX_UNITS > 0 && r2Deployments.length === 0 && r2CurrentTotalUnits === 0) {
            // If pool > 0, but player deploys nothing (explicitly 0 units for all batches)
            // This is allowed. Backend expects player_deployments_r2 to be potentially empty list if count is 0.
        }


        showMessage('R2: Finalizing deployments...');
        r2FinalizeButton.disabled = true;
        r2AddBatchButton.disabled = true;

        try {
            const response = await fetch('/submit_round_2', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    player_deployments_r2: r2Deployments,
                    ai_r1_army_details_for_r2: aiR1ArmyDetailsForR2,
                    ai_r2_data_for_r2: aiR2DataForR2,
                    player_r1_deployments: playerR1DeploymentsForR2 // Send player's R1 deployments
                }),
            });
            const data = await response.json();

            if (!response.ok) { throw new Error(data.error || `HTTP error! Status: ${response.status}`); }

            const r2res = data.round_2_results;
            playerR2ArmyDisplay.textContent = `Total ${r2res.player_army.count} units`;
            playerR2StrengthDisplay.textContent = r2res.player_army.strength;
            computerR2ArmyDisplay.textContent = `Total ${r2res.ai_army.count} units`;
            computerR2StrengthDisplay.textContent = r2res.ai_army.strength;
            r2WinnerDisplay.textContent = r2res.round_winner;
            gameWinnerDisplay.textContent = data.game_winner;
            
            renderMap(data.final_map_state); // Render final map

            r2ResultsSection.style.display = 'block';
            r2Section.style.display = 'none';
            showMessage('Game Over! Refresh to play again.');

        } catch (error) {
            console.error('Error in Round 2 Finalize:', error);
            showMessage(`R2 Finalize Error: ${error.message}`, true);
            r2FinalizeButton.disabled = false;
            r2AddBatchButton.disabled = false;
        }
    });
    
    // --- Initial Game Setup ---
    function initializeGame() {
        createMapGrid();
        currentRound = 1;
        r1Deployments = [];
        r1CurrentTotalUnits = 0;
        r1TotalDeployedCountSpan.textContent = "0";
        r1DeploymentListUl.innerHTML = '';
        
        r2Deployments = [];
        r2CurrentTotalUnits = 0;
        R2_MAX_UNITS = 0; // Reset
        if(r2TotalDeployedCountSpan) r2TotalDeployedCountSpan.textContent = "0";
        if(r2DeploymentListUl) r2DeploymentListUl.innerHTML = '';


        r1Section.style.display = 'block';
        r1ResultsSection.style.display = 'none';
        r2Section.style.display = 'none';
        r2ResultsSection.style.display = 'none';
        
        r1AddBatchButton.disabled = false;
        r1FinalizeButton.disabled = false;
        // Ensure R2 buttons are initially disabled
        r2AddBatchButton.disabled = true;
        r2FinalizeButton.disabled = true;

        showMessage("Round 1: Deploy your units.");
        resetDeploymentInputs(r1BatchUnitTypeSelect, r1BatchUnitCountInput, r1BatchXInput, r1BatchYInput);
        if (r2BatchUnitTypeSelect && r2BatchUnitCountInput && r2BatchXInput && r2BatchYInput) {
             resetDeploymentInputs(r2BatchUnitTypeSelect, r2BatchUnitCountInput, r2BatchXInput, r2BatchYInput);
        }
    }

    initializeGame(); // Start the game
});
