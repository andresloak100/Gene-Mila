"""One authorized run, first checkpoint only. No auto-approval or code generation."""
import datetime,json,os,pathlib,signal,socket,subprocess,time,urllib.request
D=json.loads("{\"clone\":\"/Users/andresarriaga/.codex/.chatgpt-projects/g-p-6abd4598969c8191806ed119a5e711b5/gene-mila-cellforge-c\",\"rec\":\"/Users/andresarriaga/.codex/.chatgpt-projects/g-p-6abd4598969c8191806ed119a5e711b5/gene-mila-cellforge-c/docs/results/cellforge_c\",\"out\":\"/Users/andresarriaga/cellforge_adamson_export_corrected_20261028\",\"cmd\":[\"/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/.venv/bin/python\",\"/Users/andresarriaga/.codex/.chatgpt-projects/g-p-6abd4598969c8191806ed119a5e711b5/gene-mila-cellforge-c/tools/cellforge_bridge.py\",\"export\",\"--bundle\",\"/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/data/adamson_cf\",\"--h5ad\",\"/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/data/raw/AdamsonWeissman2016_GSM2406675_10X001.h5ad\",\"/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/data/raw/AdamsonWeissman2016_GSM2406677_10X005.h5ad\",\"/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/data/raw/AdamsonWeissman2016_GSM2406681_10X010.h5ad\",\"--out\",\"/Users/andresarriaga/cellforge_adamson_export_corrected_20261028\"],\"ops\":\"/Users/andresarriaga/.codex/.chatgpt-projects/g-p-6abd4598969c8191806ed119a5e711b5/cellforge_c_ops\",\"name\":\"corrected_export\",\"session\":\"gm-c-corrected-export\"}")
REC=pathlib.Path(D["rec"]); W="/Users/andresarriaga/cellforge_c_workspace"
PY=D["cmd"][0]; FPY="/Users/andresarriaga/cellforge_c_venv/bin/python"
CLIENT="cellforge-local-no-credential"; PORT=8791
assert (REC/"pytest.exit").read_text().strip()=="0", "Full suite must pass before paid execution"
assert not (REC/"analysis_pipeline.exit").exists()
base={k:v for k,v in os.environ.items() if k in ("PATH","HOME","USER","LOGNAME","LANG","LC_ALL","TMPDIR","TERM","SHELL")}
realkey=os.environ.pop("DEEPSEEK_API_KEY",None); os.environ.pop("API_KEY",None)
assert realkey, "Existing Mac environment credential missing"
proxyenv={**base,"DEEPSEEK_API_KEY":realkey,"PYTHONHASHSEED":"0"}
del realkey
proxycmd=[PY,D["ops"]+"/strict_proxy.py","--clone",D["clone"],"--ledger","/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/spend_ledger.sqlite","--pricing",D["clone"]+"/configs/default.toml","--log",str(REC/"proxy.jsonl"),"--run-id","cellforge_adamson_c_seed0","--cap","66.240534032","--port",str(PORT)]
with (REC/"proxy.command.txt").open("x") as f:
 import shlex
 f.write('DEEPSEEK_API_KEY="$API_KEY" [process environment only] '+shlex.join(proxycmd)+"\n")
proxylog=(REC/"proxy.process.log").open("x")
proxy=subprocess.Popen(proxycmd,cwd=D["ops"],env=proxyenv,stdout=proxylog,stderr=subprocess.STDOUT)
del proxyenv
def health(timeout=10):
 with urllib.request.urlopen("http://127.0.0.1:"+str(PORT)+"/healthz",timeout=timeout) as f: return json.load(f)
env={**base,"PATH":"/Users/andresarriaga/cellforge_c_venv/bin:"+base.get("PATH","/usr/bin:/bin"),
 "CELLFORGE_WORKSPACE_DIR":W,"DEEPSEEK_API_KEY":CLIENT,"DEEPSEEK_BASE_URL":"http://127.0.0.1:"+str(PORT),
 "MODEL_NAME":"deepseek-flash","PYTHONHASHSEED":"0","PYTHONDONTWRITEBYTECODE":"1",
 "MPLCONFIGDIR":W+"/cache/mpl","XDG_CACHE_HOME":W+"/cache","HF_HOME":W+"/cache/hf",
 "HF_HUB_OFFLINE":"1","TRANSFORMERS_OFFLINE":"1","QDRANT_ENABLED":"false","LLM_REQUEST_TIMEOUT":"600",
 "TOKENIZERS_PARALLELISM":"false","PYTORCH_ENABLE_MPS_FALLBACK":"1"}
rc=1; final={}
try:
 for _ in range(100):
  if proxy.poll() is not None: raise RuntimeError("meter did not start")
  try:
   h=health(1)
   assert h["ok"] and h["calls"]==0
   break
  except OSError: time.sleep(.1)
 else: raise RuntimeError("meter health unavailable")
 for phase in ("task_analysis","method_design"):
  cmd=["/usr/bin/sandbox-exec","-f",D["ops"]+"/cellforge_analysis_v2.sb","/usr/bin/nice","-n","19",
       FPY,"/Users/andresarriaga/CellForge-6585ff9/main.py","--workspace",W,"--phase",phase,
       "--dataset-path",D["out"]+"/cellforge_input.h5ad","--task-file",D["out"]+"/TASK.md","--split-seed","0"]
  with (REC/(phase+".command.txt")).open("x") as f:
   f.write("Only dummy local token in client; true credential in meter only.\n"+shlex.join(cmd)+"\n")
  with (REC/(phase+".log")).open("x") as f:
   f.write(datetime.datetime.now(datetime.timezone.utc).isoformat()+" START\n");f.flush()
   rc=subprocess.call(cmd,cwd=W,env=env,stdout=f,stderr=subprocess.STDOUT)
   f.write(datetime.datetime.now(datetime.timezone.utc).isoformat()+" EXIT "+str(rc)+"\n")
  with (REC/(phase+".exit")).open("x") as f: f.write(str(rc)+"\n")
  if rc: break
 final=health(650)
 if not final["ok"]: rc=1
except Exception as exc:
 final={"operator_error_type":type(exc).__name__};rc=1
finally:
 (REC/"analysis_pipeline_final.json").write_text(json.dumps(final,indent=2)+"\n")
 with (REC/"analysis_pipeline.exit").open("x") as f:f.write(str(rc)+"\n")
 proxy.terminate()
 try:proxy.wait(timeout=10)
 except subprocess.TimeoutExpired:proxy.kill();proxy.wait()
 proxylog.close()

