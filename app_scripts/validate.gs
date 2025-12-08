/**
 * Bowl Pool Picks Validator
 * 
 * Validates that each bettor:
 * 1. Only picks one winner per game (only one team per bowl has points wagered)
 * 2. Makes exactly 10 picks (exactly 10 rows with points wagered > 0)
 * 3. Uses numbers 1-10, each number exactly once (points wagered values are 1-10 with no duplicates)
 */

function showMessage(message) {
  // Calculate height based on message length (roughly 20px per line, min 160, max 600)
  var lines = message.split('\n').length;
  var height = Math.min(Math.max(160, lines * 20 + 80), 600);
  
  var html = HtmlService
    .createHtmlOutput(
      '<div style="font-family:Arial; font-size:14px; padding:8px; max-height:500px; overflow-y:auto;">'
      + message.replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br>') +
      '</div><div style="text-align:right; padding:8px;"><button onclick="google.script.host.close()">OK</button></div>'
    )
    .setWidth(500)
    .setHeight(height);
  SpreadsheetApp.getUi().showModalDialog(html, 'Validation Results');
}

function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('Validate')
    .addItem('Validate Picks', 'validateAllPicks')
    .addToUi();
}

function validateAllPicks() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var picksSheet = ss.getSheetByName('Picks');
  
  if (!picksSheet) {
    showMessage('Validation Failed\n\nMissing required tab: "Picks"');
    return;
  }
  
  var picksData = picksSheet.getDataRange().getValues();
  
  if (picksData.length < 2) {
    showMessage('Validation Failed\n\nPicks tab: No data found');
    return;
  }
  
  // Validate picks (bettor-level)
  var validationResults = validatePicks(picksData);
  var picksErrors = validationResults.errors;
  var validBettors = validationResults.validBettors;
  
  // Sort valid bettors alphabetically
  validBettors.sort();
  
  // Sort errors by bettor name (extract bettor name from error string)
  picksErrors.sort(function(a, b) {
    var bettorA = a.split(':')[0];
    var bettorB = b.split(':')[0];
    return bettorA.localeCompare(bettorB);
  });
  
  var message = '';
  
  // Show valid submissions first
  if (validBettors.length > 0) {
    message += '✓ Valid submissions:\n';
    for (var i = 0; i < validBettors.length; i++) {
      message += '  • ' + validBettors[i] + '\n';
    }
    message += '\n';
  }
  
  // Then show errors
  if (picksErrors.length === 0) {
    if (validBettors.length > 0) {
      message += 'All submissions are valid!';
    } else {
      message = '✓ All submissions are valid!';
    }
    showMessage(message);
  } else {
    message += 'VALIDATION ERRORS FOUND:\n\n';
    message += 'Please fix the following issues:\n\n';
    for (var j = 0; j < picksErrors.length; j++) {
      message += (j + 1) + '. ' + picksErrors[j] + '\n\n';
    }
    
    showMessage(message);
  }
}

function validatePicks(picksData) {
  var errors = [];
  var validBettors = [];
  var bettors = getUniqueBettors(picksData);
  
  for (var i = 0; i < bettors.length; i++) {
    var bettorErrors = validateBettor(picksData, bettors[i]);
    if (bettorErrors.length === 0) {
      validBettors.push(bettors[i]);
    } else {
      for (var j = 0; j < bettorErrors.length; j++) {
        errors.push(bettors[i] + ': ' + bettorErrors[j]);
      }
    }
  }
  
  return {
    errors: errors,
    validBettors: validBettors
  };
}

function validateBettor(data, bettorName) {
  var errors = [];
  var picks = [];
  var bowlsWithPicks = {}; // Track which bowls have picks and which teams
  var pointsUsed = {}; // Track which point values are used and on which bowls
  
  // Skip header row (index 0)
  for (var i = 1; i < data.length; i++) {
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
      var message = 'You need to pick exactly 10 games. You currently have ' + numPicks + ' picks. Please add ' + (10 - numPicks) + ' more game(s).';
      if (missingPoints.length > 0) {
        message += ' You have not used these point values yet: ' + missingPoints.join(', ') + '. Please assign these point values to your new picks.';
      }
      errors.push(message);
    } else {
      errors.push('You need to pick exactly 10 games. You currently have ' + numPicks + ' picks. Please remove ' + (numPicks - 10) + ' pick(s).');
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

function parsePoints(value) {
  if (value === '' || value === null || value === undefined) {
    return 0;
  }
  var num = parseInt(value);
  return isNaN(num) ? 0 : num;
}

function getUniqueBettors(data) {
  var bettors = [];
  var seen = {};
  
  // Skip header row
  for (var i = 1; i < data.length; i++) {
    var bettor = data[i][6];
    if (bettor && bettor !== 'Bettor' && !seen[bettor]) {
      // Skip divider rows
      var bowl = data[i][0];
      if (bowl && bowl !== 'Non-playoff games' && bowl !== 'Play-in games' && 
          bowl !== 'Quarterfinals' && bowl !== 'Semis' && bowl !== 'National Championship') {
        bettors.push(bettor);
        seen[bettor] = true;
      }
    }
  }
  
  return bettors;
}
