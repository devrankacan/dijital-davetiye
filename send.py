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
        emoji  = '✅' if rsvp == 'Geliyorum' else '❌'
        subject = f'{emoji} Nişan RSVP – {name}'

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = GMAIL_USER
        msg['To']      = GMAIL_USER

        text = f'Ad Soyad: {name}\nKatılım Durumu: {rsvp}'
        html = f"""
        <div style="font-family:Georgia,serif;max-width:480px;margin:0 auto;
                    border:1px solid #E8DDD0;padding:32px;background:#FAF7F2">
          <h2 style="font-size:22px;font-weight:400;color:#1E1714;margin:0 0 20px">
            {emoji} Nişan RSVP
          </h2>
          <table style="width:100%;border-collapse:collapse">
            <tr>
              <td style="padding:10px 0;color:#7A6452;font-size:12px;
                         letter-spacing:.1em;text-transform:uppercase">Ad Soyad</td>
              <td style="padding:10px 0;color:#1E1714;font-size:16px">{name}</td>
            </tr>
            <tr style="border-top:1px solid #EDE4D6">
              <td style="padding:10px 0;color:#7A6452;font-size:12px;
                         letter-spacing:.1em;text-transform:uppercase">Katılım</td>
              <td style="padding:10px 0;color:#1E1714;font-size:16px;
                         font-weight:700">{rsvp}</td>
            </tr>
          </table>
          <p style="margin:24px 0 0;font-size:11px;color:#A8906E">
            Merve &amp; Devran Nişanı · 10 Ekim 2026
          </p>
        </div>"""

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
