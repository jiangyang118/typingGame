#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成可视化学习报告（HTML + 内嵌 SVG），无第三方依赖。

读取 data/scores.csv，按模式绘制：
- 折线图（最近 N 次成绩，默认 30）
- 周汇总柱状图（最近 12 周平均分）

用法：
  python tools/visualize_report.py --recent 30 --out data/report.html

输出：data/report.html
"""
import argparse
import csv
import os
from datetime import datetime


MODE_NAME = {1: '大写字母', 2: '小写字母', 3: '拼音'}
MODE_COLOR = {1: '#ff6a5c', 2: '#4ecdc4', 3: '#556cd6'}


def read_rows(csv_path):
    rows = []
    if not os.path.exists(csv_path):
        return rows
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                ts = r.get('timestamp', '')
                try:
                    dt = datetime.fromisoformat(ts)
                except Exception:
                    continue
                rows.append({
                    'dt': dt,
                    'timestamp': ts,
                    'level': int(r.get('level', '0') or 0),
                    'mode': r.get('mode', ''),
                    'score': int(r.get('score', '0') or 0),
                    'duration_sec': int(r.get('duration_sec', '0') or 0),
                    'completed': int(r.get('completed', '0') or 0),
                })
            except Exception:
                continue
    # 时间升序
    rows.sort(key=lambda x: x['dt'])
    return rows


def group_by_mode(rows):
    out = {1: [], 2: [], 3: []}
    for r in rows:
        if r['level'] in out:
            out[r['level']].append(r)
    return out


def isoweek_key(dt: datetime):
    year, week, _ = dt.isocalendar()
    return f"{year}-W{week:02d}"


def weekly_aggregate(rows):
    # 返回最近 12 周（有数据的周）平均分列表
    bucket = {}
    for r in rows:
        k = isoweek_key(r['dt'])
        bucket.setdefault(k, []).append(r['score'])
    items = []
    for k, scores in bucket.items():
        if scores:
            items.append((k, int(sum(scores)/len(scores))))
    items.sort(key=lambda x: x[0])
    return items[-12:]


def stats_summary(rows):
    if not rows:
        return {'count': 0, 'best': 0, 'avg': 0}
    count = len(rows)
    best = max(r['score'] for r in rows)
    avg = int(sum(r['score'] for r in rows)/count)
    return {'count': count, 'best': best, 'avg': avg}


def nice_max(val, step=50):
    if val <= 0:
        return step
    m = ((val + step - 1) // step) * step
    return max(m, step)


def svg_line_chart(title, points, width=760, height=260, color='#556cd6'):
    # points: list of (label, value)
    padding = 40
    inner_w = width - padding*2
    inner_h = height - padding*2
    if not points:
        return f"""
<div class='chart'>
  <h3>{title}</h3>
  <div class='nodata'>暂无数据</div>
</div>"""
    values = [v for _, v in points]
    vmax = nice_max(max(values), 50)
    # 坐标转换
    def tx(i):
        if len(points) == 1:
            return padding + inner_w // 2
        return padding + int(i * inner_w / (len(points)-1))
    def ty(v):
        return padding + int((vmax - v) * inner_h / vmax)
    # polyline
    pts = " ".join(f"{tx(i)},{ty(v)}" for i, (_, v) in enumerate(points))
    # x 轴刻度每 1 个点、y 轴每 step
    y_grid = []
    step = vmax // 5 or 10
    for yv in range(0, vmax+1, step):
        y = ty(yv)
        y_grid.append(f"<line x1='{padding}' y1='{y}' x2='{width-padding}' y2='{y}' class='grid' />"
                      f"<text x='{padding-8}' y='{y+4}' class='axis' text-anchor='end'>{yv}</text>")
    # x 轴仅显示首尾标签
    x_labels = []
    if points:
        x_labels.append(f"<text x='{tx(0)}' y='{height-8}' class='axis' text-anchor='start'>{points[0][0]}</text>")
        if len(points) > 1:
            x_labels.append(f"<text x='{tx(len(points)-1)}' y='{height-8}' class='axis' text-anchor='end'>{points[-1][0]}</text>")

    dots = "\n".join(f"<circle cx='{tx(i)}' cy='{ty(v)}' r='3' fill='{color}' />" for i, (_, v) in enumerate(points))
    svg = f"""
<div class='chart'>
  <h3>{title}</h3>
  <svg width='{width}' height='{height}' viewBox='0 0 {width} {height}'>
    <rect x='0' y='0' width='{width}' height='{height}' fill='white'/>
    {''.join(y_grid)}
    <polyline fill='none' stroke='{color}' stroke-width='2' points='{pts}' />
    {dots}
    {''.join(x_labels)}
  </svg>
</div>"""
    return svg


def svg_bar_chart(title, items, width=760, height=260, color='#4ecdc4'):
    # items: list of (label, value)
    padding = 40
    inner_w = width - padding*2
    inner_h = height - padding*2
    if not items:
        return f"""
<div class='chart'>
  <h3>{title}</h3>
  <div class='nodata'>暂无数据</div>
</div>"""
    vmax = nice_max(max(v for _, v in items), 50)
    n = len(items)
    bar_w = max(8, int(inner_w / max(1, n) * 0.6))
    gap = int(inner_w / max(1, n))
    def bx(i):
        return padding + i*gap + (gap - bar_w)//2
    def by(v):
        return padding + int((vmax - v) * inner_h / vmax)
    y_grid = []
    step = vmax // 5 or 10
    for yv in range(0, vmax+1, step):
        y = by(yv)
        y_grid.append(f"<line x1='{padding}' y1='{y}' x2='{width-padding}' y2='{y}' class='grid' />"
                      f"<text x='{padding-8}' y='{y+4}' class='axis' text-anchor='end'>{yv}</text>")
    bars = []
    labels = []
    for i, (lab, v) in enumerate(items):
        x = bx(i)
        y = by(v)
        h = (padding + inner_h) - y
        bars.append(f"<rect x='{x}' y='{y}' width='{bar_w}' height='{h}' fill='{color}' />")
        labels.append(f"<text x='{x+bar_w/2}' y='{padding+inner_h+12}' class='axis' text-anchor='middle'>{lab}</text>")
    svg = f"""
<div class='chart'>
  <h3>{title}</h3>
  <svg width='{width}' height='{height}' viewBox='0 0 {width} {height}'>
    <rect x='0' y='0' width='{width}' height='{height}' fill='white'/>
    {''.join(y_grid)}
    {''.join(bars)}
    {''.join(labels)}
  </svg>
</div>"""
    return svg


def build_html(mode_rows, recent=30):
    parts = []
    header = """
<!doctype html>
<html lang="zh-CN">
<meta charset="utf-8" />
<title>学习报告</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', 'Noto Sans CJK SC', Arial, sans-serif; color: #333; }
  h1 { margin: 16px 0; }
  .section { margin-bottom: 28px; }
  .chart { margin: 12px 0 24px; }
  .chart h3 { margin: 8px 0; font-weight: 600; }
  .grid { stroke: #eee; stroke-width: 1; }
  .axis { fill: #666; font-size: 12px; }
  .summary { display: flex; gap: 16px; flex-wrap: wrap; margin: 8px 0 12px; }
  .card { border: 1px solid #eee; border-radius: 8px; padding: 8px 12px; background: #fafafa; }
  .mode-title { display: inline-flex; align-items: center; gap: 8px; }
  .dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
  .nodata { color: #999; font-size: 14px; padding: 8px 0; }
  .footer { color: #aaa; font-size: 12px; margin-top: 24px; }
</style>
<body>
<h1>学习报告</h1>
<div class='section'>最近 {recent} 次：折线图；最近 12 周：柱状图</div>
""".replace('{recent}', str(recent))
    parts.append(header)

    for lvl in (1, 2, 3):
        rows = mode_rows.get(lvl, [])
        name = MODE_NAME.get(lvl, str(lvl))
        color = MODE_COLOR.get(lvl, '#556cd6')
        parts.append("<div class='section'>")
        parts.append(f"<div class='mode-title'><span class='dot' style='background:{color}'></span><h2 style='margin:0'>{name}</h2></div>")

        # 概览
        s_all = stats_summary(rows)
        recent_rows = rows[-recent:]
        s_recent = stats_summary(recent_rows)
        parts.append("<div class='summary'>")
        parts.append(f"<div class='card'>历史次数：{s_all['count']}</div>")
        parts.append(f"<div class='card'>历史最佳：{s_all['best']}</div>")
        parts.append(f"<div class='card'>历史平均：{s_all['avg']}</div>")
        parts.append(f"<div class='card'>最近{recent}次平均：{s_recent['avg']}</div>")
        parts.append("</div>")

        # 折线图（最近 N 次）
        line_points = [(r['dt'].strftime('%m-%d'), r['score']) for r in recent_rows]
        parts.append(svg_line_chart('最近成绩（分数）', line_points, color=color))

        # 周汇总柱状图（最近 12 周平均）
        wk = weekly_aggregate(rows)
        # 压缩 label 显示：仅显示后缀 Wxx
        wk_items = [(lab.split('-W')[-1], avg) for (lab, avg) in wk]
        parts.append(svg_bar_chart('每周平均分（最近 12 周）', wk_items, color=color))

        parts.append("</div>")

    parts.append("<div class='footer'>由 visualize_report.py 生成</div>")
    parts.append("</body></html>")
    return "\n".join(parts)


def main():
    p = argparse.ArgumentParser(description='生成可视化学习报告（HTML + SVG）')
    p.add_argument('--data', default='data/scores.csv', help='成绩 CSV 路径')
    p.add_argument('--out', default='data/report.html', help='输出 HTML 路径')
    p.add_argument('--recent', type=int, default=30, help='折线图使用最近 N 次')
    args = p.parse_args()

    rows = read_rows(args.data)
    mode_rows = group_by_mode(rows)
    html = build_html(mode_rows, recent=args.recent)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Report written to {args.out}")


if __name__ == '__main__':
    main()

