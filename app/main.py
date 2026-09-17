import os, json, uuid, asyncio, traceback
from pathlib import Path
from datetime import datetime, date, timedelta
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

load_dotenv()
ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/"data"; REPORTS=ROOT/"reports"; RENDERS=ROOT/"renders"
for p in (DATA,REPORTS,RENDERS): p.mkdir(exist_ok=True)
DB=DATA/"jobs.json"; MAX_RETRIES=int(os.getenv("MAX_RETRIES","3"))
app=FastAPI(title="Florexia — NOIR//NULL Agent")

def load(): return json.loads(DB.read_text()) if DB.exists() else []
def save(x): DB.write_text(json.dumps(x,indent=2))
def get_job(jid): return next((x for x in load() if x["id"]==jid),None)
def create(kind,title,scheduled=None):
    x=load(); j={"id":uuid.uuid4().hex[:8],"kind":kind,"title":title,"status":"queued","retry_count":0,
    "scheduled":scheduled or str(date.today()),"approved":False,"created":datetime.now().isoformat(),"report":None,"video":None}
    x.append(j); save(x); return j
def replace_job(j):
    x=load(); save([j if z["id"]==j["id"] else z for z in x])
def notify_job(j,prefix):
    try:
        from .notify import notify
        body=f"<b>{prefix}</b>\n\n<b>Topic:</b> {j['title']}\n<b>Status:</b> {j['status']}\n<b>Job:</b> {j['id']}\n<b>Retries:</b> {j['retry_count']}"
        return notify("NOIR//NULL — "+prefix,body)
    except Exception: return {}

def write_report(j,rp,sp,qp,error=None):
    md=f"# Florexia Report — {j['title']}\n\n**Status:** {j['status']}\n\n"
    if rp:
        md+="## Research\n\n"+"".join(f"- {x}\n" for x in rp.key_facts)
        md+="\n### Sources\n\n"+"".join(f"- {x}\n" for x in rp.sources)
    if sp: md+=f"\n## Script\n\n{sp.script}\n\n## Metadata\n\nTitle: {sp.title}\n\nDescription:\n{sp.description}\n\nTags: {', '.join(sp.tags)}\n"
    if qp: md+=f"\n## QA\n\nPassed: `{qp.passed}`\n\nIssues: {qp.issues}\n"
    if error: md+=f"\n## Error\n\n```text\n{error}\n```\n"
    p=REPORTS/f"{j['id']}.md"; p.write_text(md,encoding="utf-8"); return p

async def run_job(jid):
    from .agents import run_pipeline
    from .tts import make_tts
    from .video import render
    from .creative import make_thumbnail, make_banner
    j=get_job(jid)
    if not j:return
    j["status"]="researching"; replace_job(j)
    rp=sp=qp=None
    try:
        rp,sp,qp=await run_pipeline(j["title"],j["kind"])
        if not qp.passed: raise RuntimeError("QA did not pass after repair: "+str(qp.issues))
        j["status"]="producing"; replace_job(j)
        audio=RENDERS/f"{jid}.mp3"; video=RENDERS/f"{jid}.mp4"
        thumb=RENDERS/f"{jid}_thumbnail.jpg"; banner=RENDERS/"channel_banner.jpg"
        make_thumbnail(sp.title,j["title"],thumb); make_banner(banner,os.getenv("BRAND_NAME","NOIR//NULL"))
        make_tts(sp.script,audio); render(sp.scene_text or [sp.hook],video,audio)
        j["status"]="qa_passed"; j["video"]=str(video); j["thumbnail"]=str(thumb); j["banner"]=str(banner)
        j["title_generated"]=sp.title; j["description"]=sp.description; j["tags"]=sp.tags
        j["report"]=str(write_report(j,rp,sp,qp)); replace_job(j); notify_job(j,"Production finished"); return j
    except Exception:
        j=get_job(jid); j["retry_count"]+=1
        j["status"]="retrying" if j["retry_count"]<MAX_RETRIES else "failed"
        j["report"]=str(write_report(j,rp,sp,qp,traceback.format_exc())); replace_job(j)
        notify_job(j,"Production failed / retry scheduled"); return j

def run_sync(jid): return asyncio.run(run_job(jid))
def daily_job():
    today=str(date.today()); j=next((z for z in load() if z["scheduled"]==today and z["kind"]=="short"),None)
    if not j:j=create("short","Daily fresh story from technology, AI, internet culture, privacy, or cybersecurity.",today)
    if j["status"] in ("queued","retrying") and j["retry_count"]<MAX_RETRIES: run_sync(j["id"])
def monthly_job():
    d=date.today()
    if d.day==int(os.getenv("MONTHLY_PLAN_DAY","1")):
        topics=["The Internet Never Really Forgets","Your Browser Has a Fingerprint","Why Phishing Works","What Your IP Actually Reveals","Deleted Doesn't Always Mean Gone","AI Voice Cloning Explained","Why AI Can Be Confidently Wrong","2FA Isn't Magic","Who Builds Your Digital Profile?","How Fake Login Pages Work","Why Old Websites Still Exist","What Happens When a Website Dies?","The Strange World of Web Archives","What Your Digital Footprint Reveals","Why Public Wi-Fi Gets Misunderstood","How Scams Create Urgency","Why Password Reuse Is Dangerous","What Metadata Can Reveal","How Deepfakes Change Trust","Why AI Search Can Be Wrong","How Browser Permissions Work","What Cookies Actually Do","Why QR Phishing Works","What Is a Data Broker?","Why Software Updates Matter","What Encryption Actually Means","How Social Engineering Works","Why Backups Matter","Privacy vs Anonymity","How Digital Identity Works"]
        for i,t in enumerate(topics):
            day=str(d+timedelta(days=i))
            if not any(z["title"]==t and z["scheduled"]==day for z in load()): create("short",t,day)
        if not any(z["kind"]=="flagship" and z["scheduled"].startswith(f"{d.year}-{d.month:02d}") for z in load()):
            create("flagship","The Internet Never Forgets — A Digital Memory Documentary",str(d+timedelta(days=27)))

@app.on_event("startup")
def startup():
    scheduler=BackgroundScheduler(timezone=os.getenv("APP_TIMEZONE","Asia/Kolkata"))
    h,m=os.getenv("DAILY_POST_TIME","19:30").split(":")
    scheduler.add_job(daily_job,CronTrigger(hour=int(h),minute=int(m)),id="daily",replace_existing=True)
    scheduler.add_job(monthly_job,CronTrigger(hour=0,minute=10),id="monthly",replace_existing=True)
    scheduler.start(); app.state.scheduler=scheduler

@app.get("/health")
def health(): return {"ok":True,"service":"florexia","instagram_enabled":os.getenv("INSTAGRAM_ENABLED","false").lower()=="true"}

@app.get("/",response_class=HTMLResponse)
def home():
    rows="".join(f"<tr><td>{j['id']}</td><td>{j['kind']}</td><td>{j['title']}</td><td>{j['status']}</td><td>{'YES' if j['approved'] else 'NO'}</td><td>{'<a href=/report/'+j['id']+'>report</a>' if j.get('report') else ''}</td></tr>" for j in load()[-50:])
    return f"""<!doctype html><meta name=viewport content="width=device-width,initial-scale=1"><style>
    body{{background:#050507;color:#eee;font:15px system-ui;padding:20px}}main{{max-width:1200px;margin:auto}}
    h1{{letter-spacing:6px}}a{{color:#00dff5}}button,input,select{{background:#111;color:#eee;border:1px solid #333;padding:10px;border-radius:8px;margin:4px}}
    table{{width:100%;border-collapse:collapse}}td,th{{padding:9px;border-bottom:1px solid #222;text-align:left}}</style>
    <main><h1>FLOREXIA</h1><p>NOIR//NULL Content Agent · Instagram: OFF</p>
    <p><a href=/youtube/connect>Connect YouTube</a> · <a href=/plan>Build 30-Day Plan</a> · <a href=/stats>YouTube Stats</a></p>
    <form method=post action=/create><input name=title placeholder="topic" required><select name=kind><option>short</option><option>flagship</option></select><button>Create</button></form>
    <table><tr><th>ID</th><th>Type</th><th>Topic</th><th>Status</th><th>Approved</th><th>Report</th></tr>{rows}</table></main>"""

@app.get("/plan")
def plan(): monthly_job(); return RedirectResponse("/",303)
@app.post("/create")
def create_route(title:str=Form(...),kind:str=Form("short")): create(kind,title); return RedirectResponse("/",303)
@app.post("/run/{jid}")
def run_route(jid): run_sync(jid); return RedirectResponse("/",303)
@app.post("/approve/{jid}")
def approve(jid):
    j=get_job(jid)
    if not j or j["status"]!="qa_passed": raise HTTPException(400,"Job must pass QA first")
    j["approved"]=True; j["status"]="approved"; replace_job(j); return RedirectResponse("/",303)
@app.post("/publish/{jid}")
def publish(jid):
    j=get_job(jid)
    if not j or not j["approved"]: raise HTTPException(400,"Approve the job first")
    from .youtube import upload
    result=upload(j["video"],j.get("title_generated",j["title"]),j.get("description",""),j.get("tags",[]),os.getenv("YOUTUBE_PRIVACY","private"))
    j["status"]="uploaded_private"; j["youtube_id"]=result["id"]; replace_job(j); notify_job(j,"Uploaded privately"); return RedirectResponse("/",303)
@app.get("/report/{jid}",response_class=HTMLResponse)
def report(jid):
    j=get_job(jid)
    if not j or not j.get("report"): raise HTTPException(404,"Report not found")
    report_path=Path(j["report"]).resolve()
    if REPORTS not in report_path.parents: raise HTTPException(400,"Invalid report path")
    return "<pre style='white-space:pre-wrap;font:15px system-ui'>"+Path(j["report"]).read_text(encoding="utf-8")+"</pre>"
@app.get("/youtube/connect")
def yt_connect():
    from .youtube import auth_url
    return RedirectResponse(auth_url())
@app.get("/youtube/callback")
def yt_callback(code:str=None,error:str=None,state:str=None):
    if error:return HTMLResponse("YouTube OAuth error: "+error)
    from .youtube import callback
    callback(code,state); return RedirectResponse("/",303)

@app.post("/telegram/webhook")
async def telegram_webhook(request:Request):
    data=await request.json(); msg=data.get("message",{}); chat=msg.get("chat",{}); text=(msg.get("text") or "").strip()
    allowed=os.getenv("TELEGRAM_CHAT_ID")
    if not allowed or str(chat.get("id"))!=str(allowed): return {"ok":True}
    from .notify import telegram_send
    def send(t): telegram_send(t)
    if text.startswith("/start"): send("🌸 <b>Florexia online.</b>\nCommands: /status /plan /run /report /approve JOB_ID /publish JOB_ID /stats")
    elif text.startswith("/status"):
        send("\n".join(f"• {z['id']} — {z['status']} — {z['title']}" for z in load()[-5:]) or "Queue empty.")
    elif text.startswith("/plan"): monthly_job(); send("📅 Content plan refreshed.")
    elif text.startswith("/run"):
        parts=text.split(maxsplit=1); j=get_job(parts[1]) if len(parts)>1 else next((z for z in reversed(load()) if z["status"] in ("queued","retrying")),None)
        if not j: send("No queued job found.")
        else: send(f"⏳ Starting {j['id']}…"); asyncio.create_task(run_job(j["id"]))
    elif text.startswith("/report"):
        parts=text.split(maxsplit=1); j=get_job(parts[1]) if len(parts)>1 else (load()[-1] if load() else None)
        send("No jobs yet." if not j else f"<b>Report</b>\nTopic: {j['title']}\nStatus: {j['status']}\nRetries: {j['retry_count']}\nReport: {j.get('report','not generated')}")
    elif text.startswith("/approve"):
        parts=text.split(maxsplit=1)
        if len(parts)<2: send("Use /approve JOB_ID")
        else:
            j=get_job(parts[1])
            if not j: send("Job not found.")
            elif j["status"]!="qa_passed": send("❌ QA must pass first.")
            else: j["approved"]=True; j["status"]="approved"; replace_job(j); send(f"✅ Approved {j['id']}.")
    elif text.startswith("/publish"):
        parts=text.split(maxsplit=1)
        if len(parts)<2: send("Use /publish JOB_ID")
        else:
            j=get_job(parts[1])
            if not j or not j.get("approved"): send("❌ Approve first.")
            else:
                try:
                    from .youtube import upload
                    r=upload(j["video"],j.get("title_generated",j["title"]),j.get("description",""),j.get("tags",[]),os.getenv("YOUTUBE_PRIVACY","private"))
                    j["status"]="uploaded_private"; j["youtube_id"]=r["id"]; replace_job(j); send(f"📺 Uploaded privately: <code>{r['id']}</code>")
                except Exception as e: send(f"❌ Upload failed: {e}")
    elif text.startswith("/stats"):
        try:
            from .youtube import recent_stats
            s=recent_stats(10); send("\n".join(f"• {x['title']} — {x['views']} views" for x in s) or "No stats yet.")
        except Exception as e: send(f"Stats unavailable: {e}")
    else: send("Unknown command. Try /status /plan /run /report /approve JOB_ID /publish JOB_ID /stats")
    return {"ok":True}

@app.get("/stats")
def stats():
    from .youtube import recent_stats
    return {"videos":recent_stats(10)}
