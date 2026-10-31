import { strict as assert } from 'node:assert';
import { test } from 'node:test';
import { classifyRisk } from '../src/lib/risk-level.ts';

test('KSS 0 is low risk', () => {
  assert.equal(classifyRisk(0, 0), 'LOW');
});

test('KSS 5 is moderate risk', () => {
  assert.equal(classifyRisk(50, 5), 'MODERATE');
});

test('KSS 10 is critical risk', () => {
  assert.equal(classifyRisk(100, 10), 'CRITICAL');
});
