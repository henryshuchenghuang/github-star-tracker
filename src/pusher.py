import smtplib
from email.mime.text import MIMEText

import requests

TIMEOUT = 30


def push_email(config, subject, body):
    """通过 Resend API 发送邮件"""
    email_cfg = config.get("push", {}).get("email", {})
    if not email_cfg.get("enabled"):
        return False, "Email disabled"

    try:
        import resend

        resend.api_key = email_cfg["api_key"]
        resend.Emails.send({
            "from": email_cfg["from"],
            "to": email_cfg["to"],
            "subject": subject,
            "html": body.replace("\n", "<br>\n"),
        })
        return True, "Email sent"
    except ImportError:
        pass

    # SMTP fallback
    try:
        msg = MIMEText(body, "html", "utf-8")
        msg["Subject"] = subject
        msg["From"] = email_cfg["from"]
        msg["To"] = email_cfg["to"]
        with smtplib.SMTP_SSL(
            email_cfg.get("smtp_host", "smtp.resend.com"), 465, timeout=TIMEOUT
        ) as s:
            s.login("resend", email_cfg["api_key"])
            s.send_message(msg)
        return True, "Email sent via SMTP"
    except Exception as e:
        return False, str(e)


def push_wechat(config, title, body):
    """通过 Server酱 推送到微信"""
    wx_cfg = config.get("push", {}).get("wechat", {})
    if not wx_cfg.get("enabled"):
        return False, "WeChat disabled"

    try:
        token = wx_cfg["token"]
        summary = body[:500]
        url = f"https://sctapi.ftqq.com/{token}.send"
        resp = requests.post(url, data={"title": title, "desp": summary}, timeout=TIMEOUT)
        return resp.status_code == 200, resp.text[:200]
    except Exception as e:
        return False, str(e)


def push_feishu(config, title, body):
    """通过飞书 Webhook 推送"""
    fs_cfg = config.get("push", {}).get("feishu", {})
    if not fs_cfg.get("enabled"):
        return False, "Feishu disabled"

    try:
        webhook_url = fs_cfg["webhook_url"]
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {"title": {"tag": "plain_text", "content": title}},
                "elements": [{"tag": "markdown", "content": body}],
            },
        }
        resp = requests.post(webhook_url, json=payload, timeout=TIMEOUT)
        return resp.status_code == 200, resp.text[:200]
    except Exception as e:
        return False, str(e)


def push_all(config, subject, body):
    """推送到所有已启用的渠道"""
    results = {}
    for channel, fn in [
        ("email", push_email),
        ("wechat", push_wechat),
        ("feishu", push_feishu),
    ]:
        success, msg = fn(config, subject, body)
        results[channel] = {"success": success, "message": msg}
    return results
