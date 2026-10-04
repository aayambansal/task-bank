# Task bank

A simple directory of AI research, ML engineering, and scientific benchmark tasks. Search, filter by field or resources, and open a task to read its objective, working environment, submission, and grader. White and black themes; no account required. Saved tasks stay in the browser.

The October 4, 2026 snapshot contains **38 benchmarks and 2,425 task records**, including **1,799 original instruction documents**. Some records are model–target configurations, research briefs, or private catalog entries rather than individual executable environments. Benchmark coverage notes explain these distinctions.

## Run locally

```sh
npm ci
npm run dev
```

## Build and verify

```sh
npm run build
npm run check
npm test
```

Vite writes the static website to `dist/`. `vercel.json` configures the Vercel build. Task and benchmark links use hash routing and work on a plain static host.

## Content

- `data/parts/` contains the collected source records.
- `data/editorial-overrides.json` contains 54 individually reviewed briefs for OpenRSI Index, Scale RSI-Bench, and the public RSI-Exam tasks.
- `scripts/enrich-catalog.mjs` extracts complete source paragraphs, preserves resource qualifiers, and assigns topic labels for browsing.
- `scripts/build-catalog.mjs` creates the metadata index, individual instruction files, and the complete JSON download under `public/data/`.
- `data/RESEARCH-SOURCES.md`, `data/ml-source-manifest.json`, `data/rsi-source-licenses.txt`, and `data/licenses/` document provenance and licenses.

Briefs are reading aids condensed from linked specifications. They are not independent benchmark instructions. Original source text is available in each reader where redistribution permits it. Summaries and unpublished instructions are marked. Missing requirements are never filled in with guessed GPU allocations or grading protocols.

Source import scripts use local caches and may require Python dependencies and GitHub authentication. The regular build is offline and uses the checked-in source records. No benchmark code is executed by the website.

## Deployment

Repository: https://github.com/aayambansal/task-bank

Deploy with Vercel's Git integration or run `vercel --prod` from this directory after linking the project. The directory is independent of the Horizon repository.
