#!/usr/bin/env python3
from __future__ import annotations
import argparse
import os
import json
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from pathlib import Path

try:
    import yaml
except Exception:
    yaml = None

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def find_font() -> Optional[str]:
    cand = ["DejaVuSans.ttf","NotoSans-Regular.ttf","LiberationSans-Regular.ttf","FreeSans.ttf","Ubuntu-R.ttf"]
    roots = ["/usr/share/fonts","/usr/local/share/fonts","/usr/share/fonts/truetype","/usr/share/fonts/opentype"]
    for root in roots:
        if os.path.isdir(root):
            for dp,_,fs in os.walk(root):
                for n in cand:
                    p=os.path.join(dp,n)
                    if os.path.isfile(p): return p
    return None

def build_styles(font_name:str):
    st=getSampleStyleSheet()
    for s in st.byName.values(): s.fontName=font_name
    st.add(ParagraphStyle(name="Small", parent=st["Normal"], fontSize=9, leading=12, alignment=TA_LEFT, fontName=font_name))
    return st

def md_table(headers: List[str], rows: List[List[str]]) -> str:
    lines=["| "+" | ".join(headers)+" |","|"+"|".join(["---"]*len(headers))+"|"]
    for r in rows: lines.append("| "+" | ".join(r)+" |")
    return "\n".join(lines)

@dataclass
class NoteData:
    title: str
    date: str
    author: str = "Foritech"
    version: str = "v1.0"
    summary: str = ""
    context: List[str] = field(default_factory=list)
    achieved: List[str] = field(default_factory=list)
    decisions: List[List[str]] = field(default_factory=list)  # [topic, decision, reason, impact]
    risks: List[str] = field(default_factory=list)
    next_today: List[str] = field(default_factory=list)
    next_2_3_days: List[str] = field(default_factory=list)
    next_week: List[str] = field(default_factory=list)
    ci: List[str] = field(default_factory=list)
    metrics: List[str] = field(default_factory=list)
    links: List[str] = field(default_factory=list)

def render_md(nd: NoteData) -> str:
    parts=[]
    parts.append(f"# {nd.title}\n")
    parts.append(f"**Дата:** {nd.date}  \n**Автор:** {nd.author}  \n**Версия:** {nd.version}\n")
    parts.append("## Резюме\n"+(nd.summary.strip() or "(попълни)")+"\n")
    if nd.context: parts.append("## Контекст\n"+"\n".join(f"- {x}" for x in nd.context)+"\n")
    if nd.achieved: parts.append("## Постигнато\n"+"\n".join(f"- [x] {x}" for x in nd.achieved)+"\n")
    if nd.decisions:
        parts.append("## Взети решения")
        parts.append(md_table(["Тема","Решение","Причина","Влияние"], nd.decisions)); parts.append("")
    if nd.risks: parts.append("## Блокери / Рискове\n"+"\n".join(f"- {x}" for x in nd.risks)+"\n")
    parts.append("## Следващи стъпки")
    parts.append("**Днес:**\n"+"\n".join(f"- {x}" for x in (nd.next_today or ["(попълни)"])))
    parts.append("\n**Следващи 2–3 дни:**\n"+"\n".join(f"- {x}" for x in (nd.next_2_3_days or ["(попълни)"])))
    parts.append("\n**Следваща седмица:**\n"+"\n".join(f"- {x}" for x in (nd.next_week or ["(попълни)"]))+"\n")
    if nd.ci: parts.append("## CI/Автоматизация\n"+"\n".join(f"- {x}" for x in nd.ci)+"\n")
    if nd.metrics: parts.append("## Метрики / Тестове\n"+"\n".join(f"- {x}" for x in nd.metrics)+"\n")
    if nd.links: parts.append("## Артефакти/Линкове\n"+"\n".join(f"- {x}" for x in nd.links)+"\n")
    return "\n".join(parts)

def render_pdf(path: str, nd: NoteData):
    fp=find_font(); font="EmbeddedSans"
    if fp: pdfmetrics.registerFont(TTFont(font, fp))
    else: font="Helvetica"
    st=build_styles(font); story=[]
    story.append(Paragraph(nd.title, st["Title"])); story.append(Spacer(1,8))
    meta=[["Дата", nd.date],["Автор", nd.author],["Версия", nd.version]]
    t=Table(meta, colWidths=[110,380]); t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#4CAF50")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTNAME",(0,0),(-1,-1),font),
        ("FONTSIZE",(0,0),(-1,-1),9),
        ("GRID",(0,0),(-1,-1),0.5,colors.grey),
    ]))
    story.append(t); story.append(Spacer(1,8))
    def bullets(title, items):
        if not items: return
        story.append(Paragraph(title, st["Heading2"]))
        story.append(ListFlowable([ListItem(Paragraph(x, st["Normal"])) for x in items], bulletType="bullet"))
        story.append(Spacer(1,8))
    story.append(Paragraph("Резюме", st["Heading2"]))
    story.append(Paragraph(nd.summary or "(попълни)", st["Normal"])); story.append(Spacer(1,8))
    bullets("Контекст", nd.context)
    bullets("Постигнато", nd.achieved)
    if nd.decisions:
        data=[["Тема","Решение","Причина","Влияние"], *nd.decisions]
        tt=Table(data, colWidths=[90,150,140,110]); tt.setStyle(TableStyle([
            ("FONTNAME",(0,0),(-1,-1),font),
            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#4CAF50")),
            ("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("GRID",(0,0),(-1,-1),0.5,colors.grey)
        ])); story.append(Paragraph("Взети решения", st["Heading2"])); story.append(tt); story.append(Spacer(1,8))
    bullets("Блокери / Рискове", nd.risks)
    story.append(Paragraph("Следващи стъпки", st["Heading2"]))
    bullets("Днес", nd.next_today or ["(попълни)"])
    bullets("Следващи 2–3 дни", nd.next_2_3_days or ["(попълни)"])
    bullets("Следваща седмица", nd.next_week or ["(попълни)"])
    bullets("CI/Автоматизация", nd.ci)
    bullets("Метрики / Тестове", nd.metrics)
    bullets("Артефакти/Линкове", nd.links)
    SimpleDocTemplate(path, pagesize=A4, leftMargin=36,rightMargin=36,topMargin=36,bottomMargin=36).build(story)

def load_sections(path:str)->dict:
    p=Path(path)
    if not p.exists(): raise SystemExit(f"Sections file not found: {p}")
    if p.suffix.lower() in (".yml",".yaml"):
        if yaml is None: raise SystemExit("PyYAML required. pip install pyyaml")
        return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    if p.suffix.lower()==".json":
        return json.loads(p.read_text(encoding="utf-8"))
    raise SystemExit("Use .yml/.yaml or .json")

def main()->int:
    ap=argparse.ArgumentParser(description="Foritech Note generator (MD + PDF)")
    sub=ap.add_subparsers(dest="cmd", required=True)
    t=sub.add_parser("template"); t.add_argument("--out", required=True)
    n=sub.add_parser("note")
    n.add_argument("--title", required=True); n.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    n.add_argument("--author", default="Foritech"); n.add_argument("--version", default="v1.0")
    n.add_argument("--sections", required=True); n.add_argument("--out", required=True)
    args=ap.parse_args()

    if args.cmd=="template":
        nd=NoteData(title="Foritech Project Note — TEMPLATE", date=datetime.now().strftime("%Y-%m-%d"),
                    summary="Кратко обобщение (2–3 изречения).",
                    context=["Проект/модул: …","Branch/tag: …","Обхват на бележката: …"],
                    achieved=["Точка 1","Точка 2","Точка 3"],
                    decisions=[["Тема","Решение","Причина","Влияние"]],
                    risks=["Риск/Блокер: …  |  Митигиране: …"],
                    next_today=["(попълни)"], next_2_3_days=["(попълни)"], next_week=["(попълни)"],
                    ci=["Статус на CI: …","Нощни джобове / ъпдейти: …"],
                    metrics=["Изпълнени тестове: …","Производителност: …"],
                    links=["PR/Commit: …","Документация: …","Билд артефакт: …"])
        Path(args.out+".md").write_text(render_md(nd), encoding="utf-8")
        render_pdf(args.out+".pdf", nd); print(f"Wrote {args.out}.md and {args.out}.pdf"); return 0

    if args.cmd=="note":
        sec=load_sections(args.sections)
        nd=NoteData(title=args.title, date=args.date, author=args.author, version=args.version,
                    summary=sec.get("summary",""),
                    context=list(sec.get("context",[]) or []),
                    achieved=list(sec.get("achieved",[]) or []),
                    decisions=[list(map(str,row)) for row in (sec.get("decisions",[]) or [])],
                    risks=list(sec.get("risks",[]) or []),
                    next_today=list(sec.get("next_today",[]) or []),
                    next_2_3_days=list(sec.get("next_2_3_days",[]) or []),
                    next_week=list(sec.get("next_week",[]) or []),
                    ci=list(sec.get("ci",[]) or []),
                    metrics=list(sec.get("metrics",[]) or []),
                    links=list(sec.get("links",[]) or []))
        Path(args.out+".md").write_text(render_md(nd), encoding="utf-8")
        render_pdf(args.out+".pdf", nd); print(f"Wrote {args.out}.md and {args.out}.pdf"); return 0
    return 1

if __name__=="__main__":
    raise SystemExit(main())
