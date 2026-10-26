import argparse, datetime, json, os
from pathlib import Path
from bot.content import choose_fact, script_for, optional_ai_rewrite, video_metadata
from bot.video import make_video
from bot.youtube import client, upload

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--day', default=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).date().isoformat())
    p.add_argument('--upload', action='store_true', help='Upload as private, unless --schedule is also set')
    p.add_argument('--schedule', action='store_true', help='Schedule public release in 2 days; requires --upload and PUBLISH_ENABLED=1')
    args = p.parse_args()
    fact = choose_fact(args.day)
    meta = video_metadata(fact,args.day)
    print('Fact:', fact['id'], 'marker:', meta['marker'])
    narration = optional_ai_rewrite(fact,script_for(fact))
    out = Path('output') / args.day
    video = make_video(fact,narration,out)
    (out/'metadata.json').write_text(json.dumps({**meta,'narration':narration,'source':fact['source']},indent=2),encoding='utf-8')
    print('Created:',video)
    if args.schedule and not args.upload: p.error('--schedule requires --upload')
    if args.upload:
        if args.schedule and os.getenv('PUBLISH_ENABLED') != '1':
            raise RuntimeError('To schedule public release set PUBLISH_ENABLED=1')
        video_id = upload(client(),video,meta,publish=args.schedule)
        print('YouTube:', 'https://www.youtube.com/watch?v='+video_id)

if __name__=='__main__': main()
