#!/usr/bin/env python3
"""Fetch only public source/configuration text needed by ingest-ml-catalog.py.

Run: python3 scripts/fetch-ml-sources.py
Then: python3 scripts/ingest-ml-catalog.py
Dependencies: requests, PyYAML, beautifulsoup4.
No model weights, task datasets, or archive bundles are downloaded.
"""
from pathlib import Path
Path('/tmp/frontier-ml-catalog').mkdir(parents=True, exist_ok=True)
import requests,json,concurrent.futures,pathlib
repos=['METR/RE-Bench','aisa-group/PostTrainBench','GAIR-NLP/InnovatorBench','Anikethh/ResearchGym','yunx-z/MLRC-Bench','qrzou/FML-bench','openai/mle-bench','snap-stanford/MLAgentBench','facebookresearch/MLGym','chchenhui/mlrbench','MLE-Dojo/MLE-Dojo']
def get(repo):
 r=requests.get(f'https://api.github.com/repos/{repo}/git/trees/main?recursive=1',timeout=50); r.raise_for_status(); data=r.json(); pathlib.Path('/tmp/frontier-ml-catalog/'+repo.split('/')[-1]+'.tree.json').write_text(json.dumps(data)); return repo,data
for repo,data in concurrent.futures.ThreadPoolExecutor(8).map(get,repos):
 print(repo, len(data['tree']), 'tree entries', flush=True)

import json,pathlib,re,requests,concurrent.futures
root=pathlib.Path('/tmp/frontier-ml-catalog')
repos=['METR/RE-Bench','aisa-group/PostTrainBench','GAIR-NLP/InnovatorBench','Anikethh/ResearchGym','yunx-z/MLRC-Bench','qrzou/FML-bench','openai/mle-bench','snap-stanford/MLAgentBench','facebookresearch/MLGym','chchenhui/mlrbench','MLE-Dojo/MLE-Dojo']
patterns=[r'^ai_rd_.*/(README.md|manifest.yaml|ai_rd_.*.py)$',r'^src/eval/(general/(prompt.txt|get_prompt.py)|tasks/[^/]+/(benchmark.txt|info.json))$|^scripts/constants.py$|^src/commit_utils/set_env_vars.sh$|^src/harbor_adapter/adapter.py$',r'^research_gym/configs/tasks/.*yaml$',r'^tasks/test/[^/]+/(README.md|task_description.md)$|^tasks/paper_task_mapping.txt$',r'^MLAgentBench/benchmarks_base/[^/]+/scripts/research_problem.txt$|^MLAgentBench/constants.py$',r'^configs/tasks/|^ml_tasks/[^/]+/(prompt.json|config.json|baseline_results/final_info.json)$',r'^mlebench/competitions/[^/]+/(config.yaml|description.md)$|^experiments/(competition_categories.csv|splits/split75.txt)$|^environment/instructions.txt$',r'^MLAgentBench/benchmarks/[^/]+/scripts/research_problem.txt$',r'^configs/tasks/.*yaml$',r'^tasks/.*md$|^task_metadata.md$',r'^prepare/.*\.(json|txt)$|^mledojo/competitions/[^/]+/(info/description.txt|utils/metric.py)$|^config.yaml$']
items=[]
for repo,pat in zip(repos,patterns):
 name=repo.split('/')[-1]
 for x in json.loads((root/(name+'.tree.json')).read_text())['tree']:
  p=x['path']
  if x['type']=='blob' and (re.search(pat,p) or p in ['README.md','LICENSE']):items.append((repo,p))
def get(v):
 repo,p=v;dest=root/repo/p
 if not dest.exists():
  r=requests.get('https://raw.githubusercontent.com/'+repo+'/main/'+p,timeout=35);r.raise_for_status();dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(r.text)
 return v
with concurrent.futures.ThreadPoolExecutor(20) as pool:
 for i,res in enumerate(pool.map(get,items)):
  if i%100==0: print(i,'/',len(items),flush=True)
print('Downloaded',len(items))

# The small CC BY paper supplies all 20 InnovatorBench task summaries; its
# 69.7GB task workspace archive is intentionally not downloaded.
html=requests.get('https://arxiv.org/html/2510.27598v2',timeout=45)
html.raise_for_status()
(root/'innovator-paper.html').write_text(html.text)
