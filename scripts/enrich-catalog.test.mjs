import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import { DOMAIN_OPTIONS, classifyDomains, enrichTask, resourceLabel, timeLabel } from './enrich-catalog.mjs';
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const parts = readdirSync(resolve(root, 'data/parts')).filter(f => f.endsWith('.json')).map(f => JSON.parse(readFileSync(resolve(root, 'data/parts', f))));
const tasks = parts.flatMap(p => p.tasks);
const benchmarks = new Map(parts.flatMap(p => p.benchmarks).map(b => [b.id, b]));
const enrich = t => enrichTask(t, benchmarks.get(t.benchmarkId), t.instructions);

test('domains describe the target, not incidental agent/harness language', () => {
  assert.deepEqual(classifyDomains({ benchmarkId: 'algotune', name: 'AES-GCM encryption', category: 'ML systems', tags: ['algorithm','CPU'], objective: 'Encrypt plaintext using AES-GCM.' }), ['Software engineering']);
  assert.deepEqual(classifyDomains({ benchmarkId: 'kernelbench', name: 'Matrix multiplication', category: 'ML systems' }), ['ML systems']);
  assert.deepEqual(classifyDomains({ benchmarkId: 'posttrainbench', name: 'Qwen3 → AIME 2025' }), ['AI research','Language models','Mathematics']);
  assert.ok(classifyDomains({ benchmarkId: 'researchgym', name: 'Improving replay buffers' }).includes('Reinforcement learning'));
  assert.ok(classifyDomains({ benchmarkId: 'mlrc-bench', name: 'Backdoor Trigger Recovery' }).includes('AI safety'));
  assert.ok(classifyDomains({ benchmarkId: 'mls-bench', name: 'LLM Agent Tool-Use Reasoning Strategy' }).includes('Agents'));
});

test('allocation and time labels retain full ranges, negative facts, and scope', () => {
  const allocation = 'Released entries range from 0 GPUs for a data-contract wrapper to 256 H100 GPUs; inspect task-specific allocations and original-research context separately.';
  assert.equal(resourceLabel(allocation), allocation);
  const timing = '4 hours (agent task config); published benchmark protocol: 24 hours';
  assert.equal(timeLabel(timing), timing);
  assert.match(resourceLabel('0 GPUs in released wrapper; original experiment used 256 H100, not furnished.'), /0 GPUs.*256 H100, not furnished/);
  assert.equal(resourceLabel('4 GPUs; accelerator model not specified.'), '4 GPUs; accelerator model not specified.');
});

test('recover complete source objective and callable entry point from wrapped Markdown', () => {
  const t = tasks.find(t => t.id === 'autoresearch-exam--activeprune-al-unlabeled-pool-pruning');
  assert.ok(t, 'published active-pruning task exists');
  const e = enrich(t);
  assert.match(e.brief.task, /allowed to consider\./);
  assert.match(e.brief.submission, /def prune\(/);
  assert.match(e.brief.submission, /available/);
  assert.ok(e.brief.world.some(x => /fixed 128-dimensional/.test(x)));
  assert.ok(e.brief.world.some(x => /CPU only \(0 GPUs/.test(x)));
  assert.ok(e.brief.world.some(x => /4 hours.*24 hours/.test(x))); 
});

test('source code supplies task-specific kernel operation instead of a generic prompt', () => {
  const t = tasks.find(t => t.id === 'kernelbench--level1-100-hingeloss');
  const e = enrich(t);
  assert.match(e.brief.task, /Hinge Loss for binary classification/);
  assert.ok(e.brief.world.some(x => /Reference interfaces:/.test(x) && /forward/.test(x)));
  assert.ok(e.brief.world.some(x => /get_inputs/.test(x)));
  assert.ok(!e.brief.world.some(x => /class Model/.test(x)), 'full implementation stays in original instructions');
  assert.ok(!e.domains.includes('Language models'));
});

test('canary comments and truncated legacy constraints are not promoted to brief prose', () => {
  const e = enrichTask({ id:'test', benchmarkId:'x', name:'Test', constraints:['fixed roles, and a set of', 'The supplied data is read-only.'], objective:'Bad old objective', submission:'Not specified', evaluation:'Not specified' }, {}, '<!-- canary hidden -->\n# Test\n\nImprove the model on the supplied data.\n\n## World\n\nUse the frozen model,\nwhich stays read-only throughout the experiment.');
  assert.equal(e.brief.task, 'Improve the model on the supplied data.');
  assert.deepEqual(e.brief.world.slice(0, 1), ['Use the frozen model, which stays read-only throughout the experiment.']);
  assert.equal(e.brief.submission, 'Not specified in the published source.');
});

test('explicit reviewed overrides win without mutating data and retain provenance', () => {
  const task = { name:'Old name', benchmarkId:'scale-rsi-bench', category:'Applied', gpu:'1 × H100', timeBudget:'8 hours', sources:[] };
  const override = { name:'New name', field:'Agents', task:'Optimize an LLM agent swarm.', world:['Fixed node model.'], submission:'graph.json', grader:['Accuracy and efficiency.'], sourceUrl:'https://example.org/source', sources:[{label:'Source',url:'https://example.org/source'}] };
  const e = enrichTask(task, {}, '', override);
  assert.equal(e.name, override.name);
  assert.equal(e.field, 'Agents');
  assert.deepEqual(e.brief, { task:override.task, world:override.world, submission:override.submission, grader:override.grader });
  assert.deepEqual(e.sources, override.sources);
  assert.equal(task.name, 'Old name');
  assert.ok(e.domains.includes('Agents'));
});

test('every current record produces a complete schema with controlled domains and unchanged resource facts', () => {
  for (const t of tasks) {
    const e = enrich(t);
    assert.ok(e.field && e.brief.task && e.brief.submission, t.id);
    assert.ok(e.brief.world.length && e.brief.grader.length, t.id);
    assert.ok(e.domains.every(d => DOMAIN_OPTIONS.includes(d)), t.id);
    assert.ok(!e.brief.task.includes('<!--'), t.id);
    // Label cleanup may remove NVIDIA but cannot lose counts or numeric bounds.
    for (const num of (t.gpu || '').match(/\d+(?:\.\d+)?/g) || []) assert.ok(e.resourceLabel.includes(num), `${t.id}: GPU number ${num}`);
    for (const num of (t.timeBudget || '').match(/\d+(?:\.\d+)?/g) || []) assert.ok(e.timeLabel.includes(num), `${t.id}: time number ${num}`);
  }
});
