import os
from pathlib import Path
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES=["https://www.googleapis.com/auth/youtube.upload","https://www.googleapis.com/auth/youtube.readonly"]
ROOT=Path(__file__).resolve().parent.parent
TOKEN=Path(os.getenv("YOUTUBE_TOKEN_FILE",str(ROOT/"data"/"youtube_token.json")))
STATE_FILE=ROOT/"data"/"oauth_state.txt"
REDIRECT=os.getenv("YOUTUBE_REDIRECT_URI","http://127.0.0.1:8000/youtube/callback")

def config():
    client_id=os.getenv("YOUTUBE_CLIENT_ID"); client_secret=os.getenv("YOUTUBE_CLIENT_SECRET")
    if not client_id or not client_secret: raise RuntimeError("YouTube OAuth credentials are not configured")
    return {"web":{"client_id":client_id,"client_secret":client_secret,"auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","redirect_uris":[REDIRECT]}}

def auth_url():
    flow=Flow.from_client_config(config(),scopes=SCOPES,redirect_uri=REDIRECT)
    url,state=flow.authorization_url(access_type="offline",include_granted_scopes="true",prompt="consent")
    STATE_FILE.parent.mkdir(parents=True,exist_ok=True); STATE_FILE.write_text(state,encoding="utf-8"); return url

def callback(code, returned_state=None):
    if not code: raise RuntimeError("Missing OAuth code")
    if not STATE_FILE.exists(): raise RuntimeError("OAuth session expired; reconnect YouTube")
    state=STATE_FILE.read_text(encoding="utf-8").strip()
    if returned_state and returned_state != state: raise RuntimeError("Invalid OAuth state")
    flow=Flow.from_client_config(config(),scopes=SCOPES,state=state,redirect_uri=REDIRECT)
    flow.fetch_token(code=code); STATE_FILE.unlink(missing_ok=True); TOKEN.parent.mkdir(parents=True,exist_ok=True); TOKEN.write_text(flow.credentials.to_json())

def service():
    if not TOKEN.exists(): return None
    from google.oauth2.credentials import Credentials
    c=Credentials.from_authorized_user_file(str(TOKEN),SCOPES)
    if not c.valid and c.expired and c.refresh_token:
        from google.auth.transport.requests import Request
        c.refresh(Request()); TOKEN.write_text(c.to_json())
    return build("youtube","v3",credentials=c) if c.valid else None

def upload(path,title,description,tags,privacy="private"):
    yt=service()
    if not yt: raise RuntimeError("YouTube not connected. Open /youtube/connect")
    body={"snippet":{"title":title[:100],"description":description[:5000],"tags":tags[:30],"categoryId":"28"},"status":{"privacyStatus":privacy}}
    media=MediaFileUpload(str(path),chunksize=8*1024*1024,resumable=True)
    req=yt.videos().insert(part="snippet,status",body=body,media_body=media); response=None
    while response is None: _,response=req.next_chunk()
    return response

def recent_stats(limit=10):
    yt=service()
    if not yt:return []
    items=yt.channels().list(part="contentDetails",mine=True).execute().get("items",[])
    if not items: return []
    ch=items[0]
    uploads=ch["contentDetails"]["relatedPlaylists"]["uploads"]
    items=yt.playlistItems().list(part="contentDetails,snippet",playlistId=uploads,maxResults=limit).execute().get("items",[])
    ids=[x["contentDetails"]["videoId"] for x in items]
    if not ids:return []
    vids=yt.videos().list(part="snippet,statistics,status",id=",".join(ids)).execute().get("items",[])
    return [{"id":v["id"],"title":v["snippet"]["title"],"published":v["snippet"].get("publishedAt"),"views":v.get("statistics",{}).get("viewCount","0"),"likes":v.get("statistics",{}).get("likeCount","0"),"comments":v.get("statistics",{}).get("commentCount","0"),"privacy":v.get("status",{}).get("privacyStatus")} for v in vids]
