#!/usr/bin/env python3
"""Download the newest artifact per name, retaining IDs and run provenance.

GitHub reruns can retain multiple same-name artifacts; numeric artifact ID order
does not necessarily match creation time. Avoid silently reading an older run.
"""
import argparse,io,json,pathlib,subprocess,zipfile
p=argparse.ArgumentParser();p.add_argument('run',type=int);p.add_argument('--out',required=True);a=p.parse_args()
repo='cpunion/llgo-cxx-layout-tests'
def api(path):return subprocess.check_output(['gh','api','--allow-escape-sequences',path])
base=f'repos/{repo}/actions/runs/{a.run}'
run=json.loads(api(base));artifacts=[];page=1
while True:
 batch=json.loads(api(base+f'/artifacts?per_page=100&page={page}'))['artifacts'];artifacts+=batch
 if len(batch)<100:break
 page+=1
latest={}
for item in sorted(artifacts,key=lambda x:(x['created_at'],x['id'])):latest[item['name']]=item
out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=False)
for name,item in sorted(latest.items()):
 data=api(f'repos/{repo}/actions/artifacts/{item["id"]}/zip')
 with zipfile.ZipFile(io.BytesIO(data)) as z:
  assert z.testzip() is None
  for entry in z.infolist():
   path=pathlib.PurePosixPath(entry.filename)
   if path.is_absolute() or '..' in path.parts:raise ValueError('unsafe artifact path')
  z.extractall(out/name)
 print(name,item['id'],item['created_at'],flush=True)
(out/'download.json').write_text(json.dumps({'repository':repo,'run_id':a.run,'head_sha':run['head_sha'],'run_attempt':run['run_attempt'],'url':run['html_url'],'artifacts':[{'id':x['id'],'name':x['name'],'created_at':x['created_at'],'size_in_bytes':x['size_in_bytes'],'digest':x.get('digest')} for x in latest.values()]},indent=2)+'\n')
