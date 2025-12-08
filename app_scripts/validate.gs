/**
 * Bowl Pool Picks Validator - Inline Validation
 * 
 * This script provides a custom function for inline validation (no authorization required).
 * Automatically recalculates when any cell in the Picks sheet is edited.
 * 
 * SETUP:
 * 1. In cell Z1, enter any number (e.g., 1). This is the trigger cell that will be
 *    automatically updated by the onEdit trigger.
 * 2. Add a new column (e.g., column P) with header "Validation Status"
 * 3. In row 7 (first data row), enter: =VALIDATE_BETTOR_PICKS($G7, $Z$1)
 *    (assuming column G contains bettor names)
 * 4. Copy this formula down for all bettors
 * 5. Add conditional formatting: if cell contains "ERROR:", make it red
 * 
 * NOTE: The onEdit trigger automatically updates Z1 whenever any cell is edited,
 * which forces all validation functions to recalculate because they reference Z1.
 */

/**
 * Validates a single bettor's picks and returns status.
 * Returns "✓ Valid" if valid, or "ERROR: [message]" if invalid.
 * 
 * @param {string} bettorName - The name of the bettor to validate
 * @param {number} refreshTrigger - Reference to trigger cell (Z1) to force recalculation
 * @return {string} Validation status message
 * @customfunction
 */
function VALIDATE_BETTOR_PICKS(bettorName, refreshTrigger) {
  if (!bettorName || bettorName === '') {
    return '';
  }
  
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var picksSheet = ss.getSheetByName('Picks');
    
    if (!picksSheet) {
      return 'ERROR: Picks sheet not found';
    }
    
    // The refreshTrigger parameter creates a dependency on Z1, so when Z1 changes,
    // this function will automatically recalculate
    
    var picksData = picksSheet.getDataRange().getValues();
    
    if (picksData.length < 7) {
      return 'ERROR: No data found';
    }
    
    var errors = validateBettor(picksData, bettorName);
    
    if (errors.length === 0) {
      return '✓ Valid';
    } else {
      return 'ERROR: ' + errors[0]; // Show first error
    }
  } catch (e) {
    return 'ERROR: ' + e.toString();
  }
}

/**
 * Simple onEdit trigger - updates a trigger cell to force recalculation of validation functions.
 * This runs automatically without requiring authorization.
 * Triggers on ANY edit to the Picks sheet (after row 7) to ensure validation always updates.
 */
function onEdit(e) {
  try {
    // Only run on the Picks sheet
    var sheet = e.source.getActiveSheet();
    if (sheet.getName() !== 'Picks') {
      return;
    }
    
    var range = e.range;
    var row = range.getRow();
    
    // Skip instruction rows (rows 1-6) and header row (row 7)
    // But allow edits to trigger cell (Z1) itself to avoid infinite loop
    if (row <= 7 && range.getA1Notation() !== 'Z1') {
      return;
    }
    
    // Skip if we're editing the trigger cell itself to avoid infinite loop
    if (range.getA1Notation() === 'Z1') {
      return;
    }
    
    // Update trigger cell (Z1) with current timestamp to force recalculation
    // This creates a dependency that causes all validation functions to recalculate
    var triggerCell = sheet.getRange('Z1');
    var currentValue = triggerCell.getValue();
    var newValue = new Date().getTime();
    
    // Only update if value actually changed (to minimize unnecessary recalculations)
    if (currentValue !== newValue) {
      triggerCell.setValue(newValue);
    }
  } catch (e) {
    // Silently fail - don't interrupt user's editing
    // Simple triggers have limitations and may fail in some edge cases
  }
}

/**
 * Validates a single bettor's picks.
 * Checks:
 * - Exactly 10 picks
 * - Uses numbers 1-10, each exactly once
 * - Only one winner per bowl
 * 
 * @param {Array} data - All picks data from the sheet
 * @param {string} bettorName - The name of the bettor to validate
 * @return {Array} Array of error messages (empty if valid)
 */
function validateBettor(data, bettorName) {
  var errors = [];
  var picks = [];
  var bowlsWithPicks = {}; // Track which bowls have picks and which teams
  var pointsUsed = {}; // Track which point values are used and on which bowls
  
  // Skip first 5 instruction rows and header row (start at index 6)
  for (var i = 6; i < data.length; i++) {
    var row = data[i];
    var bowl = row[0];
    var team = row[2];
    var bettor = row[6];
    var pointsWagered = parsePoints(row[7]);
    
    // Skip divider rows
    if (!bowl || bowl === 'Non-playoff games' || bowl === 'Play-in games' || 
        bowl === 'Quarterfinals' || bowl === 'Semis' || bowl === 'National Championship') {
      continue;
    }
    
    // Only process rows for this bettor
    if (bettor !== bettorName) {
      continue;
    }
    
    if (pointsWagered > 0) {
      // Check required fields are not empty when points are wagered
      if (!bowl || bowl === '') {
        errors.push('Row ' + (i + 1) + ': You have entered points but the bowl name is missing. Please enter a bowl name.');
        continue;
      }
      if (!team || team === '') {
        errors.push('Row ' + (i + 1) + ': You have entered points for ' + bowl + ' but the team name is missing. Please enter a team name.');
        continue;
      }
      
      picks.push({
        bowl: bowl,
        team: team,
        points: pointsWagered,
        row: i + 1
      });
      
      // Track bowls with picks
      if (!bowlsWithPicks[bowl]) {
        bowlsWithPicks[bowl] = [];
      }
      bowlsWithPicks[bowl].push({team: team, points: pointsWagered, row: i + 1});
      
      // Track point values used
      if (!pointsUsed[pointsWagered]) {
        pointsUsed[pointsWagered] = [];
      }
      pointsUsed[pointsWagered].push({bowl: bowl, team: team, row: i + 1});
      
      // Check point value is 1-10
      if (pointsWagered < 1 || pointsWagered > 10) {
        errors.push('Point values must be between 1 and 10. You entered ' + pointsWagered + ' on row ' + (i + 1) + ' for ' + bowl + '. Please change it to a number between 1 and 10.');
      }
    }
  }
  
  // Check for multiple picks in the same bowl
  for (var bowl in bowlsWithPicks) {
    if (bowlsWithPicks[bowl].length > 1) {
      var teams = [];
      for (var k = 0; k < bowlsWithPicks[bowl].length; k++) {
        teams.push(bowlsWithPicks[bowl][k].team);
      }
      errors.push('You picked multiple winners for the ' + bowl + ' bowl (' + teams.join(' and ') + '). You can only pick one winner per bowl! Please remove all but one pick for this bowl.');
    }
  }
  
  // Check for duplicate point values
  // First, determine which point values are missing (for helpful error messages)
  var missingPoints = [];
  for (var j = 1; j <= 10; j++) {
    if (!pointsUsed[j] || pointsUsed[j].length === 0) {
      missingPoints.push(j);
    }
  }
  
  for (var pointValue in pointsUsed) {
    var pointNum = parseInt(pointValue);
    if (pointNum >= 1 && pointNum <= 10 && pointsUsed[pointValue].length > 1) {
      var bowls = [];
      for (var k = 0; k < pointsUsed[pointValue].length; k++) {
        bowls.push(pointsUsed[pointValue][k].bowl);
      }
      var message = 'You have put ' + pointValue + ' points on multiple games (' + bowls.join(', ') + '). You can only put ' + pointValue + ' points on one game!';
      if (missingPoints.length > 0) {
        message += ' You have not used these point values yet: ' + missingPoints.join(', ') + '. Please change one of the ' + pointValue + ' point picks to one of these unused values.';
      } else {
        message += ' Please change one of them to a different point value.';
      }
      errors.push(message);
    }
  }
  
  // Check exactly 10 games picked
  var numPicks = picks.length;
  
  if (numPicks !== 10) {
    if (numPicks < 10) {
      var pickWord = numPicks === 1 ? 'pick' : 'picks';
      var message = 'You need to pick exactly 10 games. You currently have ' + numPicks + ' ' + pickWord + '. Please add ' + (10 - numPicks) + ' more game(s).';
      if (missingPoints.length > 0) {
        message += ' You have not used these point values yet: ' + missingPoints.join(', ') + '. Please assign these point values to your new picks.';
      }
      errors.push(message);
    } else {
      var pickWord = numPicks === 1 ? 'pick' : 'picks';
      errors.push('You need to pick exactly 10 games. You currently have ' + numPicks + ' ' + pickWord + '. Please remove ' + (numPicks - 10) + ' pick(s).');
    }
  }
  
  // Check all numbers 1-10 are used (only if we have exactly 10 picks)
  if (numPicks === 10) {
    if (missingPoints.length > 0) {
      errors.push('You need to use all point values from 1-10, each exactly once. You are missing: ' + missingPoints.join(', ') + '. Please assign these point values to your picks.');
    }
  }
  
  return errors;
}

/**
 * Parses a points value from a cell, handling empty/null values.
 * 
 * @param {*} value - The cell value to parse
 * @return {number} The parsed points value (0 if invalid/empty)
 */
function parsePoints(value) {
  if (value === '' || value === null || value === undefined) {
    return 0;
  }
  var num = parseInt(value);
  return isNaN(num) ? 0 : num;
}

