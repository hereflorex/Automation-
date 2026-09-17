import os, smtplib, asyncio
from email.message import EmailMessage
import requests

def telegram_send(text, buttons=None):
    token=os.getenv("TELEGRAM_BOT_TOKEN")
    chat=os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat:
        return False
    payload={"chat_id":chat,"text":text,"parse_mode":"HTML"}
    if buttons:
        payload["reply_markup"]={"inline_keyboard":buttons}
    r=requests.post(f"https://api.telegram.org/bot{token}/sendMessage",json=payload,timeout=20)
    return r.ok

def email_send(subject, body):
    host=os.getenv("SMTP_HOST"); port=int(os.getenv("SMTP_PORT","587"))
    user=os.getenv("SMTP_USER"); password=os.getenv("SMTP_PASSWORD")
    to=os.getenv("REPORT_EMAIL_TO")
    if not all([host,user,password,to]): return False
    msg=EmailMessage(); msg["Subject"]=subject; msg["From"]=user; msg["To"]=to; msg.set_content(body)
    with smtplib.SMTP(host,port,timeout=20) as s:
        s.starttls(); s.login(user,password); s.send_message(msg)
    return True

def notify(subject, body, buttons=None):
    results={}
    try: results["telegram"]=telegram_send(body,buttons)
    except Exception as e: results["telegram"]=False
    try: results["email"]=email_send(subject,body)
    except Exception as e: results["email"]=False
    return results
