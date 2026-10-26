import json, os, random, time
from datetime import datetime, timedelta, timezone
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube.readonly']

def client():
    token_json = os.getenv('YOUTUBE_TOKEN_JSON')
    if token_json:
        info = json.loads(token_json)
    else:
        path = os.getenv('YOUTUBE_TOKEN_FILE', 'token.json')
        with open(path, encoding='utf-8') as f: info = json.load(f)
    creds = Credentials.from_authorized_user_info(info, SCOPES)
    if not creds.valid:
        if not creds.refresh_token: raise RuntimeError('Missing OAuth refresh token')
        creds.refresh(Request())
    return build('youtube','v3',credentials=creds,cache_discovery=False)

def retry(call, tries=5):
    for attempt in range(tries):
        try: return call()
        except HttpError as exc:
            status = exc.resp.status
            if status not in (429,500,502,503,504) or attempt == tries-1: raise
        except (ConnectionError, TimeoutError, OSError):
            if attempt == tries-1: raise
        time.sleep(min(40,2**attempt + random.random()))

def find_existing(yt, marker):
    # Check recent uploads before attempting to upload; not a globally atomic lock.
    channel = retry(lambda: yt.channels().list(part='contentDetails',mine=True).execute())
    items = channel.get('items', [])
    if not items: raise RuntimeError('YouTube channel not found for authorized user')
    playlist = items[0]['contentDetails']['relatedPlaylists']['uploads']
    token = None
    checked = 0
    while checked < 200:
        page = retry(lambda: yt.playlistItems().list(part='contentDetails',playlistId=playlist,maxResults=50,pageToken=token).execute())
        ids = [x['contentDetails']['videoId'] for x in page.get('items', [])]
        if not ids: break
        details = retry(lambda: yt.videos().list(part='snippet',id=','.join(ids)).execute())
        for item in details.get('items', []):
            if marker in item.get('snippet',{}).get('description',''):
                return item['id']
        checked += len(ids)
        token = page.get('nextPageToken')
        if not token: break
    return None

def upload(yt, path, metadata, publish=False):
    existing = find_existing(yt, metadata['marker'])
    if existing:
        print('Already uploaded:', existing)
        return existing
    status = {'privacyStatus':'private','selfDeclaredMadeForKids':False}
    if publish:
        # Schedule two days ahead, giving time to inspect output.
        dt = datetime.now(timezone.utc) + timedelta(days=2)
        dt = dt.replace(hour=12,minute=0,second=0,microsecond=0)
        status['publishAt'] = dt.isoformat().replace('+00:00','Z')
    body = {'snippet':{'title':metadata['title'],'description':metadata['description'],
                       'tags':metadata['tags'],'categoryId':'28'},'status':status}
    media = MediaFileUpload(str(path),mimetype='video/mp4',chunksize=5*1024*1024,resumable=True)
    request = yt.videos().insert(part='snippet,status',body=body,media_body=media)
    response = None
    while response is None:
        try:
            _, response = request.next_chunk()
        except HttpError as exc:
            if exc.resp.status not in (429,500,502,503,504): raise
            time.sleep(8)
            # Avoid restarting upload: resumable request retains its session.
        except (ConnectionError, TimeoutError, OSError):
            time.sleep(8)
    return response['id']
