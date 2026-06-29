from __future__ import annotations
import argparse, sys
from datetime import datetime,timedelta
from pathlib import Path
PROJECT_ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(PROJECT_ROOT/'src'))
from vli.config import load_config
from vli.open_meteo import OpenMeteoRequest,fetch_forecast
from vli.report import render_markdown
from vli.scoring import compute_index
from vli.store import save_json,save_text

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--config',default='config/locations.json'); ap.add_argument('--date'); ap.add_argument('--days',type=int,default=1); args=ap.parse_args()
    cfg=load_config(args.config); first=datetime.fromisoformat(args.date).date() if args.date else datetime.now().date(); days=max(1,args.days)
    include=bool(cfg.raw.get('data_sources',{}).get('open_meteo',{}).get('include_pressure_levels',False))
    for loc in cfg.locations:
        data=fetch_forecast(OpenMeteoRequest(loc.latitude,loc.longitude,cfg.timezone,include), forecast_days=max(days,3))
        for off in range(days):
            d=first+timedelta(days=off); result=compute_index(data,loc,d,cfg.forecast_window,cfg.sector_settings); base=f'{d.isoformat()}_{loc.id}'
            save_json(PROJECT_ROOT/'data'/'forecasts'/f'{base}.json', result)
            save_text(PROJECT_ROOT/'data'/'forecasts'/f'{base}.md', render_markdown(result))
            print('Saved', base)
if __name__=='__main__': main()
