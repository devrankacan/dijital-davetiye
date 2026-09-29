#!/usr/bin/env python3
"""
Nişan RSVP — Email gönderici
127.0.0.1:3333 üzerinde dinler, Gmail SMTP ile mail atar.
Kimlik bilgileri ortam değişkenlerinden okunur (systemd servisinde tanımlı).
"""

import os, json, smtplib, urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

GMAIL_USER = os.environ['GMAIL_USER']   # devrankacan9@gmail.com
GMAIL_PASS = os.environ['GMAIL_PASS']   # Google Uygulama Şifresi


class MailHandler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self._cors()
        self.end_headers()

    def do_POST(self):
        if self.path != '/send':
            self.send_response(404); self.end_headers(); return

        try:
            length = int(self.headers.get('Content-Length', 0))
            body   = self.rfile.read(length).decode('utf-8')
            data   = urllib.parse.parse_qs(body)

            name = data.get('ad_soyad', [''])[0].strip()
            rsvp = data.get('rsvp',     [''])[0].strip()

            if not name or not rsvp:
                self._json(400, {'ok': False, 'error': 'eksik alan'})
                return

            self._send_mail(name, rsvp)
            self._json(200, {'ok': True})

        except Exception as e:
            self._json(500, {'ok': False, 'error': str(e)})

    def _send_mail(self, name, rsvp):
        coming  = rsvp == 'Geliyorum'
        subject = f'{"✅" if coming else "❌"} {name} — Nişan RSVP'

        status_color = '#2E7D4F' if coming else '#8B3A2A'
        status_bg    = '#EDF7F1' if coming else '#FAF0EE'
        status_icon  = '✦' if coming else '✧'

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = GMAIL_USER
        msg['To']      = GMAIL_USER

        text = (
            f'Merve & Devran Nişanı — RSVP\n\n'
            f'Ad Soyad      : {name}\n'
            f'Katılım Durumu: {rsvp}\n\n'
            f'10 Ekim 2026 · Ever After - World Point, Büyükçekmece'
        )

        html = f"""<!DOCTYPE html>
<html lang="tr">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#F0EBE3;font-family:Georgia,'Times New Roman',serif">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#F0EBE3;padding:40px 16px">
  <tr><td align="center">
    <table width="100%" style="max-width:480px;background:#FAF7F2;border:1px solid #DDD3C7;border-radius:2px">

      <!-- Üst şerit -->
      <tr>
        <td style="background:linear-gradient(135deg,#C9A88A 0%,#A5784E 100%);
                   padding:28px 32px 24px;text-align:center">
          <p style="margin:0 0 4px;font-size:11px;letter-spacing:.22em;
                    text-transform:uppercase;color:rgba(255,248,235,.75)">Nişan Daveti</p>
          <h1 style="margin:0;font-size:26px;font-weight:400;font-style:italic;
                     color:#FAF5EF;letter-spacing:.04em">Merve &amp; Devran</h1>
          <p style="margin:10px 0 0;font-size:12px;letter-spacing:.14em;
                    text-transform:uppercase;color:rgba(255,248,235,.65)">10 Ekim 2026</p>
        </td>
      </tr>

      <!-- İçerik -->
      <tr>
        <td style="padding:32px 32px 24px">

          <!-- Durum rozeti -->
          <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px">
            <tr>
              <td style="background:{status_bg};border:1px solid {'#B8DFC9' if coming else '#DEB8B0'};
                         border-radius:2px;padding:14px 20px;text-align:center">
                <span style="font-size:18px;color:{status_color};
                             font-weight:700;letter-spacing:.03em">{status_icon} {rsvp}</span>
              </td>
            </tr>
          </table>

          <!-- Misafir bilgisi -->
          <table width="100%" cellpadding="0" cellspacing="0"
                 style="border-top:1px solid #EDE4D6;border-bottom:1px solid #EDE4D6">
            <tr>
              <td style="padding:13px 0;width:38%;vertical-align:top">
                <span style="font-size:10px;letter-spacing:.16em;text-transform:uppercase;
                             color:#A8906E;font-family:Helvetica,Arial,sans-serif">Ad Soyad</span>
              </td>
              <td style="padding:13px 0;vertical-align:top">
                <span style="font-size:17px;color:#1E1714;font-style:italic">{name}</span>
              </td>
            </tr>
            <tr style="border-top:1px solid #EDE4D6">
              <td style="padding:13px 0;vertical-align:top">
                <span style="font-size:10px;letter-spacing:.16em;text-transform:uppercase;
                             color:#A8906E;font-family:Helvetica,Arial,sans-serif">Mekan</span>
              </td>
              <td style="padding:13px 0;vertical-align:top">
                <span style="font-size:13px;color:#3D2E26;line-height:1.5">
                  Ever After – World Point<br>Büyükçekmece
                </span>
              </td>
            </tr>
          </table>

          <!-- Alt not -->
          <p style="margin:22px 0 0;font-size:11px;color:#B09A82;text-align:center;
                    font-family:Helvetica,Arial,sans-serif;letter-spacing:.06em">
            nisan.taslak.site
          </p>

        </td>
      </tr>

    </table>
  </td></tr>
</table>
</body>
</html>"""

        msg.attach(MIMEText(text, 'plain', 'utf-8'))
        msg.attach(MIMEText(html,  'html',  'utf-8'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(GMAIL_USER, GMAIL_PASS)
            s.send_message(msg)

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self._cors()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin',  '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def log_message(self, *_):
        pass  # sessiz mod


if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', 3333), MailHandler)
    print('RSVP mailer dinleniyor → 127.0.0.1:3333')
    server.serve_forever()
