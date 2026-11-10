import math
import random
import sys
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import time # ゲームクリアで使用

import pygame

pygame.mixer.init() # 初期化（BGM用）

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
BOSS_IMAGE = str(BASE_DIR / "assets" / "boss.png") #boss画像のパス
STAR_IMAGE = str(BASE_DIR / "assets" / "star.png") #星画像のパス
BOSS_BGM = str(BASE_DIR / "assets" / "sounds" / "boss_bgm.mp3") #ボス戦bgmのパス
CLEAR_BGM = str(BASE_DIR / "assets" / "sounds" / "clear_bgm.mp3") #  クリアBGMのパス

PLAYER_SIZE = (64, 64)
PLAYER_SPEED = 5
PLAYER_SHOT_INTERVAL = 250  # ミリ秒
PLAYER_BULLET_SPEED = 9

ENEMY_SIZE = (48, 48)
ENEMY_SPEED = 2
ENEMY_SPAWN_INTERVAL = 1400  # ミリ秒
ENEMY_SHOT_INTERVAL = 1600   # ミリ秒
ENEMY_BULLET_SPEED = 4

#bossの設定
BOSS_SIZE = (100, 100)
BOSS_SPAWN_INTERVAL = 1400      # ミリ秒
BOSS_SHOT_INTERVAL = 1000 
BOSS_BULLET_SPEED = 6

# 画像が読み込めない場合の仮表示色
PLAYER_COLOR = (80, 220, 255)
ENEMY_COLOR = (255, 100, 100)
PLAYER_BULLET_COLOR = (255, 245, 100)
ENEMY_BULLET_COLOR = (255, 120, 80)
BOSS_COLOR = (20, 220, 20) #  bossの表示色
BOSS_BULLET_COLOR = (255, 0, 0) #  bossの弾の色

# ============================================================
# 弾クラス
# ============================================================

class Projectile:
    def __init__(self, x, y, vx, vy, color, radius=5):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.color = color
        self.radius = radius

        self.rect = pygame.Rect(0, 0, radius * 2, radius * 2)
        self.rect.center = (round(self.x), round(self.y))

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.rect.center = (round(self.x), round(self.y))

    def draw(self, screen):
        pygame.draw.circle(
            screen,
            self.color,
            self.rect.center,
            self.radius
        )


# ============================================================
# 主人公クラス
# ============================================================

class Player:
    def __init__(self):
        self.image = self.load_image()
        self.rect = self.image.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80)
        )
        self.last_shot_time = 0

    def load_image(self):
        try:
            image = pygame.image.load(PLAYER_IMAGE).convert_alpha()
            return pygame.transform.smoothscale(image, PLAYER_SIZE)

        except (pygame.error, FileNotFoundError):
            print("主人公画像が見つかりません。仮画像を使用します。")

            surface = pygame.Surface(PLAYER_SIZE, pygame.SRCALPHA)
            pygame.draw.polygon(
                surface,
                PLAYER_COLOR,
                [(32, 0), (4, 58), (32, 46), (60, 58)]
            )
            return surface

    def update(self, keys):
        dx = 0
        dy = 0

        # 矢印キー・WASDによる移動
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= PLAYER_SPEED

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += PLAYER_SPEED

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= PLAYER_SPEED

        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += PLAYER_SPEED

        self.rect.x += dx
        self.rect.y += dy

        # 画面外に出ないように制限
        self.rect.clamp_ip(
            pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        )

    def shoot(self, now):
        # 一定時間ごとに弾を発射
        if now - self.last_shot_time < PLAYER_SHOT_INTERVAL:
            return None

        self.last_shot_time = now

        return Projectile(
            self.rect.centerx,
            self.rect.top,
            0,
            -PLAYER_BULLET_SPEED,
            PLAYER_BULLET_COLOR
        )

    def draw(self, screen):
        screen.blit(self.image, self.rect)


# ============================================================
# 敵クラス
# ============================================================

class Enemy:
    def __init__(self):
        self.image = self.load_image()

        x = random.randint(
            ENEMY_SIZE[0] // 2,
            SCREEN_WIDTH - ENEMY_SIZE[0] // 2
        )

        self.rect = self.image.get_rect()
        self.rect.midtop = (x, -ENEMY_SIZE[1])

        self.last_shot_time = pygame.time.get_ticks()

    def load_image(self):
        try:
            image = pygame.image.load(
                ENEMY_IMAGE
            ).convert_alpha()

            return pygame.transform.smoothscale(
                image,
                ENEMY_SIZE
            )

        except (pygame.error, FileNotFoundError):
            print("敵画像が見つかりません。仮画像を使用します。")

            surface = pygame.Surface(
                ENEMY_SIZE,
                pygame.SRCALPHA
            )

            pygame.draw.ellipse(
                surface,
                ENEMY_COLOR,
                surface.get_rect()
            )

            return surface
    def update(self):
        # 敵は画面上部から下方向へ移動
        self.rect.y += ENEMY_SPEED

    def shoot(self, now, player_center):
        if now - self.last_shot_time < ENEMY_SHOT_INTERVAL:
            return None

        self.last_shot_time = now

        # 主人公の方向に向けて弾を発射
        dx = player_center[0] - self.rect.centerx
        dy = player_center[1] - self.rect.centery

        distance = math.hypot(dx, dy)

        if distance == 0:
            distance = 1

        vx = dx / distance * ENEMY_BULLET_SPEED
        vy = dy / distance * ENEMY_BULLET_SPEED

        return Projectile(
            self.rect.centerx,
            self.rect.bottom,
            vx,
            vy,
            ENEMY_BULLET_COLOR,
            radius=6
        )

    def draw(self, screen):
        screen.blit(self.image, self.rect)

# ============================================================
# 体力ゲージクラス
# ============================================================

class Life:
    def __init__(self):
        self.hp = 100
        self.max_hp = 100

    # ダメージ処理
    def hp_damage(self, damage):
        self.hp -= damage
        if self.hp < 0:
            self.hp = 0

    # 体力ゲージ描画
    def draw(self, screen):
        x = 20
        y = 20
        width = 200
        height = 20

        # ゲージの背景
        pygame.draw.rect(screen, (100, 100, 100),(x, y, width, height))

        # HPによって色を変更
        if self.hp > 50:
            color = (0, 255, 0)
        elif self.hp > 20:
            color = (255, 255, 0)
        else:
            color = (255, 0, 0)

        # HPゲージ
        pygame.draw.rect(screen, color,(x, y, width * self.hp / self.max_hp, height))

        # HPの数値
        font = pygame.font.SysFont(None, 30)
        text = font.render(f"HP: {self.hp}/{self.max_hp}", True, (255, 255, 255))
        screen.blit(text, (x, y + 25))

# ============================================================
# ボスクラス
# ============================================================
class Boss:
    def __init__(self):
            self.image = self.load_image()

            x = random.randint(
                BOSS_SIZE[0] // 2,
                SCREEN_WIDTH - BOSS_SIZE[0] // 2
            )
            pygame.mixer.music.load(BOSS_BGM) #  BGMの読み込み
            pygame.mixer.music.play(loops=-1) #  ループ再生
            self.rect = self.image.get_rect()
            self.rect.midtop = (x, -BOSS_SIZE[1])
            self.hp = 10
            self.last_shot_time = pygame.time.get_ticks()
    
    def load_image(self):
        try:
            image = pygame.image.load(
                BOSS_IMAGE
            ).convert_alpha()

            return pygame.transform.smoothscale(
                image,
                BOSS_SIZE
            )

        except (pygame.error, FileNotFoundError):
            print("ボス画像が見つかりません。仮画像を使用します。")

            surface = pygame.Surface(
                BOSS_SIZE,
                pygame.SRCALPHA
            )

            pygame.draw.ellipse(
                surface,
                BOSS_COLOR,
                surface.get_rect()
            )

            return surface

    def update(self):
        # 画面上部の位置まで降りてくる
        if self.rect.top < 30:
            self.rect.y += 2  

    def shoot(self, now, player_center):
        if now - self.last_shot_time < BOSS_SHOT_INTERVAL:
            return None

        self.last_shot_time = now

        # 主人公の方向に向けて弾を発射
        dx = player_center[0] - self.rect.centerx
        dy = player_center[1] - self.rect.centery

        distance = math.hypot(dx, dy)

        if distance == 0:
            distance = 1

        vx = dx / distance * BOSS_BULLET_SPEED
        vy = dy / distance * BOSS_BULLET_SPEED

        return Projectile(
            self.rect.centerx,
            self.rect.bottom,
            vx,
            vy,
            BOSS_BULLET_COLOR,
            radius=6
        )
    
    def draw(self, screen):
        screen.blit(self.image, self.rect)    

# ゲームクリア関数
def game_clear(screen:pygame.Surface):
    pygame.mixer.music.stop()  # boss_bgm停止
    pygame.mixer.music.load(CLEAR_BGM) #  クリアBGM読み込み
    pygame.mixer.music.play() #  一回だけ流す
    #  背景を暗く
    brack=pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT))
    pygame.draw.rect(brack,(0,0,0),pygame.Rect(0,0,SCREEN_WIDTH,SCREEN_HEIGHT))
    brack.set_alpha(200)
    #  文字表示
    font=pygame.font.Font(None, 70)
    txt=font.render("GameClear!!",True,(255,255,0))
    text_rct=txt.get_rect(center=(SCREEN_WIDTH//2,SCREEN_HEIGHT//2))
    brack.blit(txt,text_rct)
    #  キラキラの星の表示
    star1_img=pygame.image.load(STAR_IMAGE)
    star1_img=pygame.transform.scale(star1_img,(50,50))
    star1_rct=star1_img.get_rect(center=(SCREEN_WIDTH//10,SCREEN_HEIGHT//2))
    brack.blit(star1_img,star1_rct)
    star2_img=pygame.image.load(STAR_IMAGE)
    star2_img=pygame.transform.scale(star2_img,(50,50))
    star2_rct=star2_img.get_rect(center=((SCREEN_WIDTH - SCREEN_WIDTH//10),SCREEN_HEIGHT//2))
    brack.blit(star2_img,star2_rct)

    screen.blit(brack,(0,0))
    pygame.display.update()
    time.sleep(7)
    pygame.quit()
    sys.exit()

# ============================================================
# ゲーム管理クラス
# ============================================================

class Game:
    def __init__(self):
        pygame.init()
        self.life = Life()
        pygame.display.set_caption(WINDOW_TITLE)

        self.screen = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT)
        )

        self.clock = pygame.time.Clock()
        self.running = True

        self.background = self.load_background()

        self.player = Player()

        self.enemies = []
        self.player_bullets = []
        self.enemy_bullets = []

        self.boss = None #  開始時はbossはnone
        self.boss_spawn_time = 30000 # 開始からこのミリ秒数後にスポーン
        self.last_boss_spawn = pygame.time.get_ticks()

        self.last_enemy_spawn = pygame.time.get_ticks()

    def load_background(self):
        try:
            image = pygame.image.load(
                BACKGROUND_IMAGE
            ).convert()

            return pygame.transform.scale(
                image,
                (SCREEN_WIDTH, SCREEN_HEIGHT)
            )

        except (pygame.error, FileNotFoundError):
            print("背景画像が見つかりません。単色背景を使用します。")
            return None

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def spawn_enemy(self):
        self.enemies.append(Enemy())


    def spawn_boss(self):
        if self.boss is None:
            self.boss = Boss()
            print("ボス登場")
    def update(self):
        now = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()

        # 主人公の移動
        self.player.update(keys)

        # スペースキーによる弾の発射
        if keys[pygame.K_SPACE]:
            bullet = self.player.shoot(now)

            if bullet is not None:
                self.player_bullets.append(bullet)

        # 一定時間ごとに敵を生成
        if now - self.last_enemy_spawn >= ENEMY_SPAWN_INTERVAL:
            self.spawn_enemy()
            self.last_enemy_spawn = now

        # 敵の移動と敵弾の発射
        for enemy in self.enemies:
            enemy.update()

            bullet = enemy.shoot(
                now,
                self.player.rect.center
            )

            if bullet is not None:
                self.enemy_bullets.append(bullet)

        # 弾の移動
        for bullet in self.player_bullets:
            bullet.update()

        for bullet in self.enemy_bullets:
            bullet.update()

        self.remove_offscreen_objects()
        self.check_collisions()
      
       # ボスをn秒後に1回だけ出現させる
        if (
            self.boss is None
            and now - self.last_boss_spawn >= self.boss_spawn_time
        ):
            self.spawn_boss()

        # ボスが存在するときの処理
        if self.boss is not None:
            self.boss.update() #  bossがいたらまずアップデート

            # ボスの弾を発射
            bullet = self.boss.shoot(
                now,
                self.player.rect.center
            )

            if bullet is not None:
                self.enemy_bullets.append(bullet)
        
    def remove_offscreen_objects(self):
        # 画面外に出た弾を削除
        self.player_bullets = [
            bullet for bullet in self.player_bullets
            if bullet.rect.bottom > 0
        ]

        self.enemy_bullets = [
            bullet for bullet in self.enemy_bullets
            if (
                bullet.rect.bottom > 0
                and bullet.rect.top < SCREEN_HEIGHT
                and bullet.rect.right > 0
                and bullet.rect.left < SCREEN_WIDTH
            )
        ]

        # 画面下に到達した敵を削除
        self.enemies = [
            enemy for enemy in self.enemies
            if enemy.rect.top < SCREEN_HEIGHT
        ]

    def check_collisions(self):
        # 主人公の弾と敵の当たり判定
        for bullet in self.player_bullets[:]:
            hit_enemy = None

            for enemy in self.enemies:
                if bullet.rect.colliderect(enemy.rect):
                    hit_enemy = enemy
                    break

            if hit_enemy is not None:
                self.player_bullets.remove(bullet)
                self.enemies.remove(hit_enemy)

        # 敵の弾と主人公の当たり判定
        for bullet in self.enemy_bullets:
            if bullet.rect.colliderect(self.player.rect):
                # 当たった弾を削除
                self.enemy_bullets.remove(bullet)

                # 体力を10減らす
                self.life.hp_damage(10)

                # HPが0になったらゲームオーバー
                if self.life.hp <= 0:
                    print("GAME OVER")
                    self.running = False
                break

                # print("GAME OVER: 敵の弾が主人公に命中しました。")
                # self.running = False
                # break
    def draw_damage_effect(self):
        if self.life.hp <= 10:
            x = self.player.rect.centerx
            y = self.player.rect.centery

            # 煙のアニメーション
            t = pygame.time.get_ticks() / 300

            hai = pygame.Surface(
                self.screen.get_size(), pygame.SRCALPHA
            )

            for i in range(3):
                smoke_x = x + math.sin(t + i * 2) * 15
                smoke_y = y - 35 - i * 15 - abs(math.sin(t + i)) * 10

                pygame.draw.circle(
                    hai,
                    (130, 130, 130, 100),
                    (int(smoke_x), int(smoke_y)),
                    12 + i * 3
                )

            self.screen.blit(hai, (0, 0))

            # ひび割れ
            pygame.draw.lines(
                self.screen,
                (40, 40, 40),
                False,
                [
                    (x, y - 20),
                    (x - 8, y - 5),
                    (x + 3, y + 2),
                    (x - 5, y + 18)
                ],
                3
            )

            pygame.draw.lines(
                self.screen,
                (40, 40, 40),
                False,
                [
                    (x - 8, y - 5),
                    (x - 18, y - 12),
                    (x - 22, y - 22)
                ],
                2
            )
        # 主人公の弾とボスの当たり判定
        if self.boss is not None:

            for bullet in self.player_bullets[:]:

                if bullet.rect.colliderect(self.boss.rect):

                    self.player_bullets.remove(bullet)
                    self.boss.hp -= 1

                    # print("ボスHP:", self.boss.hp)

                    # ボスを倒した場合
                    if self.boss.hp <= 0:
                        print("BOSS DEFEATED!")
                        self.boss = None
                        game_clear(self.screen)

                    break
        

    def draw(self):
        # 背景描画
        if self.background is not None:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill((5, 8, 30))

        # 各オブジェクト描画
        self.player.draw(self.screen)

        for enemy in self.enemies:
            enemy.draw(self.screen)

        for bullet in self.player_bullets:
            bullet.draw(self.screen)

        for bullet in self.enemy_bullets:
            bullet.draw(self.screen)

        self.life.draw(self.screen)
        self.draw_damage_effect()

        for enemy in self.enemies:
            enemy.draw(self.screen)

        for bullet in self.player_bullets:
            bullet.draw(self.screen)

        for bullet in self.enemy_bullets:
            bullet.draw(self.screen)
        # ボスの描画
        if self.boss is not None:
            self.boss.draw(self.screen)

        pygame.display.flip()

    def run(self):
        while self.running:
            self.clock.tick(FPS)

            self.handle_events()
            self.update()
            self.draw()

        pygame.quit()
        sys.exit()


# ============================================================
# メイン処理
# ============================================================

if __name__ == "__main__":
    game = Game()
    game.run()
