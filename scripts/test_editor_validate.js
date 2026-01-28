const assert = require('assert');
const fs = require('fs');

function validateEditor(data) {
  const errs = [];
  if (!data || typeof data !== 'object') errs.push('editor.json is not an object');
  if (data && typeof data.editors_brief !== 'string') errs.push('editor.json missing editors_brief');
  if (data && !Array.isArray(data.top_themes)) errs.push('editor.json missing top_themes[]');
  if (data && (!data.most_memeable || typeof data.most_memeable !== 'object')) errs.push('editor.json missing most_memeable');
  return errs;
}

const ed = JSON.parse(fs.readFileSync('examples/editor.example.json', 'utf8'));
assert.deepStrictEqual(validateEditor(ed), []);
console.log('ok');
