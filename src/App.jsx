import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  ArrowUpRight,
  BookmarkSimple,
  Check,
  Copy,
  MagnifyingGlass,
  Moon,
  Sun,
  X,
} from "@phosphor-icons/react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const fmt = (n) => new Intl.NumberFormat("en").format(n || 0);
const DOMAINS = [
  "AI research",
  "Agents",
  "Language models",
  "Computer vision",
  "Reinforcement learning",
  "ML systems",
  "Data curation",
  "AI safety",
  "Scientific computing",
  "Software engineering",
  "Mathematics",
  "Reproduction",
];
function readStorage(key, fallback) {
  try {
    return JSON.parse(localStorage.getItem(key)) ?? fallback;
  } catch {
    return fallback;
  }
}
function useStorage(key, fallback) {
  const [value, setValue] = useState(() => readStorage(key, fallback));
  useEffect(() => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch {}
  }, [key, value]);
  return [value, setValue];
}
function useHash() {
  const [hash, setHash] = useState(() => location.hash.slice(1) || "/");
  useEffect(() => {
    const handler = () => setHash(location.hash.slice(1) || "/");
    addEventListener("hashchange", handler);
    return () => removeEventListener("hashchange", handler);
  }, []);
  return hash;
}
function taskHref(task) {
  return `#/tasks/${task.id}`;
}
function plain(text = "") {
  return text
    .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1")
    .replace(/[`*#]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}
function compact(text = "", limit = 100) {
  const s = plain(text);
  return s.length > limit ? `${s.slice(0, limit).replace(/\s+\S*$/, "")}…` : s;
}
function External({ href, children, className = "" }) {
  return href ? (
    <a
      href={href}
      className={className}
      target="_blank"
      rel="noopener noreferrer"
    >
      {children}
      <ArrowUpRight size={13} />
    </a>
  ) : null;
}
function IconButton({ label, onClick, children, pressed }) {
  return (
    <button
      type="button"
      className="icon-button"
      title={label}
      aria-label={label}
      aria-pressed={pressed}
      onClick={onClick}
    >
      {children}
    </button>
  );
}
function Markdown({ text, sourceUrl }) {
  return (
    <div className="markdown">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ href, children }) => {
            let target = href;
            try {
              target = new URL(href, sourceUrl || location.origin).href;
            } catch {}
            return (
              <a href={target} target="_blank" rel="noopener noreferrer">
                {children}
              </a>
            );
          },
          img: ({ alt, src }) => (
            <a href={src} target="_blank" rel="noopener noreferrer">
              {alt || "View source image"}
            </a>
          ),
        }}
      >
        {text || "Not specified in the published source."}
      </ReactMarkdown>
    </div>
  );
}
function computeKind(task) {
  const s = task.gpu || "";
  if (/^(not |unknown|unspecified|varies)/i.test(s)) return "unspecified";
  if (/(?:no gpu|cpu.only|0(?: local)? gpus?)/i.test(s)) return "cpu";
  if (/managed|api.only|tinker/i.test(s)) return "api";
  if (/gpu|\b[ABHV]\d{2,3}\b|tpu/i.test(s)) return "gpu";
  if (/cpu/i.test(s)) return "cpu";
  return "unspecified";
}
function Dialog({ children, onClose, label, className = "" }) {
  const ref = useRef(null);
  useEffect(() => {
    const d = ref.current;
    const previous = document.activeElement;
    d.showModal();
    const handler = (e) => {
      e.preventDefault();
      onClose();
    };
    d.addEventListener("cancel", handler);
    return () => {
      d.removeEventListener("cancel", handler);
      d.close();
      previous?.focus?.();
    };
  }, []);
  return (
    <dialog
      ref={ref}
      aria-label={label}
      className={className}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      {children}
    </dialog>
  );
}

export default function App() {
  const [catalog, setCatalog] = useState(null),
    [error, setError] = useState("");
  const [theme, setTheme] = useStorage("task-bank-theme", "light"),
    [saved, setSaved] = useStorage("task-bank-saved", []);
  const [query, setQuery] = useState(""),
    [domains, setDomains] = useState([]),
    [benchmark, setBenchmark] = useState(""),
    [compute, setCompute] = useState(""),
    [availability, setAvailability] = useState(""),
    [savedOnly, setSavedOnly] = useState(false),
    [sort, setSort] = useState("default"),
    [page, setPage] = useState(1),
    [about, setAbout] = useState(false),
    [notice, setNotice] = useState("");
  const searchRef = useRef(null),
    returnRoute = useRef("/");
  const route = useHash();
  useEffect(() => {
    const controller = new AbortController();
    fetch("/data/catalog.json", { signal: controller.signal })
      .then((r) => {
        if (!r.ok) throw new Error("Could not load the task catalog.");
        return r.json();
      })
      .then(setCatalog)
      .catch((e) => {
        if (e.name !== "AbortError") setError(e.message);
      });
    return () => controller.abort();
  }, []);
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document
      .querySelector('meta[name="theme-color"]')
      ?.setAttribute("content", theme === "dark" ? "#000000" : "#ffffff");
  }, [theme]);
  useEffect(() => {
    const handler = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        searchRef.current?.focus();
      }
      if (
        e.key === "/" &&
        !["INPUT", "TEXTAREA", "SELECT"].includes(
          document.activeElement?.tagName,
        ) &&
        !document.querySelector("dialog[open]")
      ) {
        e.preventDefault();
        searchRef.current?.focus();
      }
    };
    addEventListener("keydown", handler);
    return () => removeEventListener("keydown", handler);
  }, []);
  useEffect(() => {
    if (!notice) return;
    const timer = setTimeout(() => setNotice(""), 2500);
    return () => clearTimeout(timer);
  }, [notice]);
  useEffect(() => {
    setPage(1);
  }, [query, domains, benchmark, compute, availability, savedOnly, sort]);
  const benchmarks = catalog?.benchmarks || [],
    tasks = catalog?.tasks || [];
  const byBenchmark = useMemo(
    () => Object.fromEntries(benchmarks.map((b) => [b.id, b])),
    [benchmarks],
  );
  const selectedTask = route.startsWith("/tasks/")
    ? tasks.find((t) => t.id === route.split("/")[2])
    : null;
  const backgroundRoute = route.startsWith("/tasks/")
    ? returnRoute.current
    : route;
  const selectedBenchmark = backgroundRoute.startsWith("/benchmarks/")
    ? byBenchmark[backgroundRoute.split("/")[2]]
    : null;
  useEffect(() => {
    if (!route.startsWith("/tasks/")) returnRoute.current = route;
  }, [route]);
  const closeTask = () => {
    location.hash = returnRoute.current.startsWith("/tasks/")
      ? "/"
      : returnRoute.current;
  };
  const toggleSaved = (id) =>
    setSaved((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  const toggleDomain = (name) =>
    setDomains((prev) =>
      prev.includes(name) ? prev.filter((x) => x !== name) : [...prev, name],
    );
  const clear = () => {
    setQuery("");
    setDomains([]);
    setBenchmark("");
    setCompute("");
    setAvailability("");
    setSavedOnly(false);
    setSort("default");
  };
  const filtered = useMemo(() => {
    const terms = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
    const results = tasks.filter(
      (t) =>
        (!selectedBenchmark || t.benchmarkId === selectedBenchmark.id) &&
        (!benchmark || t.benchmarkId === benchmark) &&
        (!domains.length || domains.some((d) => t.domains?.includes(d))) &&
        (!compute || computeKind(t) === compute) &&
        (!availability || t.instructionType === availability) &&
        (!savedOnly || saved.includes(t.id)) &&
        terms.every((term) =>
          `${t.searchText} ${t.name} ${t.field} ${t.domains?.join(" ")} ${byBenchmark[t.benchmarkId]?.name}`
            .toLowerCase()
            .includes(term),
        ),
    );
    return results.sort((a, b) =>
      sort === "name"
        ? a.name.localeCompare(b.name)
        : sort === "benchmark"
          ? byBenchmark[a.benchmarkId].name.localeCompare(
              byBenchmark[b.benchmarkId].name,
            ) || a.name.localeCompare(b.name)
          : (a.id.includes("minference-sparse-prefill")
              ? -2
              : a.benchmarkId === "openrsi-index"
                ? -1
                : (byBenchmark[a.benchmarkId]?.rank ?? 99)) -
            (b.id.includes("minference-sparse-prefill")
              ? -2
              : b.benchmarkId === "openrsi-index"
                ? -1
                : (byBenchmark[b.benchmarkId]?.rank ?? 99)),
    );
  }, [
    tasks,
    query,
    domains,
    benchmark,
    compute,
    availability,
    savedOnly,
    saved,
    sort,
    byBenchmark,
    selectedBenchmark,
  ]);
  const activeFilters = !!(
    query ||
    domains.length ||
    benchmark ||
    compute ||
    availability ||
    savedOnly
  );
  const domainCounts = useMemo(
    () =>
      Object.fromEntries(
        DOMAINS.map((d) => [
          d,
          tasks.filter((t) => t.domains?.includes(d)).length,
        ]),
      ),
    [tasks],
  );
  const availableDomains = DOMAINS.filter((d) => domainCounts[d] > 0);
  const size = 40,
    totalPages = Math.max(1, Math.ceil(filtered.length / size)),
    safePage = Math.min(page, totalPages);
  const sortByName = () => setSort((v) => (v === "name" ? "default" : "name"));
  return (
    <div className="site">
      <a
        className="skip-link"
        href="#results"
        onClick={(e) => {
          e.preventDefault();
          const results = document.getElementById("results");
          results?.focus();
          results?.scrollIntoView({ block: "start" });
        }}
      >
        Skip to tasks
      </a>
      <header className="site-header">
        <div className="identity">
          <h1 className="brand-heading">
            <a
              href="#/"
              className="wordmark"
              onClick={() => {
                clear();
              }}
            >
              Task search
            </a>
          </h1>
          <span>A directory of research problems.</span>
        </div>
        <nav aria-label="Site">
          <button className="text-button" onClick={() => setAbout(true)}>
            About the data
          </button>
          <External
            href="https://github.com/aayambansal/task-bank"
            className="github-link"
          >
            GitHub
          </External>
          <IconButton
            label={
              theme === "light"
                ? "Switch to dark theme"
                : "Switch to light theme"
            }
            onClick={() => setTheme((t) => (t === "light" ? "dark" : "light"))}
          >
            {theme === "light" ? <Moon size={18} /> : <Sun size={18} />}
          </IconButton>
        </nav>
      </header>
      <main>
        {selectedBenchmark ? (
          <section className="benchmark-intro">
            <a href="#/" className="back-link" onClick={clear}>
              <ArrowLeft size={14} />
              All tasks
            </a>
            <h1>{selectedBenchmark.name}</h1>
            <p>{selectedBenchmark.description}</p>
            <div className="benchmark-sources">
              <span>{fmt(selectedBenchmark.indexedCount)} task records</span>
              <External
                href={selectedBenchmark.repository || selectedBenchmark.website}
              >
                Benchmark source
              </External>
              <External href={selectedBenchmark.paper}>Paper</External>
            </div>
            <details className="benchmark-context">
              <summary>Overview &amp; catalog coverage</summary>
              <Markdown text={selectedBenchmark.overview} />
              <p>{selectedBenchmark.coverageNote}</p>
            </details>
          </section>
        ) : (
          <section className="intro">
            <p>
              Benchmark tasks, with the setup, constraints, and grading criteria
              in one place.
            </p>
          </section>
        )}
        <section
          className="search-controls"
          aria-label="Search and filter tasks"
        >
          <div className="search-row">
            <label className="search-input">
              <MagnifyingGlass size={19} />
              <input
                ref={searchRef}
                type="search"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                aria-label="Search tasks"
                placeholder="Search tasks, methods, models…"
              />
              <kbd>/</kbd>
            </label>
            <button
              className={`saved-filter ${savedOnly ? "selected" : ""}`}
              aria-pressed={savedOnly}
              onClick={() => setSavedOnly((v) => !v)}
            >
              <BookmarkSimple
                size={16}
                weight={savedOnly ? "fill" : "regular"}
              />
              <span>Saved</span>
              <span className="saved-count">{saved.length}</span>
            </button>
          </div>
          <div className="domain-filter">
            <span className="filter-label">Field</span>
            <div className="domain-options">
              {availableDomains.map((d) => (
                <button
                  key={d}
                  aria-pressed={domains.includes(d)}
                  className={`filter-chip ${domains.includes(d) ? "selected" : ""}`}
                  onClick={() => toggleDomain(d)}
                >
                  {d}
                  <small>{fmt(domainCounts[d])}</small>
                </button>
              ))}
            </div>
          </div>
          <div className="secondary-filters">
            <span className="filter-label">Filter</span>
            <div className="select-filters">
              {!selectedBenchmark && (
                <select
                  aria-label="Filter by benchmark"
                  value={benchmark}
                  onChange={(e) => setBenchmark(e.target.value)}
                >
                  <option value="">All benchmarks</option>
                  {[...benchmarks]
                    .sort((a, b) => a.name.localeCompare(b.name))
                    .map((b) => (
                      <option value={b.id} key={b.id}>
                        {b.name}
                      </option>
                    ))}
                </select>
              )}
              <select
                aria-label="Filter by compute"
                value={compute}
                onChange={(e) => setCompute(e.target.value)}
              >
                <option value="">Any compute</option>
                <option value="cpu">CPU / no GPU</option>
                <option value="gpu">GPU / TPU</option>
                <option value="api">API / managed</option>
                <option value="unspecified">Not specified</option>
              </select>
              <select
                aria-label="Filter by instructions"
                value={availability}
                onChange={(e) => setAvailability(e.target.value)}
              >
                <option value="">All instructions</option>
                <option value="source">Original available</option>
                <option value="summary">Brief only</option>
                <option value="unavailable">Unpublished</option>
              </select>
              {activeFilters && (
                <button className="clear-filters" onClick={clear}>
                  Clear filters
                  <X size={12} />
                </button>
              )}
            </div>
          </div>
        </section>
        <div className="results-bar">
          <p aria-live="polite">
            {catalog ? (
              <>
                <strong>{fmt(filtered.length)}</strong> of {fmt(tasks.length)}{" "}
                tasks<span> · {benchmarks.length} benchmarks</span>
              </>
            ) : (
              "Loading tasks…"
            )}
          </p>
          <label className="sort-control">
            <span>Sort</span>
            <select
              aria-label="Sort tasks"
              value={sort}
              onChange={(e) => setSort(e.target.value)}
            >
              <option value="default">Default</option>
              <option value="name">Task name</option>
              <option value="benchmark">Benchmark</option>
            </select>
          </label>
        </div>
        <div id="results" className="results" tabIndex={-1}>
          {error ? (
            <div className="empty">
              <h2>Couldn’t load the directory</h2>
              <p>{error}</p>
              <button onClick={() => location.reload()}>Try again</button>
            </div>
          ) : !catalog ? (
            <div className="skeleton" aria-label="Loading tasks">
              {Array.from({ length: 6 }, (_, i) => (
                <div key={i} />
              ))}
            </div>
          ) : !filtered.length ? (
            <div className="empty">
              <h2>No matching tasks</h2>
              <p>Try a different search or remove a filter.</p>
              <button onClick={clear}>Clear filters</button>
            </div>
          ) : (
            <div className="table-scroll">
              <table className="task-table">
                <thead>
                  <tr>
                    <th
                      className="task-col"
                      aria-sort={sort === "name" ? "ascending" : "none"}
                    >
                      <button onClick={sortByName}>
                        Task{sort === "name" && <ArrowDown size={11} />}
                      </button>
                    </th>
                    <th className="field-col">Field</th>
                    <th className="benchmark-col">
                      <button onClick={() => setSort("benchmark")}>
                        Benchmark
                        {sort === "benchmark" && <ArrowDown size={11} />}
                      </button>
                    </th>
                    <th className="compute-col">Compute</th>
                    <th className="budget-col">Budget</th>
                    <th className="save-col">
                      <span className="sr-only">Save task</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filtered
                    .slice((safePage - 1) * size, safePage * size)
                    .map((t) => (
                      <tr key={t.id}>
                        <td className="task-col">
                          <a className="task-title" href={taskHref(t)}>
                            {t.name}
                            <ArrowUpRight size={13} />
                          </a>
                          <p
                            className="task-description"
                            title={plain(t.brief?.task || t.objective)}
                          >
                            {compact(
                              t.brief?.task || t.objective || t.summary,
                              160,
                            )}
                          </p>
                          {t.access !== "public" && (
                            <span className="record-note">
                              {t.access === "private"
                                ? "Private task"
                                : "Proposal"}
                            </span>
                          )}
                        </td>
                        <td className="field-col">
                          <div className="row-fields">
                            {(t.domains?.length
                              ? t.domains.length > 1
                                ? t.domains.filter((d) => d !== "AI research")
                                : t.domains
                              : []
                            )
                              .slice(0, 2)
                              .map((d) => (
                                <button
                                  key={d}
                                  className="field-tag"
                                  onClick={() => setDomains([d])}
                                >
                                  {d}
                                </button>
                              ))}
                          </div>
                        </td>
                        <td className="benchmark-col">
                          <a
                            className="benchmark-link"
                            href={`#/benchmarks/${t.benchmarkId}`}
                            onClick={clear}
                          >
                            {byBenchmark[t.benchmarkId]?.name}
                          </a>
                        </td>
                        <td className="compute-col">
                          <span title={t.gpu}>
                            {t.resourceLabel || compact(t.gpu, 48)}
                          </span>
                        </td>
                        <td className="budget-col">
                          <span title={t.timeBudget}>
                            {t.timeLabel || compact(t.timeBudget, 34)}
                          </span>
                        </td>
                        <td className="save-col">
                          <IconButton
                            label={`${saved.includes(t.id) ? "Unsave" : "Save"} ${t.name}`}
                            pressed={saved.includes(t.id)}
                            onClick={() => toggleSaved(t.id)}
                          >
                            <BookmarkSimple
                              size={16}
                              weight={saved.includes(t.id) ? "fill" : "regular"}
                            />
                          </IconButton>
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
        {filtered.length > size && (
          <div className="pagination">
            <span>
              {fmt((safePage - 1) * size + 1)}–
              {fmt(Math.min(safePage * size, filtered.length))} of{" "}
              {fmt(filtered.length)}
            </span>
            <div>
              <button
                disabled={safePage <= 1}
                onClick={() => {
                  setPage(safePage - 1);
                  document
                    .getElementById("results")
                    ?.scrollIntoView({ block: "start" });
                }}
              >
                <ArrowLeft size={13} />
                Previous
              </button>
              <span>
                {safePage} / {totalPages}
              </span>
              <button
                disabled={safePage >= totalPages}
                onClick={() => {
                  setPage(safePage + 1);
                  document
                    .getElementById("results")
                    ?.scrollIntoView({ block: "start" });
                }}
              >
                Next
                <ArrowRight size={13} />
              </button>
            </div>
          </div>
        )}
      </main>
      <footer>
        <span>Source snapshot · October 4, 2026</span>
        <div>
          <button onClick={() => setAbout(true)}>Sources &amp; coverage</button>
          <a href="/data/catalog-export.json" download="task-bank.json">
            Download JSON
            <ArrowDown size={12} />
          </a>
        </div>
      </footer>
      {selectedTask && (
        <TaskSheet
          key={selectedTask.id}
          task={selectedTask}
          benchmark={byBenchmark[selectedTask.benchmarkId]}
          saved={saved.includes(selectedTask.id)}
          toggleSaved={() => toggleSaved(selectedTask.id)}
          onClose={closeTask}
          notify={setNotice}
        />
      )}
      {catalog && route.startsWith("/tasks/") && !selectedTask && (
        <Dialog
          label="Task not found"
          className="about-dialog"
          onClose={() => {
            location.hash = "/";
          }}
        >
          <div className="dialog-heading">
            <h2>Task not found</h2>
            <IconButton
              label="Close"
              onClick={() => {
                location.hash = "/";
              }}
            >
              <X size={18} />
            </IconButton>
          </div>
          <p>This task isn’t in the current catalog.</p>
        </Dialog>
      )}
      {about && (
        <Dialog
          label="About the data"
          className="about-dialog"
          onClose={() => setAbout(false)}
        >
          <div className="dialog-heading">
            <h2>About the data</h2>
            <IconButton label="Close about" onClick={() => setAbout(false)}>
              <X size={18} />
            </IconButton>
          </div>
          <p>
            This directory brings together published AI and ML benchmark tasks,
            with links to the specifications and code that define them.
          </p>
          <p>
            Briefs condense those sources into four parts: the task, the working
            environment, the submission, and the grader. They are reading aids;
            the linked specification remains authoritative.
          </p>
          <dl>
            <dt>Original instructions</dt>
            <dd>Imported source text, available inside the task reader.</dd>
            <dt>Brief only</dt>
            <dd>
              A summary and source links; complete instructions are not mirrored
              here.
            </dd>
            <dt>Unpublished</dt>
            <dd>
              Only public catalog information is available. Missing requirements
              are not inferred.
            </dd>
          </dl>
          <p>
            Fields are browsing labels assigned from each task’s subject. Counts
            may represent environments, paper reproductions, or model–target
            configurations; each benchmark’s coverage note explains its unit.
          </p>
          <p>
            Compute and time limits preserve source qualifications. A paper’s
            experiment hardware is not automatically a task requirement. Saved
            tasks stay in this browser.
          </p>
          <div className="about-bottom">
            <External href="https://github.com/aayambansal/task-bank">
              Source &amp; corrections
            </External>
            <span>Snapshot: October 4, 2026</span>
          </div>
        </Dialog>
      )}
      {notice && (
        <div role="status" className="toast">
          <Check size={14} />
          {notice}
        </div>
      )}
    </div>
  );
}

function TaskSheet({
  task: t,
  benchmark: b,
  saved,
  toggleSaved,
  onClose,
  notify,
}) {
  const [detail, setDetail] = useState(null),
    [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    fetch("/" + t.instructionPath, { signal: controller.signal })
      .then((r) => {
        if (!r.ok)
          throw new Error("Original instructions could not be loaded.");
        return r.json();
      })
      .then(setDetail)
      .catch((e) => {
        if (e.name !== "AbortError") setError(e.message);
      });
    return () => controller.abort();
  }, [t.id, t.instructionPath]);
  const brief = t.brief || {
    task: t.objective,
    world: [...t.constraints, `Compute: ${t.gpu}`, `Time: ${t.timeBudget}`],
    submission: t.submission,
    grader: [t.evaluation],
  };
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(location.href);
      notify("Task link copied");
    } catch {
      notify("Use the address bar to copy this task link");
    }
  };
  return (
    <Dialog label={t.name} className="task-dialog" onClose={onClose}>
      <div className="sheet-toolbar">
        <button className="close-reader" onClick={onClose}>
          <ArrowLeft size={14} />
          Back to tasks
        </button>
        <div>
          <IconButton label="Copy task link" onClick={copy}>
            <Copy size={16} />
          </IconButton>
          <IconButton
            label={saved ? "Unsave task" : "Save task"}
            pressed={saved}
            onClick={toggleSaved}
          >
            <BookmarkSimple size={17} weight={saved ? "fill" : "regular"} />
          </IconButton>
          <IconButton label="Close task" onClick={onClose}>
            <X size={18} />
          </IconButton>
        </div>
      </div>
      <article className="task-article">
        <h1>{t.name}</h1>
        <dl className="task-byline">
          <div>
            <dt>Benchmark</dt>
            <dd>
              <a href={`#/benchmarks/${b.id}`}>
                {b.name}
                <ArrowUpRight size={13} />
              </a>
            </dd>
          </div>
          <div>
            <dt>Field</dt>
            <dd>{t.field || t.category}</dd>
          </div>
        </dl>
        {t.access !== "public" && (
          <p className="availability-note">
            {t.access === "private"
              ? "Private task. Only the published catalog details are available."
              : "Published proposal; acceptance into the benchmark has not been confirmed."}
          </p>
        )}
        <section className="brief-section">
          <h2>Task</h2>
          <Markdown text={brief.task} sourceUrl={t.sourceUrl} />
        </section>
        <section className="brief-section">
          <h2>World</h2>
          {brief.world?.length ? (
            <ul className="brief-list">
              {brief.world.map((line, i) => (
                <li key={i}>
                  <Markdown text={line} sourceUrl={t.sourceUrl} />
                </li>
              ))}
            </ul>
          ) : (
            <p className="unspecified">
              The published brief does not specify the working environment.
            </p>
          )}
        </section>
        <section className="brief-section">
          <h2>Submission</h2>
          <Markdown text={brief.submission} sourceUrl={t.sourceUrl} />
        </section>
        <section className="brief-section">
          <h2>Grader</h2>
          {brief.grader?.length ? (
            <ul className="brief-list">
              {brief.grader.map((line, i) => (
                <li key={i}>
                  <Markdown text={line} sourceUrl={t.sourceUrl} />
                </li>
              ))}
            </ul>
          ) : (
            <p className="unspecified">
              The grading contract is not published.
            </p>
          )}
        </section>
        <details className="original-instructions">
          <summary>
            <span>
              {t.instructionType === "source"
                ? "Read original instructions"
                : t.instructionType === "summary"
                  ? "Read extended source notes"
                  : "Instruction availability"}
            </span>
            <span>
              {t.instructionType === "source"
                ? "Source text"
                : t.instructionType === "summary"
                  ? "Brief only"
                  : "Unpublished"}
            </span>
          </summary>
          <div>
            {error ? (
              <p>
                {error} <External href={t.sourceUrl}>Read at source</External>
              </p>
            ) : detail ? (
              <Markdown text={detail.instructions} sourceUrl={t.sourceUrl} />
            ) : (
              <p className="unspecified">Loading source text…</p>
            )}
          </div>
        </details>
        <section className="task-sources">
          <h2>Sources</h2>
          <ul>
            {t.sources.map((s, i) => (
              <li key={s.url + i}>
                <External href={s.url}>{s.label}</External>
              </li>
            ))}
          </ul>
          <p>
            Condensed from the linked specifications. Check the original source
            before running this task.
          </p>
        </section>
      </article>
    </Dialog>
  );
}
