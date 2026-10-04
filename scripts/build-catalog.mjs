import fs from "node:fs";
import path from "node:path";
import { enrichTask } from "./enrich-catalog.mjs";
const root = process.cwd();
const overrideFile = path.join(root, "data/editorial-overrides.json");
const editorial = fs.existsSync(overrideFile)
  ? JSON.parse(fs.readFileSync(overrideFile, "utf8"))
  : {};
const partsDir = path.join(root, "data/parts");
const files = fs.existsSync(partsDir)
  ? fs
      .readdirSync(partsDir)
      .filter((f) => f.endsWith(".json"))
      .sort()
  : [];
const readingOrder = [
  "scale-rsi-bench",
  "rsi-exam",
  "openrsi-index",
  "posttrainbench",
  "autoresearch-bench",
  "autoresearch-exam",
  "re-bench",
  "mls-bench",
  "airs-bench",
  "ai4ai-bench",
  "innovatorbench",
  "curatebench",
  "frontierswe-v2",
  "rsibench-data",
  "researchgym",
];
const benchmarks = [],
  tasks = [],
  ids = new Set(),
  taskIds = new Set();
const clean = (v, fallback = "Not specified in the published source") =>
  typeof v === "string" && v.trim()
    ? v.trim()
    : Array.isArray(v)
      ? v.join("; ")
      : fallback;
const sources = (items, url) => {
  const all = Array.isArray(items) ? items : [];
  if (url && !all.some((s) => s.url === url))
    all.push({ label: "Task source", url });
  return all
    .filter((s) => s && /^https?:\/\//.test(s.url))
    .map((s) => ({ label: s.label || "Source", url: s.url }));
};
const dir = path.join(root, "public/data");
fs.rmSync(path.join(dir, "instructions"), { recursive: true, force: true });
fs.mkdirSync(path.join(dir, "instructions"), { recursive: true });
const instructionBodies = new Map();
for (const file of files) {
  const part = JSON.parse(fs.readFileSync(path.join(partsDir, file), "utf8"));
  for (const b of part.benchmarks || []) {
    if (ids.has(b.id)) throw new Error(`Duplicate benchmark ${b.id}`);
    ids.add(b.id);
    benchmarks.push({
      ...b,
      description: clean(b.description, ""),
      overview: clean(b.overview, b.description || ""),
      gpu: clean(b.gpu),
      timeBudget: clean(b.timeBudget),
      tags: b.tags || [],
      sources: sources(b.sources),
      taskCountReported: Number.isFinite(b.taskCountReported)
        ? b.taskCountReported
        : null,
    });
  }
  for (const t of part.tasks || []) {
    if (!/^[a-zA-Z0-9_.-]+$/.test(t.id))
      throw new Error(`Unsafe task ID ${t.id}`);
    if (taskIds.has(t.id)) throw new Error(`Duplicate task ${t.id}`);
    taskIds.add(t.id);
    const instructions = clean(
      t.instructions,
      "The complete instructions are not available in this catalog. Open the original source for the published task specification.",
    );
    instructionBodies.set(t.id, instructions);
    const instructionType = t.instructionType || "summary";
    const instructionPath = `data/instructions/${t.id}.json`;
    fs.writeFileSync(
      path.join(root, "public", instructionPath),
      JSON.stringify({
        instructions,
        instructionType,
        sources: sources(t.sources, t.sourceUrl),
      }),
    );
    const { instructions: _instructions, ...meta } = t;
    tasks.push({
      ...meta,
      instructionType,
      instructionPath,
      gpu: clean(t.gpu),
      timeBudget: clean(t.timeBudget),
      summary: clean(t.summary, t.objective || ""),
      objective: clean(t.objective, t.summary || ""),
      constraints: Array.isArray(t.constraints)
        ? t.constraints
        : t.constraints
          ? [String(t.constraints)]
          : [],
      sources: sources(t.sources, t.sourceUrl),
      tags: t.tags || [],
      access: t.access || "public",
      submission: clean(t.submission),
      evaluation: clean(t.evaluation),
      searchText: [
        t.name,
        t.summary,
        t.objective,
        t.category,
        t.gpu,
        ...(t.tags || []),
      ]
        .join(" ")
        .toLowerCase(),
    });
  }
}
for (const task of tasks)
  if (!ids.has(task.benchmarkId)) throw new Error(`Orphan task ${task.id}`);
for (const task of tasks) {
  const benchmark = benchmarks.find((b) => b.id === task.benchmarkId);
  const originalSources = task.sources;
  Object.assign(
    task,
    enrichTask(
      task,
      benchmark,
      instructionBodies.get(task.id),
      editorial[task.id] || {},
    ),
  );
  task.sources = [
    ...new Map(
      [...originalSources, ...(task.sources || [])].map((s) => [s.url, s]),
    ).values(),
  ];
  task.searchText = [
    task.searchText,
    task.name,
    task.field,
    ...task.domains,
    task.brief.task,
  ]
    .join(" ")
    .toLowerCase();
}
for (const b of benchmarks) {
  b.rank = readingOrder.includes(b.id) ? readingOrder.indexOf(b.id) : 99;
  b.priority = b.rank < 15;
  const bt = tasks.filter((t) => t.benchmarkId === b.id);
  b.indexedCount = bt.length;
  b.publicCount = bt.filter((t) => t.access === "public").length;
  b.privateCount = bt.filter((t) => t.access === "private").length;
  b.sourceInstructionCount = bt.filter(
    (t) => t.instructionType === "source",
  ).length;
  b.readableCount = bt.filter(
    (t) => t.instructionType !== "unavailable",
  ).length;
}
benchmarks.sort((a, b) => a.rank - b.rank || a.name.localeCompare(b.name));
const catalog = {
  title: "Task search",
  reviewedAt: "2026-10-04",
  builtAt: new Date().toISOString(),
  benchmarks,
  tasks,
  stats: {
    benchmarks: benchmarks.length,
    tasks: tasks.length,
    public: tasks.filter((t) => t.access === "public").length,
    private: tasks.filter((t) => t.access === "private").length,
    sourceInstructions: tasks.filter((t) => t.instructionType === "source")
      .length,
  },
};
fs.writeFileSync(path.join(dir, "catalog.json"), JSON.stringify(catalog));
fs.writeFileSync(
  path.join(dir, "catalog-export.json"),
  JSON.stringify(
    {
      ...catalog,
      tasks: tasks.map(({ searchText, instructionPath, ...t }) => ({
        ...t,
        instructions: instructionBodies.get(t.id),
      })),
    },
    null,
    2,
  ),
);
console.log(
  `Built ${benchmarks.length} benchmarks and ${tasks.length} tasks from ${files.length} source collections.`,
);
