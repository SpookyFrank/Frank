"""Run locally, never in GitHub Actions. Requires OAuth Desktop app client JSON."""
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from bot.youtube import SCOPES

flow = InstalledAppFlow.from_client_secrets_file('client_secret.json',SCOPES)
creds = flow.run_local_server(port=0,access_type='offline',prompt='consent')
if not creds.refresh_token:
    raise RuntimeError('No refresh token. Revoke previous grant and retry with prompt=consent.')
with open('token.json','w',encoding='utf-8') as f:
    f.write(creds.to_json())
print('Saved token.json locally. NEVER commit it. Copy its complete JSON to GitHub secret YOUTUBE_TOKEN_JSON.')
