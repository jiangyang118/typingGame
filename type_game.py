#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pygame
import random
import sys
import os
import glob
import csv
import time
from datetime import datetime
import webbrowser
import importlib

# --- 初始化设置 ---
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("一年级彩虹打字大冒险")

# --- 颜色定义 (马卡龙色系，保护视力且可爱) ---
WHITE = (255, 255, 255)
BLACK = (50, 50, 50)
BG_COLOR = (230, 245, 255) # 淡蓝色背景
COLORS = [(255, 105, 97), (255, 180, 128), (248, 243, 141), (66, 214, 164), (89, 173, 246)]

def load_fonts():
    """加载支持中文的字体：优先使用项目自带字体，其次匹配系统常见中文字体。

    返回: (GAME_FONT, SCORE_FONT)
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    assets_font_dir = os.path.join(base_dir, 'assets', 'fonts')

    # 1) 项目自带字体（将 .ttf/.otf 放到 assets/fonts/ 下即可生效）
    custom_fonts = []
    for pattern in ("*.ttf", "*.otf", "*.ttc"):
        custom_fonts.extend(glob.glob(os.path.join(assets_font_dir, pattern)))

    if custom_fonts:
        font_file = sorted(custom_fonts)[0]
        try:
            game_font = pygame.font.Font(font_file, 60)
            score_font = pygame.font.Font(font_file, 30)
            return game_font, score_font
        except Exception:
            pass

    # 2) 尝试通过 match_font 精确匹配常见中文字体文件路径
    match_candidates = [
        # Windows
        'msyh', 'microsoft yahei', 'simhei', 'simsun', 'dengxian',
        # macOS
        'pingfang sc', 'heiti sc', 'stheiti', 'hiragino sans gb',
        # Linux / 通用
        'noto sans cjk sc', 'noto sans cjk', 'source han sans cn', 'wenquanyi zen hei'
    ]

    for name in match_candidates:
        try:
            path = pygame.font.match_font(name)
            if path:
                game_font = pygame.font.Font(path, 60)
                score_font = pygame.font.Font(path, 30)
                return game_font, score_font
        except Exception:
            continue

    # 3) 系统常见中文字体候选（跨平台）使用 SysFont 名称
    candidates = [
        # Windows
        'Microsoft YaHei', 'msyh', 'SimHei', 'SimSun', 'DengXian',
        # macOS
        'PingFang SC', 'Heiti SC', 'STHeiti', 'Hiragino Sans GB',
        # Linux / 通用
        'Noto Sans CJK SC', 'Source Han Sans CN', 'WenQuanYi Zen Hei', 'Noto Sans CJK',
        # 英文字体中包含全字库的（有时可用）
        'Arial Unicode MS'
    ]

    for name in candidates:
        try:
            # SysFont 会在找不到时降级，但这里我们只要能成功创建就算可用
            game_font = pygame.font.SysFont(name, 60)
            score_font = pygame.font.SysFont(name, 30)
            if game_font and score_font:
                return game_font, score_font
        except Exception:
            continue

    # 4) 兜底：Arial（可能无法显示中文，会出现方块）
    return (
        pygame.font.SysFont('arial', 60, bold=True),
        pygame.font.SysFont('arial', 30)
    )

# --- 字体设置 ---
GAME_FONT, SCORE_FONT = load_fonts()

# --- 游戏数据 ---
# 第一关：认识字母（大写）
LEVEL_1 = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
# 第二关：认识字母（小写）
LEVEL_2 = list("abcdefghijklmnopqrstuvwxyz")
# 第三关：简单拼音（声母+韵母）
LEVEL_3 = ["ba", "bo", "ma", "fo", "de", "te", "ni", "le", "ge", "ke", "he"]

class Target:
    def __init__(self, text, speed):
        self.text = text
        self.color = random.choice(COLORS)
        self.x = random.randint(50, WIDTH - 100)
        self.y = -50
        self.speed = speed
        self.completed_part = "" # 已经打出的部分 (用于拼音模式)

    def draw(self, surface):
        # 渲染未完成的部分
        full_surf = GAME_FONT.render(self.text, True, self.color)
        surface.blit(full_surf, (self.x, self.y))
        
        # 如果打对了一部分，用灰色覆盖显示进度（针对拼音）
        if self.completed_part:
            comp_surf = GAME_FONT.render(self.completed_part, True, (200, 200, 200))
            surface.blit(comp_surf, (self.x, self.y))

    def move(self):
        self.y += self.speed

def main():
    clock = pygame.time.Clock()
    score = 0
    game_state = "MENU" # MENU, PLAY, GAMEOVER
    current_level = 1
    session_active = False
    session_start_ts = None
    
    targets = []
    spawn_timer = 0
    
    # 难度控制
    speed = 1.0
    spawn_rate = 120 # 帧数

    # 进度记录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    scores_csv = os.path.join(data_dir, 'scores.csv')

    def save_session(level:int, final_score:int, start_ts:float):
        try:
            duration = max(0, int(time.time() - (start_ts or time.time())))
            completed = max(0, final_score // 10)
            mode_name = {1: '大写字母', 2: '小写字母', 3: '拼音'}[level]
            is_new = not os.path.exists(scores_csv)
            with open(scores_csv, 'a', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                if is_new:
                    writer.writerow(['timestamp', 'level', 'mode', 'score', 'duration_sec', 'completed'])
                writer.writerow([datetime.now().isoformat(timespec='seconds'), level, mode_name, final_score, duration, completed])
        except Exception:
            # 不因记录失败中断游戏
            pass

    recent_options = [5, 10, 30]
    recent_idx = 0
    recent_n = recent_options[recent_idx]

    def load_scores():
        rows = []
        if not os.path.exists(scores_csv):
            return rows
        try:
            with open(scores_csv, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for r in reader:
                    try:
                        rows.append({
                            'timestamp': r.get('timestamp',''),
                            'level': int(r.get('level', '0') or 0),
                            'mode': r.get('mode',''),
                            'score': int(r.get('score','0') or 0),
                            'duration_sec': int(r.get('duration_sec','0') or 0),
                            'completed': int(r.get('completed','0') or 0),
                        })
                    except Exception:
                        continue
        except Exception:
            pass
        return rows

    def compute_stats(rows, n):
        stats = {}
        for lvl in (1,2,3):
            lv_rows = [r for r in rows if r['level']==lvl]
            if not lv_rows:
                stats[lvl] = {'best': 0, 'recent_avg': 0}
            else:
                best = max(r['score'] for r in lv_rows)
                recent = lv_rows[-n:]
                if recent:
                    avg = int(sum(r['score'] for r in recent)/len(recent))
                else:
                    avg = 0
                stats[lvl] = {'best': best, 'recent_avg': avg}
        return stats

    cached_rows = load_scores()
    # 菜单渲染时动态计算，确保按 T 切换生效

    # --- 菜单按钮与动作 ---
    last_message = ""
    last_message_ttl = 0  # 帧计数，>0 时显示消息

    def set_message(text: str, ttl_frames: int = 180):
        nonlocal last_message, last_message_ttl
        last_message = text
        last_message_ttl = ttl_frames

    def export_report(period: str):
        try:
            sys.path.append(os.path.join(base_dir, 'tools'))
            export_report_mod = importlib.import_module('export_report')
            rows = export_report_mod.read_rows(scores_csv)
            agg = export_report_mod.aggregate(rows, period)
            out_path = os.path.join(data_dir, f'report_{"weekly" if period=="weekly" else "monthly"}.csv')
            export_report_mod.write_csv(agg, out_path)
            set_message(f"已导出{ '周报' if period=='weekly' else '月报' }到 {out_path}")
        except Exception:
            set_message("导出失败，请稍后再试")

    def build_and_open_html_report(recent_count: int = 30):
        try:
            sys.path.append(os.path.join(base_dir, 'tools'))
            viz = importlib.import_module('visualize_report')
            rows = viz.read_rows(scores_csv)
            mode_rows = viz.group_by_mode(rows)
            html = viz.build_html(mode_rows, recent=recent_count)
            out_path = os.path.join(data_dir, 'report.html')
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(html)
            opened = webbrowser.open('file://' + out_path)
            set_message("已生成并尝试打开报告" + ("" if opened else "（请手动打开 data/report.html）"))
        except Exception:
            set_message("生成报告失败，请稍后再试")

    running = True
    while running:
        screen.fill(BG_COLOR)
        
        # --- 事件处理 ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # 关闭前保存当前局成绩
                if game_state == "PLAY" and session_active:
                    save_session(current_level, score, session_start_ts)
                    cached_rows.append({'timestamp': datetime.now().isoformat(timespec='seconds'), 'level': current_level, 'mode': {1:'大写字母',2:'小写字母',3:'拼音'}[current_level], 'score': score, 'duration_sec': max(0,int(time.time()-(session_start_ts or time.time()))), 'completed': max(0, score//10)})
                    cached_stats = compute_stats(cached_rows)
                    session_active = False
                running = False
            
            if event.type == pygame.KEYDOWN:
                if game_state == "MENU":
                    if event.key == pygame.K_1:
                        current_level = 1
                        targets = []
                        score = 0
                        session_active = True
                        session_start_ts = time.time()
                        game_state = "PLAY"
                    elif event.key == pygame.K_2:
                        current_level = 2
                        targets = []
                        score = 0
                        session_active = True
                        session_start_ts = time.time()
                        game_state = "PLAY"
                    elif event.key == pygame.K_3:
                        current_level = 3
                        targets = []
                        score = 0
                        session_active = True
                        session_start_ts = time.time()
                        game_state = "PLAY"
                    elif event.key == pygame.K_t:
                        # 切换“最近 N 次”统计窗口
                        recent_idx = (recent_idx + 1) % len(recent_options)
                        recent_n = recent_options[recent_idx]
                    elif event.key == pygame.K_e:
                        export_report('weekly')
                    elif event.key == pygame.K_m:
                        export_report('monthly')
                    elif event.key == pygame.K_v:
                        build_and_open_html_report(recent_n)
                
                elif game_state == "PLAY":
                    if event.key == pygame.K_ESCAPE:
                        # 返回菜单并保存成绩
                        if session_active:
                            save_session(current_level, score, session_start_ts)
                            cached_rows.append({'timestamp': datetime.now().isoformat(timespec='seconds'), 'level': current_level, 'mode': {1:'大写字母',2:'小写字母',3:'拼音'}[current_level], 'score': score, 'duration_sec': max(0,int(time.time()-(session_start_ts or time.time()))), 'completed': max(0, score//10)})
                            session_active = False
                        game_state = "MENU"
                        continue
                    char = event.unicode
                    # 寻找屏幕上最靠下的一个目标进行匹配
                    if targets:
                        # 找到最下面的且未完成的目标
                        target = min(targets, key=lambda t: t.y)
                        
                        # 逻辑：检查按键是否匹配目标当前需要的字符
                        needed_char = target.text[len(target.completed_part)]
                        
                        # 忽略大小写差异（对一年级友好）
                        if char.lower() == needed_char.lower():
                            target.completed_part += needed_char
                            # 播放音效占位 print("Ding!") 
                            
                            if target.completed_part == target.text:
                                score += 10
                                targets.remove(target)
                        
        # --- 游戏逻辑与渲染 ---
        if game_state == "MENU":
            # UI 常量
            PANEL_BG = (250, 252, 255)
            PANEL_BORDER = (210, 220, 230)

            def draw_panel(x, y, w, h, title_text=None):
                rect = pygame.Rect(x, y, w, h)
                pygame.draw.rect(screen, PANEL_BG, rect, border_radius=12)
                pygame.draw.rect(screen, PANEL_BORDER, rect, width=2, border_radius=12)
                if title_text:
                    title = SCORE_FONT.render(title_text, True, (70, 70, 70))
                    screen.blit(title, (x + 12, y + 8))
                return rect

            def draw_button(text, x, y, action, center=False):
                surf = SCORE_FONT.render(text, True, (30, 30, 30))
                padding_x, padding_y = 16, 8
                rect = pygame.Rect(0, 0, surf.get_width() + padding_x * 2, surf.get_height() + padding_y * 2)
                if center:
                    rect.centerx = x
                    rect.y = y
                else:
                    rect.x = x
                    rect.y = y
                pygame.draw.rect(screen, (255, 255, 255), rect, border_radius=8)
                pygame.draw.rect(screen, PANEL_BORDER, rect, width=2, border_radius=8)
                screen.blit(surf, (rect.x + padding_x, rect.y + padding_y))
                menu_buttons.append((rect, action))

            # 标题
            title_surf = GAME_FONT.render("彩虹打字大冒险", True, COLORS[0])
            screen.blit(title_surf, (WIDTH//2 - title_surf.get_width()//2, 50))

            # 操作反馈提示（标题下方）
            if last_message_ttl > 0 and last_message:
                msg = SCORE_FONT.render(last_message, True, (60, 120, 60))
                screen.blit(msg, (WIDTH//2 - msg.get_width()//2, 120))
                last_message_ttl -= 1

            menu_buttons = []

            # 左侧：开始面板
            left_x, left_y, left_w, left_h = 60, 150, 360, 260
            draw_panel(left_x, left_y, left_w, left_h, "开始练习")
            btn_y = left_y + 60
            vspace = 68
            draw_button("开始：大写字母", left_x + 20, btn_y, 'START_1')
            draw_button("开始：小写字母", left_x + 20, btn_y + vspace, 'START_2')
            draw_button("开始：拼音", left_x + 20, btn_y + vspace * 2, 'START_3')

            # 右侧：统计面板
            right_x, right_y, right_w = 460, 150, 280
            stat_h = 170
            draw_panel(right_x, right_y, right_w, stat_h, "统计（按 T 也可切换）")
            def stat_line(lvl):
                s = compute_stats(cached_rows, recent_n).get(lvl, {'best': 0, 'recent_avg': 0})
                return f"最佳 {s['best']}｜最近{recent_n}次 {s['recent_avg']}"
            s1 = SCORE_FONT.render("大写：" + stat_line(1), True, (80, 80, 80))
            s2 = SCORE_FONT.render("小写：" + stat_line(2), True, (80, 80, 80))
            s3 = SCORE_FONT.render("拼音：" + stat_line(3), True, (80, 80, 80))
            screen.blit(s1, (right_x + 16, right_y + 50))
            screen.blit(s2, (right_x + 16, right_y + 50 + 40))
            screen.blit(s3, (right_x + 16, right_y + 50 + 80))
            draw_button(f"切换统计：最近{recent_n}次", right_x + 16, right_y + stat_h - 54, 'TOGGLE_RECENT')

            # 右下：报表与报告
            rep_y = right_y + stat_h + 20
            rep_h = 180
            draw_panel(right_x, rep_y, right_w, rep_h, "报表与报告")
            draw_button("导出周报 CSV", right_x + 16, rep_y + 50, 'EXPORT_WEEKLY')
            draw_button("导出月报 CSV", right_x + 16, rep_y + 50 + 48, 'EXPORT_MONTHLY')
            draw_button("查看学习报告", right_x + 16, rep_y + 50 + 96, 'VIEW_REPORT')

            # 底部提示
            tip = SCORE_FONT.render("快捷键：1/2/3 开始 · T 切换统计 · E/M 导出 · V 查看报告", True, (120, 120, 120))
            screen.blit(tip, (WIDTH//2 - tip.get_width()//2, HEIGHT - 50))
            
        elif game_state == "PLAY":
            # 生成目标
            spawn_timer += 1
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and game_state == "MENU":
                mx, my = event.pos
                for rect, action in menu_buttons:
                    if rect.collidepoint(mx, my):
                        if action == 'START_1':
                            current_level = 1; targets = []; score = 0; session_active = True; session_start_ts = time.time(); game_state = 'PLAY'
                        elif action == 'START_2':
                            current_level = 2; targets = []; score = 0; session_active = True; session_start_ts = time.time(); game_state = 'PLAY'
                        elif action == 'START_3':
                            current_level = 3; targets = []; score = 0; session_active = True; session_start_ts = time.time(); game_state = 'PLAY'
                        elif action == 'TOGGLE_RECENT':
                            recent_idx = (recent_idx + 1) % len(recent_options)
                            recent_n = recent_options[recent_idx]
                        elif action == 'EXPORT_WEEKLY':
                            export_report('weekly')
                        elif action == 'EXPORT_MONTHLY':
                            export_report('monthly')
                        elif action == 'VIEW_REPORT':
                            build_and_open_html_report(recent_n)
                        break
            if spawn_timer > spawn_rate:
                spawn_timer = 0
                if current_level == 1:
                    txt = random.choice(LEVEL_1)
                elif current_level == 2:
                    txt = random.choice(LEVEL_2)
                else:
                    txt = random.choice(LEVEL_3)
                targets.append(Target(txt, speed))
            
            # 更新和绘制目标
            for t in targets[:]:
                t.move()
                t.draw(screen)
                if t.y > HEIGHT:
                    targets.remove(t)
                    # 不扣分，不Game Over，只通过让其消失来降低挫败感
            
            # 显示分数
            score_surf = SCORE_FONT.render(f"得分: {score}", True, COLORS[4])
            screen.blit(score_surf, (20, 20))
            
            # 简单的退出提示
            esc_surf = SCORE_FONT.render("按 ESC 返回（将记录成绩）", True, (150, 150, 150))
            screen.blit(esc_surf, (WIDTH - 260, 20))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
