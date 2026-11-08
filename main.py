import math
import random
import sys
import pygame


# ============================================================
# 設定
# ============================================================

SCREEN_WIDTH = 480
SCREEN_HEIGHT = 800
FPS = 60 
WINDOW_TITLE = "SPACE SHOOTER"

BACKGROUND_IMAGE = "assets/background.png"
PLAYER_IMAGE = "assets/player.png"
ENEMY_IMAGE = "assets/enemy.png"

PLAYER_SIZE = (64, 64)
PLAYER_SPEED = 5
PLAYER_SHOT_INTERVAL = 250       # ミリ秒
PLAYER_BULLET_SPEED = 9

#50点ごとに発射感覚を短くする設定
SHOT_INTERVAL_DECREASE = 25
MIN_SHOT_INTERVAL = 80

ENEMY_SIZE = (48, 48)
ENEMY_SPEED = 2
ENEMY_SPAWN_INTERVAL = 1400      # ミリ秒
ENEMY_SHOT_INTERVAL = 1600       # ミリ秒
ENEMY_BULLET_SPEED = 4

# 画像が読み込めない場合の仮表示色
PLAYER_COLOR = (80, 220, 255)
ENEMY_COLOR = (255, 100, 100)
PLAYER_BULLET_COLOR = (255, 245, 100)
ENEMY_BULLET_COLOR = (255, 120, 80)

class Score:
    """
    ・撃ち落とした爆弾や敵機の数をスコアとして表示する
      →爆弾: 1点, 敵機: 10点
    ・そのスコア数によって能力向上
      →100点を更新する度、弾速やその大きさが変化する
    """
    def __init__(self):
        self.font = pygame.font.Font(None, 50)
        self.color = (255, 255, 255)
        self.value = 0
        
    def add(self, point):
        self.value += point
        
    def draw(self, screen):
        image = self.font.render(
            f"Score: {self.value}", True, self.color
        )
        rect = image.get_rect()
        rect.bottomleft = (15, SCREEN_HEIGHT - 15)
        screen.blit(image, rect)
        

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

    def shoot(self, now, shot_interval):
        # 一定時間ごとに弾を発射
        if now - self.last_shot_time < shot_interval:
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
# ゲーム管理クラス
# ============================================================

class Game:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption(WINDOW_TITLE)

        self.screen = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT)
        )

        self.clock = pygame.time.Clock()
        self.running = True
        self.background = self.load_background()

        self.reset_game()

        # self.enemies = []
        # self.player_bullets = []
        # self.enemy_bullets = []
        # self.explosions = []
        # self.last_enemy_spawn = pygame.time.get_ticks()
        
    def reset_game(self):
        #ゲーム開始時・再スタート時の初期化
        self.score = Score()
        self.player = Player()
        
        self.enemies = []
        self.player_bullets = []
        self.enemy_bullets = []
        
        self.last_enemy_spawn = pygame.time.get_ticks()
        self.game_over = False

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
                
            #ゲームオーバー時の操作
            elif event.type == pygame.KEYDOWN and self.game_over:
                if event.key == pygame.K_r:
                    self.reset_game()
                    
                elif event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                    self.running = False

    def spawn_enemy(self):
        self.enemies.append(Enemy())
        
    def get_shot_interval(self):
        #50点ごとに発射間隔を短縮
        level = self.score.value // 50
        interval = (
            PLAYER_SHOT_INTERVAL - level * SHOT_INTERVAL_DECREASE
        )
        
        #発射間隔短縮の限界
        return max(MIN_SHOT_INTERVAL, interval)

    def update(self):
        #ゲームオーバー時はゲーム内の動きを停止
        if self.game_over:
            return
        
        now = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()

        # 主人公の移動
        self.player.update(keys)

        # スペースキーによる弾の発射
        if keys[pygame.K_SPACE]:
            bullet = self.player.shoot(now, self.get_shot_interval())

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
        # 主人公の弾と敵の当たり判定(敵機倒すと10点)
        for bullet in self.player_bullets[:]:
            hit_enemy = None

            for enemy in self.enemies:
                if bullet.rect.colliderect(enemy.rect):
                    hit_enemy = enemy
                    break

            if hit_enemy is not None:
                self.player_bullets.remove(bullet)
                self.enemies.remove(hit_enemy)
                self.score.add(10)

        #敵の攻撃を撃ち落とす(撃ち落とすと1点)
        for player_bullet in self.player_bullets[:]:
            hit_enemy_bullet = None
            
            for enemy_bullet in self.enemy_bullets:
                if player_bullet.rect.colliderect(enemy_bullet.rect):
                    hit_enemy_bullet = enemy_bullet
                    break
            
            if hit_enemy_bullet is not None:
                self.player_bullets.remove(player_bullet)
                self.enemy_bullets.remove(hit_enemy_bullet)
                self.score.add(1)

        # 敵の弾と主人公の当たり判定(ゲームオーバー)
        for bullet in self.enemy_bullets:
            if bullet.rect.colliderect(self.player.rect):
                self.game_over = True
                break

    def draw_game_over(self):
        # 画面全体に半透明の黒い幕を重ねる
        overlay = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        title_font = pygame.font.Font(None, 72)
        text_font = pygame.font.Font(None, 36)

        title = title_font.render(
            "GAME OVER", True, (255, 80, 80)
        )

        final_score = text_font.render(
            f"Final Score: {self.score.value}",
            True, (255, 255, 255)
        )

        retry = text_font.render(
            "Press R to Restart", True, (255, 255, 255)
        )

        quit_text = text_font.render(
            "Press Q to Quit", True, (255, 255, 255)
        )

        self.screen.blit(
            title,
            title.get_rect(center=(SCREEN_WIDTH // 2, 320))
        )

        self.screen.blit(
            final_score,
            final_score.get_rect(center=(SCREEN_WIDTH // 2, 390))
        )

        self.screen.blit(
            retry,
            retry.get_rect(center=(SCREEN_WIDTH // 2, 455))
        )

        self.screen.blit(
            quit_text,
            quit_text.get_rect(center=(SCREEN_WIDTH // 2, 500))
        )

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
            
        #スコア表示    
        self.score.draw(self.screen)
        
        #ゲームオーバー画面
        if self.game_over:
            self.draw_game_over()

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