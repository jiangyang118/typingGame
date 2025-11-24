import pygame
import random
import sys

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

# --- 字体设置 ---
# 尝试使用系统黑体，如果失败则使用默认
try:
    font_path = pygame.font.match_font('simhei') # 寻找黑体
    GAME_FONT = pygame.font.Font(font_path, 60)
    SCORE_FONT = pygame.font.Font(font_path, 30)
except:
    GAME_FONT = pygame.font.SysFont('arial', 60, bold=True)
    SCORE_FONT = pygame.font.SysFont('arial', 30)

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
    
    targets = []
    spawn_timer = 0
    
    # 难度控制
    speed = 1.0
    spawn_rate = 120 # 帧数

    running = True
    while running:
        screen.fill(BG_COLOR)
        
        # --- 事件处理 ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if game_state == "MENU":
                    if event.key == pygame.K_1:
                        current_level = 1
                        targets = []
                        score = 0
                        game_state = "PLAY"
                    elif event.key == pygame.K_2:
                        current_level = 2
                        targets = []
                        score = 0
                        game_state = "PLAY"
                    elif event.key == pygame.K_3:
                        current_level = 3
                        targets = []
                        score = 0
                        game_state = "PLAY"
                
                elif game_state == "PLAY":
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
            esc_surf = SCORE_FONT.render("按 ESC 返回", True, (150, 150, 150))
            screen.blit(esc_surf, (WIDTH - 150, 20))
            
            # 检查 ESC
            keys = pygame.key.get_pressed()
            if keys[pygame.K_ESCAPE]:
                game_state = "MENU"

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()