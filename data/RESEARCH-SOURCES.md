# Research-suite source ledger

Reviewed 2026-10-04. This ledger covers the 15 suites owned by `parts/research.json`: **1,666 task entries**. It records the source snapshot and import treatment; per-task source links and resource/evaluation details remain in the JSON. Counts refer to published task families or configurations, not generated test cases.

| Suite | Indexed scope | Primary source snapshot | Imported-text attribution | Coverage note |
| --- | --- | --- | --- | --- |
| Autoresearch Bench | 20 public task families | [Task website](https://www.autoresearch-bench.com/) · accessed 2026-10-04 | Website summaries; no redistribution license located. | 20 separate task pages; repository is a release placeholder. |
| AutoResearchExam | 29 task packages | [7758e84af55f](https://github.com/bespokelabsai/AutoResearchExam/tree/7758e84af55f7666cbdcdd7192959f45b09827af) | Apache-2.0; Bespoke Labs. | All instruction.md/task.toml pairs. Task-config defaults and the published 24-hour protocol are distinguished. |
| FrontierSWE V2 | 34 task packages | [da83f84f8fbc](https://github.com/Proximal-Labs/frontier-swe-v2/tree/da83f84f8fbcec3cbf0f2b17c98ebc811355c2df/tasks) | Summaries and configuration facts; no general repository license located. | Includes the entire released suite, including non-ML systems tasks. |
| AIRS-Bench | 20 RAD tasks | [18e4f1d50106](https://github.com/facebookresearch/airs-bench/tree/18e4f1d501069cf7d7e2740d81c2ca748c56a6a1/airsbench/tasks/rad) | CC BY-NC 4.0; Meta FAIR and contributors. | RAD is canonical here; equivalent MLGym packages are not duplicated. QM9 targets and time-series subsets remain distinct. |
| MLS-Bench | 140 canonical tasks | [80cf5c5cc8f7](https://github.com/Imbernoulli/MLS-Bench/tree/80cf5c5cc8f70fb1b09f185e59ebf5eca04f610c/tasks) | Summaries and configuration facts; no general repository license located. | Complete tasks subtree used because the root recursive GitHub tree is truncated. MLS-Bench-Lite is a subset, not additional tasks. |
| WeirdML | 11 v3 task families | [398be8e15888](https://github.com/htihle/htihle.github.io/blob/398be8e15888515412b714b61b4f28af229627d3/assets/data/weirdml_v3.json) | Summaries only; no general website/repository license located. | 15 hint configurations collapse to 11 families. Four public case studies; seven full prompts unavailable. Historical v2 tasks excluded. |
| PaperBench | 20 canonical papers | [51052cede8cc](https://github.com/openai/frontier-evals/tree/51052cede8cc608f95bb00346635e03759013e5a/project/paperbench) | MIT for benchmark instructions, addenda and rubrics; OpenAI. | Canonical experiments/splits/all.txt; three extra packages excluded. Git LFS addenda resolved. Research paper text is linked, not copied. |
| EXP-Bench | 461 experiment rows | [db1b1f56159b](https://github.com/Just-Curieous/Curie/tree/db1b1f56159b591515f77e03c55bf473d5c1c201/benchmark/exp_bench) | CC BY 4.0 for the Hugging Face annotations; Apache-2.0 for Curie code. | Official CSV from 51 papers; one row per experiment. Annotation question, instructions and implementation requirements are retained. |
| Scientist-Bench | 27 published paper instances | [f9a6f8480860](https://github.com/HKUDS/AI-Researcher/tree/f9a6f8480860c193afff600eeffe3defcee8a978/benchmark/final) | Summaries only; no general repository license located. | All benchmark/final JSONs. task1/task2 are paired conditions, not 54 tasks. Repository also calls the collection Inno-Bench. |
| MLReplicate | 8 shared paper inputs | [c0bdd77e33f4](https://github.com/gsasikiran/MLReplicate-benchmarking/tree/c0bdd77e33f425fc65274c3effd3e8de0d6522c4/AgentLaboratory/dataset) | Apache-2.0; MLReplicate authors. | Agent Laboratory YAML representation of the eight source papers. Other system adapters and bundled inherited benchmarks are not additional tasks. |
| ScienceAgentBench (Verified) | 102 Verified annotations | [c26e151ed601](https://github.com/OSU-NLP-Group/ScienceAgentBench/tree/c26e151ed601ba109dc4d35e057ff8e73fec469d) | CC BY 4.0 for most tasks; source-project exceptions below. MIT for repository code. | Verified split, April 2026 release. No large scientific inputs or hidden evaluator assets are packaged. |
| Automated LLM Speedrunning | 20 published record configs | [ec3e4afd6dcf](https://github.com/facebookresearch/llm-speedrunner/tree/ec3e4afd6dcf7c99f7b0be35898e40df6e1257c9/config/task/nanogpt_speedrun) | CC BY-NC 4.0; Meta and collaborators. | Paper reports 19 tasks; repository has 20 speedrun_record configs. Hint levels are conditions, not separate tasks. |
| KernelBench | 270 current workloads | [423217d9fda9](https://github.com/ScalingIntelligence/KernelBench/tree/423217d9fda91e0c2d67e4a43bf62f96f6d104f1/KernelBench) | MIT; Anne Ouyang, Simon Guo, Azalia Mirhoseini, Scaling Intelligence Lab. | All level1–level4 Python task files, including input generators. Count reflects this repository snapshot. |
| TritonBench | 350 operators: 184 G + 166 T | [603e28a5050e](https://github.com/thunlp/TritonBench/tree/603e28a5050e8c268f6883a69709d477a272d49a/data) | Apache-2.0; TritonBench authors. | Official complex-prompt evaluation catalogs. Simple/complex variants combine per operator; training corpora are not packaged. |
| AlgoTune | 154 task descriptions | [dff9914c1080](https://github.com/oripress/AlgoTune/tree/dff9914c10800c7a031c9e8c3d4d1c8cd1b38906/AlgoTuneTasks) | MIT; Ori Press and AlgoTune contributors. | All AlgoTuneTasks/*/description.txt files. Procedurally generated test inputs are not separate catalog tasks. |

## Dataset provenance

- EXP-Bench annotations: [official CSV at dataset revision 5b35c4c717a9](https://huggingface.co/datasets/Just-Curieous/EXP-Bench/blob/5b35c4c717a9f7ddd6a255b94a462f8ca51b0668/exp_bench_dataset.csv). The [dataset metadata](https://huggingface.co/api/datasets/Just-Curieous/EXP-Bench) declares `cc-by-4.0`. This differs from the Apache-2.0 license of the Curie execution code.
- ScienceAgentBench: [Verified split](https://huggingface.co/datasets/osunlp/ScienceAgentBench/viewer/default/verified), dataset revision `9c6e96c9e74572e979b0930ee735041cef528cb7`, retrieved through the Hugging Face rows API in two pages. [Dataset metadata](https://huggingface.co/api/datasets/osunlp/ScienceAgentBench) declares `cc-by-4.0`.
- Autoresearch Bench and Hugging Face viewer pages are live services. Their access date is recorded; the local annotation/page cache is not a promise that the upstream pages remain unchanged.

## License evidence and attribution

Source readers preserve publisher attribution and identify the license. Formatting changes add reader headings, task contracts or source links; summaries are explicitly marked separately. Original benchmark copyright remains with its respective owners.
- [AutoResearchExam license](https://github.com/bespokelabsai/AutoResearchExam/blob/7758e84af55f7666cbdcdd7192959f45b09827af/LICENSE).
- [AIRS-Bench license](https://github.com/facebookresearch/airs-bench/blob/18e4f1d501069cf7d7e2740d81c2ca748c56a6a1/LICENSE).
- [PaperBench license](https://github.com/openai/frontier-evals/blob/51052cede8cc608f95bb00346635e03759013e5a/LICENSE.md).
- [EXP-Bench license](https://github.com/Just-Curieous/Curie/blob/db1b1f56159b591515f77e03c55bf473d5c1c201/LICENSE).
- [MLReplicate license](https://github.com/gsasikiran/MLReplicate-benchmarking/blob/c0bdd77e33f425fc65274c3effd3e8de0d6522c4/LICENSE).
- [Automated LLM Speedrunning license](https://github.com/facebookresearch/llm-speedrunner/blob/ec3e4afd6dcf7c99f7b0be35898e40df6e1257c9/LICENSE).
- [KernelBench license](https://github.com/ScalingIntelligence/KernelBench/blob/423217d9fda91e0c2d67e4a43bf62f96f6d104f1/LICENSE).
- [TritonBench license](https://github.com/thunlp/TritonBench/blob/603e28a5050e8c268f6883a69709d477a272d49a/LICENSE).
- [AlgoTune license](https://github.com/oripress/AlgoTune/blob/dff9914c10800c7a031c9e8c3d4d1c8cd1b38906/LICENSE).
- [ScienceAgentBench licensing statement](https://github.com/OSU-NLP-Group/ScienceAgentBench/blob/c26e151ed601ba109dc4d35e057ff8e73fec469d/README.md#licensing-information): instances **32, 46, 53, 54, 84** retain [rasterio’s original license](https://github.com/rasterio/rasterio?tab=License-1-ov-file); instance **3** retains [matminer’s original license](https://github.com/hackingmaterials/matminer?tab=License-1-ov-file). The majority-task CC BY 4.0 label does not replace those exceptions.

AIRS-Bench and LLM Speedrunning use **Attribution–NonCommercial 4.0**. This ledger records their source terms; it does not grant additional commercial reuse rights. Where no general redistribution license was located (FrontierSWE, MLS-Bench, Scientist-Bench, WeirdML and Autoresearch Bench), the dashboard contains condensed summaries/factual metadata and links rather than a mirror of full instructions. PaperBench research papers retain their own rights and are not reproduced.

## Extraction and validation

`research_fetch.py`, `research_download.py`, and `research_web_fetch.py` retrieve source catalogs; `build_research.py` followed by `research_supplement.py` writes the part. Python dependencies are PyYAML and BeautifulSoup, with `gh` used for GitHub metadata. Sources are cached under `.local/dashboard-research`; no benchmark execution is performed.

Checks completed: 1,666 unique task IDs; every entry maps to one of the 15 suite IDs; required reader/source fields present; 20 canonical PaperBench entries; 11 current WeirdML families; no unresolved Git LFS pointers; representative commit links across seven repositories returned HTTP 200. Reader treatment totals: **1,434 source**, **225 summary**, **7 unavailable**. Large task datasets, model checkpoints and Triton training corpora are not included in the dashboard artifact.

“General Context” remains an unresolved publisher reference from the original request. It has not been silently equated with another organization. FrontierSWE is attributed to Proximal and Autoresearch Bench to Emulated on their own primary-source evidence.
