#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出周报/月报：基于 data/scores.csv 生成聚合报告。

输出：
- data/report_weekly.csv 或 data/report_monthly.csv

字段：period, level, mode, count, avg_score, best_score, avg_duration_sec, avg_completed
"""
import argparse
import csv
import os
from datetime import datetime


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
                    'level': int(r.get('level', '0') or 0),
                    'mode': r.get('mode', ''),
                    'score': int(r.get('score', '0') or 0),
                    'duration_sec': int(r.get('duration_sec', '0') or 0),
                    'completed': int(r.get('completed', '0') or 0),
                })
            except Exception:
                continue
    return rows


def group_key(period, dt: datetime):
    if period == 'weekly':
        year, week, _ = dt.isocalendar()
        return f"{year}-W{week:02d}"
    else:  # monthly
        return f"{dt.year}-{dt.month:02d}"


def aggregate(rows, period: str):
    groups = {}
    for r in rows:
        key = group_key(period, r['dt'])
        lvl = r['level']
        groups.setdefault(key, {}).setdefault(lvl, []).append(r)

    out = []
    mode_name = {1: '大写字母', 2: '小写字母', 3: '拼音'}
    for key, lv_map in sorted(groups.items()):
        for lvl in (1, 2, 3):
            items = lv_map.get(lvl, [])
            if not items:
                continue
            count = len(items)
            avg_score = int(sum(i['score'] for i in items) / count)
            best_score = max(i['score'] for i in items)
            avg_dur = int(sum(i['duration_sec'] for i in items) / count)
            avg_completed = float(sum(i['completed'] for i in items) / count)
            out.append({
                'period': key,
                'level': lvl,
                'mode': mode_name.get(lvl, str(lvl)),
                'count': count,
                'avg_score': avg_score,
                'best_score': best_score,
                'avg_duration_sec': avg_dur,
                'avg_completed': f"{avg_completed:.2f}",
            })
    return out


def write_csv(rows, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    headers = ['period', 'level', 'mode', 'count', 'avg_score', 'best_score', 'avg_duration_sec', 'avg_completed']
    with open(out_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def main():
    parser = argparse.ArgumentParser(description='导出成绩的周报/月报汇总')
    parser.add_argument('--period', choices=['weekly', 'monthly'], default='weekly', help='统计周期')
    parser.add_argument('--data', default='data/scores.csv', help='成绩 CSV 路径')
    parser.add_argument('--out', default=None, help='输出 CSV 路径（默认 data/report_*.csv）')
    args = parser.parse_args()

    rows = read_rows(args.data)
    agg = aggregate(rows, args.period)
    if not args.out:
        suffix = 'weekly' if args.period == 'weekly' else 'monthly'
        args.out = f'data/report_{suffix}.csv'
    write_csv(agg, args.out)
    print(f"Exported {len(agg)} rows to {args.out}")


if __name__ == '__main__':
    main()

