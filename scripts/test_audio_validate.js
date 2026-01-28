const assert = require('assert');
const fs = require('fs');

function validateAudioIndex(data) {
  const errs = [];
  if (!data || typeof data !== 'object') errs.push('audio.json is not an object');
  if (data && typeof data.latest !== 'string') errs.push('audio.json missing latest');
  if (data && !Array.isArray(data.items)) errs.push('audio.json missing items[]');
  return errs;
}

const ax = JSON.parse(fs.readFileSync('examples/audio.example.json', 'utf8'));
assert.deepStrictEqual(validateAudioIndex(ax), []);
console.log('ok');
