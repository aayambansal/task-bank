"""Selective, cached source retrieval for research benchmark catalog. No datasets fetched."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,urllib.request,subprocess,time
ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'.local/dashboard-research'
REPOS={
'frontierswe-v2':'Proximal-Labs/frontier-swe-v2','airs-bench':'facebookresearch/airs-bench','autoresearch-exam':'bespokelabsai/AutoResearchExam','mls-bench':'Imbernoulli/MLS-Bench','paperbench':'openai/frontier-evals','exp-bench':'Just-Curieous/Curie','scientist-bench':'HKUDS/AI-Researcher','mlreplicate':'gsasikiran/MLReplicate-benchmarking','scienceagentbench':'OSU-NLP-Group/ScienceAgentBench','llm-speedrunning':'facebookresearch/llm-speedrunner','kernelbench':'ScalingIntelligence/KernelBench','tritonbench':'thunlp/TritonBench','algotune':'oripress/AlgoTune','weirdml':'htihle/htihle.github.io'}
def api(path):
 r=subprocess.run(['gh','api',path],capture_output=True,text=True)
 if r.returncode: raise RuntimeError(r.stderr)
 return json.loads(r.stdout)
from functools import lru_cache
@lru_cache(maxsize=None)
def tree(key):
 p=CACHE/key/'tree.json';p.parent.mkdir(parents=True,exist_ok=True)
 if not p.exists():
  repo=api('repos/'+REPOS[key]);branch=repo['default_branch'];data=api('repos/'+REPOS[key]+'/git/trees/'+branch+'?recursive=1');data['branch']=branch;data['commit']=api('repos/'+REPOS[key]+'/commits/'+branch)['sha'];p.write_text(json.dumps(data))
 return json.loads(p.read_text())
def raw(key,path):
 p=CACHE/key/path
 if p.exists():return p.read_text(errors='replace')
 branch=tree(key)['branch'];url='https://raw.githubusercontent.com/'+REPOS[key]+'/'+branch+'/'+urllib.parse.quote(path)
 for attempt in range(3):
  try:
   val=urllib.request.urlopen(url,timeout=40).read().decode();p.parent.mkdir(parents=True,exist_ok=True);p.write_text(val);return val
  except Exception:
   if attempt==2:raise
   time.sleep(1)
def batch(key,paths):
 with ThreadPoolExecutor(max_workers=12) as pool:
  results=list(pool.map(lambda p:(p,raw(key,p)),paths))
 return dict(results)
if __name__=='__main__':
 def fetch(k):
  try:
   data=tree(k); print(k,len(data['tree']),data.get('truncated'),flush=True)
   base=[r['path'] for r in data['tree'] if r['type']=='blob' and '/' not in r['path'] and ('readme' in r['path'].lower() or 'license' in r['path'].lower())];batch(k,base)
  except Exception as e:print(k,'ERROR',str(e),flush=True)
 with ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(fetch,REPOS))
