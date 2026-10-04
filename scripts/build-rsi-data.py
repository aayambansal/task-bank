"""Build the RSI/model-development source catalog from small, cached source files.

Input cache: /tmp/frontier-dashboard-rsi (GitHub source files, HF public task
specifications and official catalog HTML; no model weights or dataset assets).
This builder never runs benchmark code. Source snapshots are identified by SHA.
"""
import json, re, sys, tomllib, html
from pathlib import Path
sys.path.insert(0, '/tmp/frontier-dashboard-rsi/pylibs')
from bs4 import BeautifulSoup
import yaml

ROOT = Path('/tmp/frontier-dashboard-rsi')
OUT = Path(__file__).resolve().parents[1] / 'data/parts/rsi.json'
benchmarks, tasks = [], []
UNKNOWN = 'Not specified'

def read(repo, path):
    p = ROOT / 'repos' / repo / path
    return p.read_text() if p.exists() else ''

def sha(repo):
    return json.loads((ROOT / (repo.replace('/', '__')+'.json')).read_text())['sha']

def link(repo,path):
    return f'https://github.com/{repo}/blob/{sha(repo)}/{path}'

def source(label,url): return {'label':label,'url':url}
def clean(t):
    t = re.sub(r'<[^>]+>', '', t)
    t = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', t)
    return re.sub(r'\s+', ' ', t.replace('`','').replace('**','')).strip()

def first_para(s):
    for p in re.split(r'\n\s*\n',s):
        if not p.strip().startswith(('#','```','<!--','<','|','>')) and len(clean(p))>35:
            return clean(p)[:800]
    return UNKNOWN

def section(s,pattern):
    lines=s.splitlines(); found=False; out=[]
    for line in lines:
        if re.match(r'^#{1,4} ',line):
            if found:break
            if re.search(pattern,line,re.I):found=True;continue
        elif found:out.append(line)
    return clean('\n'.join(out))[:1500] or UNKNOWN

def lines_matching(s, pattern, n=5):
    return [clean(x.lstrip('-* ')) for x in s.splitlines() if re.search(pattern,x,re.I) and len(clean(x))>4][:n]

def resources(spec,s, fallback_gpu=UNKNOWN):
    env=spec.get('environment',{}); meta=spec.get('metadata',{});agent=spec.get('agent',{})
    count=env.get('gpus',meta.get('budget_gpus'))
    types=env.get('gpu_types') or [meta.get('budget_gpu_type','')]
    gpu=('0 local GPUs declared (CPU/API environment)' if count == 0 else f"{count} × {' / '.join(types) or 'GPU (type unspecified)'}" if count is not None else fallback_gpu)
    hw=lines_matching(s,r'(?:\d\s*[×x]?\s*(?:\d+\s*GB\s*)?GPUs?|\d\s*[×x]\s*(?:H100|A100|H200|B200|B300)|one GPU|TPU v6e|Hardware:)',2)
    if gpu==UNKNOWN and hw:gpu='; '.join(hw)[:450]
    duration=agent.get('timeout_sec')
    clock=f'{duration/3600:g} hours (task configuration)' if isinstance(duration,(int,float)) else UNKNOWN
    budget=lines_matching(s,r'(?:Hard agent budget:|^Budget:|outer allocation lasts|run budget is|session budget is)',1)
    if budget:clock='; '.join(budget)[:400] + (f' Runtime timeout: {duration/3600:g} hours.' if duration else '')
    return gpu,clock

def add_b(id,name,organization,category,description,overview,website,repo='',paper='',gpu=UNKNOWN,time=UNKNOWN,count=None,coverage='',tags=None,priority=True):
    sources=[source('Official website',website)]
    if repo:sources.append(source('Source repository','https://github.com/'+repo))
    if paper:sources.append(source('Paper',paper))
    benchmarks.append(dict(id=id,name=name,organization=organization,category=category,description=description,overview=overview,website=website,repository='https://github.com/'+repo if repo else '',paper=paper,priority=priority,tags=tags or [],gpu=gpu,timeBudget=time,taskCountReported=count,coverageNote=coverage,sources=sources,reviewedAt='2026-10-04'))

def add_t(b,slug,name,category,summary,instructions,url,**kw):
    d=dict(id=b+'--'+slug,benchmarkId=b,name=name,category=category,summary=summary,objective=summary,instructions=instructions,instructionType='summary',gpu=UNKNOWN,timeBudget=UNKNOWN,constraints=[],submission=UNKNOWN,evaluation=UNKNOWN,access='public',sourceUrl=url,sources=[source('Task source',url)],tags=[])
    d.update(kw); tasks.append(d);return d

def licensed_instructions(text,repo,path,license_name):
    return text+'\n\n---\n\nSource: ['+repo+'/'+path+']('+link(repo,path)+'). Reproduced under '+license_name+'. [License]('+link(repo,'LICENSE')+').'

# Scale's accepted sample catalog; proposal PRs are deliberately not included.
repo='scaleapi/rsi-benchmark';bid='scale-rsi-bench'
add_b(bid,'RSI Bench','Scale AI','Research suites','Expert-authored tasks across the AI development lifecycle.','Agents start from a working research environment, use a bounded compute allocation to improve a method, and submit an artifact to a verifier. The four released samples cover data curation, on-policy distillation, robustness, and agent orchestration. The contribution pipeline, baseline calibration, artifact contracts, and separate final evaluation are especially relevant to FrontierML.', 'https://labs.scale.com/rsi-benchmark',repo,gpu='Task-specific; 1–4 H100 GPUs in released samples',time='Task-specific (see individual task.toml)',count=4,coverage='All 4 released sample task instructions and resource specifications. The call for 50 contributions is a target, not 50 accepted tasks. Proposal PRs and test fixtures are excluded.',tags=['AI R&D','post-training','data','artifact grading'])
for f in sorted((ROOT/'repos'/repo/'samples').glob('*/instruction.md')):
    rel=str(f.relative_to(ROOT/'repos'/repo));spec=tomllib.loads(f.with_name('task.toml').read_text());s=f.read_text();meta=spec.get('metadata',{});gpu,clock=resources(spec,s)
    add_t(bid,f.parent.name,f.parent.name.replace('-',' ').title(),meta.get('taxonomy','AI R&D'),spec['task']['description'],licensed_instructions(s,repo,rel,'MIT'),link(repo,rel),instructionType='source',gpu=gpu,timeBudget=clock,constraints=lines_matching(s,r'fixed|must not|do not|budget|only',6),submission=section(s,'submit|deliverable|output|artifact'),evaluation=meta.get('metric',section(s,'evaluat|judg|scor')),tags=spec['task'].get('keywords',[]),sources=[source('Agent instructions',link(repo,rel)),source('Task configuration',link(repo,rel.replace('instruction.md','task.toml'))),source('MIT license',link(repo,'LICENSE'))])

# RSI-Exam: preserve public/private distinction, and source-site vs HF aliases.
bid='rsi-exam'; repo='aiming-lab/RSI-Exam'
add_b(bid,'RSI-Exam','AIMING Lab','Research suites','Long-horizon executable research with a final hidden-set test.','Each assignment asks an agent to improve an inherited executable method or a harness around a frozen model. A research phase exposes development feedback; a separate verifier evaluates the submitted artifact on hidden data. The catalog spans AI, systems, physical science, optimization, life science, and professional domains. Private entries expose titles and brief catalog descriptions, not downloadable tasks.','https://rsi-exam.ai/',repo,gpu='Per task: CPU-only, GPU, and TPU assignments; inspect individual instructions',time='Up to 12 hours at suite level; task instructions may set shorter budgets',count=88,coverage='All 88 official catalog titles: 35 public and 53 private. All 35 public instruction.md and task.toml files were retrieved from the MIT-licensed Hugging Face release. Private records expose catalog metadata only; no hidden instructions are invented. Some public task instructions and runtime timeout declarations differ and both are shown.',tags=['hidden evaluation','long horizon','methods','harnesses'])
aliases={'2048_strategy':'game2048_policy_search','bbo_noisy_continuous_v1':'bbo_noisy_continuous','bbo_simopt_inventory_v1':'bbo_simopt_inventory','vggt_multiview_dense_reconstruction':'multiview_dense_reconstruction','gate_sizing':'eda_gate_sizing','ahc066_macro_controller':'warehouse_robot_macro_routing','cellflux_rxrx1':'perturbed_cell_morphology_generation'}
catalog=BeautifulSoup((ROOT/'exam_tasks.html').read_text(),'html.parser');status='public'
for card in catalog.select('.cardsplit,a.tcard'):
    if 'cardsplit' in card.get('class',[]):status=card['data-status'];continue
    slug=card['data-task-id']; name=card.h3.get_text(' ',strip=True);brief=card.select_one('.ts').get_text(' ',strip=True);category=card.select_one('.tg').get_text(' ',strip=True);url='https://rsi-exam.ai/tasks/'+slug+'.html'
    hfslug=aliases.get(slug,slug);base=ROOT/'hf'/hfslug
    if status=='public' and (base/'instruction.md').exists():
        s=(base/'instruction.md').read_text();spec=tomllib.loads((base/'task.toml').read_text());gpu,clock=resources(spec,s);hf='https://huggingface.co/datasets/RSI-Exam/RSI-Exam/blob/main/'+hfslug+'/'
        ins=s+'\n\n---\n\nSource: [RSI-Exam public task instruction]('+hf+'instruction.md). Reproduced under the [MIT license](https://huggingface.co/datasets/RSI-Exam/RSI-Exam/blob/main/LICENSE).'
        add_t(bid,slug,name,category,brief,ins,url,instructionType='source',gpu=gpu,timeBudget=clock,constraints=lines_matching(s,r'budget|must not|do not|offline|fixed|only',7),submission=section(s,'what you submit|submission|output|artifact'),evaluation=spec.get('scoring',{}).get('metric',section(s,'judg|scor|evaluat')),sources=[source('Official task page',url),source('Public instructions',hf+'instruction.md'),source('Task configuration',hf+'task.toml')],tags=[category,'public task'])
    else:
        ins=f'## Published catalog entry\n\n{name}\n\n{brief}.\n\n## Availability\n\nThis assignment belongs to the 53-task private partition. The official catalog publishes its title and scope, but does not provide an accessible instruction file, resource specification, executable environment, submission contract, or grader for this task. The research and evaluation protocol is described at the suite level. Task-specific GPU and time limits are not specified publicly.\n\n[View the official task catalog](https://rsi-exam.ai/tasks.html).'
        add_t(bid,slug,name,category,brief,ins,'https://rsi-exam.ai/tasks.html',instructionType='unavailable',access='private',tags=[category,'private catalog entry'])

# OpenRSI has 15 advertised entries, including a catalog-only DataComp task.
repo='OpenRSI-Foundation/OpenRSI-Index';bid='openrsi-index'
add_b(bid,'OpenRSI Index','OpenRSI Foundation','Research suites','Improve established model-development recipes across scales.','The Index wraps existing research codebases as measurable improvement environments. It includes data and architecture choices, post-training, retrieval, robotics, agent methods, and GPU kernels, plus large-scale signature projects. Entries differ in maturity: runnable public tasks, signature experiments, and advertised work must be distinguished when planning reproductions.','https://index.openrsi.foundation/index.html',repo,gpu='Released entries range from 0 GPUs for a data-contract wrapper to 256 H100 GPUs; inspect task-specific allocations and original-research context separately.',time='Task-specific; several public environments allow multi-day runs',count=15,coverage='All 15 advertised README entries. Fourteen have task.toml/instruction.md packages in the inspected commit; datacomp-small-filtering is advertised but its package is absent. Signature entries are identified in tags, not counted as ordinary validated public tasks.',tags=['AI R&D','pretraining','post-training','ML systems'])
for line in read(repo,'README.md').splitlines():
    if not line.startswith('| [`'):continue
    cells=[x.strip() for x in line.strip('|').split('|')];m=re.search(r'\[`([^`]+)`\]\((rsi-tasks/[^)]+)/\)',cells[0])
    if not m:continue
    name,folder=m.groups();slug=folder.split('/')[-1];s=read(repo,folder+'/instruction.md');gpu=cells[4];clock=UNKNOWN;url=link(repo,folder+'/instruction.md') if s else link(repo,'README.md')
    if s:
        spec=tomllib.loads(read(repo,folder+'/task.toml'));_,clock=resources(spec,s,gpu);instructions=licensed_instructions(s,repo,folder+'/instruction.md','Apache-2.0');typ='source'
    else:
        spec={};instructions=f'## Advertised task\n\n{name}: {cells[3]}\n\nThe official README lists {gpu}. No corresponding task directory, instructions, baseline, or evaluator was present in the inspected source snapshot. Treat this as a catalog entry awaiting a published task package. The exact selection budget, training timeout, submission schema, and scoring protocol are not specified in the available catalog.';typ='unavailable'
    add_t(bid,slug,name,cells[2],cells[3],instructions,url,instructionType=typ,gpu=gpu,timeBudget=clock,constraints=lines_matching(s,r'fixed|must not|do not|budget|only',6),submission=section(s,'submit|deliverable|output|artifact'),evaluation=section(s,'evaluat|judg|scor'),tags=[cells[1],cells[2]]+(['catalog only'] if not s else []),sources=[source('Task catalog',link(repo,'README.md'))]+([source('Instructions',url),source('Resource specification',link(repo,folder+'/task.toml'))] if s else []))

# AI4AI exact frozen task packages.
repo='Einsia/AI4AI-Bench';bid='ai4ai-bench'
add_b(bid,'AI4AI-Bench','Einsia / AI4AI-Bench authors','Model development','Redesign training algorithms in ten existing research repositories.','The agent edits a working training recipe during a four-hour exploration phase. Only a source patch is transferred to a fresh formal training environment, which runs for up to twelve hours and exports at most three checkpoints. Frozen validation and final evaluation measure the learned result, separating exploratory success from reproducibility.','https://lab.einsia.ai/ai4ai/',repo,'https://arxiv.org/abs/2608.20318',gpu='1 × NVIDIA B300 per official run',time='4 hours exploration + up to 12 hours formal retraining; evaluator timeout is separate',count=10,coverage='All 10 task packages, full agent instructions, pinned model/data identities, metrics, and resource specifications. Public release supports self-hosted evaluation; no official blind evaluation service is claimed.',tags=['training algorithms','fresh retraining','source patch'])
for f in sorted((ROOT/'repos'/repo/'tasks').glob('*/instruction.md')):
    rel=str(f.relative_to(ROOT/'repos'/repo));spec=tomllib.loads(f.with_name('task.toml').read_text());s=f.read_text();meta=spec.get('metadata',{});gpu,_=resources(spec,s)
    add_t(bid,f.parent.name,spec['task']['description'],'Training algorithm',spec['task']['description'],licensed_instructions(s,repo,rel,'Apache-2.0'),link(repo,rel),instructionType='source',gpu=gpu,timeBudget='4 hours exploration; 12 hours formal retraining; final evaluation has its own timeout',constraints=lines_matching(s,r'fixed|must not|do not|budget|only',7),submission='Source patch; a fresh formal retraining run emits up to three eligible checkpoints.',evaluation=meta.get('final_metric',UNKNOWN)+(' — '+meta['final_gate'] if 'final_gate' in meta else ''),tags=[meta.get('shipped_method','training'),meta.get('base_model','')],sources=[source('Agent instructions',link(repo,rel)),source('Task specification',link(repo,rel.replace('instruction.md','task.toml')))])

# Evolvent's six researcher-task profiles, not their downstream evaluation items.
repo='evolvent-ai/RSIBench-Data';bid='rsibench-data'
add_b(bid,'RSIBench-Data','Evolvent AI','Model development','Synthetic-data research with a fixed post-training backend.','A research agent creates training data, launches LoRA supervised fine-tuning, examines evaluation feedback, and selects a target-model checkpoint. Tinker runs training and sampling; Harbor evaluation executes in E2B sandboxes. Profiles lock the downstream scaffold and metric so changes can be attributed to data research.','https://rsibench.co/data/',repo,'https://arxiv.org/abs/2607.25886',gpu='Managed Tinker training/sampling; no fixed local GPU allocation specified',time='Configured wall-clock and Tinker spend limits; README examples use 4 hours and $25',count=6,coverage='All 6 published benchmark profiles and spec.json contracts. These are 6 data-research assignments, not 519 independent research tasks: downstream SWE/terminal/QA/math evaluation instances are not expanded. Example budgets are labeled as examples.',tags=['synthetic data','LoRA','fixed backend','checkpoint selection'])
for f in sorted((ROOT/'repos'/repo/'benchmarks').glob('*/spec.json')):
    j=json.loads(f.read_text());name=j.get('display_name',j['name']);rel=str(f.relative_to(ROOT/'repos'/repo));n=j['official_eval']['n_tasks'];attempts=j['official_eval'].get('n_attempts',1);metric=j.get('primary_metric',UNKNOWN)
    desc=f'Improve the fixed target model on {name} by developing a better post-training data strategy.'
    ins=f'## Research assignment\n\n{desc} The published profile uses {j["harbor_agent"]} as its evaluation harness. Training and serving remain under the shared Tinker backend; research changes concern data generation and selection.\n\n## Iterative workflow\n\nDiagnose model weaknesses using the allowed feedback, prepare new grounded training records, validate the dataset, submit LoRA SFT jobs, and evaluate the resulting checkpoints. Compare candidates within the configured wall-clock and spend ceilings, then retain the strongest valid checkpoint as the final artifact. Benchmark examples and evaluation outputs must not be repurposed as training records.\n\n## Profile and measurement\n\n- Official dataset: `{j["harbor_dataset"]}`.\n- Evaluation instances: {n}; attempts per instance: {attempts}.\n- Allowed seed factories: {", ".join(j.get("seed_factories",[]))}.\n- Primary metric: `{metric}`.\nThis reading guide paraphrases the profile. [Open the complete source configuration]({link(repo,rel)}) for the locked evaluation and serving contract. The repository carries a CC BY-NC 4.0 notice; its prompts and code are linked rather than reproduced here.'
    add_t(bid,j['target_benchmark'],name,'Data-centric post-training',desc,ins,link(repo,rel),gpu='Tinker-managed target-model training and sampling; GPU type/count not specified',timeBudget='Session-configured; 4 hours/$25 in README examples',constraints=['Target model and training/evaluation stack are controlled.','Do not derive training records from benchmark items or evaluation artifacts.','Honor the configured wall-clock and Tinker cost budgets.'],submission='Final selected Tinker sampler checkpoint and its training-data artifacts.',evaluation=f'{metric}; {n} downstream instances, {attempts} attempt(s) each',tags=[j.get('task_family',''),j.get('harbor_agent','')],sources=[source('Profile specification',link(repo,rel)),source('Research protocol',link(repo,'README.md'))])

# Datology's three base-model research settings; four metrics are a joint suite.
bid='curatebench';url='https://www.datologyai.com/blog/datasmith'
add_b(bid,'CurateBench','DatologyAI','Model development','Improve a model by changing only its SFT data.','CurateBench measures data curation under a fixed optimizer, training recipe, and evaluation suite. Every trained model is evaluated jointly across mathematics, coding, and tool use, making mixture quality and capability tradeoffs visible. The public DataSmith report describes three base-model settings and compares research harnesses on them.','https://www.datologyai.com/blog/datasmith',gpu='8 × H100 for each training submission (reported recipe)',time='Up to 20 training submissions; no total research-time cap',count=3,coverage='All 3 reported base-model settings. AIME2025, GSM8K, HumanEval, and BFCL are joint outcome evaluations, not four separate curation tasks. Public report only; no runnable task packages or full agent prompts were found.',tags=['data selection','synthetic data','mixtures','report only'])
for model in ['Qwen3-1.7B-Base','Qwen3-4B-Base','SmolLM3-3B-Base']:
    objective=f'Develop SFT data that improves {model} across the joint evaluation suite.'
    ins=f'## Published experimental setting\n\n{objective}\n\nThe research agent chooses and prepares training records; model identity and optimization settings stay fixed. It can combine retrieved datasets with synthetic examples. Candidate data must pass evaluation-overlap checks.\n\nEach submission trains for 350 steps with global batch 64, sequence length 16,384, and learning rate 1e-5: approximately 367 million tokens. Up to 20 candidate training runs are allowed. Success is measured jointly on AIME2025, GSM8K, HumanEval, and BFCL. The public description provides the research setup, not the complete executable agent prompt.'
    add_t(bid,model.lower().replace('.','-'),model+' — reported model configuration','Data curation',objective,ins,url,gpu='8 × H100 per training submission',timeBudget='20 submissions maximum; research wall time uncapped',constraints=['Only training data may change.','Fixed SFT recipe and evaluation suite.','Training records must be decontaminated.'],submission='Training dataset',evaluation='Aggregate performance across AIME2025, GSM8K, HumanEval, and BFCL',tags=['reported model configuration','not a downloadable task'])

# Exact YAML configs; Pro includes published smoke/development variants.
for bid,repo,prefix,name,reported in [('curation-bench','feiyang-k/curation-bench','','Curation-Bench',8),('curation-bench-pro','Jiachen-T-Wang/curation-bench-pro','curation-bench/','Curation-Bench Pro',5)]:
    pro=bool(prefix)
    add_b(bid,name,'Curation-Bench authors' if not pro else 'Jiachen T. Wang / Curation-Bench Pro','Model development','Select data under a fixed training and evaluation pipeline.','An agent receives a raw pool, base model, and selection budget. It submits a dataset subset; the controlled harness trains and evaluates the resulting model, then provides feedback for another curation iteration. '+('The Pro extension separates agent and train/eval containers and adds text, code, and SWE settings to the original vision-language tasks.' if pro else 'The original suite varies the vision-language model, source pool, and subset size while evaluating eight vision benchmarks.'),'https://github.com/'+repo,repo,'https://arxiv.org/abs/2606.04261' if not pro else '',gpu='Task/profile-specific NVIDIA GPU; 7B targets need at least 24 GB in original README' if not pro else 'Task/profile-specific Slurm GPU allocation; README launcher example requests one GPU',time='No per-iteration strategy timeout in original full configs' if not pro else 'Per task configuration and Slurm allocation',count=reported,coverage='All 8 published task YAMLs and exact selection/model/evaluation configurations.' if not pro else 'All 5 published full task families, with exact task YAMLs. Ten additional smoke/development configurations are linked inside related readers rather than counted as separate tasks.',tags=['data selection','fixed training']+(['Slurm'] if pro else ['vision-language']))
    pro_full={'llava665k_llava_8bench_10k_judge','lessmix_llama2_2bench','tulu3_olmo2_1b_devsuite','opencode_qwen1.5b_code4bench','swe_traj_qwen7b_verified'}
    for f in sorted((ROOT/'repos'/repo/(prefix+'src/benchmark/tasks')).glob('*.yaml')):
        if pro and f.stem not in pro_full:continue
        j=yaml.safe_load(f.read_text());q=j.get('task',j);slug=q.get('task_id',f.stem);rel=str(f.relative_to(ROOT/'repos'/repo));goal=clean(q.get('goal',slug));model=q.get('model_key',q.get('model_name_or_path',UNKNOWN));dataset=q.get('dataset',{}).get('dataset_id',UNKNOWN);train=q.get('training_config',{});clock=q.get('strategy_timeout_seconds');ev=q.get('target_evals',[])
        title=f'{dataset} → {model} · {q.get("target_rows",UNKNOWN):,} rows' if isinstance(q.get('target_rows'),int) else slug.replace('_',' ')
        ins=f'## Task objective\n\n{goal}\n\n## Controlled curation loop\n\nInspect the supplied pool and implement a selection policy in the editable curation workspace. Produce the requested subset with the required schema, run the audit, and submit it through the benchmark CLI. The harness trains the fixed base model using the prescribed recipe and evaluates the checkpoint. Use the returned feedback to revise the selection policy. Do not alter the protected training or evaluation implementation.\n\n## Exact published task configuration\n\n```yaml\n{f.read_text().strip()}\n```\n\nConfiguration source: [{rel}]({link(repo,rel)}), [Apache-2.0 license]({link(repo,"LICENSE")}).'
        hw=f'{train.get("num_processes")} training process(es); GPU model/memory allocation is profile-specific' if train.get('num_processes') else 'Not specified in task YAML; use the declared Slurm/profile allocation'
        if pro:
            family=slug.split('_')[0]
            variants=[v for v in sorted(f.parent.glob('*.yaml')) if v.stem not in pro_full and v.stem.startswith(family+'_')]
            if variants:ins+='\n\n## Related smoke/development configurations\n\nThese are configuration variants of this family, not separate research tasks.\n\n'+'\n'.join('- ['+v.stem+']('+link(repo,str(v.relative_to(ROOT/'repos'/repo)))+')' for v in variants)
        add_t(bid,slug,title,'Data curation',goal,ins,link(repo,rel),instructionType='source',gpu=hw,timeBudget=(f'{clock} seconds per curation iteration' if clock else 'No per-iteration strategy timeout')+f'; training timeout {train.get("timeout_seconds",UNKNOWN)} seconds',constraints=[f'Selection size: {q.get("target_rows",UNKNOWN)} rows.',f'Fixed model: {model}.',f'Raw pool: {dataset}.','Training and evaluator are controlled by the harness.'],submission=q.get('default_submission_dir','A curated dataset subset in the schema required by the task'),evaluation=', '.join(ev) if isinstance(ev,list) else str(ev),tags=[dataset,model,'full configuration'],sources=[source('Exact task YAML',link(repo,rel)),source('Benchmark protocol',link(repo,'docs/reference/benchmark-protocol.md' if pro else 'BENCHMARK.md'))])

# FT-Dojo: original 13 paper tasks, excluding extra adapters now in the repo.
repo='microsoft/RD-Agent';bid='ft-dojo';paper='https://arxiv.org/abs/2603.01712'
add_b(bid,'FT-Dojo','Microsoft Research / FT-Dojo authors','Model development','Autonomous domain fine-tuning with data preparation and iterative feedback.','FT-Dojo supplies a shared raw-data repository, isolated execution, training tools, validation feedback, and final held-out evaluation. The research agent must turn imperfect source data into useful training examples, choose a training configuration, run experiments, and diagnose failures. The original evaluation contains thirteen tasks over five domains.','https://proceedings.mlr.press/v306/li26jl.html',repo,paper,gpu='1 × NVIDIA B200 in the paper’s reported experiments',time='12 hours end to end in reported experiments',count=13,coverage='All 13 original paper tasks. The current RD-Agent README also lists AIME24 and four biology adapters; those extensions are not silently counted as original FT-Dojo tasks. Instructions here are task-specific reading guides based on the paper and source adapter descriptions.',tags=['fine-tuning','data processing','domain adaptation'])
dojo=[('aime25','AIME 2025','Mathematics','Solve competition mathematics with exact integer answers','deepscaler','Accuracy'),('panorama_par4pc','Prior Art Retrieval','Patent examination','Identify prior patents cited as grounds for rejecting a claim','panorama','Accuracy and Macro-F1'),('panorama_noc4pc','Novelty Classification','Patent examination','Classify claims as allowed, lacking novelty, or obvious','panorama','Accuracy and Macro-F1'),('panorama_pi4pc','Paragraph Identification','Patent examination','Identify the prior-art paragraph relevant to a claim rejection','panorama','Accuracy'),('chemcotbench_mol_und','Molecular Understanding','Chemistry','Infer chemical properties, functional groups, scaffolds, and molecular equivalence from SMILES','chemcot','MAE and Tanimoto similarity'),('chemcotbench_mol_edit','Molecule Editing','Chemistry','Apply requested functional-group changes to molecular structures','chemcot','Accuracy and Tanimoto similarity'),('chemcotbench_mol_opt','Molecule Optimization','Chemistry','Improve requested molecular properties while respecting scaffold constraints','chemcot','Success rate and valid ratio'),('chemcotbench_reaction','Reaction Prediction','Chemistry','Predict reaction products, conditions, and plausible mechanisms','chemcot','FTS and BLEU'),('FinanceIQ_gen','Financial QA','Finance','Answer Chinese financial examination questions requiring quantitative and domain reasoning','financeiq','Accuracy'),('tablebench_data_analysis','Data Analysis','Table QA','Analyze correlations, forecasts, and statistical patterns in tables','tableinstruct','Accuracy'),('tablebench_fact_checking','Fact Checking','Table QA','Decide whether statements are supported by table entries','tableinstruct','Exact match'),('tablebench_numerical_reasoning','Numerical Reasoning','Table QA','Compute arithmetic and comparisons over tabular data','tableinstruct','Accuracy'),('tablebench_visualization','Visualization','Table QA','Generate working Python visualizations from tables and chart requests','tableinstruct','Pass@1 and execution correctness rate')]
scenarios_path='rdagent/app/finetune/llm/job/scenarios.json'
scenario_data=json.loads(read(repo,scenarios_path))
for slug,name,domain,goal,dataset,metric in dojo:
    ins=f'## Research objective\n\nFine-tune the target language model to improve {name.lower()} in the {domain.lower()} domain. The downstream requirement is: {goal.lower()}.\n\n## Available starting point\n\nThe reported experiment starts from Qwen2.5-7B-Instruct and draws raw material from `{dataset}` in the shared repository. Inspect the data, construct suitable input/output training records, and create a LLaMA-Factory configuration. The source interface expects Alpaca-style instruction, input, and output fields.\n\n## Experiment loop\n\nCheck generated data and configuration before launching the full training job. Train a candidate, inspect validation results and failure cases, and revise the data or training approach within the remaining budget. Use validation feedback for iteration; the test split is reserved for final reporting.\n\n## Evaluation and budget\n\nThe task reports {metric}. The paper uses one NVIDIA B200 and a twelve-hour end-to-end limit, including preparation, training, evaluation, and agent interaction. These are suite-level experimental settings, not a separate per-task GPU declaration.\n\nThis is a task-specific summary of the paper and released interface, not a verbatim original agent prompt.'
    if slug in scenario_data:
        ins+='\n\n## Official task-specific input description\n\n'+scenario_data[slug]['benchmark_description']+'\n\nSource: [RD-Agent scenario registry]('+link(repo,scenarios_path)+'), MIT licensed. This is the complete registry description, alongside the summarized research protocol above.'
    add_t(bid,slug,name,domain,goal,ins,paper,instructionType='summary',gpu='1 × B200 (suite-level reported experimental setting)',timeBudget='12 hours end to end (suite-level reported setting)',constraints=['Keep training, validation, and final test roles separate.','Generated training data must follow the validated schema.','The reported baseline caps each training experiment at 2,000 examples; larger-budget ablations are separate.'],submission='Fine-tuned target model checkpoint and experiment artifacts.',evaluation=metric,tags=[domain,dataset,'original paper task'],sources=[source('Paper and task table',paper),source('Released interface',link(repo,'rdagent/app/finetune/llm/README.md')),source('Scenario descriptions',link(repo,scenarios_path))])

# TREX / FT-Bench exact task.json metadata, summarized rather than copied.
repo='trex-project/ftbench';bid='ft-bench'
add_b(bid,'FT-Bench','TREX project','Model development','Ten requirements-driven LLM fine-tuning assignments.','FT-Bench asks research agents to improve a base language model for concrete domains and capabilities. Each task JSON identifies the objective, data descriptions, base model, data allowance, GPU count, and core metric. TREX is the associated research agent, not the benchmark itself. The repository provides a common evaluation interface.','https://github.com/trex-project/ftbench',repo,'https://arxiv.org/abs/2604.14116',gpu='Task JSONs each allow 4 GPUs; GPU type and memory are not specified there',time='Not specified in the retrieved task JSONs',count=10,coverage='All 10 published task.json files. Task objectives and resource/metric facts are summarized; original JSONs are linked. A GPU count is not treated as evidence of a particular accelerator type.',tags=['fine-tuning','task requirements','target model'])
ftnames={'aci':('Clinical note generation','Medicine','Turn consultation dialogue into structured clinical documentation.'),'csbench':('Computer-science knowledge and reasoning','Computer science','Improve multilingual computer-science knowledge and reasoning answers.'),'econlogicqa':('Economic logical reasoning','Economics','Improve logical sequence reasoning in economic and business scenarios.'),'gta_tool':('Tool selection and use','Tool use','Train the model to choose and use tools appropriately.'),'hoc':('Hallmarks of Cancer classification','Medicine','Classify biomedical sentences by their cancer hallmarks using multiple labels.'),'lawbench':('Chinese legal capabilities','Law','Improve Chinese legal knowledge, understanding, and application.'),'omebench':('Organic reaction mechanism reasoning','Chemistry','Improve mechanistic reaction reasoning, intermediates, conditions, and electron-flow interpretation.'),'openfindata':('Financial-domain question answering','Finance','Improve financial analysis, compliance, calculations, and knowledge questions.'),'sst2':('Sentiment classification','Language understanding','Improve movie-review sentiment classification on SST-2.'),'tomgbench':('Instruction-conditioned molecular generation','Chemistry','Generate, edit, and optimize molecules while following chemical and SMILES constraints.')}
for f in sorted((ROOT/'repos'/repo/'ftbench/tasks').glob('*/task.json')):
    j=json.loads(f.read_text());slug=f.parent.name;name,domain,goal=ftnames[slug];rel=str(f.relative_to(ROOT/'repos'/repo));base=j.get('base_model',UNKNOWN);n=j.get('data_limit',UNKNOWN);metric=j.get('core_metric',UNKNOWN)
    ins=f'## Task objective\n\n{goal}\n\n## Target and resources\n\nStart from `{base}`. The published task permits {j.get("gpu_limit",UNKNOWN)} GPUs and a training-data allowance of {n} examples. Accelerator model, GPU memory, and a wall-clock cap are not specified in this task JSON.\n\n## Research work\n\nInspect the task-provided data descriptions and available training splits. Prepare examples and a fine-tuning strategy suited to the domain, run training experiments, and evaluate the resulting model through FT-Bench’s evaluation interface. Compare feedback and adjust the data or recipe. The source JSON contains detailed benchmark descriptions and dataset-format examples.\n\n## Required result\n\nSubmit a trained model accessible through the evaluation interface and optimize `{metric}`. Preserve separation between data used to train the model and the benchmark’s evaluation split.\n\nThis is a structured paraphrase; [open the original task.json]({link(repo,rel)}) for the complete source request and input examples.'
    add_t(bid,slug,name,domain,goal,ins,link(repo,rel),gpu=f'{j.get("gpu_limit",UNKNOWN)} GPUs; type and VRAM not specified',constraints=[f'Base model: {base}.',f'Training data limit: {n}.'],submission='Trained model served through the benchmark’s OpenAI-compatible evaluation interface.',evaluation=metric,tags=[domain,base],sources=[source('Task JSON',link(repo,rel)),source('Evaluation interface',link(repo,'README.md'))])

# Agent² RL: full common prompt plus original per-domain description.
repo='microsoft/RD-Agent';bid='agent2-rl-bench';basepath='rdagent/scenarios/rl/autorl_bench'
add_b(bid,'Agent² RL-Bench','Microsoft Research','Model development','Can an agent engineer an entire RL post-training pipeline?','Six assignments progress from rule-verified static tasks to judge-based optimization and interactive environments requiring trajectory collection. The research agent trains a target model, submits checkpoints through a grading API, and uses feedback within a fixed budget. Operating modes distinguish SFT, RL, unrestricted methods, and multi-agent research.','https://wanyichen06.github.io/agent2-rlbench/',repo,'https://arxiv.org/abs/2604.10547',gpu='Assigned GPU allocation is run-specific; paper case studies use one H200 (do not generalize to every task)',time='12 hours by default; run_meta.json is authoritative',count=6,coverage='All 6 released task descriptions plus the complete common agent instruction. GPU type is not hard-coded in the task description files. Additional Smith adapters are extensions, not part of the six-task reported suite.',tags=['RL post-training','online rollouts','SFT','grading API'])
common=read(repo,basepath+'/core/instructions.md')
rl={'gsm8k':('GSM8K','Level 1 · rule-based','Improve mathematical word-problem accuracy.','Exact-match answer accuracy'),'humaneval':('HumanEval','Level 1 · rule-based','Improve code-generation correctness.','Pass@1'),'alpacaeval':('AlpacaEval 2.0','Level 2 · judge-based','Improve instruction-following responses under a preference judge.','AlpacaEval score'),'alfworld':('ALFWorld','Level 3 · interactive','Improve a text-agent model for household interaction tasks.','Task success rate'),'webshop':('WebShop','Level 3 · interactive','Improve product-search and purchase behavior in a shopping environment.','WebShop evaluation score'),'deepsearchqa':('DeepSearchQA','Level 3 · interactive','Improve a model’s multi-step search and question-answering performance.','DeepSearchQA evaluation score')}
for slug,(name,level,goal,metric) in rl.items():
    path=basepath+'/benchmarks/'+slug+'/description.md';s=read(repo,path);ins='# '+name+' research task\n\n'+goal+'\n\n## Published task description (original language)\n\n'+s+'\n\n## Common agent instructions\n\n'+common
    ins=licensed_instructions(ins,repo,path,'MIT')
    add_t(bid,slug,name,level,goal,ins,link(repo,path),instructionType='source',gpu='Not specified in task description; choose only GPUs assigned to the run',timeBudget='12 hours by default; exact run budget in run_meta.json',constraints=['Work inside the isolated workspace.','Source data and base model are read-only.','Submit model paths under the output directory.','Use only allocated GPUs; run metadata controls the time budget.'],submission='Target model checkpoint directory submitted to POST /submit.',evaluation=metric,tags=[level,'post-training'],sources=[source('Task description',link(repo,path)),source('Common agent instructions',link(repo,basepath+'/core/instructions.md')),source('Paper','https://arxiv.org/abs/2604.10547')])

# Proprietary Vals tasks: restrained summaries with exact resource facts.
bid='vals-rsi-index';url='https://www.vals.ai/benchmarks/rsi_index'
add_b(bid,'Vals RSI Index','Vals AI','Research suites','Four measured campaigns in autonomous LLM development.','The Index covers lossless compression, language-model training, agent-harness engineering, and post-training. Agents run in their native coding harnesses under fixed resource budgets and submit one artifact. Scores compare outcomes with task-specific reference results; these references differ in origin and should not be read as a uniform human frontier. Public methodology is available, while the benchmark is proprietary.',url,gpu='Task-specific; see individual task cards',time='12–30 hours depending on task',count=4,coverage='All 4 current tasks. Concise methodology summaries and published resource facts are included; full proprietary prompts, datasets, and graders are not publicly distributed.',tags=['proprietary','AI R&D','reference anchored'])
vals=[('compression','Compression','Build a compact lossless representation of enwik8.','1 × H100; 8 CPU cores','24 hours','Sealed offline environment; exact byte reconstruction required.','Self-extracting compressed archive, including required runtime dependencies.','Total archive size in bits per byte.'),('lm-training','LM training','Develop a better language-model training recipe.','1 × H100 80GB; 24 accelerator-hours','24 hours research, last hour for packaging; three 30-minute final retrainings','Offline enwik9 splits: 800 MB training, 100 MB development, 100 MB test.','Reproducible training recipe.','Median BPB across three retrainings; 32,768 hidden windows.'),('harness-engineering','Harness engineering','Improve Gemini 3.5 Flash-Lite’s Vibe Code Bench judging workflow.','No local GPUs; hosted judge calls','12 hours','12 development apps; aggregate feedback only.','Agent harness.','Agreement over 205 substeps from 24 held-out apps; three runs.'),('post-training','Post-training','Adapt Qwen3.6-35B-A3B for finance-agent tasks.','2 nodes × 8 RTX PRO 6000 96GB GPUs','30 hours','27 public development examples; $100 external inference credits; derive checkpoint from the provided model.','Adapted checkpoint and generation settings.','Finance Agent v2 mean score across three runs on 126 held-out tasks.')]
for slug,name,goal,gpu,clock,limit,submission,evaluation in vals:
    ins=f'## Published task summary\n\n{goal}\n\nResources: {gpu}. Budget: {clock}.\n\n{limit}\n\nSubmission: {submission}\n\nMeasurement: {evaluation}\n\nThe complete proprietary prompt and verifier are not released; consult the official methodology for the current contract.'
    add_t(bid,slug,name,'Autonomous LLM R&D',goal,ins,url,gpu=gpu,timeBudget=clock,constraints=[limit],submission=submission,evaluation=evaluation,access='private',tags=['published methodology','proprietary task'])

# Important exceptions which must not be flattened into a catalog-level budget.
byid={t['id']:t for t in tasks}
t=byid['openrsi-index--post-training-qwen-122B-rl']
t.update(name='Qwen-122B-RL — released data-contract wrapper',summary='Produce a synthetic RL intervention dataset; the released wrapper checks structure only.',objective='Create 2,560 synthetic records across five domains while satisfying the released JSONL data contract.',gpu='0 GPUs for released wrapper; 256 × H100 describes the original research context only',evaluation='Binary structural JSONL validity; this wrapper does not train or measure model quality.',submission='/workspace/candidate/intervention.jsonl: 512 records in each of five domains.')
t['tags']+=['data-contract wrapper','no model-quality grading']
t=byid['openrsi-index--gpic_generation']
t.update(gpu='Published continuation: 4 × H100 per job. Legacy packaged task: 8 × H100.',timeBudget='Published continuation: 6,144 H100-hours per trajectory; 96-hour Claude research window. Legacy packaged candidate budget differs.',evaluation='Published continuation logs: matched FD-DINOv2 validation screens; no sealed 50k final score reported. Legacy package defines a separate 50k FD-DINOv2 evaluator.',submission='Legacy source prompt describes a trained text-to-image artifact; continuation logs retain checkpoints and validation screens.')
t['tags']+=['historical protocol mismatch','validation screens']
t=byid['openrsi-index--pre-training-optimizer-update-geometry']
t.update(gpu='256 × H100 outer allocation; individual ladder rungs use 8, 32, or 128 GPUs',timeBudget='72-hour allocation; 68-hour agent envelope',evaluation='Paloma micro/macro BPB and fixed-window training loss at declared scoring updates across six scales; novelty, reload, mechanism-ablation, and regression gates.',submission='One scale-general optimizer implementation plus required checkpoints and mechanism evidence.')
byid['rsi-exam--teacher_student_math_posttraining']['gpu']='2 GPUs × 48 GB VRAM (instruction); GPU model not specified'
byid['rsi-exam--teacher_student_math_posttraining']['timeBudget']='8 hours in instructions; 12-hour runtime timeout in task.toml'
byid['rsi-exam--clevr_cogent_grpo_qwen2vl']['gpu']='2 GPUs × 48 GB VRAM (instruction); GPU model not specified'
byid['rsi-exam--clevr_cogent_grpo_qwen2vl']['timeBudget']='8 hours in instructions; 12-hour runtime timeout in task.toml'
byid['rsi-exam--splash_attention_strata_speedup']['gpu']='TPU v6e chip (task instruction); not a GPU task'
byid['rsi-exam--protein_ligand_cofolding_posebusters']['gpu']='1 GPU (instruction); accelerator type not specified'

# Deliver the license texts alongside the source-bearing catalog.
license_repos=['scaleapi/rsi-benchmark','OpenRSI-Foundation/OpenRSI-Index','Einsia/AI4AI-Bench','microsoft/RD-Agent','feiyang-k/curation-bench','Jiachen-T-Wang/curation-bench-pro']
notices=['THIRD-PARTY SOURCE NOTICES\n\nFull task instructions and configuration excerpts in rsi.json retain their original licensing. Upstream model/data assets may have separate terms; none were downloaded.\n']
for r in license_repos:
    notices.append('\n\n'+r+'\n'+link(r,'LICENSE')+'\n\n'+read(r,'LICENSE'))
notices.append('\n\nRSI-Exam public task set\nhttps://huggingface.co/datasets/RSI-Exam/RSI-Exam/blob/main/LICENSE\n\n'+(ROOT/'hf/LICENSE').read_text())
license_path=OUT.parent.parent/'rsi-source-licenses.txt'
license_path.parent.mkdir(parents=True,exist_ok=True)
license_path.write_text('\n'.join(notices))

OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps({'benchmarks':benchmarks,'tasks':tasks},ensure_ascii=False,indent=2)+'\n')
from collections import Counter
print(f'Wrote {len(benchmarks)} benchmarks / {len(tasks)} task records to {OUT}')
print(json.dumps(Counter(t['benchmarkId'] for t in tasks),indent=2))
