import fs from "node:fs";
import assert from "node:assert/strict";
const c = JSON.parse(fs.readFileSync("public/data/catalog.json", "utf8"));
const names = new Set(c.benchmarks.map((b) => b.id));
assert.equal(c.benchmarks.length, 38, "Expected all 38 researched suites");
const exported = JSON.parse(
  fs.readFileSync("public/data/catalog-export.json", "utf8"),
);
assert.equal(
  exported.tasks.length,
  c.tasks.length,
  "Export must include every task",
);
assert.ok(
  exported.tasks.every(
    (t) => typeof t.instructions === "string" && t.instructions.length > 10,
  ),
  "Export must contain standalone instruction text",
);
assert.equal(names.size, c.benchmarks.length, "Benchmark IDs must be unique");
assert.equal(
  new Set(c.tasks.map((t) => t.id)).size,
  c.tasks.length,
  "Task IDs must be unique",
);
for (const b of c.benchmarks) {
  assert.ok(b.id && b.name && b.description, `Incomplete benchmark ${b.id}`);
  assert.match(
    b.website || b.repository || b.paper,
    /^https?:\/\//,
    `Missing benchmark source ${b.id}`,
  );
  assert.ok(b.indexedCount > 0, `Empty suite ${b.id}`);
  assert.equal(
    b.indexedCount,
    c.tasks.filter((t) => t.benchmarkId === b.id).length,
  );
}
for (const t of c.tasks) {
  assert.ok(names.has(t.benchmarkId), `Unknown benchmark for ${t.id}`);
  assert.ok(t.name && t.gpu && t.timeBudget, `Incomplete task ${t.id}`);
  assert.ok(t.sources.length, `Missing provenance for ${t.id}`);
  assert.ok(
    ["source", "summary", "unavailable"].includes(t.instructionType),
    `Invalid instruction type ${t.id}`,
  );
  assert.ok(
    ["public", "private", "proposal"].includes(t.access),
    `Invalid access ${t.id}`,
  );
  const details = JSON.parse(
    fs.readFileSync("public/" + t.instructionPath, "utf8"),
  );
  assert.ok(details.instructions.length > 10, `Empty instructions ${t.id}`);
  assert.ok(
    !details.instructions.startsWith(
      "version https://git-lfs.github.com/spec/v1",
    ),
    `Unresolved source pointer ${t.id}`,
  );
}
console.log(
  `Validated ${c.benchmarks.length} suites, ${c.tasks.length} task records, and ${c.tasks.length} instruction files.`,
);
for (const b of c.benchmarks)
  console.log(
    `${b.name}: ${b.indexedCount} indexed; ${b.sourceInstructionCount} source instructions; reported ${b.taskCountReported ?? "unspecified"}`,
  );
