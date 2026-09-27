#!/usr/bin/env python3
"""
Reusable, idempotent Metabase provisioner for the ktayl Data Platform.

Config-as-code (NOT a throwaway script): re-runnable, secret-free (all creds pulled from Vault at
runtime), and reproducible on any cluster. Creates/ensures: the analytics DB source, the Policy
Portfolio cards, and the dashboard. Safe to run repeatedly — everything is matched by name and only
created if missing.

Prereqs (per cluster):
  - Metabase reachable at $MB_BASE (default https://metabase.10.0.0.200.nip.io)
  - Vault secret/platform/data-platform holds: analytics-password, metabase-admin-email,
    metabase-admin-password  (admin creds are the login on a set-up instance, or seed the first
    admin on a fresh one).
  - A Vault token in $VAULT_TOKEN (or ~/.vault-ops-token) able to READ secret/platform/data-platform.

Run:  VAULT_TOKEN=... python3 provision_dashboard.py
  (or in-cluster as a Job with the git-clone pattern, like the dbt CronJob.)
"""
import json, os, ssl, subprocess, urllib.request, urllib.error

MB   = os.environ.get("MB_BASE", "https://metabase.10.0.0.200.nip.io")
VADDR= os.environ.get("VAULT_ADDR", "https://vault.10.0.0.200.nip.io")
DBHOST = os.environ.get("ANALYTICS_PG_HOST", "dp-postgres-rw.data-platform.svc.cluster.local")
CTX  = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
TOK  = os.environ.get("VAULT_TOKEN") or open(os.path.expanduser("~/.vault-ops-token")).read().strip()

def vault(prop):
    out = subprocess.run(["/usr/bin/curl","-sk","-H",f"X-Vault-Token: {TOK}",
        f"{VADDR}/v1/secret/data/platform/data-platform"],capture_output=True,text=True).stdout
    return json.loads(out)["data"]["data"][prop]

def api(method, path, body=None, session=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(MB+path, data=data, method=method); req.add_header("Content-Type","application/json")
    if session: req.add_header("X-Metabase-Session", session)
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=90) as r:
            t=r.read().decode(); return r.status,(json.loads(t) if t else {})
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:400]

DBPW = vault("analytics-password"); EMAIL = vault("metabase-admin-email"); PW = vault("metabase-admin-password")

# --- session: setup a fresh instance with the Vault admin creds, else log in ---
_, props = api("GET","/api/session/properties"); token = props.get("setup-token") if isinstance(props,dict) else None
if token:
    print("[mb] fresh instance → setup with Vault admin creds")
    st,res = api("POST","/api/setup",{"token":token,"user":{"first_name":"Andre","last_name":"K","email":EMAIL,"password":PW,"site_name":"ktayl"},"prefs":{"site_name":"ktayl","allow_tracking":False}})
    assert st in (200,201), (st,res); session=res["id"]
else:
    st,res = api("POST","/api/session",{"username":EMAIL,"password":PW}); assert st in (200,201), (st,res); session=res["id"]

# --- ensure the analytics DB source (idempotent by name) ---
_,dbs = api("GET","/api/database",session=session); dblist = dbs["data"] if isinstance(dbs,dict) and "data" in dbs else dbs
db = next((d for d in dblist if d["name"]=="ktayl analytics"), None)
if not db:
    _,db = api("POST","/api/database",{"engine":"postgres","name":"ktayl analytics","is_full_sync":True,
        "details":{"host":DBHOST,"port":5432,"dbname":"analytics","user":"analytics","password":DBPW,"ssl":False,"tunnel-enabled":False}},session)
dbid = db["id"]; api("POST",f"/api/database/{dbid}/sync_schema",{},session); print("[mb] analytics db id",dbid)

# --- cards (idempotent by name) ---
T="business.policy_portfolio"
CARDS = [
 ("GWP proxy (annualised premium €)", f"SELECT sum(annualised_premium_eur) AS gwp FROM {T}", "scalar"),
 ("Total Insured Value (TIV €)",      f"SELECT sum(total_insured_amount_eur) AS tiv FROM {T}", "scalar"),
 ("Active policies",                  f"SELECT count(*) AS active FROM {T} WHERE is_active", "scalar"),
 ("GWP by product",                   f"SELECT product_code, sum(annualised_premium_eur) AS gwp FROM {T} GROUP BY 1 ORDER BY 2 DESC", "bar"),
 ("Policies by status",               f"SELECT status, count(*) AS policies FROM {T} GROUP BY 1 ORDER BY 2 DESC", "bar"),
 ("Policy portfolio",                 f"SELECT policy_number, product_code, status, inception_year, scheduled_premium_eur, annualised_premium_eur, total_insured_amount_eur, coverage_count FROM {T} ORDER BY total_insured_amount_eur DESC", "table"),
]
_,existing = api("GET","/api/card",session=session); by_name={c["name"]:c["id"] for c in (existing if isinstance(existing,list) else [])}
ids=[]
for name,sql,disp in CARDS:
    if name in by_name: ids.append(by_name[name]); print("  card exists:",name); continue
    _,r = api("POST","/api/card",{"name":name,"display":disp,"visualization_settings":{},
        "dataset_query":{"type":"native","native":{"query":sql,"template-tags":{}},"database":dbid}},session)
    ids.append(r["id"]); print("  card created:",name,"->",r["id"])

# --- dashboard (idempotent by name) ---
_,dl = api("GET","/api/dashboard",session=session); dash = next((d for d in (dl if isinstance(dl,list) else []) if d["name"]=="Policy Portfolio (ktayl)"), None)
if not dash: _,dash = api("POST","/api/dashboard",{"name":"Policy Portfolio (ktayl)"},session)
did = dash["id"]
POS=[(0,0,4,3),(4,0,4,3),(8,0,4,3),(0,3,6,5),(6,3,6,5),(0,8,12,6)]
dc=[{"id":-(i+1),"card_id":c,"row":p[1],"col":p[0],"size_x":p[2],"size_y":p[3],"parameter_mappings":[],"visualization_settings":{}} for i,(c,p) in enumerate(zip(ids,POS)) if c]
api("PUT",f"/api/dashboard/{did}",{"dashcards":dc},session)
print(f"[mb] dashboard '{dash['name']}' id={did} ({len(dc)} cards) — /dashboard/{did}")
