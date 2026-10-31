"""Free fake-upstream tests; never contacts any remote endpoint or real ledger."""
import importlib.util, json, sys, tempfile, threading, types, http.client
from pathlib import Path
sys.path.insert(0, "/Users/andresarriaga/.codex/.chatgpt-projects/g-p-6abd4598969c8191806ed119a5e711b5/gene-mila-cellforge-c2/tools/baselines")
import ledger_proxy as lp
spec=importlib.util.spec_from_file_location("strict_proxy", "/Users/andresarriaga/.codex/.chatgpt-projects/g-p-6abd4598969c8191806ed119a5e711b5/cellforge_c2_ops/strict_proxy.py")
s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
from http.server import HTTPServer
checks=[]
with tempfile.TemporaryDirectory(prefix="cellforge_meter_test_") as tmp:
 def setup(case,doc=None,cap=5):
  root=Path(tmp)/case; root.mkdir(); ledger=root/"fake.sqlite"; lp.SpendLedger(ledger)
  a=types.SimpleNamespace(ledger=str(ledger),log=str(root/"proxy.jsonl"),run_id="FREE_TEST",pricing="/Users/andresarriaga/.codex/.chatgpt-projects/g-p-6abd4598969c8191806ed119a5e711b5/gene-mila-cellforge-c2/configs/default.toml",cap=cap)
  M,H=s.classes(lp); p=M(a,"fake-upstream-credential"); dispatched=[]
  class Resp:
   status=200
   def getheader(self,k,default=""): return default
   def read(self,n): return json.dumps(doc or {"model":"deepseek-flash","usage":{"prompt_tokens":1000,"completion_tokens":10,"prompt_cache_hit_tokens":100,"prompt_cache_miss_tokens":900},"choices":[{"message":{"content":"ok"}}]}).encode()
  class Conn:
   def request(self,*args,**kwargs): dispatched.append(1)
   def getresponse(self): return Resp()
   def close(self): pass
  p.connect=lambda:Conn()
  bound=type("Bound",(H,),{"proxy":p}); server=HTTPServer(("127.0.0.1",0),bound)
  thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
  def call():
   c=http.client.HTTPConnection("127.0.0.1",server.server_port)
   req={"model":"deepseek-flash","messages":[{"role":"user","content":"free test"}],"max_tokens":100,"temperature":0.7}
   c.request("POST","/v1/chat/completions",body=json.dumps(req),headers={"Authorization":"Bearer "+s.CLIENT_TOKEN,"Content-Type":"application/json"})
   r=c.getresponse(); status=r.status; r.read(); c.close(); return status
  return p,dispatched,server,call
 p,c,sv,call=setup("normal")
 assert call()==200 and p.calls==1 and len(c)==1 and p.ledger.total("deepseek")>0; checks.append("known usage settled")
 assert call()==402 and len(c)==1 and p.halted; checks.append("duplicate retry refused without billing")
 sv.shutdown(); sv.server_close()
 for label,doc in [
  ("missing",{"model":"deepseek-flash","choices":[]}),
  ("string",{"model":"deepseek-flash","usage":{"prompt_tokens":"100","completion_tokens":1}}),
  ("cache",{"model":"deepseek-flash","usage":{"prompt_tokens":100,"completion_tokens":1,"prompt_cache_hit_tokens":101}})]:
  p,c,sv,call=setup(label,doc)
  assert call()==502 and p.halted and p.calls==0 and call()==402 and len(c)==1
  checks.append(label+" usage halts without retry")
  sv.shutdown();sv.server_close()
 p,c,sv,call=setup("outputbound",{"model":"deepseek-flash","usage":{"prompt_tokens":10,"completion_tokens":101}})
 assert call()==502 and p.calls==1 and p.halted; checks.append("bound violation accounted then halted")
 sv.shutdown();sv.server_close()
 p,c,sv,call=setup("cap",cap=3)
 assert call()==402 and not c; checks.append("full-context cap refuses before upstream")
 sv.shutdown();sv.server_close()
 p,c,sv,call=setup("external")
 p.ledger.add("unrelated","deepseek","deepseek-flash","test",lp.Usage(),.01)
 assert call()==402 and not c; checks.append("external ledger writer refused")
 sv.shutdown();sv.server_close()
 for bad in [True,1.2,"3",None]:
  try: s.usage({"usage":{"prompt_tokens":bad,"completion_tokens":1}},lp)
  except ValueError: continue
  raise AssertionError("invalid token type admitted")
 checks.append("strict token types")
result={"all_pass":True,"checks":checks,"remote_calls":0,"real_ledger_opened":False}
Path("/Users/andresarriaga/.codex/.chatgpt-projects/g-p-6abd4598969c8191806ed119a5e711b5/gene-mila-cellforge-c2/docs/results/cellforge_c2/preflight_resumed_20261030/strict_proxy_free_tests.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result))

