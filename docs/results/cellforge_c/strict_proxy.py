"""Plan C strict meter; pinned CellForge and lab pricing are unmodified.
Reserve the entire documented 1M-token context plus output at the largest
unchanged lab rates before each serialized request. No tokenizer estimate.
Only this process holds the upstream key. No body or auth is logged.
"""
import argparse, hashlib, hmac, http.client, json, math, os, sys, time
from decimal import Decimal as D
from http.server import HTTPServer
from pathlib import Path

CONTEXT_BOUND = 1048576
MAX_BODY = 1048576
MAX_REPLY = 8388608
MARGIN = D("0.000001")
MODEL = "deepseek-flash"
CLIENT_TOKEN = "cellforge-local-no-credential"

def request(body):
    r = json.loads(body)
    if not isinstance(r, dict) or set(r)-{"model","messages","temperature","max_tokens","stream"}:
        raise ValueError("unsupported shape")
    if r.get("model") != MODEL or r.get("stream",False) is not False:
        raise ValueError("unsupported model/stream")
    n=r.get("max_tokens")
    if type(n) is not int or not 1<=n<=4096: raise ValueError("output limit")
    m=r.get("messages")
    if not isinstance(m,list) or len(m) not in (1,2): raise ValueError("messages")
    roles=["user"] if len(m)==1 else ["system","user"]
    for x,role in zip(m,roles):
        if not isinstance(x,dict) or set(x)!={"role","content"} or x["role"]!=role or not isinstance(x["content"],str):
            raise ValueError("plain text only")
    t=r.get("temperature",0.7)
    if type(t) not in (int,float) or not math.isfinite(t) or not 0<=t<=2: raise ValueError("temperature")
    # The current Flash model defaults to thinking; the pinned client expects
    # non-thinking content (its retired deepseek-chat route). Record this setting.
    r["thinking"]={"type":"disabled"}
    return r,n

def usage(doc,lp):
    u=doc.get("usage") if isinstance(doc,dict) else None
    if not isinstance(u,dict): raise ValueError("usage absent")
    for k in ("prompt_tokens","completion_tokens"):
        if type(u.get(k)) is not int or u[k]<0: raise ValueError("usage count")
    for k in ("prompt_cache_hit_tokens","prompt_cache_miss_tokens"):
        if k in u and (type(u[k]) is not int or u[k]<0): raise ValueError("cache count")
    v=lp.usage_openai(u)
    if not 0<=v.cached_tokens<=v.input_tokens: raise ValueError("cache bound")
    return v

def classes(lp):
    class Meter(lp.Proxy):
        def __init__(self,a,key):
            if not Path(a.ledger).is_file(): raise ValueError("existing ledger required")
            p=Path(a.log); p.parent.mkdir(parents=True,exist_ok=True)
            with p.open("x"): pass
            super().__init__("https://api.deepseek.com",Path(a.ledger),a.run_id,"cellforge",5.0,a.cap,p,lp.load_pricing(Path(a.pricing)),key)
            self.start=D(str(self.ledger_total)); self.cap=D(str(a.cap)); self.settled=D("0"); self.seen=set()
            if not self.start<=self.cap<=self.start+D("5.000000001"): raise ValueError("invalid fixed cap")
            tables=[*self.pricing.values(),{"input_cache_hit":3,"input_cache_miss":3,"output":15}]
            self.inrate=max(D(str(t[k])) for t in tables for k in ("input_cache_hit","input_cache_miss"))
            self.outrate=max(D(str(t["output"])) for t in tables)
            self.log(route="start",status=0,ledger_before_exact=str(self.start),cap_exact=str(self.cap),context_token_bound=CONTEXT_BOUND)
        def admit(self,digest,n):
            if self.halted: raise ValueError("halted")
            if digest in self.seen: self.halt("duplicate request refused"); raise ValueError("duplicate")
            total=D(str(self.ledger.total("deepseek"))); self.ledger_total=float(total)
            if abs(total-self.start-self.settled)>MARGIN: self.halt("external ledger change"); raise ValueError("overlap")
            bound=(D(CONTEXT_BOUND)*self.inrate+D(n)*self.outrate)/D(1000000)
            if total+bound+MARGIN>self.cap or self.settled+bound+MARGIN>D(5):
                self.halt("full-context reservation exceeds remaining cap"); raise ValueError("cap")
            self.seen.add(digest)
            self.log(route="dispatch",status=0,request_sha256=digest,reserved_usd=str(bound),max_output_tokens=n)
            return bound
    class Handler(lp.Handler):
        def do_POST(self):
            p=self.proxy
            if not self._loopback(): return self._error(403,"forbidden","loopback only")
            if self.path not in ("/v1/chat/completions","/chat/completions"): return self._error(404,"not_found","chat only")
            if not hmac.compare_digest(self.headers.get("Authorization",""),"Bearer "+CLIENT_TOKEN):
                return self._error(403,"forbidden","local token required")
            try:
                length=int(self.headers.get("Content-Length","0"))
                if self.headers.get("Transfer-Encoding") or not 0<length<=MAX_BODY: raise ValueError()
                self.connection.settimeout(15); body=self.rfile.read(length)
                if len(body)!=length: raise ValueError()
                req,n=request(body)
            except (ValueError,OSError): return self._error(400,"invalid_request","rejected before dispatch")
            digest=hashlib.sha256(body).hexdigest()
            try: reservation=p.admit(digest,n)
            except ValueError: return self._error(402,"budget_halt","permanently halted or cap refused")
            conn=None; priced=False; started=time.monotonic()
            try:
                conn=p.connect()
                conn.request("POST","/chat/completions",body=json.dumps(req).encode(),headers={
                    "Authorization":"Bearer "+p.key,"Content-Type":"application/json","Accept-Encoding":"identity","Connection":"close"})
                resp=conn.getresponse()
                if resp.status!=200: raise ValueError("upstream status")
                if resp.getheader("Content-Encoding","identity")!="identity": raise ValueError("encoding")
                raw=resp.read(MAX_REPLY+1)
                if len(raw)>MAX_REPLY: raise ValueError("reply size")
                doc=json.loads(raw); u=usage(doc,lp); served=doc.get("model")
                if not isinstance(served,str) or not served: raise ValueError("served model")
                pk=lp.price_key(p.pricing,MODEL,served); cost=lp.cost_of(p.pricing,pk,u)
                if not math.isfinite(cost) or cost<0: raise ValueError("cost")
                p.settle(served,u,cost); p.settled+=D(str(cost)); priced=True
                p.log(route="settled",status=200,request_sha256=digest,model_requested=MODEL,model_served=served,
                    priced_as=pk,input_tokens=u.input_tokens,cached_tokens=u.cached_tokens,output_tokens=u.output_tokens,
                    cost_usd=cost,latency_s=round(time.monotonic()-started,3))
                if u.input_tokens>CONTEXT_BOUND or u.output_tokens>n or D(str(cost))>reservation: raise ValueError("provider bound")
                self._relay(200,"application/json",raw)
            except Exception as e:
                p.halt("upstream/accounting/client failure; no retry")
                p.log(route="halt",status=502,request_sha256=digest,error_type=type(e).__name__,priced=priced,unpriced=not priced)
                try: self._error(502,"permanent_halt","operator review required")
                except OSError: pass
            finally:
                if conn: conn.close()
    return Meter,Handler

def main():
    ap=argparse.ArgumentParser()
    for x in ("clone","ledger","pricing","log","run-id"): ap.add_argument("--"+x,required=True)
    ap.add_argument("--cap",type=float,required=True); ap.add_argument("--port",type=int,default=8791)
    a=ap.parse_args()
    sys.path.insert(0,str(Path(a.clone)/"tools/baselines")); import ledger_proxy as lp
    key=os.environ.get("DEEPSEEK_API_KEY")
    if not key: raise SystemExit("upstream credential absent")
    Meter,Handler=classes(lp); meter=Meter(a,key)
    Bound=type("Bound",(Handler,),{"proxy":meter})
    # Single-threaded server: at most one billed request in flight.
    HTTPServer(("127.0.0.1",a.port),Bound).serve_forever()
if __name__=="__main__": main()

