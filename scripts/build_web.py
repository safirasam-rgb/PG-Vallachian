from __future__ import annotations
import argparse, sys
from datetime import datetime,timedelta
from pathlib import Path
PROJECT_ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(PROJECT_ROOT/'src'))
from vli.config import load_config
from vli.store import load_json,save_json
DAYS={0:'pondělí',1:'úterý',2:'středa',3:'čtvrtek',4:'pátek',5:'sobota',6:'neděle'}
def date_label(d): return f'{DAYS[d.weekday()]} {d.day}. {d.month}. {d.year}'
def rel(i): return {0:'dnes',1:'zítra',2:'pozítří'}.get(i,f'+{i} dní')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--config',default='config/locations.json'); ap.add_argument('--date'); ap.add_argument('--days',type=int,default=3); args=ap.parse_args()
    cfg=load_config(args.config); first=datetime.fromisoformat(args.date).date() if args.date else datetime.now().date(); loc=cfg.locations[0]; out=[]
    for i in range(max(1,args.days)):
        d=first+timedelta(days=i); p=PROJECT_ROOT/'data'/'forecasts'/f'{d.isoformat()}_{loc.id}.json'
        if not p.exists(): print('Missing',p); continue
        r=load_json(p); r['web_label']=rel(i); r['date_label']=date_label(d); out.append(r)
    payload={'generated_at':datetime.now().astimezone().isoformat(timespec='seconds'),'today_label':date_label(first),'location':{'id':loc.id,'name':loc.name,'latitude':loc.latitude,'longitude':loc.longitude},'days':out}
    save_json(PROJECT_ROOT/'docs'/'data'/'latest.json', payload); print('Saved docs/data/latest.json')
if __name__=='__main__': main()
