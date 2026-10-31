import pathlib,subprocess,json,os,socket,threading
from http.server import HTTPServer,BaseHTTPRequestHandler
rec=pathlib.Path("/Users/andresarriaga/.codex/.chatgpt-projects/g-p-6abd4598969c8191806ed119a5e711b5/gene-mila-cellforge-c2/docs/results/cellforge_c2/preflight_resumed_20261030")
class H(BaseHTTPRequestHandler):
 def do_GET(self):
  self.send_response(200); self.end_headers(); self.wfile.write(b"free test")
 def log_message(self,*args): pass
srv=HTTPServer(("127.0.0.1",8793),H); t=threading.Thread(target=srv.serve_forever,daemon=True); t.start()
env={k:v for k,v in os.environ.items() if k in ("PATH","HOME","USER","LOGNAME","LANG","LC_ALL","TMPDIR","SHELL")}
env.update(CELLFORGE_WORKSPACE_DIR="/Users/andresarriaga/cellforge_c2_workspace",XDG_CACHE_HOME="/Users/andresarriaga/cellforge_c2_workspace/cache",HF_HOME="/Users/andresarriaga/cellforge_c2_workspace/cache/hf",MPLCONFIGDIR="/Users/andresarriaga/cellforge_c2_workspace/cache/mpl",HF_HUB_OFFLINE="1",TRANSFORMERS_OFFLINE="1",PYTHONDONTWRITEBYTECODE="1")
base=["/usr/bin/sandbox-exec","-f","/Users/andresarriaga/.codex/.chatgpt-projects/g-p-6abd4598969c8191806ed119a5e711b5/cellforge_c2_ops/cellforge_analysis.sb","/Users/andresarriaga/cellforge_c_venv/bin/python","-c"]
tests={}
p=subprocess.run(base+["import urllib.request; assert urllib.request.urlopen('http://127.0.0.1:8793/healthz').status==200"],cwd="/Users/andresarriaga/cellforge_c2_workspace",env=env,capture_output=True,text=True)
tests["only_meter_port_reachable"]=p.returncode==0
code="""import socket
try: socket.create_connection(("1.1.1.1",80),timeout=1)
except PermissionError: pass
else: raise AssertionError("egress unexpectedly allowed")
"""
p=subprocess.run(base+[code],cwd="/Users/andresarriaga/cellforge_c2_workspace",env=env,capture_output=True,text=True)
tests["remote_egress_denied"]=p.returncode==0
srv.shutdown();srv.server_close()
r={"checks":tests,"all_pass":all(tests.values()),"remote_api_calls":0}
(rec/"network_boundary_free_tests.json").write_text(json.dumps(r,indent=2)+"\n")
assert r["all_pass"],r
print(json.dumps(r))

