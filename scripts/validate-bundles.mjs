#!/usr/bin/env node
/**
 * GuardSpine Evidence Bundle Schema Validator
 *
 * Validates bundles against the v0.2.0 JSON Schema using AJV.
 *
 * Usage:
 *   npm run validate             # Validate all
 *   npm run validate:examples    # Validate examples only
 *   npm run validate:golden      # Validate golden vectors only
 *
 * Exit codes:
 *   0 = All validations passed
 *   1 = Validation failures detected
 */

import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';
import { readFileSync, readdirSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

// Parse arguments
const args = process.argv.slice(2);
const examplesOnly = args.includes('--examples-only');
const goldenOnly = args.includes('--golden-only');
const verbose = args.includes('--verbose') || args.includes('-v');

// ANSI colors
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  cyan: '\x1b[36m',
  dim: '\x1b[2m',
};

function log(msg, color = 'reset') {
  console.log(`${colors[color]}${msg}${colors.reset}`);
}

// Initialize AJV with 2020-12 draft support
const ajv = new Ajv2020({
  allErrors: true,
  strict: false,  // 2020-12 has some features that trigger strict mode
  validateFormats: true,
});
addFormats(ajv);

// Load and compile schema
const schemaPath = join(ROOT, 'schemas', 'evidence-bundle-v0.2.0.schema.json');
if (!existsSync(schemaPath)) {
  log(`ERROR: Schema not found: ${schemaPath}`, 'red');
  process.exit(1);
}

const schema = JSON.parse(readFileSync(schemaPath, 'utf-8'));
const validate = ajv.compile(schema);

// Results tracking
const results = {
  valid: [],
  invalid: [],
  expectedFailures: [],
  unexpectedPasses: [],
  errors: [],
};

/**
 * Validate a single bundle file
 * @param {string} filePath Path to the bundle JSON file
 * @param {boolean} expectValid Whether we expect this to be valid
 * @returns {object} Validation result
 */
function validateBundle(filePath, expectValid = true) {
  const relPath = filePath.replace(ROOT, '').replace(/\\/g, '/');

  try {
    const content = readFileSync(filePath, 'utf-8');
    const bundle = JSON.parse(content);
    const isValid = validate(bundle);

    if (isValid) {
      if (expectValid) {
        results.valid.push(relPath);
        return { path: relPath, valid: true, expected: true };
      } else {
        results.unexpectedPasses.push(relPath);
        return { path: relPath, valid: true, expected: false };
      }
    } else {
      if (expectValid) {
        results.invalid.push({
          path: relPath,
          errors: validate.errors,
        });
        return { path: relPath, valid: false, expected: true, errors: validate.errors };
      } else {
        results.expectedFailures.push(relPath);
        return { path: relPath, valid: false, expected: false };
      }
    }
  } catch (err) {
    results.errors.push({ path: relPath, error: err.message });
    return { path: relPath, error: err.message };
  }
}

// Files that are not bundles (metadata, lookup tables, etc.)
const NON_BUNDLE_FILES = [
  'expected-hashes.json',
  'expected-chain.json',
];

/**
 * Validate all files in a directory
 */
function validateDirectory(dirPath, expectValid = true, label = '') {
  if (!existsSync(dirPath)) {
    log(`  [SKIP] Directory not found: ${dirPath}`, 'yellow');
    return;
  }

  const files = readdirSync(dirPath)
    .filter((f) => f.endsWith('.json'))
    .filter((f) => !NON_BUNDLE_FILES.includes(f));

  if (files.length === 0) {
    log(`  [SKIP] No JSON files in: ${dirPath}`, 'yellow');
    return;
  }

  for (const file of files) {
    const filePath = join(dirPath, file);
    const result = validateBundle(filePath, expectValid);

    if (verbose) {
      if (result.error) {
        log(`  [ERR] ${file}: ${result.error}`, 'red');
      } else if (result.valid && result.expected) {
        log(`  [OK]  ${file}`, 'green');
      } else if (!result.valid && !result.expected) {
        log(`  [OK]  ${file} (expected failure)`, 'green');
      } else if (result.valid && !result.expected) {
        log(`  [FAIL] ${file} (should have failed but passed)`, 'red');
      } else if (!result.valid && result.expected) {
        log(`  [FAIL] ${file}`, 'red');
        if (result.errors) {
          for (const err of result.errors.slice(0, 3)) {
            log(`         ${err.instancePath}: ${err.message}`, 'dim');
          }
        }
      }
    }
  }
}

// Main execution
log('');
log('GuardSpine Evidence Bundle Schema Validator', 'cyan');
log('=' .repeat(50), 'dim');
log('');

if (!examplesOnly) {
  // Validate golden vectors (valid bundles)
  log('Validating golden vectors (valid bundles)...', 'cyan');
  validateDirectory(join(ROOT, 'fixtures', 'golden-vectors'), true, 'golden-valid');
  log('');

  // Validate malformed vectors (should FAIL)
  log('Validating malformed vectors (must fail)...', 'cyan');
  validateDirectory(join(ROOT, 'fixtures', 'golden-vectors', 'malformed'), false, 'golden-malformed');
  log('');
}

if (!goldenOnly) {
  // Validate examples
  log('Validating examples...', 'cyan');
  validateDirectory(join(ROOT, 'examples'), true, 'examples');
  log('');
}

// Summary
log('=' .repeat(50), 'dim');
log('SUMMARY', 'cyan');
log('');

const passCount = results.valid.length + results.expectedFailures.length;
const failCount = results.invalid.length + results.unexpectedPasses.length + results.errors.length;

log(`  Valid bundles:           ${results.valid.length}`, 'green');
log(`  Expected failures:       ${results.expectedFailures.length}`, 'green');
log(`  Unexpected passes:       ${results.unexpectedPasses.length}`, results.unexpectedPasses.length > 0 ? 'red' : 'green');
log(`  Validation failures:     ${results.invalid.length}`, results.invalid.length > 0 ? 'red' : 'green');
log(`  Parse/load errors:       ${results.errors.length}`, results.errors.length > 0 ? 'red' : 'green');
log('');

if (results.invalid.length > 0) {
  log('VALIDATION FAILURES:', 'red');
  for (const item of results.invalid) {
    log(`  ${item.path}`, 'red');
    for (const err of (item.errors || []).slice(0, 3)) {
      log(`    - ${err.instancePath || '/'}: ${err.message}`, 'dim');
    }
  }
  log('');
}

if (results.unexpectedPasses.length > 0) {
  log('UNEXPECTED PASSES (malformed bundles that should have failed):', 'red');
  for (const path of results.unexpectedPasses) {
    log(`  ${path}`, 'red');
  }
  log('');
}

if (results.errors.length > 0) {
  log('ERRORS:', 'red');
  for (const item of results.errors) {
    log(`  ${item.path}: ${item.error}`, 'red');
  }
  log('');
}

if (failCount === 0) {
  log('All validations passed!', 'green');
  process.exit(0);
} else {
  log(`${failCount} validation(s) failed.`, 'red');
  process.exit(1);
}
