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
            title_surf = GAME_FONT.render("彩虹打字大冒险", True, COLORS[0])
            info_surf1 = SCORE_FONT.render("按 1 : 大写字母练习", True, BLACK)
            info_surf2 = SCORE_FONT.render("按 2 : 小写字母练习", True, BLACK)
            info_surf3 = SCORE_FONT.render("按 3 : 拼音练习 (如 ba)", True, BLACK)
            
            screen.blit(title_surf, (WIDTH//2 - title_surf.get_width()//2, 150))
            screen.blit(info_surf1, (WIDTH//2 - info_surf1.get_width()//2, 250))
            screen.blit(info_surf2, (WIDTH//2 - info_surf2.get_width()//2, 300))
            screen.blit(info_surf3, (WIDTH//2 - info_surf3.get_width()//2, 350))

            # 显示每个模式的历史最佳与最近平均（最近 5 次）
            def stat_line(lvl):
                s = compute_stats(cached_rows, recent_n).get(lvl, {'best':0,'recent_avg':0})
                return f"最佳: {s['best']}  最近{recent_n}次平均: {s['recent_avg']}"
            stats1 = SCORE_FONT.render(stat_line(1), True, (80,80,80))
            stats2 = SCORE_FONT.render(stat_line(2), True, (80,80,80))
            stats3 = SCORE_FONT.render(stat_line(3), True, (80,80,80))
            screen.blit(stats1, (WIDTH//2 - stats1.get_width()//2, 250+30))
            screen.blit(stats2, (WIDTH//2 - stats2.get_width()//2, 300+30))
            screen.blit(stats3, (WIDTH//2 - stats3.get_width()//2, 350+30))

            # 提示切换统计窗口
            tip = SCORE_FONT.render("按 T 切换统计窗口 (5/10/30)", True, (120,120,120))
            screen.blit(tip, (WIDTH//2 - tip.get_width()//2, 400+30))
            
        elif game_state == "PLAY":
            # 生成目标
            spawn_timer += 1
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
