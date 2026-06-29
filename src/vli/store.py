from __future__ import annotations
from pathlib import Path
import json
from typing import Any

def save_json(path:Path,data:dict[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def save_text(path:Path,text:str)->None:
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(text,encoding='utf-8')
def load_json(path:Path)->dict[str,Any]: return json.loads(path.read_text(encoding='utf-8'))
