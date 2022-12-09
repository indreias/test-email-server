#!/usr/bin/python3 -u
#
# Some code inspired from: send-smtp.py | https://gist.github.com/indreias/7275508a44aff37ff15b3e64df2cf294
#

import sys
import os.path
import gzip

import smtplib

import socket
socket.setdefaulttimeout(20)

import logging
logging.basicConfig(format='%(asctime)s.%(msecs)03d\t%(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.DEBUG, stream=sys.stdout)

SMTP_DEBUG_LEVEL = int(os.getenv("SMTP_DEBUG_LEVEL", 0))
# 0 = none
# 1 = logged on stderr
# 2 = 1 + timestamps

try:
  target   = sys.argv[1]
  mailFrom = sys.argv[2]
  rcptTo   = sys.argv[3].split(',')
  emlFile  = sys.argv[4]
except:
  print()
  print("Usage: %s <[user:password%%]server[:port]> <mailFrom> <rcptTo[,rcptTo...]> <emlFile> [tls|ssl|none=default]" % sys.argv[0])
  print("""
Environment variables:
  SMTP_DEBUG_LEVEL (default=0)
""")
  print()
  print("Examples:")
  print("$ %s mail.domain.org a.b@domain.org c.d@domain.org"% sys.argv[0])
  print("$ SMTP_DEBUG_LEVEL=2 %s u1@example.com:my-secrect%%localhost:465 u1@example.com u2@domain.org,u3@test.mail ./data/ ssl 2>>/var/log/activity.log" % sys.argv[0])
  print()
  sys.exit(1)

try:
  tlsType = sys.argv[5]
except:
  tlsType = 'none'
  pass

###############################################################################################

def smtpConnect(remote, tls):
  serverHost = remote.split(':')[0]
  serverPort = remote.split(':')[-1]
  if serverPort == serverHost:
    serverPort = 25
  smtpObj = None
  if tls == 'ssl':
    smtpObj = smtplib.SMTP_SSL(serverHost, serverPort, 'test.localdomain', timeout=20)
  else:
    smtpObj = smtplib.SMTP(serverHost, serverPort, 'test.localdomain', timeout=20)
    if tls == 'tls':
      smtpObj.starttls()
  return smtpObj

def smtpAUTH(smtpObj, conn_type, mail_from, mail_to, mail_msg, auth_user, auth_password):
  smtpObj.login(auth_user, auth_password)
  smtpObj.sendmail(mail_from, mail_to, mail_msg)
  smtpObj.quit()

def smtpINMX(smtpObj, conn_type, mail_from, mail_to, mail_msg):
  smtpObj.sendmail(mail_from, mail_to, mail_msg)
  smtpObj.quit()

def sendmail(filename):
  if not os.path.isfile(filename):
    logging.info("[Fail] File '%s' not found" & filename)
    sys.exit(0)
  if filename.endswith('gz'):
    f = gzip.open(filename)
    message = f.read()
    f.close()
  else:
    with open(filename) as f:
      message = f.read()
  smtp = None
  try:
    smtp = smtpConnect(server, tlsType)
    smtp.set_debuglevel(SMTP_DEBUG_LEVEL)
  except Exception as e:
    logging.info("[Fail] Connect failure to: %s (%s)" %(server, str(e)))
    return()
  try:
    if isAuth:
      smtpAUTH(smtp, 'sim', mailFrom, rcptTo, message, authUser, authPassword)
    else:
      smtpINMX(smtp, 'sim', mailFrom, rcptTo, message)
    logging.info("[OK] Mail sent succesfully: %s" % filename)
  except Exception as e:
    logging.info("[Fail] Failed to send mail: %s (%s)" % (filename,str(e)))
  if smtp != None:
    smtp.close()

def sendmail_recursively(folder):
  for root, dirs, files in os.walk(folder):
    for file in files:
      file_path = os.path.join(root, file)
      if file.endswith('eml') or file.endswith('gz'):
        sendmail(file_path)

###

credentials = target.split('%')[0]
server = target.split('%')[-1]

if credentials != server:
  isAuth = True
  authUser = credentials.split(':')[0]
  authPassword = credentials.split(':')[1]
else:
  isAuth = False


if os.path.isfile(emlFile):
  sendmail(emlFile)
else:
  sendmail_recursively(emlFile)
