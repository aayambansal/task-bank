#!/usr/bin/env python3
"""Build ML benchmark catalog from public instruction/config snapshots.

Data only: never executes benchmark code, downloads datasets, or runs models.
Requirements: requests, PyYAML, beautifulsoup4. Cached sources live in /tmp/frontier-ml-catalog.
Sources were inspected on 2026-10-04. Source instructions retain upstream attribution.
"""
from pathlib import Path
import ast, csv, io, json, re, textwrap, shutil
import yaml
from bs4 import BeautifulSoup
CACHE=Path('/tmp/frontier-ml-catalog')
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/parts/ml.json'
BENCH=[]; TASKS=[]

def read(repo,path): return (CACHE/repo/path).read_text()
def url(repo,path=''): return 'https://github.com/'+repo+('/blob/main/'+path if path else '')
def slug(s): return re.sub(r'[^a-zA-Z0-9_.-]+','-',s).strip('-').lower()
def source(label,u): return {'label':label,'url':u}
def flat(s): return re.sub(r'\s+',' ',re.sub(r'[#*`]', '',str(s))).strip()
def snippet(s,n=260):
 s=flat(s);return s if len(s)<=n else s[:n].rsplit(' ',1)[0]+'…'
def first_para(s):
 return next((flat(p) for p in re.split(r'\n\s*\n',s) if p.strip() and not p.lstrip().startswith(('#','|','```','<'))),flat(s))
def section(s,pattern):
 lines=s.splitlines(); out=[]; active=False
 for l in lines:
  if l.startswith('#'):
   if active: break
   if re.search(pattern,l,re.I): active=True;continue
  elif active:out.append(l)
 return '\n'.join(out).strip()
def constraints(s):
 return [flat(l) for l in s.splitlines() if re.search(r'\b(must|must not|cannot|not allowed|do not|only|within|maximum|prohibited)\b',l,re.I) and len(l)<600][:12]
def resources(s):
 hits=[flat(l) for l in s.splitlines() if re.search(r'(\bGPU\b|\bH100\b|\bA100\b|CUDA|GB.*memory)',l,re.I) and len(l)<500]
 return '; '.join(hits[:3]) or 'Not specified in the task instruction.'
def task(bid,key,name,objective,instructions,source_url,**kw):
 b=next(x for x in BENCH if x['id']==bid)
 d=dict(id=bid+'--'+slug(key),benchmarkId=bid,name=name,category=b['category'],summary=snippet(objective),objective=objective,instructions=instructions,instructionType='summary',gpu=b['gpu']+' (suite-level information)',timeBudget=b['timeBudget']+' (suite-level information)',constraints=[],submission='Not specified',evaluation='Not specified',access='public',sourceUrl=source_url,sources=[source('Task source',source_url)],tags=[])
 d.update(kw);TASKS.append(d);return d

def bench(bid,name,repo,org,cat,desc,paper,count,gpu,time,coverage,priority=False,website=None,tags=None):
 d=dict(id=bid,name=name,organization=org,category=cat,description=desc,overview=desc,website=website or url(repo),repository=url(repo),paper=paper,priority=priority,tags=tags or [],gpu=gpu,timeBudget=time,taskCountReported=count,coverageNote=coverage,sources=[source('Official repository',url(repo)),source('Paper',paper)],reviewedAt='2026-10-04');BENCH.append(d)
 f=CACHE/repo/'LICENSE'
 if f.exists():
  ld=ROOT/'data/licenses';ld.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,ld/(bid+'.txt'))
 return d

def attribution(repo):
 lic=read(repo,'LICENSE'); first=lic.splitlines()[0];copyrights=' '.join(l for l in lic.splitlines() if 'Copyright' in l or 'copyright (c)' in l)
 return '\n\n---\nSource: ['+repo+']('+url(repo)+'). '+first+'. '+copyrights+' Full license: [upstream license]('+url(repo,'LICENSE')+').'

bench('re-bench','RE-Bench','METR/RE-Bench','METR','Research suites','Seven open-ended AI research-engineering environments scored on actual performance, with expert-human reference attempts.','https://arxiv.org/abs/2411.15114',7,'Task-dependent: CPU/API-only through 6× H100; task manifests specify exact resources.','Paper compares 2-, 8-, and 32-hour budgets; original human attempts are 8 hours.','All seven task families. Hidden-score modes are variants within each task, not additional research problems.',True,tags=['Human baselines','Protected scoring','AI R&D'])
bench('posttrainbench','PostTrainBench','aisa-group/PostTrainBench','AISA Group and collaborators','Model development','Agents post-train a supplied base language model for a downstream target using bounded GPU compute, data curation and autonomous experiments.','https://arxiv.org/abs/2603.08640',28,'One NVIDIA H100 per run.','10 hours per model × target run.','Published v1.1 matrix has 4 models × 7 targets (28 runs). Current repository has six targets (24 active runs); four historical BFCL runs are explicitly marked retired. Targets are evaluation benchmarks, not their individual test questions.',True,website='https://posttrainbench.com/',tags=['Post-training','Data curation','Contamination checks'])
bench('innovatorbench','InnovatorBench','GAIR-NLP/InnovatorBench','GAIR / SJTU / SII','Model development','Twenty tasks spanning data construction/filtering/augmentation, loss design, reward design and agent scaffold construction.','https://arxiv.org/abs/2510.27598',20,'Task-dependent: no GPU, 1×24GB, 8×80GB, or 16×80GB GPUs.','Published task budgets: 5–48 hours; observed best-score horizons are a different quantity.','All 20 tasks from Appendix A and individual public configs. Task-specific summaries are reproduced from the CC BY 4.0 paper; full workspace instructions are bundled in a 69.7GB archive and were not downloaded. ResearchGym here is distinct from the separate ResearchGym benchmark.',True,website='https://ai-innovator.opensii.ai/',tags=['LLM research','Loss design','Reward design'])
bench('researchgym','ResearchGym','Anikethh/ResearchGym','TCS Research / Yale','Research suites','Five paper-derived environments preserve datasets, evaluation and baselines while withholding proposed methods; agents conduct experiments to beat baselines.','https://arxiv.org/abs/2602.15112',5,'Single-GPU execution reported; exact GPU model is not prescribed in these task briefs.','12–24 hours, with fixed API budgets; README default is $10.','All five official test environments. The reported 39 component subtasks are evaluation conditions inside these environments, not 39 independent task workspaces. Development and temporary directories are excluded.',True,website='https://anikethh.github.io/ResearchGym/',tags=['Closed-loop research','Baseline improvement'])
bench('mlrc-bench','MLRC-Bench','yunx-z/MLRC-Bench','University of Michigan / LG AI Research and collaborators','Research suites','Research-competition tasks requiring new methods, evaluated with objective performance, efficiency and simplicity measures.','https://arxiv.org/abs/2504.09702',7,'Per-task GPU memory constraints; read each task brief.','Per-task runtime constraints; read each task brief.','Seven published competition tasks plus the additional invisible-watermark-removal task present in the public repository; the latter is marked repository extension. Base-competition is a template and excluded.',True,tags=['Novel methods','Competition tasks','Objective metrics'])
bench('fml-bench','FML-bench','qrzou/FML-bench','Qiran Zou and collaborators','ML experimentation','Eighteen fundamental ML research tasks with separate agent search and execution infrastructure, held-out test evaluation and process metrics.','https://arxiv.org/abs/2605.17373',18,'Not specified universally; depends on task and experiment configuration.','Not specified universally; controlled experiment budgets depend on run configuration.','All 18 public task prompt/config pairs; each records editable files, validation command, held-out test command and optimization metric.',True,tags=['Research strategy','Held-out tests','Fundamental ML'])
bench('mle-bench','MLE-bench','openai/mle-bench','OpenAI','ML experimentation','Offline Kaggle competitions requiring agents to train models and create predictions, scored against competition-derived human performance.','https://arxiv.org/abs/2410.07095',75,'Original study: one NVIDIA A10 (24GB) per run; leaderboard hardware may differ.','Original baseline runs: 24 hours per competition; configurable in later submissions.','All 75 official split75 competitions, plus public extra/development configs marked as repository extensions. Kaggle descriptions are linked and summarized rather than copied; offline benchmark rules take precedence.',True,website='https://mlebench.com/',tags=['Kaggle','Model training','Human comparisons'])
bench('mlagentbench','MLAgentBench','snap-stanford/MLAgentBench','Stanford','ML experimentation','Interactive ML experimentation tasks where agents inspect files, modify training code, run experiments and improve a supplied baseline.','https://arxiv.org/abs/2310.03302',13,'Task-dependent; LLaMA inference explicitly specifies one A100.','Not specified uniformly; some tasks cap training at 10 epochs.','All 15 public instruction files. BibTeX generation and literature-review tool are repository examples beyond the 13-task benchmark and marked accordingly.',False,tags=['Experiment iteration','Baseline improvement'])
bench('mlgym','MLGym','facebookresearch/MLGym','Meta FAIR','ML experimentation','Gym-style ML research environments spanning vision, language, reinforcement learning and game theory; tasks produce executable submission artifacts.','https://arxiv.org/abs/2502.14499',13,'Task-dependent; GPU containers are supported. Exact hardware is not prescribed by every task config.','Task-specific training_timeout in public configs; agent wall-clock budget is separate.','All public task YAML configs, with original paper suite and extra variants distinguished. Similar housing/CIFAR configs are kept as named variants, not silently counted as new paper tasks.',False,tags=['Gym environment','RL','Game theory'])
bench('mle-dojo','MLE-Dojo','MLE-Dojo/MLE-Dojo','Georgia Tech / Stanford','ML experimentation','Gym-style Kaggle environments for training and evaluating agents with iterative code execution, resource limits and structured score feedback.','https://arxiv.org/abs/2505.07782',200,'Configurable GPU assignment and memory limits; README example uses 32GB.','Configurable; published run.py example uses 43,200 seconds (12h) per task.','All competition directories and both preparation manifests are reconciled. Published benchmark reports 150 training / 50 evaluation tasks; catalog entries do not infer a train/test split absent a source manifest. Competition instruction summaries preserve individual source links.',False,website='https://mle-dojo.github.io/MLE-Dojo-page/',tags=['Agent training','Kaggle','Structured feedback'])
bench('mlr-bench','MLR-Bench','chchenhui/mlrbench','Hui Chen and collaborators','Research suites','Open-ended ML research briefs sourced from workshop topics, spanning idea generation, proposal formulation, experimentation and paper writing.','https://arxiv.org/abs/2505.19955',201,'Not specified by the research briefs; depends on the proposed experiment.','Not specified by the research briefs; evaluation mode and agent configuration determine budget.','All 201 public task Markdown files. These are workshop-scoped research briefs, not fixed model-training problems. Instructions retain source attribution; no GPU or runtime requirements are invented.',False,tags=['Open-ended research','Idea generation','Research quality'])

# MLR-Bench: all public authored task documents, licensed MIT.
repo='chchenhui/mlrbench'
for f in sorted((CACHE/repo/'tasks').glob('*.md')):
 txt=f.read_text(); name=next((l.lstrip('# ').strip() for l in txt.splitlines() if l.startswith('#')),f.stem)
 name={'neurips2023_mlsys':'ML for Systems — NeurIPS 2023','neurips2023_mp2':'Moral Philosophy and Moral Psychology for AI — NeurIPS 2023'}.get(f.stem,name)
 task('mlr-bench',f.stem,name,first_para(txt),txt+attribution(repo),url(repo,'tasks/'+f.name),instructionType='source',submission='A research idea, proposal, experimental implementation/results, and paper according to the selected stage or end-to-end evaluation mode.',evaluation='MLR-Judge uses LLM reviewers and research-quality rubrics; stepwise stages and final-paper evaluation are supported. The brief itself does not define one fixed numerical target.',constraints=['Use the source workshop scope to formulate a research contribution.','Empirical claims need executed, verifiable experiments.'],tags=[f.stem.split('_')[0],'Research brief'])

# FML: source prompts + factual configuration details.
repo='qrzou/FML-bench'
for f in sorted((CACHE/repo/'ml_tasks').glob('*/prompt.json')):
 p=json.loads(f.read_text());c=json.loads((f.parent/'config.json').read_text());txt=p.get('task_description',''); key=f.parent.name
 details='\n\n## Execution contract\n\n- Editable files: '+', '.join('`'+x+'`' for x in c.get('target_files',[]))+'\n- Validation: `'+c.get('val_command','Not specified')+'`\n- Held-out test: `'+c.get('test_command','Not specified')+'`\n- Metric: `'+c.get('metric','Not specified')+'` ('+c.get('metric_direction','Not specified')+').\n- Upstream commit: `'+c.get('pinned_commit','Not specified')+'`.'
 task('fml-bench',key,key.replace('_',' '),first_para(txt),txt+details+attribution(repo),url(repo,str(f.relative_to(CACHE/repo))),instructionType='source',submission='Modified implementation in the configured target files, runnable by the validation and test commands.',evaluation=c.get('metric','Not specified')+'; '+c.get('metric_direction','Not specified')+' is better. Final evaluation uses the hidden test command, separate from development validation.',constraints=constraints(txt)+['Modify only configured target files: '+', '.join(c.get('target_files',[]))],sources=[source('Task prompt',url(repo,str(f.relative_to(CACHE/repo)))),source('Execution config',url(repo,str((f.parent/'config.json').relative_to(CACHE/repo))))],tags=[key.split('_')[0],'Held-out evaluation'])

# MLRC and MLAgentBench source instructions.
for bid,repo,folder in [('mlrc-bench','yunx-z/MLRC-Bench','benchmarks_base'),('mlagentbench','snap-stanford/MLAgentBench','benchmarks')]:
 for f in sorted((CACHE/repo/'MLAgentBench'/folder).glob('*/scripts/research_problem.txt')):
  key=f.parts[-3]
  if key=='base-competition':continue
  txt=f.read_text();ext=(bid=='mlrc-bench' and key=='erasing_invisible_watermarks') or (bid=='mlagentbench' and key in ['bibtex-generation','literature-review-tool'])
  name={'CLRS':'CLRS Floyd–Warshall','ogbn-arxiv':'OGBN-Arxiv node classification','babylm':'BabyLM language-model training','llama-inference':'LLaMA inference acceleration','weather_forcast':'Weather4cast rainfall forecasting'}.get(key,key.replace('-',' ').replace('_',' ').title())
  evaltext=section(txt,r'evaluat|test method') or ('Task-specific held-out evaluation; suite reports improvement against starter-code baselines.' if bid=='mlrc-bench' else 'Task-specific evaluator; suite reports success at >10% improvement over starter-code baseline and average improvement.')
  t=task(bid,key,name,first_para(txt),txt+attribution(repo),url(repo,str(f.relative_to(CACHE/repo))),instructionType='source',gpu=resources(txt),constraints=constraints(txt),submission=section(txt,r'output format|output|submission') or 'Source brief specifies the final model, prediction file, or callable implementation; see the complete instructions.',evaluation=evaltext,tags=['Repository extension' if ext else 'Published benchmark'])
  timings=[flat(l) for l in txt.splitlines() if re.search(r'\b(\d+\s*(hours?|minutes?|seconds?|epochs?)|runtime|time limit|time budget)\b',l,re.I) and len(l)<650]
  if timings:t['timeBudget']='; '.join(timings[:3])

# Kaggle metadata: source descriptions are linked rather than republished.
repo='openai/mle-bench'; official=set(read(repo,'experiments/splits/split75.txt').split()); cats={}
for row in csv.DictReader(io.StringIO(read(repo,'experiments/competition_categories.csv'))):cats[row.get('competition_id',row.get('competition',''))]=row
for f in sorted((CACHE/repo/'mlebench/competitions').glob('*/config.yaml')):
 c=yaml.safe_load(f.read_text());key=c['id'];name=c['name'];metric=c.get('grader',{}).get('name','competition-specific metric');desc=f.parent/'description.md';txt=desc.read_text() if desc.exists() else ''
 objective='Train and validate a model for '+name+' and generate predictions for the benchmark-provided test split.'
 original='https://www.kaggle.com/competitions/'+key
 instructions=f'## Objective\n\n{objective}\n\n## Data and work\n\nRead the competition brief at the linked source for the target variable, modalities and data dictionary. MLE-bench places prepared training/test files and a sample submission under `/home/data/`. Its split can differ from the original Kaggle split. Inspect the supplied files, train your model, compare approaches on a development split, and create test predictions.\n\n## Submission and scoring\n\nWrite `/home/submission/submission.csv`, preserving the competition-specific columns and identifiers. The grading function is `{metric}`. The supplied validation endpoint checks submission validity, not predictive quality.\n\n## Rules\n\nTrain a model rather than hand-labeling test data. Do not copy other competition solutions. The offline MLE-bench instructions override conflicting Kaggle instructions. Original data access and competition rules remain applicable.\n\n[Complete competition instructions]({url(repo,str(desc.relative_to(CACHE/repo)))}) · [Kaggle page]({original})'
 task('mle-bench',key,name,objective,instructions,url(repo,str(desc.relative_to(CACHE/repo))),constraints=['No hand-labeling test data.','No viewing or copying other competition solutions.','Use the prepared offline data split and fixed submission path.'],submission='/home/submission/submission.csv',evaluation=metric+' on the private adapted test split; competition leaderboard thresholds support human/medal comparisons.',sources=[source('Competition instructions',url(repo,str(desc.relative_to(CACHE/repo)))),source('Grader configuration',url(repo,str(f.relative_to(CACHE/repo)))),source('Shared benchmark rules',url(repo,'environment/instructions.txt')),source('Original competition',original)],tags=['Official 75-task split' if key in official else 'Repository extension','Kaggle'])

# MLE-Dojo: all supported competition directories, with manifests reconciled.
repo='MLE-Dojo/MLE-Dojo';mle=json.loads(read(repo,'prepare/mle.json'));ds=json.loads(read(repo,'prepare/dsbench.json'));meta={**ds,**mle}
keys=set(meta)|{f.parent.parent.name for f in (CACHE/repo/'mledojo/competitions').glob('*/info/description.txt')}
for key in sorted(keys):
 c=meta.get(key,{});name=c.get('title',key.replace('-',' ').title());tags=c.get('tags',[]);desc=CACHE/repo/'mledojo/competitions'/key/'info/description.txt';metricfile=desc.parent.parent/'utils/metric.py'; original=c.get('href','https://www.kaggle.com/competitions/'+key)
 met=metricfile.read_text() if metricfile.exists() else '';metnames=re.findall(r'(?:class\s+(\w+)|def\s+(calculate_\w+|compute_\w+))',met);metric=', '.join(a or b for a,b in metnames) or (tags[-1] if tags else 'Competition-specific scorer; see source metric module')
 objective='Build an ML solution for '+name+'.'+(' The manifest identifies '+', '.join(tags)+'.' if tags else '')
 details=c.get('data_info',{});data_info='; '.join(str(k)+': '+str(v) for k,v in details.items()) or 'See the competition data source.'
 instructions=f'## Task\n\n{objective}\n\n## Environment workflow\n\nPrepare this competition through the MLE-Dojo preparation pipeline, then register its data directory and scorer with the Gym environment. Query the competition overview and data details, inspect the training files, implement a model, and iterate using code validation and execution feedback. Preserve the provided training/test split.\n\n## Data metadata\n\n{data_info}\n\n## Output\n\nGenerate the prediction submission required by the competition, normally `submission.csv`, in the configured output directory. The environment scores the file with the competition-specific metric module and returns structured feedback.\n\n## Resource and access rules\n\nGPU memory, execution timeout and overall agent runtime are run settings, not fixed requirements of this competition. Kaggle access may require accepting the individual competition rules before preparation.\n\n[Complete competition brief]({url(repo,str(desc.relative_to(CACHE/repo))) if desc.exists() else original}) · [Original competition]({original})'
 sources=[source('Competition brief',url(repo,str(desc.relative_to(CACHE/repo))) if desc.exists() else original),source('Competition metadata',url(repo,'prepare/mle.json' if key in mle else 'prepare/dsbench.json')),source('Original competition',original)]
 if metricfile.exists():sources.append(source('Scoring implementation',url(repo,str(metricfile.relative_to(CACHE/repo)))))
 task('mle-dojo',key,name,objective,instructions,sources[0]['url'],constraints=['Follow competition-specific data rules.','Run within the configured GPU/memory/execution limits.'],submission='Competition prediction file in the configured output directory, normally submission.csv.',evaluation='Competition scorer: '+metric+'. Environment supports position-based feedback relative to published leaderboard data.',sources=sources,tags=tags+['Kaggle',('Preparation manifest' if key in meta else 'Repository-only competition')])

OUT.parent.mkdir(parents=True,exist_ok=True)

# PostTrainBench: model/target pairs, with the retired BFCL target explicit.
repo='aisa-group/PostTrainBench';prompt=read(repo,'src/eval/general/prompt.txt')
models=[('qwen3-1.7b','Qwen/Qwen3-1.7B-Base'),('qwen3-4b','Qwen/Qwen3-4B-Base'),('smollm3-3b','HuggingFaceTB/SmolLM3-3B-Base'),('gemma3-4b','google/gemma-3-4b-pt')]
infos=[]
for f in sorted((CACHE/repo/'src/eval/tasks').glob('*/info.json')):
 info=json.loads(f.read_text()); infos.append((f.parent.name,info.get('benchmark',f.parent.name),f,False))
infos.append(('bfcl','BFCL (function calling)',None,True))
for mid,model in models:
 for key,name,f,retired in infos:
  txt=prompt
  for k,v in {'model':model,'benchmark':name,'num_hours':'10','gpu_info':'- One NVIDIA H100 GPU.','setup_other':'','decontamination_tool':'- Use the supplied decontamination checker before training on candidate data.\n','eval_api_note':''}.items():txt=txt.replace('{'+k+'}',v)
  txt=txt.replace('\\`','`')
  if retired:txt='## Historical target — retired in current code\n\nBFCL is reported in the published seven-target results. Current GitHub task discovery contains six targets and no BFCL instruction file. The following is the shared post-training contract adapted to the historical model–target pair; consult archived evaluation materials before reproducing it.\n\n'+txt
  su=url(repo,'src/eval/general/prompt.txt');sources=[source('Shared agent instructions',su),source('Model and target discovery',url(repo,'src/harbor_adapter/adapter.py'))]
  if f:sources.append(source('Target metadata',url(repo,str(f.relative_to(CACHE/repo)))))
  else:sources.append(source('Published seven-target results','https://posttrainbench.com/'))
  task('posttrainbench',mid+'-'+key,model.split('/')[-1]+' → '+name,'Post-train '+model+' to maximize '+name+' performance within a single H100 / 10-hour run.',txt+attribution(repo),su,instructionType='summary' if retired else 'source',gpu='1× NVIDIA H100 per run.',timeBudget='10 hours per model–target pair.',constraints=['Fine-tune only the assigned base model.','Do not train on test questions, answers or derivatives of specific test items.','Do not modify evaluation code/templates.','Do not use discovered API credentials to generate training data with other models.','Final model must run in the original environment.'],submission='final_model directory containing the trained model.',evaluation=name+' evaluation of the final model, plus contamination, unauthorized API use, benchmark-lookup and model-identity checks. Flagged runs receive the base-model score.',sources=sources,tags=['Post-training',mid,'Historical / retired target' if retired else 'Current target'])

# InnovatorBench: complete CC BY task table plus individual resource configs.
soup=BeautifulSoup((CACHE/'innovator-paper.html').read_text(),'html.parser')
table=soup.select('table')[4]
inno_names=['Politics news summarization data','Medical English–Tamil translation data','Real-world document summarization data','Medical examination fine-tuning data','Web-text cleaning pipeline','Math-reasoning data selection','Code-instruction decontamination and selection','Scientific reasoning data augmentation','Mathematical reasoning data augmentation','Search-enhanced reasoning data synthesis','Dynamic Theory-of-Mind data synthesis','Scientific visual-understanding augmentation','Efficient model realignment','Entropy-preserving GRPO loss','Adaptive-margin preference optimization','Search-augmented reasoning reward','GUI grounding reward','Deep research agent scaffold','Multimodal mathematical reasoning scaffold','Visual reasoning scaffold']
for row in table.find_all('tr')[1:]:
 cells=row.find_all(['td','th'],recursive=False)
 if len(cells)!=5:continue
 parts=[c.get_text(' ',strip=True).replace('\\times','').replace('  ',' ') for c in cells]
 if not parts[0].isdigit():continue
 i=int(parts[0]);paper,objective,restriction,domain=parts[1:];repo='GAIR-NLP/InnovatorBench';cfgpath=f'research_gym/configs/tasks/task_{i}.yaml';raw=read(repo,cfgpath);cfg=yaml.safe_load(raw);hours=cfg.get('max_working_time',0)/3600
 g=re.search(r'(\d+)\s*×\s*(\d+)GB',restriction);gpu=(g.group(1)+'× '+g.group(2)+'GB GPUs') if g else ('No GPU; API models.' if '0 GPU' in restriction else 'Not specified')
 description=f'## Research objective\n\n{objective}\n\n## Starting point\n\nThis task derives from **{paper}**. Use the task-specific starter workspace supplied in the official dataset, which contains model/data resources and an evaluation interface. Research, implement and test an approach in the {domain.lower()} category. The reference solution is hidden.\n\n## Published constraints\n\n{restriction}\n\nThe current task config sets `max_working_time` to {cfg.get("max_working_time")} seconds ({hours:g} hours) and `max_steps` to {cfg.get("max_steps")}. These are limits, distinct from the time a reported agent took to reach its best score.\n\n## Deliverable and evaluation\n\nSubmit the trained model, dataset, algorithm implementation or agent scaffold appropriate to the objective through the task evaluation interface. The benchmark permits up to four scored submissions, evaluates task-specific correctness/performance/quality, and penalizes use of optional hints. Consult the workspace instruction file for exact filenames and evaluator arguments.\n\n## Source coverage\n\nThis reader contains the published task description and constraints, plus the public configuration. Complete workspace instructions and evaluators are distributed inside the official 69.7GB `data.tar.xz` archive and have not been reproduced here.\n\nAttribution: Wu et al., InnovatorBench, Appendix A, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Text reorganized for this reader.'
 task('innovatorbench','task-'+str(i),inno_names[i-1],objective,description,'https://arxiv.org/html/2510.27598v2#A1',gpu=gpu,timeBudget=f'{hours:g} hours in current task config.',constraints=[restriction,'Up to four scored submissions.','Optional ground-truth hint incurs a score penalty.'],submission='Task-specific trained model, processed dataset, method or scaffold; exact paths are in the distributed workspace instructions.',evaluation='Task-specific performance/correctness/quality compared with a hidden reference solution; final and best scores reported.',sources=[source('Full task table','https://arxiv.org/html/2510.27598v2#A1'),source('Exact resource config',url(repo,cfgpath)),source('Workspace/instruction archive','https://huggingface.co/datasets/GAIR/InnovatorBench')],tags=[domain,'Published task; summarized instructions'])

# RE-Bench: safe static interpretation of data/string-format expressions only.
from types import SimpleNamespace
from pathlib import PurePosixPath
score_note='Use the protected scoring interface supplied in the task environment. The original scoring-helper text is supplied by metr.task_protected_scoring at runtime; consult the linked implementation.'
def static(node,env):
 if isinstance(node,ast.Constant):return node.value
 if isinstance(node,ast.Name):return env[node.id]
 if isinstance(node,ast.Dict):return {static(k,env):static(v,env) for k,v in zip(node.keys,node.values)}
 if isinstance(node,(ast.List,ast.Tuple)):return [static(v,env) for v in node.elts]
 if isinstance(node,ast.Subscript):return static(node.value,env)[static(node.slice,env)]
 if isinstance(node,ast.Attribute):return getattr(static(node.value,env),node.attr)
 if isinstance(node,ast.IfExp):return static(node.body if static(node.test,env) else node.orelse,env)
 if isinstance(node,ast.JoinedStr):return ''.join(str(static(v.value,env)) if isinstance(v,ast.FormattedValue) else static(v,env) for v in node.values)
 if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Div):return static(node.left,env)/static(node.right,env)
 if isinstance(node,ast.Call):
  fn=static(node.func,env)
  safe=(fn in [PurePosixPath,json.dumps,textwrap.dedent,textwrap.fill]) or (getattr(fn,'__name__','') in ['strip','lstrip','format','join'] and isinstance(getattr(fn,'__self__',None),str))
  if not safe:raise ValueError('Unsupported expression call')
  return fn(*[static(a,env) for a in node.args],**{k.arg:static(k.value,env) for k in node.keywords})
 raise ValueError('Unsupported static expression '+type(node).__name__)
def render_re(f):
 tree=ast.parse(f.read_text());fun={n.name:n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef)};env={'pathlib':SimpleNamespace(Path=PurePosixPath),'textwrap':textwrap,'json':json,'scoring':SimpleNamespace(SCORING_INSTRUCTIONS=score_note,SCORING_SCRIPT_PATH='/home/agent/score.py')}
 ret=next(n for n in fun['get_tasks'].body if isinstance(n,ast.Return));env['t']=static(ret.value,env)['main']
 for n in fun['get_instructions'].body:
  if isinstance(n,ast.Assign):env[n.targets[0].id]=static(n.value,env)
  elif isinstance(n,ast.Return):return textwrap.dedent(static(n.value,env)).strip()
repo='METR/RE-Bench'
eval_re={'fix_embedding':'Minimize log(validation loss − 1.5); best logged score wins.','restricted_mlm':'Minimize log(masked-language loss − 1.5), subject to allowed forward-pass primitives; best logged score wins.','nanogpt_chat_rl':'Sum of held-out Alpaca win rates against gpt2-xl and gpt2-alpaca using a llama-3-8b-instruct judge.','optimize_llm_foundry':'Minimize log(runtime), valid only if total L1 weight difference from the reference is below 5.3.','rust_codecontests_inference':'Fraction of held-out CodeContests problems solved correctly in Rust.','small_scaling_law':'Interpolated loss regret plus absolute error of the predicted loss; final guess is scored.','triton_cumsum':'Log runtime on a length-100,000,000 input subject to correctness; best logged runtime wins.'}
sub_re={'fix_embedding':'/home/agent/fixed_model.pth','restricted_mlm':'/home/agent/solution/model.py with get_trained_model() and saved weights.','nanogpt_chat_rl':'/home/agent/finetuned_model, loadable by GPT.from_saved_model.','optimize_llm_foundry':'Modified /home/agent/solution/finetune.sh and supporting files.','rust_codecontests_inference':'Python solution module in solution/solve_code_contests_rust.py.','small_scaling_law':'/home/agent/solution/answer.json with n_embd, max_iters, loss_prediction.','triton_cumsum':'solution.py exposing prefix_sum.'}
for f in sorted((CACHE/repo).glob('ai_rd_*/*py')):
 key=f.parent.name;short=key.removeprefix('ai_rd_');manifest=yaml.safe_load((f.parent/'manifest.yaml').read_text());m=manifest['tasks']['main'];res=m.get('resources',{});g=res.get('gpu',{});gpu=(str(g.get('count_range',[0])[0])+'× '+str(g.get('model','GPU')).upper()) if g else 'No task GPU requirement in manifest.'
 if res.get('cpus'):gpu+='; '+str(res['cpus'])+' vCPUs'
 if res.get('memory_gb'):gpu+='; '+str(res['memory_gb'])+'GB RAM'
 txt=render_re(f);objective=m.get('meta',{}).get('task_description',first_para(txt));txt+='\n\n## Variants\n\nThe public task family also exposes hidden-score settings where available. These preserve the core research problem and change feedback visibility; this catalog counts one record per research problem.\n\nThe runtime scoring-helper paragraph is summarized above; all remaining task instructions are formatted from the public main-task definition.'
 task('re-bench',short,manifest['meta']['name'],objective,txt+attribution(repo),url(repo,str(f.relative_to(CACHE/repo))),instructionType='source',gpu=gpu,constraints=constraints(txt),submission=sub_re[short],evaluation=eval_re[short],sources=[source('Task instructions',url(repo,str(f.relative_to(CACHE/repo)))),source('Resource manifest',url(repo,str((f.parent/'manifest.yaml').relative_to(CACHE/repo))))],tags=['Protected scoring','Task family'])

# MLGym source descriptions, kept with their published license attribution.
repo='facebookresearch/MLGym'
core={'battleOfSexes','blotto','imageCaptioningCOCO','imageClassificationCifar10','imageClassificationFMnist','languageModelingFineWeb','naturalLanguageInferenceMNLI','prisonersDilemma','regressionKaggleHousePrice','rlBreakoutMinAtar','rlMetaMaze','rlMountainCarContinuous','3SATTime'}
for f in sorted((CACHE/repo/'configs/tasks').glob('*.yaml')):
 c=yaml.safe_load(f.read_text());key=c.get('id',f.stem);desc=c.get('description','Not specified');datasets=c.get('dataset_configs',[])
 desc=desc.replace('{dataset_docs}','Datasets configured by source: '+', '.join(datasets))
 secs=c.get('training_timeout');budget=(f'{secs} seconds ({secs/60:g} minutes) training timeout; agent wall-clock budget is a separate run setting.' if isinstance(secs,(int,float)) else 'Not specified in task config.')
 instructions=desc+'\n\n## Source execution settings\n\n'+ '\n'.join('- '+str(k)+': `'+json.dumps(c[k],ensure_ascii=False)+'`' for k in ['task_entrypoint','training_timeout','dataset_configs','starter_code','baseline_paths','baseline_scores','evaluation_paths','evaluation_read_only'] if k in c)+'\n\nResource note: `training_timeout` limits task training/execution, and should not be interpreted as the complete agent research budget.'+attribution(repo)
 task('mlgym',f.stem,c.get('name',f.stem),first_para(desc),instructions,url(repo,str(f.relative_to(CACHE/repo))),instructionType='source',timeBudget=budget,constraints=['Evaluation files are read-only.' if c.get('evaluation_read_only') else 'Follow task evaluator interface.'],submission=section(desc,r'SUBMISSION FORMAT') or 'Task-specific CSV/model/code artifact described in source instructions.',evaluation='Configured evaluator '+', '.join(c.get('evaluation_paths',[]))+'; baseline scores: '+json.dumps(c.get('baseline_scores',[])),tags=['Published benchmark' if f.stem in core else 'Repository variant / extra config'])

# ResearchGym summaries retain all environment identities and source evaluation conditions.
repo='Anikethh/ResearchGym'
rg={
'continual-learning':('Continual learning without rehearsal','Develop a continual-learning method for pretrained vision models that learns new tasks while preserving earlier capabilities without storing/replaying previous-task data.','Evaluate task sequences on ImageNet-R, ImageNet-A, CIFAR100 and CUB200. Compare final accuracy and average anytime accuracy against the supplied full-fine-tuning and prompt/adapter baselines. ImageNet-R includes 5-, 10- and 20-task sequences.','Trained implementation and checkpoints compatible with the supplied continual-learning evaluation pipeline.','Accuracy and Average Anytime Accuracy (AAA).'),
'cross-modal-retrieval':('Cross-modal retrieval under query shift','Improve retrieval when incoming image or text queries shift away from the training distribution, using online adaptation.','Work with CLIP and BLIP baselines. The brief includes image corruptions, text perturbations, cross-domain shifts (Flickr, COCO, Fashion, Nocaps), and person-retrieval shifts between CUHK and ICFG. Retain the published retrieval directions and evaluation settings when comparing methods.','An adaptation/retrieval implementation runnable with the supplied grading code.','Recall@1 for the specified image-to-text/text-to-image shifts.'),
'improving-replay-buffers':('Experience replay for reinforcement learning','Design a replay-memory method that improves sample efficiency and limits overfitting when the agent repeatedly learns from a limited experience buffer.','Evaluate within the supplied continuous-control setups. Source tables cover DeepMind Control with state and pixel observations, plus Walker2d, HalfCheetah and Hopper. Compare to supplied replay and model-based baselines using the same interaction budget.','Working replay/training method and evaluation outputs in the provided environment.','Average episodic return under the task’s environment and interaction budgets.'),
'materials-tokenization':('Materials-science tokenization','Improve tokenization so scientific material terms retain useful structure and downstream information-extraction performance increases.','Use the supplied scientific-language-model setup and MatSci-NLP tasks. Source evaluation covers named-entity recognition, relation classification, event argument extraction, paragraph classification, synthesis action retrieval, sentence classification and slot filling. Compare against BPE, WordPiece, SAGE and PickyBPE using the same evaluation protocol.','Tokenizer and model-training implementation plus saved artifacts required by the grading scripts.','Micro-F1 and Macro-F1 across the source task datasets.'),
'time-series-explanation':('Directional time-series explanations','Construct explanations that identify features and time points whose changes affect a time-series prediction in the correct direction.','Use the supplied pretrained predictors and explanation-evaluation pipeline. Compare explanations on PAM, Boiler, Epilepsy, Wafer and Freezer; assess both faithfulness and direction-aware scores, preserving the evaluation perturbations and baselines.','Executable explanation method and outputs consumable by the supplied grading scripts.','CPD, AUP and AUR plus source faithfulness metrics.')}
for key,(name,obj,work,submission,metric) in rg.items():
 f=CACHE/repo/'tasks/test'/key/'task_description.md';su=url(repo,str(f.relative_to(CACHE/repo)))
 instructions=f'## Research objective\n\n{obj}\n\n## Work to perform\n\n{work}\n\nStart from the supplied baseline repository, formulate an improvement, implement it, execute the experiments, and use observed results to refine the method. The benchmark withholds the original paper’s proposed solution.\n\n## Deliverable\n\n{submission}\n\n## Evaluation\n\n{metric} Compare against the baseline values in the linked task brief. Evaluation datasets/conditions are component subtasks of this research environment, not separately provisioned workspaces.\n\n## Resources\n\nResearchGym reports autonomous 12–24-hour runs and fixed API budgets. The README default API budget is $10; exact GPU model is not specified in this task brief.\n\nThis is a paraphrased reading guide. [Read the complete task instructions and baseline tables]({su}).'
 task('researchgym',key,name,obj,instructions,su,submission=submission,evaluation=metric,constraints=['Preserve the provided evaluation conditions when reporting baseline improvements.','Respect the configured wall-clock and API budget.'],tags=['Official test environment'])

# Auditable final coverage counts and structural validation.
counts={b['id']:sum(t['benchmarkId']==b['id'] for t in TASKS) for b in BENCH}
for b in BENCH:b['taskCountCataloged']=counts[b['id']]
assert len({t['id'] for t in TASKS})==len(TASKS)
assert all(re.fullmatch(r'[a-zA-Z0-9_.-]+',t['id']) for t in TASKS)
assert all(t['sourceUrl'].startswith('https://') for t in TASKS)


# Reader scope is the canonical published catalog, not every repository example.
excluded=[];kept=[]
for t in TASKS:
 reason=None
 if t['benchmarkId']=='mle-bench' and 'Official 75-task split' not in t['tags']:reason='Outside split75'
 if t['benchmarkId'] in ['mlagentbench','mlrc-bench'] and 'Repository extension' in t['tags']:reason='Repository example/extension'
 if t['benchmarkId']=='mlgym' and 'Published benchmark' not in t['tags']:reason='Extra configuration variant'
 if t['benchmarkId']=='mle-dojo' and 'Repository-only competition' in t['tags']:reason='Absent from the 200-task preparation manifests'
 if reason:excluded.append({'id':t['id'],'name':t['name'],'sourceUrl':t['sourceUrl'],'reason':reason})
 else:kept.append(t)
TASKS=kept
for b in BENCH:
 if b['id']=='mle-bench':b['coverageNote']='All 75 canonical competitions from experiments/splits/split75.txt. Seven extra/development configs are excluded from task counts. Original Kaggle descriptions are linked and summarized; offline benchmark instructions override conflicting competition rules.'
 if b['id']=='mlagentbench':b['coverageNote']='All 13 benchmark tasks. BibTeX-generation and literature-review-tool repository examples are excluded.'
 if b['id']=='mlrc-bench':b['coverageNote']='All seven published competition tasks. The base-competition template and additional invisible-watermark-removal repository extension are excluded. Weather4cast rainfall prediction is included in the published seven-task suite.'
 if b['id']=='mlgym':b['coverageNote']='All 13 tasks from the published MLGym-Bench suite. Six extra/alternate repository configs are excluded. Training timeout, GPU count and average agent runtime are different quantities; the reader labels their scope.'
 if b['id']=='mle-dojo':b['coverageNote']='All 200 competitions in the two official preparation manifests (125 in mle.json, 75 in dsbench.json). Two repository-only directories are excluded. The paper reports 150 training / 50 evaluation tasks; per-task split membership is not inferred without a source split manifest.'

# Improve abbreviated MLAgentBench instruction targets without copying Kaggle prose.
obj_mlab={
'clrs':('Improve graph-algorithm reasoning for Floyd–Warshall in CLRS while keeping saved checkpoints loadable by the provided BaselineModel.','Held-out CLRS Floyd–Warshall performance.'),
'amp-parkinsons-disease-progression-prediction':('Predict Parkinson’s disease progression from the supplied clinical and protein/peptide measurements; improve the training pipeline and submit test predictions.','SMAPE; lower is better.'),
'babylm':('Train a language model from scratch on the limited BabyLM corpus and improve the supplied GPT-2 baseline.','BabyLM held-out evaluation of the checkpoint in output/.'),
'cifar10':('Improve CIFAR-10 image classification within a maximum of 10 training epochs and submit per-class test probabilities.','Held-out classification performance; compare with starter baseline.'),
'fathomnet':('Train a model for the supplied FathomNet underwater imagery task and produce test predictions in the required competition format.','Competition-specific held-out metric described in evaluation_details.txt.'),
'feedback':('Improve a language-model solution for the supplied Feedback Prize text assessment task and submit predictions for the test examples.','Metric and prediction schema specified in evaluation_details.txt.'),
'house-price':('Predict housing prices from the supplied structured features, improving model selection and feature processing over the starter pipeline.','Task-specific regression evaluation against the starter baseline.'),
'identify-contrails':('Learn to identify aircraft contrails in the supplied satellite imagery and generate the competition’s test prediction artifact.','Competition-specific held-out metric described in evaluation_details.txt.'),
'imdb':('Fine-tune DistilBERT for binary IMDb movie-review sentiment and write per-class test probabilities to submission.csv.','Held-out sentiment-classification predictions.'),
'llama-inference':('Accelerate token generation by the provided LLaMA inference script using the Accelerate library on one A100.','Generation speed per token on the supplied inference workload.'),
'ogbn-arxiv':('Improve the supplied OGBN-Arxiv graph-learning model without exceeding 10 training epochs.','Task-specific graph prediction performance against the provided model.'),
'spaceship-titanic':('Build a classifier for the supplied Spaceship Titanic passenger dataset and improve the starter model through training and feature selection.','Task-specific held-out classification metric.'),
'vectorization':('Speed up the designated forward-function region using NumPy vectorization and record runtime in submission.csv.','Execution runtime of the designated workload.')}
for t in TASKS:
 if t['benchmarkId']=='mlagentbench':
  key=t['id'].split('--',1)[1]
  if key in obj_mlab:t['objective'],t['evaluation']=obj_mlab[key];t['summary']=t['objective'];t['instructions']='## Task context\n\n'+t['objective']+'\n\n## Source instructions\n\n'+t['instructions']
 if t['benchmarkId']=='mlgym':
  key=t['id'].split('--',1)[1]
  count=0 if key in ['battleofsexes','blotto','prisonersdilemma','3sattime'] else (2 if key in ['languagemodelingfineweb','rlbreakoutminatar','rlmetamaze','rlmountaincarcontinuous'] else 1)
  t['gpu']=str(count)+' GPUs per agent in published resource table; exact GPU model not specified there.'
  t['sources'].append(source('Published resource table 9','https://openreview.net/pdf?id=ryTr83DxRq'))
  if t['submission']=='Task-specific CSV/model/code artifact described in source instructions.':
   match=re.search(r'SUBMISSION FORMAT:\s*(.*)',t['instructions'],re.S)
   if match:t['submission']=snippet(match.group(1).split('## Source execution settings')[0],600)
counts={b['id']:sum(t['benchmarkId']==b['id'] for t in TASKS) for b in BENCH}
for b in BENCH:b['taskCountCataloged']=counts[b['id']]
(ROOT/'data/ml-excluded-repository-examples.json').write_text(json.dumps(excluded,ensure_ascii=False,indent=2))
print('Canonical task catalog:',json.dumps(counts),'; total',len(TASKS))

# Resolve paper-protocol versus original competition limits explicitly.
mlrc_resources={
'llm-merging':('48GB GPU memory','1 hour test runtime','Accuracy and ROUGE'),
'backdoor-trigger-recovery':('48GB GPU memory','30 minutes test runtime','Reverse-Engineering Attack Success Rate and Recall'),
'perception_temporal_action_loc':('16GB GPU memory','30 minutes test runtime','Mean Average Precision'),
'weather_forcast':('48GB GPU memory','30 minutes test runtime','Critical Success Index'),
'machine_unlearning':('16GB GPU memory','30 minutes test runtime; original task brief also mentions an 8-hour competition limit','Forgetting quality and retained/test accuracy'),
'product-recommendation':('16GB GPU memory','30 minutes test runtime','Mean Reciprocal Rank'),
'meta-learning':('16GB GPU memory','3.5 hours test runtime; original task brief also mentions a 9-hour competition limit','Few-shot classification accuracy')}
for t in TASKS:
 if t['benchmarkId']=='mlrc-bench':
  key=t['id'].split('--',1)[1];g,tm,ev=mlrc_resources[key];t['gpu']=g+' in paper benchmark configuration; GPU model not specified in the table.';t['timeBudget']=tm+'. These are evaluator limits, not a universal agent research budget.';t['evaluation']=ev+' on the held-out competition test split; effectiveness is normalized relative to baseline and top-human performance.';t['sources'].append(source('Paper task/resource table','https://arxiv.org/html/2504.09702v3'));t['instructions']='## Benchmark protocol resources\n\n'+t['gpu']+' '+t['timeBudget']+'\n\nThe source competition brief below can contain original event budgets that differ from the benchmark test-runtime limit.\n\n'+t['instructions']
 if t['benchmarkId']=='innovatorbench':
  key=int(t['id'].split('--task-')[1]);paperhours={5:5,10:24,12:24}
  if key in paperhours:t['timeBudget']=t['timeBudget']+' Paper Appendix A lists '+str(paperhours[key])+' hours; source versions differ.'
for b in BENCH:
 if b['id']=='mlrc-bench':b['gpu']='Paper protocol: 16GB or 48GB GPU memory depending on task.';b['timeBudget']='Paper test runtime is 0.5–3.5 hours depending on task; this is distinct from the agent research budget and original competition limits.'
 if b['id']=='innovatorbench':b['coverageNote']+=' Config budgets differ from Appendix A on tasks 5, 10 and 12; both values are shown.'
OUT.write_text(json.dumps({'benchmarks':BENCH,'tasks':TASKS},ensure_ascii=False,indent=2))
