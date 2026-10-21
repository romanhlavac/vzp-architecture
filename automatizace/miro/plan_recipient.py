#!/usr/bin/env python3
"""Recipient-encrypted plan transport; no plaintext model data in repository or logs."""
import os,json,base64,pathlib,subprocess,tempfile
P=pathlib.Path('private-evidence');P.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory() as td:
 k=pathlib.Path(td)/'private.pem';cert=pathlib.Path(td)/'cert.pem';wrapped=pathlib.Path(td)/'wrapped.bin'
 subprocess.run(['openssl','req','-x509','-newkey','rsa:3072','-keyout',str(k),'-out',str(cert),'-days','2','-nodes','-subj','/CN=ephemeral-plan-recipient'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 subprocess.run(['openssl','enc','-aes-256-cbc','-salt','-pbkdf2','-iter','200000','-pass','env:MIRO_DIAGNOSTIC_TOKEN','-in',str(k),'-out',str(wrapped)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 (P/'recipient.json').write_text(json.dumps({'certificate':cert.read_text(),'wrapped_private':base64.b64encode(wrapped.read_bytes()).decode()}))
print('EPHEMERAL_RECIPIENT_READY; no board writes')
