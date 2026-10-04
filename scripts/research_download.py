from research_fetch import *
import re

def paths(k):return [x['path'] for x in tree(k)['tree'] if x['type']=='blob']
# MLS tree root exceeded GitHub recursive limit: task rendering is already complete before truncation; verify count, fetch source root separately.
r=api('repos/'+REPOS['mls-bench']+'/git/trees/main')
for name in ['tasks','harbor']:
 item=next(x for x in r['tree'] if x['path']==name)
 if name=='tasks':
  sub=api('repos/'+REPOS['mls-bench']+'/git/trees/'+item['sha']+'?recursive=1');(CACHE/'mls-bench/tasks-tree.json').write_text(json.dumps(sub))
selectors={
'frontierswe-v2':lambda p:bool(re.fullmatch(r'tasks/[^/]+/(instruction.md|task.toml)',p)),
'autoresearch-exam':lambda p:bool(re.fullmatch(r'[^/]+/(instruction.md|task.toml)',p)),
'airs-bench':lambda p:p.startswith('airsbench/tasks/rad/') and p.endswith(('metadata.yaml','project_description.md')),
'mls-bench':lambda p:bool(re.fullmatch(r'harbor/tasks-daytona/[^/]+/(instruction.md|task.toml|tests/meta/evaltask/task_description.md)',p)),
'paperbench':lambda p:p.startswith('project/paperbench/') and p.endswith(('.md','.txt','.yaml','.json')) and not p.endswith('/paper.md') and not any(x in p for x in ['judge_eval','/tests/','/judge/']),
'exp-bench':lambda p:p.startswith('benchmark/exp_bench/') and (p.endswith('_complete_final.json') or 'complete_final_sonnet' in p or p.endswith(('tasks.json','README.md','LICENSE'))),
'scientist-bench':lambda p:p.startswith('benchmark/final/') and p.endswith('.json') or p=='benchmark/README.md',
'scienceagentbench':lambda p:p=='benchmark/README.md',
'mlreplicate':lambda p:bool(re.fullmatch(r'AgentLaboratory/dataset/[^/]+\.yaml',p)),
'llm-speedrunning':lambda p:p.endswith(('level_2_description.txt','data.jsonl')) or p.endswith('.yaml'),
'kernelbench':lambda p:bool(re.fullmatch(r'KernelBench/level[1-4]/[^/]+\.py',p)) or p=='EVAL.md',
'tritonbench':lambda p:bool(re.fullmatch(r'data/TritonBench_[GT]_(?:comp_alpac|simp_alpac|v1)[^/]*\.json',p)),
'algotune':lambda p:bool(re.fullmatch(r'AlgoTuneTasks/[^/]+/description.txt',p)),
'weirdml':lambda p:p.endswith(('.md','.json','.csv')) and not p.startswith(('assets/icons','data_patches')),
}
def run(item):
 k,sel=item;chosen=[p for p in paths(k) if sel(p)];print('fetch',k,len(chosen),flush=True)
 try:batch(k,chosen);print('done',k,flush=True)
 except Exception as e:print('ERROR',k,str(e),flush=True)
with ThreadPoolExecutor(max_workers=5) as pool:list(pool.map(run,selectors.items()))

# Enumerate canonical MLS tasks from the untruncated subtree.
mlstree=json.loads((CACHE/'mls-bench/tasks-tree.json').read_text())
batch('mls-bench',['tasks/'+x['path'] for x in mlstree['tree'] if x['type']=='blob' and re.fullmatch(r'[^/]+/(task_description.md|config.json|score_spec.py)',x['path'])])

# Git LFS addenda are small instruction documents; never fetch paper PDFs or datasets.
def resolve_addendum(p):
 if not p.read_text().startswith('version https://git-lfs'):return
 rel=str(p.relative_to(CACHE/'paperbench'));u='https://media.githubusercontent.com/media/'+REPOS['paperbench']+'/'+tree('paperbench')['branch']+'/'+rel
 p.write_bytes(urllib.request.urlopen(u,timeout=45).read())
with ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(resolve_addendum,(CACHE/'paperbench').glob('project/paperbench/data/papers/*/addendum.md')))
