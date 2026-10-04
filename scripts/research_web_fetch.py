from research_fetch import *
from bs4 import BeautifulSoup
import re

def urlsave(url,path):
 p=CACHE/path
 if not p.exists():p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(urllib.request.urlopen(url,timeout=45).read())
 return p.read_text()
urlsave('https://huggingface.co/datasets/Just-Curieous/EXP-Bench/resolve/main/exp_bench_dataset.csv',Path('exp-bench/catalog.csv'))
urlsave('https://datasets-server.huggingface.co/rows?dataset=osunlp/ScienceAgentBench&config=default&split=verified&offset=0&length=100',Path('scienceagentbench/verified1.json'))
urlsave('https://datasets-server.huggingface.co/rows?dataset=osunlp/ScienceAgentBench&config=default&split=verified&offset=100&length=100',Path('scienceagentbench/verified2.json'))
slugs='post-training reasoning-adapter knowledge-edit opcd shampoo-parity cell-seg ecgdig lintrack ogbg-code2 ogbl-biokg attribution-speedup cheri-triton-training dbscan-speedup qwen-mtp-speedup pca-speedup regulatory-dna-design aux-channel-protocol hutter manifold-representation additive-smoothing'.split()
def taskpage(slug):
 html=urlsave('https://www.autoresearch-bench.com/tasks/'+slug,Path('autoresearch-bench')/(slug+'.html'))
 soup=BeautifulSoup(html,'html.parser');[s.decompose() for s in soup(['script','style'])]
 for pre in soup.find_all('pre'):pre.decompose()
 d={'name':soup.find('h1').get_text(' ',strip=True),'text':soup.get_text('\n',strip=True),'sections':[{'name':h.get_text(' ',strip=True),'text':' '.join(x.get_text(' ',strip=True) for x in h.find_next_siblings() if x.name not in ['pre','script'])} for h in soup.find_all(['h2','h3'])]}
 (CACHE/'autoresearch-bench'/(slug+'.json')).write_text(json.dumps(d));return slug
with ThreadPoolExecutor(max_workers=8) as pool:print(list(pool.map(taskpage,slugs)))
