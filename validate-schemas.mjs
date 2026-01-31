import { readFileSync, readdirSync } from 'fs';
import { join } from 'path';

const results = { schemas: [], examples: [], errors: [] };

const schemaDir = 'D:/Projects/guardspine-spec/schemas';
for (const f of readdirSync(schemaDir)) {
  if (!f.endsWith('.json')) continue;
  try {
    const schema = JSON.parse(readFileSync(join(schemaDir, f), 'utf-8'));
    results.schemas.push({ file: f, valid: true, type: schema.type || 'complex', properties: Object.keys(schema.properties || {}).length });
  } catch (e) {
    results.schemas.push({ file: f, valid: false, error: e.message });
    results.errors.push(f);
  }
}

const exDir = 'D:/Projects/guardspine-spec/examples';
for (const f of readdirSync(exDir)) {
  if (!f.endsWith('.json')) continue;
  try {
    const ex = JSON.parse(readFileSync(join(exDir, f), 'utf-8'));
    results.examples.push({ file: f, valid: true, hasItems: Array.isArray(ex.items), itemCount: ex.items?.length || 0 });
  } catch (e) {
    results.examples.push({ file: f, valid: false, error: e.message });
    results.errors.push(f);
  }
}

results.summary = { schemasValid: results.schemas.filter(s => s.valid).length, examplesValid: results.examples.filter(e => e.valid).length, totalErrors: results.errors.length };
console.log(JSON.stringify(results, null, 2));
