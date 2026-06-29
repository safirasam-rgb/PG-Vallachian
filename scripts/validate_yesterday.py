from __future__ import annotations
import argparse, sys
from datetime import datetime,timedelta
from pathlib import Path
PROJECT_ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(PROJECT_ROOT/'src'))
from vli.config import load_config
from vli.open_meteo import OpenMeteoRequest,fetch_historical_actual
from vli.store import load_json,save_json,save_text
from vli.validation import summarize_actual,compare_forecast_to_actual,render_validation_markdown

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--config',default='config/locations.json'); ap.add_argument('--date'); args=ap.parse_args()
    cfg=load_config(args.config); d=datetime.fromisoformat(args.date).date() if args.date else datetime.now().date()-timedelta(days=1)
    for loc in cfg.locations:
        base=f'{d.isoformat()}_{loc.id}'; p=PROJECT_ROOT/'data'/'forecasts'/f'{base}.json'
        if not p.exists(): print('Forecast file not found, skipping:',p); continue
        forecast=load_json(p); actual=fetch_historical_actual(OpenMeteoRequest(loc.latitude,loc.longitude,cfg.timezone),d); summary=summarize_actual(actual,d,cfg.forecast_window); val=compare_forecast_to_actual(forecast,summary)
        save_json(PROJECT_ROOT/'data'/'validation'/f'{base}_validation.json', val); save_text(PROJECT_ROOT/'data'/'validation'/f'{base}_validation.md', render_validation_markdown(val)); print('Saved validation',base)
if __name__=='__main__': main()
