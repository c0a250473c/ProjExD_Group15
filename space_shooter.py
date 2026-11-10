import math
import random
import sys
from pathlib import Path
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))


import pygame as pg


# ============================================================
# 設定
# ============================================================
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 800
FPS = 60
WINDOW_TITLE = "SPACE SHOOTER"

BASE_DIR = Path(__file__).resolve().parent
ASSET_DIR = BASE_DIR / "assets"

BACKGROUND_IMAGE = ASSET_DIR / "background.png"
PLAYER_IMAGE = ASSET_DIR / "player.png"
ENEMY_IMAGE = ASSET_DIR / "enemy.png"
BOSS_IMAGE = ASSET_DIR / "boss.png"
STAR_IMAGE = ASSET_DIR / "star.png"
BOSS_BGM = ASSET_DIR / "sounds" / "boss_bgm.mp3"
CLEAR_BGM = ASSET_DIR / "sounds" / "clear_bgm.mp3"

PLAYER_SIZE = (64, 64)
PLAYER_SPEED = 5
PLAYER_SHOT_INTERVAL = 250
PLAYER_BULLET_SPEED = 9
PLAYER_MAX_HP = 3

# 50点ごとに発射間隔を短縮
SHOT_INTERVAL_DECREASE = 25
MIN_SHOT_INTERVAL = 80

ENEMY_SIZE = (48, 48)
ENEMY_SPEED = 2
ENEMY_SPAWN_INTERVAL = 1400
ENEMY_SHOT_INTERVAL = 1600
ENEMY_BULLET_SPEED = 4
ZIGZAG_ENEMY_SPEED_X=3
ZIGZAG_ENEMY_RATE=0.25
ARMOR_ENEMY_SIZE=(64,64)
ARMOR_ENEMY_SPEED=1
ARMOR_ENEMY_RATE=0.15
ARMOR_WEAK_KIND="big"



BOSS_SIZE = (100, 100)
BOSS_SPAWN_TIME = 30000
BOSS_SHOT_INTERVAL = 1000
BOSS_BULLET_SPEED = 6

PLAYER_COLOR = (80, 220, 255)
ENEMY_COLOR = (255, 100, 100)
PLAYER_BULLET_COLOR = (255, 245, 100)
ENEMY_BULLET_COLOR = (255, 120, 80)
BOSS_COLOR = (20, 220, 20)
BOSS_BULLET_COLOR = (255, 0, 0)

ITEM_SIZE = (32, 32)
ITEM_SPEED = 2
ITEM_DROP_RATE = 0.20

ITEM_HEAL = 0
ITEM_STUN = 1
ITEM_INVINCIBLE = 2
ITEM_RAPID = 3

ITEM_IMAGES = {
    ITEM_HEAL: ASSET_DIR / "item_heal.png",
    ITEM_STUN: ASSET_DIR / "item_stun.png",
    ITEM_INVINCIBLE: ASSET_DIR / "item_invincible.png",
    ITEM_RAPID: ASSET_DIR / "item_rapid.png",
}
ITEM_COLORS = {
    ITEM_HEAL: (50, 255, 50),
    ITEM_STUN: (255, 255, 50),
    ITEM_INVINCIBLE: (255, 100, 255),
    ITEM_RAPID: (50, 255, 255),
}
ITEM_NAMES = {
    ITEM_HEAL: "HEAL",
    ITEM_STUN: "STUN",
    ITEM_INVINCIBLE: "INVINCIBLE",
    ITEM_RAPID: "RAPID FIRE",
}


def load_scaled_image(path, size, fallback_color, shape="rect"):
    """画像があれば読み込み、なければ仮画像を作る。"""
    try:
        image = pg.image.load(str(path)).convert_alpha()
        return pg.transform.smoothscale(image, size)
    except (pg.error, FileNotFoundError):
        surface = pg.Surface(size, pg.SRCALPHA)
        if shape == "triangle":
            pg.draw.polygon(
                surface, fallback_color,
                [(size[0] // 2, 0), (4, size[1] - 6),
                 (size[0] // 2, size[1] - 18), (size[0] - 4, size[1] - 6)]
            )
        elif shape == "ellipse":
            pg.draw.ellipse(surface, fallback_color, surface.get_rect())
        else:
            pg.draw.rect(surface, fallback_color, surface.get_rect(), border_radius=8)
        return surface


class Score:
    """
    ・撃ち落とした爆弾や敵機の数をスコアとして表示する
      →爆弾: 1点, 敵機: 10点
    ・そのスコア数によって能力向上
      →50点を更新する度、弾速やその大きさが変化する
    """
    def __init__(self):
        self.font = pg.font.Font(None, 42)
        self.value = 0

    def add(self, point):
        self.value += point

    def draw(self, screen):
        image = self.font.render(f"Score: {self.value}", True, (255, 255, 255))
        rect = image.get_rect(bottomleft=(15, SCREEN_HEIGHT - 60))
        screen.blit(image, rect)
# どでか弾と鬱スタミナの数字
MAX_STAMINA = 100.0
UTSU_THRESHOLD = 30.0
UTSU_SPEED = 2.0
STAMINA_RECOVERY = 0.15
DODEKA_COST = 50.0
DODEKA_RADIUS = 40
DODEKA_COLOR = (255, 50, 50)
DODEKA_INTERVAL = 500


# ============================================================
# 弾クラス
# ============================================================
class Projectile(pg.sprite.Sprite):
    def __init__(self, x, y, vx, vy, color, radius=5, kind="normal"):
        super().__init__()

        self.vx = float(vx)
        self.vy = float(vy)
        self.kind = kind

        self.image = pg.Surface(
            (radius * 2, radius * 2),
            pg.SRCALPHA
        )

        pg.draw.circle(
            self.image,
            color,
            (radius, radius),
            radius
        )

        self.rect = self.image.get_rect(
            center=(round(x), round(y))
        )

        self.color = color
        self.radius = radius

    def update(self):
        self.rect.x += round(self.vx)
        self.rect.y += round(self.vy)

        if (self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT
                or self.rect.right < 0 or self.rect.left > SCREEN_WIDTH):
            self.kill()

    def draw(self, screen):
        screen.blit(self.image, self.rect) 

    def update(self):
        self.rect.x += round(self.vx)
        self.rect.y += round(self.vy)
        if (self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT
                or self.rect.right < 0 or self.rect.left > SCREEN_WIDTH):
            self.kill()
    def draw(self, screen):
        screen.blit(self.image, self.rect)

# ============================================================
# アイテムクラス
# ============================================================
class Item(pg.sprite.Sprite):
    def __init__(self, x, y, item_type):
        super().__init__()

        self.type = item_type

        self.image = load_scaled_image(
            ITEM_IMAGES[item_type],
            ITEM_SIZE,
            ITEM_COLORS[item_type]
        )

        # アイテムの位置を設定
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        # アイテムを下方向に移動
        self.rect.y += ITEM_SPEED

        # 画面外に出たら削除
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

# ============================================================
# 主人公クラス
# ============================================================
class Player(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = load_scaled_image(PLAYER_IMAGE, PLAYER_SIZE, PLAYER_COLOR, "triangle")
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))
        self.last_shot_time = 0
        self.hp = PLAYER_MAX_HP
        self.stock_item = None
        self.invincible_end_time = 0
        self.rapid_fire_end_time = 0
        self.stamina = MAX_STAMINA # タミナを満タンにして、大技をすぐに撃てる状態にセットするコード
        self.last_dodeka_time = 0
    def load_image(self):
        try:
            image = pg.image.load(PLAYER_IMAGE).convert_alpha()
            return pg.transform.smoothscale(image, PLAYER_SIZE)

        except (pg.error, FileNotFoundError):
            print("主人公画像が見つかりません。仮画像を使用します。")

            surface = pg.Surface(PLAYER_SIZE, pg.SRCALPHA)
            pg.draw.polygon(
                surface,
                PLAYER_COLOR,
                [(32, 0), (4, 58), (32, 46), (60, 58)]
            )
            return surface

    def update(self, keys):
        if self.stamina < MAX_STAMINA:
            self.stamina = min(self.stamina + STAMINA_RECOVERY, MAX_STAMINA)
        current_speed = PLAYER_SPEED if self.stamina >= UTSU_THRESHOLD else UTSU_SPEED
        # このコードは、ゲームが動いている間、毎フレーム（常に）キャラクターの状態を更新する処理の一部
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

        # 矢印キー・WASDによる移動
        if keys[pg.K_LEFT] or keys[pg.K_a]:
            dx -= current_speed # 変更

        if keys[pg.K_RIGHT] or keys[pg.K_d]:
            dx += current_speed # 変更

        if keys[pg.K_UP] or keys[pg.K_w]:
            dy -= current_speed # 変更

        if keys[pg.K_DOWN] or keys[pg.K_s]:
            dy += current_speed # 変更

        self.rect.x += dx
        self.rect.y += dy
        self.rect.clamp_ip(pg.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))

    def shoot(self, now, shot_interval):
        if now - self.last_shot_time < shot_interval:
        # 画面外に出ないように制限
            self.rect.clamp_ip(
            pg.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        )

    def shoot(self, now, shot_interval):
    # 一定時間ごとに弾を発射
        if now - self.last_shot_time < shot_interval:
            return None

        self.last_shot_time = now
        return Projectile(
        self.rect.centerx, self.rect.top, 0, -PLAYER_BULLET_SPEED,
        PLAYER_BULLET_COLOR
    )

    def draw(self, screen):
        screen.blit(self.image, self.rect)
    def shoot_dodeka(self, now):
        if now - self.last_dodeka_time < DODEKA_INTERVAL:
            return None
        
        if  self.stamina >= DODEKA_COST:
            self.stamina -= DODEKA_COST
            self.last_dodeka_time = now
            return Projectile(
                self.rect.centerx, self.rect.top, 0,
                -PLAYER_BULLET_SPEED + 2, DODEKA_COLOR, radius=DODEKA_RADIUS
            )
        return None
        # 時間経過とスタミナの量の2つの条件を満たした時スタミナをガッツリ消費し巨大な弾を発射する


# ============================================================
# 敵クラス
# ============================================================
class Enemy(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = load_scaled_image(ENEMY_IMAGE, ENEMY_SIZE, ENEMY_COLOR, "ellipse")
        self.speed = ENEMY_SPEED
        self.rect = self.image.get_rect()
        self.rect.midtop = (
            random.randint(ENEMY_SIZE[0] // 2, SCREEN_WIDTH - ENEMY_SIZE[0] // 2),
            -ENEMY_SIZE[1]
        )
        self.last_shot_time = pg.time.get_ticks()

        self.last_shot_time = pg.time.get_ticks()

    def load_image(self):
        try:
            image = pg.image.load(
                ENEMY_IMAGE
            ).convert_alpha()

            return pg.transform.smoothscale(
                image,
                ENEMY_SIZE
            )

        except (pg.error, FileNotFoundError):
            print("敵画像が見つかりません。仮画像を使用します。")

            surface = pg.Surface(
                ENEMY_SIZE,
                pg.SRCALPHA
            )

            pg.draw.ellipse(
                surface,
                ENEMY_COLOR,
                surface.get_rect()
            )

            return surface
    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

    def hit(self, bullet):
        return True
    
        

    def shoot(self, now, player_center):
        if now - self.last_shot_time < ENEMY_SHOT_INTERVAL:
            return None
        self.last_shot_time = now
        dx = player_center[0] - self.rect.centerx
        dy = player_center[1] - self.rect.centery
        distance = math.hypot(dx, dy) or 1
        return Projectile(
            self.rect.centerx, self.rect.bottom,
            dx / distance * ENEMY_BULLET_SPEED,
            dy / distance * ENEMY_BULLET_SPEED,
            ENEMY_BULLET_COLOR, 6
        )

# ============================================================
# 体力ゲージクラス
# ============================================================
class Life:
    def __init__(self):
        self.hp = 100
        self.max_hp = 100

    def hp_damage(self, damage):
        self.hp = max(0, self.hp - damage)

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def draw(self, screen):
        x, y, width, height = 20, 20, 200, 20
        pg.draw.rect(screen, (100, 100, 100), (x, y, width, height))
        if self.hp > 50:
            color = (0, 255, 0)
        elif self.hp > 20:
            color = (255, 255, 0)
        else:
            color = (255, 0, 0)
        pg.draw.rect(
            screen, color,
            (x, y, width * self.hp / self.max_hp, height)
        )
        font = pg.font.SysFont(None, 30)
        text = font.render(f"HP: {self.hp}/{self.max_hp}", True, (255, 255, 255))
        screen.blit(text, (x, y + 25))

# ============================================================
# ボスクラス
# ============================================================
class Boss:
    def __init__(self):
        self.image = load_scaled_image(BOSS_IMAGE, BOSS_SIZE, BOSS_COLOR, "ellipse")
        x = random.randint(BOSS_SIZE[0] // 2, SCREEN_WIDTH - BOSS_SIZE[0] // 2)
        self.rect = self.image.get_rect(midtop=(x, -BOSS_SIZE[1]))
        self.hp = 10
        self.last_shot_time = pg.time.get_ticks()

    def update(self):
        if self.rect.top < 30:
            self.rect.y += 2

    def shoot(self, now, player_center):
        if now - self.last_shot_time < BOSS_SHOT_INTERVAL:
            return None
        self.last_shot_time = now
        dx = player_center[0] - self.rect.centerx
        dy = player_center[1] - self.rect.centery
        distance = math.hypot(dx, dy) or 1
        return Projectile(
            self.rect.centerx, self.rect.bottom,
            dx / distance * BOSS_BULLET_SPEED,
            dy / distance * BOSS_BULLET_SPEED,
            BOSS_BULLET_COLOR, 6
        )

    def draw(self, screen):
        screen.blit(self.image, self.rect)
class ZigZagEnemy(Enemy):
    def __init__(self):
        super().__init__()
        pg.draw.rect(self.image,(80,255,80),self.image.get_rect(),3)
        self.vx=random.choice([-ZIGZAG_ENEMY_SPEED_X,ZIGZAG_ENEMY_SPEED_X])

    def update(self)->None:
        super().update()
        self.rect.x+=self.vx
        if self.rect.left<0 or self.rect.right>SCREEN_WIDTH:
            self.vx*=-1

class ArmorEnemy(Enemy):
    def __init__(self):

        super().__init__()
        self.image=pg.transform.smoothscale(self.image,ARMOR_ENEMY_SIZE)
        self.rect=self.image.get_rect(midtop=self.rect.midtop)
        pg.draw.rect(self.image,(220,220,220),self.image.get_rect(),5)
        self.speed=ARMOR_ENEMY_SPEED
    def hit(self,bullet:Projectile)->bool:
        return bullet.kind==ARMOR_WEAK_KIND

# ============================================================
# ゲーム管理クラス
# ============================================================
class Game:
    def __init__(self):
        pg.init()
        pg.font.init()
        pg.display.set_caption(WINDOW_TITLE)
        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

        pg.display.set_caption(WINDOW_TITLE)

        self.screen = pg.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT)
        )

        self.clock = pg.time.Clock()
        self.running = True
        self.font = pg.font.SysFont(None, 28)

        try:
            pg.mixer.init()
        except pg.error:
            pass

        self.background = None
        try:
            image = pg.image.load(str(BACKGROUND_IMAGE)).convert()
            self.background = pg.transform.scale(image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except (pg.error, FileNotFoundError):
            pass

        self.reset_game()

    def reset_game(self):
        self.score = Score()
        self.player = Player()
        self.life = Life()
        self.enemies = pg.sprite.Group()
        self.player_bullets = pg.sprite.Group()
        self.enemy_bullets = pg.sprite.Group()
        self.items = pg.sprite.Group()
        self.boss = None
        self.start_time = pg.time.get_ticks()
        self.last_enemy_spawn = self.start_time
        self.global_stun_end_time = 0
        self.game_over = False
        self.boss_bgm_playing = False

    def get_shot_interval(self, now):
        interval = PLAYER_SHOT_INTERVAL
        if now < self.player.rapid_fire_end_time:
            interval = 80
        else:
            level = self.score.value // 50
            interval -= level * SHOT_INTERVAL_DECREASE
        return max(MIN_SHOT_INTERVAL, interval)
        self.background = self.load_background()

        self.player = Player()

        self.enemies = []
        self.player_bullets = []
        self.enemy_bullets = []

        self.last_enemy_spawn = pg.time.get_ticks()

    def load_background(self):
        try:
            image = pg.image.load(
                BACKGROUND_IMAGE
            ).convert()

            return pg.transform.scale(
                image,
                (SCREEN_WIDTH, SCREEN_HEIGHT)
            )

        except (pg.error, FileNotFoundError):
            print("背景画像が見つかりません。単色背景を使用します。")
            return None

    def handle_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            elif event.type == pg.KEYDOWN:
                if self.game_over:
                    if event.key == pg.K_r:
                        self.reset_game()
                    elif event.key in (pg.K_q, pg.K_ESCAPE):
                        self.running = False
                elif event.key == pg.K_x:
                    self.use_item()

    def use_item(self):
        item_type = self.player.stock_item
        if item_type is None:
            return
        self.player.stock_item = None
        now = pg.time.get_ticks()

        if item_type == ITEM_HEAL:
            self.player.hp = min(self.player.hp + 1, PLAYER_MAX_HP)
            self.life.heal(34)
        elif item_type == ITEM_STUN:
            self.global_stun_end_time = now + 4000
        elif item_type == ITEM_INVINCIBLE:
            self.player.invincible_end_time = now + 5000
        elif item_type == ITEM_RAPID:
            self.player.rapid_fire_end_time = now + 5000

    def damage_player(self, now):
        if now < self.player.invincible_end_time:
            return

        self.player.hp -= 1
        self.life.hp_damage(34)
        self.player.invincible_end_time = now + 1500

        print("プレイヤーHP:", self.player.hp)
        print("ライフ:", self.life.hp)

        if self.player.hp <= 0 or self.life.hp <= 0:
            print("GAME OVERになりました！")
            self.game_over = True
            pg.mixer.music.stop()

    def update(self):
        if self.game_over:
            return
        now = pg.time.get_ticks()
        keys = pg.key.get_pressed()

        now = pg.time.get_ticks()
        keys = pg.key.get_pressed()
        self.player.update(keys)

        if keys[pg.K_SPACE]:
            bullet = self.player.shoot(now, self.get_shot_interval(now))
        # スペースキーによる弾の発射

            if bullet is not None:
                self.player_bullets.add(bullet)

        is_stunned = now < self.global_stun_end_time
        if not is_stunned and now - self.last_enemy_spawn >= ENEMY_SPAWN_INTERVAL:

            if keys[pg.K_t ]:# tキーによるどでか弾の発射
                dodeka_bullet = self.player.shoot_dodeka(now)

                if dodeka_bullet is not None:
                    self.player_bullets.add(dodeka_bullet)
 
        # 一定時間ごとに敵を生成
        if now - self.last_enemy_spawn >= ENEMY_SPAWN_INTERVAL:
            self.spawn_enemy()
            self.last_enemy_spawn = now

        self.enemies.update()
        if not is_stunned:
            for enemy in self.enemies:
                bullet = enemy.shoot(now, self.player.rect.center)
                if bullet is not None:
                    self.enemy_bullets.add(bullet)


        self.player_bullets.update()
        self.enemy_bullets.update()
        self.items.update()

            # if hit_enemy is not None:
            #     self.player_bullets.remove(bullet)
            #     if hit_enemy.hit(bullet):
            #         self.enemies.remove(hit_enemy)


        if self.boss is None and now - self.start_time >= BOSS_SPAWN_TIME:
            self.boss = Boss()
            try:
                pg.mixer.music.load(str(BOSS_BGM))
                pg.mixer.music.play(-1)
                self.boss_bgm_playing = True
            except pg.error:
                pass

        if self.boss is not None:
            self.boss.update()
            bullet = self.boss.shoot(now, self.player.rect.center)
            if bullet is not None:
                self.enemy_bullets.add(bullet)

        self.check_collisions(now)

    def check_collisions(self, now):
        # 自機の弾と敵機：敵機1機につき10点
                # 自機の弾と敵機：敵機1機につき10点
        for bullet in list(self.player_bullets):
            hit_enemies = pg.sprite.spritecollide(bullet, self.enemies, False)
            if hit_enemies:
                enemy = hit_enemies[0]
                bullet.kill()
                if enemy.hit(bullet):
                    enemy.kill()
                    self.score.add(10)
                    if random.random() < ITEM_DROP_RATE:
                        item_type = random.choice(
                            [ITEM_HEAL, ITEM_STUN, ITEM_INVINCIBLE, ITEM_RAPID]
                        )
                        self.items.add(Item(enemy.rect.centerx, enemy.rect.centery, item_type))

        # 自機の弾で敵弾を撃ち落とす：1発につき1点
        bullet_hits = pg.sprite.groupcollide(
            self.player_bullets, self.enemy_bullets, True, True
        )
        for _ in bullet_hits:
            self.score.add(1)

        # 自機の弾とボス
        if self.boss is not None:
            boss_hits = pg.sprite.spritecollide(
                self.boss, self.player_bullets, True
            )
            self.boss.hp -= len(boss_hits)
            if self.boss.hp <= 0:
                self.boss = None
                pg.mixer.music.stop()
                self.show_game_clear()
                self.running = False
                return

        # 敵弾・敵機と自機
        if now >= self.player.invincible_end_time:
            bullet_hit = pg.sprite.spritecollide(
                self.player, self.enemy_bullets, True
            )
            enemy_hit = pg.sprite.spritecollide(
                self.player, self.enemies, True
            )
            if bullet_hit or enemy_hit:
                self.damage_player(now)

        # アイテム取得
        item_hits = pg.sprite.spritecollide(
            self.player, self.items, False
        )
        for item in item_hits:
            if self.player.stock_item is None:
                self.player.stock_item = item.type
                item.kill()

    def draw_damage_effect(self):
        if self.life.hp <= 30:
            x = self.player.rect.centerx
            y = self.player.rect.centery
            t = pg.time.get_ticks() / 300
            smoke = pg.Surface(self.screen.get_size(), pg.SRCALPHA)
            for i in range(3):
                smoke_x = x + math.sin(t + i * 2) * 15
                smoke_y = y - 35 - i * 15 - abs(math.sin(t + i)) * 10
                pg.draw.circle(
                    smoke, (130, 130, 130, 100),
                    (int(smoke_x), int(smoke_y)), 12 + i * 3
                )
            self.screen.blit(smoke, (0, 0))
            pg.draw.lines(
                self.screen, (40, 40, 40), False,
                [(x, y - 20), (x - 8, y - 5), (x + 3, y + 2),
                 (x - 5, y + 18)], 3
            )

    def draw_ui(self, now):
        if self.player.stock_item is None:
            item_text = self.font.render("ITEM: NONE", True, (150, 150, 150))
        else:
            name = ITEM_NAMES[self.player.stock_item]
            color = ITEM_COLORS[self.player.stock_item]
            item_text = self.font.render(f"ITEM: {name} [Press X]", True, color)
        self.screen.blit(item_text, (20, 80))

        y_offset = 110
        messages = [
            (now < self.player.invincible_end_time, "INVINCIBLE ACTIVE!", ITEM_INVINCIBLE),
            (now < self.player.rapid_fire_end_time, "RAPID FIRE ACTIVE!", ITEM_RAPID),
            (now < self.global_stun_end_time, "ENEMY STUNNED!", ITEM_STUN),
        ]
        for active, message, item_type in messages:
            if active:
                text = self.font.render(message, True, ITEM_COLORS[item_type])
                self.screen.blit(text, (20, y_offset))
                y_offset += 25

    def draw_game_over(self):
        overlay = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        title_font = pg.font.Font(None, 72)
        text_font = pg.font.Font(None, 36)
        texts = [
            (title_font, "GAME OVER", (255, 80, 80), 320),
            (text_font, f"Final Score: {self.score.value}", (255, 255, 255), 390),
            (text_font, "Press R to Restart", (255, 255, 255), 455),
            (text_font, "Press Q to Quit", (255, 255, 255), 500),
        ]
        for font, message, color, y in texts:
            image = font.render(message, True, color)
            self.screen.blit(image, image.get_rect(center=(SCREEN_WIDTH // 2, y)))

    def show_game_clear(self):
        pg.mixer.music.stop()
        try:
            pg.mixer.music.load(str(CLEAR_BGM))
            pg.mixer.music.play()
        except pg.error:
            pass

        overlay = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        font = pg.font.Font(None, 70)
        text = font.render("Game Clear!!", True, (255, 255, 0))
        overlay.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))

        #　星の描画
        try:
            star = pg.image.load(str(STAR_IMAGE)).convert_alpha()
            star = pg.transform.scale(star, (50, 50))
            overlay.blit(star, star.get_rect(center=(SCREEN_WIDTH // 10, SCREEN_HEIGHT // 2)))
            overlay.blit(star, star.get_rect(center=(SCREEN_WIDTH - SCREEN_WIDTH // 10, SCREEN_HEIGHT // 2)))
        except (pg.error, FileNotFoundError):
            pass

        self.screen.blit(overlay, (0, 0))
        pg.display.flip()
        pg.time.delay(7000) # ジングルが流れ終わるまで待つ

    def draw_stamina_bar(self):
        bar_width = 200 * (self.player.stamina / MAX_STAMINA)
        bar_color = (150, 255, 100) if self.player.stamina >= UTSU_THRESHOLD else (128, 0, 128)
        pg.draw.rect(self.screen, (50, 50, 50), (10, SCREEN_HEIGHT - 30, 200, 15))
        if bar_width > 0:
            pg.draw.rect(self.screen, bar_color, (10, SCREEN_HEIGHT - 30, bar_width, 15))
            # 現在のスタミナ残量を示すゲージ（バー）」を描画するための処理

    def draw(self):
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
        self.score.draw(self.screen)

        
        for bullet in self.enemy_bullets:
            bullet.draw(self.screen)

        self.draw_stamina_bar()

        # ゲームオーバーならゲームオーバー画面を表示
        if self.game_over:
            self.draw_game_over()

        pg.display.flip()
    def spawn_enemy(self):    
        r=random.random()
        if r<ARMOR_ENEMY_RATE:
            self.enemies.add(ArmorEnemy())
        elif r<ARMOR_ENEMY_RATE+ZIGZAG_ENEMY_RATE:
            self.enemies.add(ZigZagEnemy())
        else:
            self.enemies.add(Enemy())    
             
    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.draw()

        pg.quit()
        sys.exit()

if __name__ == "__main__":
    Game().run()