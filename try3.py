import math
import random
import sys
import os
import time
from pathlib import Path

import pygame as pg

os.chdir(os.path.dirname(os.path.abspath(__file__)))
pg.mixer.init() # 初期化（BGM用）

# ============================================================
# 設定
# ============================================================

SCREEN_WIDTH = 480
SCREEN_HEIGHT = 800
FPS = 60 
WINDOW_TITLE = "SPACE SHOOTER"

# Pythonファイルが保存されているフォルダ
BASE_DIR = Path(__file__).resolve().parent

# 画像ファイルの場所
BACKGROUND_IMAGE = str(BASE_DIR / "assets" / "background.png")
PLAYER_IMAGE = str(BASE_DIR / "assets" / "player.png")
ENEMY_IMAGE = str(BASE_DIR / "assets" / "enemy.png")
BOSS_IMAGE = str(BASE_DIR / "assets" / "boss.png") 
STAR_IMAGE = str(BASE_DIR / "assets" / "star.png") 
BOSS_BGM = str(BASE_DIR / "assets" / "sounds" / "boss_bgm.mp3") 
CLEAR_BGM = str(BASE_DIR / "assets" / "sounds" / "clear_bgm.mp3") 

PLAYER_SIZE = (64, 64)
PLAYER_SPEED = 5
PLAYER_SHOT_INTERVAL = 250  
PLAYER_BULLET_SPEED = 9
PLAYER_MAX_HP = 3                

ENEMY_SIZE = (48, 48)
ENEMY_SPEED = 2
ENEMY_SPAWN_INTERVAL = 1400  
ENEMY_SHOT_INTERVAL = 1600   
ENEMY_BULLET_SPEED = 4

# bossの設定
BOSS_SIZE = (100, 100)
BOSS_SPAWN_INTERVAL = 1400      
BOSS_SHOT_INTERVAL = 1000 
BOSS_BULLET_SPEED = 6

# 画像が読み込めない場合の仮表示色
PLAYER_COLOR = (80, 220, 255)
ENEMY_COLOR = (255, 100, 100)
PLAYER_BULLET_COLOR = (255, 245, 100)
ENEMY_BULLET_COLOR = (255, 120, 80)
BOSS_COLOR = (20, 220, 20) 
BOSS_BULLET_COLOR = (255, 0, 0) 

# アイテム設定
ITEM_SIZE = (32, 32)
ITEM_SPEED = 2
ITEM_DROP_RATE = 0.20 

# アイテムの種類
ITEM_HEAL = 0        
ITEM_STUN = 1        
ITEM_INVINCIBLE = 2  
ITEM_RAPID = 3       

# アイテムの画像パス
ITEM_IMAGES = {
    ITEM_HEAL: "assets/item_heal.png",
    ITEM_STUN: "assets/item_stun.png",
    ITEM_INVINCIBLE: "assets/item_invincible.png",
    ITEM_RAPID: "assets/item_rapid.png"
}

# 画像が見つからない場合の仮表示色
ITEM_COLORS = {
    ITEM_HEAL: (50, 255, 50),       
    ITEM_STUN: (255, 255, 50),      
    ITEM_INVINCIBLE: (255, 100, 255),
    ITEM_RAPID: (50, 255, 255)      
}

ITEM_NAMES = {
    ITEM_HEAL: "HEAL",
    ITEM_STUN: "STUN",
    ITEM_INVINCIBLE: "INVINCIBLE",
    ITEM_RAPID: "RAPID FIRE"
}


# ============================================================
# 弾クラス
# ============================================================
class Projectile(pg.sprite.Sprite):
    def __init__(self, x: float, y: float, vx: float, vy: float, color: tuple[int, int, int], radius: int = 5) -> None:
        super().__init__()
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        
        self.image = pg.Surface((radius * 2, radius * 2), pg.SRCALPHA)
        pg.draw.circle(self.image, color, (radius, radius), radius)
        self.rect = self.image.get_rect(center=(round(self.x), round(self.y)))

    def update(self) -> None:
        self.x += self.vx
        self.y += self.vy
        self.rect.center = (round(self.x), round(self.y))
        
        if self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT or \
           self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()


# ============================================================
# アイテムクラス
# ============================================================
class Item(pg.sprite.Sprite):
    def __init__(self, x: int, y: int, item_type: int) -> None:
        super().__init__()
        self.type = item_type
        self.image = self.load_image()
        self.rect = self.image.get_rect(center=(x, y))

    def load_image(self) -> pg.Surface:
        try:
            image = pg.image.load(ITEM_IMAGES[self.type]).convert_alpha()
            return pg.transform.smoothscale(image, ITEM_SIZE)
        except (pg.error, FileNotFoundError):
            surface = pg.Surface(ITEM_SIZE, pg.SRCALPHA)
            pg.draw.rect(surface, ITEM_COLORS[self.type], surface.get_rect(), border_radius=8)
            pg.draw.circle(surface, (255, 255, 255), (ITEM_SIZE[0]//2, ITEM_SIZE[1]//2), 4)
            return surface

    def update(self) -> None:
        self.rect.y += ITEM_SPEED
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


# ============================================================
# 主人公クラス
# ============================================================
class Player(pg.sprite.Sprite):
    def __init__(self) -> None:
        super().__init__()
        self.image = self.load_image()
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))
        
        self.last_shot_time = 0
        self.hp = PLAYER_MAX_HP
        self.stock_item = None
        self.invincible_end_time = 0
        self.rapid_fire_end_time = 0

    def load_image(self) -> pg.Surface:
        try:
            image = pg.image.load(PLAYER_IMAGE).convert_alpha()
            return pg.transform.smoothscale(image, PLAYER_SIZE)
        except (pg.error, FileNotFoundError):
            surface = pg.Surface(PLAYER_SIZE, pg.SRCALPHA)
            pg.draw.polygon(surface, PLAYER_COLOR, [(32, 0), (4, 58), (32, 46), (60, 58)])
            return surface

    def update(self, keys: tuple) -> None:
        dx = 0
        dy = 0
        if keys[pg.K_LEFT] or keys[pg.K_a]:
            dx -= PLAYER_SPEED
        if keys[pg.K_RIGHT] or keys[pg.K_d]:
            dx += PLAYER_SPEED
        if keys[pg.K_UP] or keys[pg.K_w]:
            dy -= PLAYER_SPEED
        if keys[pg.K_DOWN] or keys[pg.K_s]:
            dy += PLAYER_SPEED

        self.rect.x += dx
        self.rect.y += dy
        self.rect.clamp_ip(pg.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))

    def shoot(self, now: int) -> Projectile | None:
        current_interval = PLAYER_SHOT_INTERVAL
        if now < self.rapid_fire_end_time:
            current_interval = 80  

        if now - self.last_shot_time < current_interval:
            return None

        self.last_shot_time = now
        return Projectile(self.rect.centerx, self.rect.top, 0, -PLAYER_BULLET_SPEED, PLAYER_BULLET_COLOR)


# ============================================================
# 敵クラス
# ============================================================
class Enemy(pg.sprite.Sprite):
    def __init__(self) -> None:
        super().__init__()
        self.image = self.load_image()
        self.rect = self.image.get_rect()
        self.rect.midtop = (random.randint(ENEMY_SIZE[0] // 2, SCREEN_WIDTH - ENEMY_SIZE[0] // 2), -ENEMY_SIZE[1])
        self.last_shot_time = pg.time.get_ticks()

    def load_image(self) -> pg.Surface:
        try:
            image = pg.image.load(ENEMY_IMAGE).convert_alpha()
            return pg.transform.smoothscale(image, ENEMY_SIZE)
        except (pg.error, FileNotFoundError):
            surface = pg.Surface(ENEMY_SIZE, pg.SRCALPHA)
            pg.draw.ellipse(surface, ENEMY_COLOR, surface.get_rect())
            return surface

    def update(self) -> None:
        self.rect.y += ENEMY_SPEED
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

    def shoot(self, now: int, player_center: tuple[int, int]) -> Projectile | None:
        if now - self.last_shot_time < ENEMY_SHOT_INTERVAL:
            return None

        self.last_shot_time = now
        dx = player_center[0] - self.rect.centerx
        dy = player_center[1] - self.rect.centery
        distance = math.hypot(dx, dy)

        if distance == 0:
            distance = 1

        vx = dx / distance * ENEMY_BULLET_SPEED
        vy = dy / distance * ENEMY_BULLET_SPEED

        return Projectile(self.rect.centerx, self.rect.bottom, vx, vy, ENEMY_BULLET_COLOR, radius=6)

# ============================================================
# 体力ゲージクラス
# ============================================================
class Life:
    def __init__(self):
        self.hp = 100
        self.max_hp = 100

    def hp_damage(self, damage):
        self.hp -= damage
        if self.hp < 0:
            self.hp = 0
            
    def heal(self, amount):
        self.hp += amount
        if self.hp > self.max_hp:
            self.hp = self.max_hp

    def draw(self, screen):
        x = 20
        y = 20
        width = 200
        height = 20

        pg.draw.rect(screen, (100, 100, 100),(x, y, width, height))

        if self.hp > 50:
            color = (0, 255, 0)
        elif self.hp > 20:
            color = (255, 255, 0)
        else:
            color = (255, 0, 0)

        pg.draw.rect(screen, color,(x, y, width * self.hp / self.max_hp, height))

        font = pg.font.SysFont(None, 30)
        text = font.render(f"HP: {self.hp}/{self.max_hp}", True, (255, 255, 255))
        screen.blit(text, (x, y + 25))

# ============================================================
# ボスクラス
# ============================================================
class Boss:
    def __init__(self):
        self.image = self.load_image()
        x = random.randint(BOSS_SIZE[0] // 2, SCREEN_WIDTH - BOSS_SIZE[0] // 2)
        
        try:
            pg.mixer.music.load(BOSS_BGM) 
            pg.mixer.music.play(loops=-1) 
        except pg.error:
            pass # BGMが読み込めない場合はスキップ
            
        self.rect = self.image.get_rect()
        self.rect.midtop = (x, -BOSS_SIZE[1])
        self.hp = 10
        self.last_shot_time = pg.time.get_ticks()
    
    def load_image(self):
        try:
            image = pg.image.load(BOSS_IMAGE).convert_alpha()
            return pg.transform.smoothscale(image, BOSS_SIZE)
        except (pg.error, FileNotFoundError):
            surface = pg.Surface(BOSS_SIZE, pg.SRCALPHA)
            pg.draw.ellipse(surface, BOSS_COLOR, surface.get_rect())
            return surface

    def update(self):
        if self.rect.top < 30:
            self.rect.y += 2  

    def shoot(self, now, player_center):
        if now - self.last_shot_time < BOSS_SHOT_INTERVAL:
            return None

        self.last_shot_time = now

        dx = player_center[0] - self.rect.centerx
        dy = player_center[1] - self.rect.centery
        distance = math.hypot(dx, dy)

        if distance == 0:
            distance = 1

        vx = dx / distance * BOSS_BULLET_SPEED
        vy = dy / distance * BOSS_BULLET_SPEED

        return Projectile(self.rect.centerx, self.rect.bottom, vx, vy, BOSS_BULLET_COLOR, radius=6)
    
    def draw(self, screen):
        screen.blit(self.image, self.rect)    

def game_clear(screen:pg.Surface):
    pg.mixer.music.stop()
    try:
        pg.mixer.music.load(CLEAR_BGM) 
        pg.mixer.music.play() 
    except pg.error:
        pass
        
    brack=pg.Surface((SCREEN_WIDTH,SCREEN_HEIGHT))
    pg.draw.rect(brack,(0,0,0),pg.Rect(0,0,SCREEN_WIDTH,SCREEN_HEIGHT))
    brack.set_alpha(200)
    
    font=pg.font.Font(None, 70)
    txt=font.render("GameClear!!",True,(255,255,0))
    text_rct=txt.get_rect(center=(SCREEN_WIDTH//2,SCREEN_HEIGHT//2))
    brack.blit(txt,text_rct)
    
    try:
        star1_img = pg.image.load(STAR_IMAGE)
        star1_img = pg.transform.scale(star1_img,(50,50))
        star1_rct = star1_img.get_rect(center=(SCREEN_WIDTH//10,SCREEN_HEIGHT//2))
        brack.blit(star1_img,star1_rct)
        star2_img = pg.image.load(STAR_IMAGE)
        star2_img = pg.transform.scale(star2_img,(50,50))
        star2_rct = star2_img.get_rect(center=((SCREEN_WIDTH - SCREEN_WIDTH//10),SCREEN_HEIGHT//2))
        brack.blit(star2_img,star2_rct)
    except pg.error:
        pass

    screen.blit(brack,(0,0))
    pg.display.update()
    time.sleep(7)
    pg.quit()
    sys.exit()


# ============================================================
# ゲーム管理クラス
# ============================================================
class Game:
    def __init__(self) -> None:
        pg.init()
        pg.font.init()
        pg.display.set_caption(WINDOW_TITLE)

        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pg.time.Clock()
        self.running = True
        self.font = pg.font.SysFont(None, 28)

        self.background = self.load_background()
        self.player = Player()
        self.life = Life()

        self.enemies = pg.sprite.Group()
        self.player_bullets = pg.sprite.Group()
        self.enemy_bullets = pg.sprite.Group()
        self.items = pg.sprite.Group()

        self.boss = None 
        self.boss_spawn_time = 30000 # 開始から30秒後にスポーン
        self.last_boss_spawn = pg.time.get_ticks()

        self.last_enemy_spawn = pg.time.get_ticks()
        self.global_stun_end_time = 0 

    def load_background(self) -> pg.Surface | None:
        try:
            image = pg.image.load(BACKGROUND_IMAGE).convert()
            return pg.transform.scale(image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except (pg.error, FileNotFoundError):
            return None

    def handle_events(self) -> None:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_x:
                    self.use_item()

    def use_item(self) -> None:
        if self.player.stock_item is None:
            return
            
        item_type = self.player.stock_item
        self.player.stock_item = None
        now = pg.time.get_ticks()

        if item_type == ITEM_HEAL:
            self.player.hp = min(self.player.hp + 1, PLAYER_MAX_HP)
            self.life.heal(34) # UI体力ゲージの回復
        elif item_type == ITEM_STUN:
            self.global_stun_end_time = now + 4000  
        elif item_type == ITEM_INVINCIBLE:
            self.player.invincible_end_time = now + 5000  
        elif item_type == ITEM_RAPID:
            self.player.rapid_fire_end_time = now + 5000  

    def spawn_boss(self):
        if self.boss is None:
            self.boss = Boss()

    def update(self) -> None:
        now = pg.time.get_ticks()
        keys = pg.key.get_pressed()

        self.player.update(keys)

        if keys[pg.K_SPACE]:
            bullet = self.player.shoot(now)
            if bullet is not None:
                self.player_bullets.add(bullet)

        is_stunned = now < self.global_stun_end_time

        # 敵の生成と更新
        if not is_stunned:
            if now - self.last_enemy_spawn >= ENEMY_SPAWN_INTERVAL:
                self.enemies.add(Enemy())
                self.last_enemy_spawn = now

            self.enemies.update()
            for enemy in self.enemies:
                bullet = enemy.shoot(now, self.player.rect.center)
                if bullet is not None:
                    self.enemy_bullets.add(bullet)

        # 弾やアイテムの更新
        self.player_bullets.update()
        self.enemy_bullets.update()
        self.items.update()
      
        # ボス出現処理
        if self.boss is None and now - self.last_boss_spawn >= self.boss_spawn_time:
            self.spawn_boss()

        if self.boss is not None:
            self.boss.update()
            bullet = self.boss.shoot(now, self.player.rect.center)
            if bullet is not None:
                self.enemy_bullets.add(bullet)

        self.check_collisions(now)
        
    def check_collisions(self, now: int) -> None:
        # 主人公の弾と敵の当たり判定
        hits = pg.sprite.groupcollide(self.enemies, self.player_bullets, True, True)
        for enemy in hits.keys():
            if random.random() < ITEM_DROP_RATE:
                item_type = random.choice([ITEM_HEAL, ITEM_STUN, ITEM_INVINCIBLE, ITEM_RAPID])
                self.items.add(Item(enemy.rect.centerx, enemy.rect.centery, item_type))

        # 主人公の弾とボスの当たり判定
        if self.boss is not None:
            for bullet in list(self.player_bullets):
                if bullet.rect.colliderect(self.boss.rect):
                    bullet.kill()
                    self.boss.hp -= 1
                    if self.boss.hp <= 0:
                        self.boss = None
                        game_clear(self.screen)
                        break

        # 主人公と敵・敵弾の当たり判定 (無敵時間外)
        if now >= self.player.invincible_end_time:
            bullet_hits = pg.sprite.spritecollide(self.player, self.enemy_bullets, True)
            enemy_hits = pg.sprite.spritecollide(self.player, self.enemies, True)
            
            if bullet_hits or enemy_hits:
                self.player.hp -= 1
                self.life.hp_damage(34) # UI体力ゲージにもダメージを反映
                self.player.invincible_end_time = now + 1500  
                if self.player.hp <= 0 or self.life.hp <= 0:
                    self.running = False

        # 主人公とアイテムの当たり判定
        item_hits = pg.sprite.spritecollide(self.player, self.items, False)
        for item in item_hits:
            if self.player.stock_item is None:
                self.player.stock_item = item.type
                item.kill() 

    def draw_damage_effect(self):
        if self.life.hp <= 30: # ダメージエフェクトの発生閾値を調整
            x = self.player.rect.centerx
            y = self.player.rect.centery
            t = pg.time.get_ticks() / 300
            hai = pg.Surface(self.screen.get_size(), pg.SRCALPHA)

            for i in range(3):
                smoke_x = x + math.sin(t + i * 2) * 15
                smoke_y = y - 35 - i * 15 - abs(math.sin(t + i)) * 10
                pg.draw.circle(hai, (130, 130, 130, 100), (int(smoke_x), int(smoke_y)), 12 + i * 3)

            self.screen.blit(hai, (0, 0))
            pg.draw.lines(self.screen, (40, 40, 40), False, [(x, y - 20), (x - 8, y - 5), (x + 3, y + 2), (x - 5, y + 18)], 3)
            pg.draw.lines(self.screen, (40, 40, 40), False, [(x - 8, y - 5), (x - 18, y - 12), (x - 22, y - 22)], 2)

    def draw_ui(self, now: int) -> None:
        if self.player.stock_item is not None:
            item_name = ITEM_NAMES[self.player.stock_item]
            item_text = self.font.render(f"ITEM: {item_name} [Press X]", True, ITEM_COLORS[self.player.stock_item])
        else:
            item_text = self.font.render("ITEM: NONE", True, (150, 150, 150))
        self.screen.blit(item_text, (20, 80))

        y_offset = 110
        if now < self.player.invincible_end_time:
            text = self.font.render("INVINCIBLE ACTIVE!", True, ITEM_COLORS[ITEM_INVINCIBLE])
            self.screen.blit(text, (20, y_offset))
            y_offset += 25
        if now < self.player.rapid_fire_end_time:
            text = self.font.render("RAPID FIRE ACTIVE!", True, ITEM_COLORS[ITEM_RAPID])
            self.screen.blit(text, (20, y_offset))
            y_offset += 25
        if now < self.global_stun_end_time:
            text = self.font.render("ENEMY STUNNED!", True, ITEM_COLORS[ITEM_STUN])
            self.screen.blit(text, (20, y_offset))

    def draw(self) -> None:
        now = pg.time.get_ticks()

        if self.background is not None:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill((5, 8, 30))

        self.enemies.draw(self.screen)
        self.items.draw(self.screen)
        self.player_bullets.draw(self.screen)
        self.enemy_bullets.draw(self.screen)
            
        self.screen.blit(self.player.image, self.player.rect)
        
        if self.boss is not None:
            self.boss.draw(self.screen)

        self.draw_ui(now)
        self.life.draw(self.screen)
        self.draw_damage_effect()

        pg.display.flip()

    def run(self) -> None:
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.draw()

        pg.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()