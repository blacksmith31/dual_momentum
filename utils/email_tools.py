import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

port = 465
password = "77asBnXuJu0M0oI6JZqs"
smtp_server = "smtp.gmail.com"
from_addr = "jhm.trading.updates@gmail.com"
to_addr = "jamesonhmarshall@gmail.com"

text = """There should be a table here..."""
# html = """\
# <html>
#   <body>
#     <p>Hi,<br>
#        How are you?<br>
#        <a href="http://www.realpython.com">Real Python</a> 
#        has many great tutorials.
#     </p>
#   </body>
# </html>
# """

def send_mail(subject, html, config=None):

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr

    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    msg.attach(part1)
    msg.attach(part2)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(from_addr, password)
        server.sendmail(from_addr, to_addr, msg.as_string())
  
