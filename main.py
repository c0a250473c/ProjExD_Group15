import math
import random
import sys
import os
import pygame as pg

os.chdir(os.path.dirname(os.path.abspath(__file__)))

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
PLAYER_MAX_HP = 3                # プレイヤーの最大HP

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

# アイテム設定
ITEM_SIZE = (32, 32)
ITEM_SPEED = 2
ITEM_DROP_RATE = 0.20 # 敵撃破時のドロップ率 (20%)

# アイテムの種類
ITEM_HEAL = 0        # 回復
ITEM_STUN = 1        # スタン（敵の動きと攻撃を止める）
ITEM_INVINCIBLE = 2  # 無敵
ITEM_RAPID = 3       # 連射速度アップ

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
    """
    弾に関するクラス（主人公および敵の弾）
    """
    def __init__(self, x: float, y: float, vx: float, vy: float, color: tuple[int, int, int], radius: int = 5) -> None:
        """
        弾Surfaceを生成する
        引数 x, y: 弾の初期座標
        引数 vx, vy: 弾の速度ベクトル
        引数 color: 弾の色
        引数 radius: 弾の半径
        """
        super().__init__()
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        
        self.image = pg.Surface((radius * 2, radius * 2), pg.SRCALPHA)
        pg.draw.circle(self.image, color, (radius, radius), radius)
        self.rect = self.image.get_rect(center=(round(self.x), round(self.y)))

    def update(self) -> None:
        """
        弾を速度ベクトルに基づき移動させる
        画面外に出た場合はkill()を呼び出してグループから削除する
        """
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
    """
    ドロップアイテムに関するクラス
    """
    def __init__(self, x: int, y: int, item_type: int) -> None:
        """
        アイテムSurfaceを生成する
        引数 x, y: アイテムの初期座標
        引数 item_type: アイテムの種類を示す定数
        """
        super().__init__()
        self.type = item_type
        self.image = self.load_image()
        self.rect = self.image.get_rect(center=(x, y))

    def load_image(self) -> pg.Surface:
        """
        アイテム画像を読み込む
        戻り値: 画像Surface
        """
        try:
            image = pg.image.load(ITEM_IMAGES[self.type]).convert_alpha()
            return pg.transform.smoothscale(image, ITEM_SIZE)
        except (pg.error, FileNotFoundError):
            surface = pg.Surface(ITEM_SIZE, pg.SRCALPHA)
            pg.draw.rect(surface, ITEM_COLORS[self.type], surface.get_rect(), border_radius=8)
            pg.draw.circle(surface, (255, 255, 255), (ITEM_SIZE[0]//2, ITEM_SIZE[1]//2), 4)
            return surface

    def update(self) -> None:
        """
        アイテムを落下させる
        画面外に出た場合はkill()を呼び出してグループから削除する
        """
        self.rect.y += ITEM_SPEED
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


# ============================================================
# 主人公クラス
# ============================================================
class Player(pg.sprite.Sprite):
    """
    主人公キャラクターに関するクラス
    """
    def __init__(self) -> None:
        """
        主人公Surfaceを生成し、初期状態を設定する
        """
        super().__init__()
        self.image = self.load_image()
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))
        
        self.last_shot_time = 0
        self.hp = PLAYER_MAX_HP
        self.stock_item = None
        self.invincible_end_time = 0
        self.rapid_fire_end_time = 0

    def load_image(self) -> pg.Surface:
        """
        主人公画像を読み込む
        戻り値: 画像Surface
        """
        try:
            image = pg.image.load(PLAYER_IMAGE).convert_alpha()
            return pg.transform.smoothscale(image, PLAYER_SIZE)
        except (pg.error, FileNotFoundError):
            surface = pg.Surface(PLAYER_SIZE, pg.SRCALPHA)
            pg.draw.polygon(surface, PLAYER_COLOR, [(32, 0), (4, 58), (32, 46), (60, 58)])
            return surface

    def update(self, keys: tuple) -> None:
        """
        押下キーに応じて主人公を移動させる
        引数 keys: 押下キーの真理値タプル
        """
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
        """
        弾を発射する
        引数 now: 現在のゲーム経過時間
        戻り値: 生成されたProjectileインスタンス、発射間隔に満たない場合はNone
        """
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
    """
    敵機に関するクラス
    """
    def __init__(self) -> None:
        """
        敵機Surfaceを生成し、ランダムな初期座標を設定する
        """
        super().__init__()
        self.image = self.load_image()
        self.rect = self.image.get_rect()
        self.rect.midtop = (random.randint(ENEMY_SIZE[0] // 2, SCREEN_WIDTH - ENEMY_SIZE[0] // 2), -ENEMY_SIZE[1])
        self.last_shot_time = pg.time.get_ticks()

    def load_image(self) -> pg.Surface:
        """
        敵機画像を読み込む
        戻り値: 画像Surface
        """
        try:
            image = pg.image.load(ENEMY_IMAGE).convert_alpha()
            return pg.transform.smoothscale(image, ENEMY_SIZE)
        except (pg.error, FileNotFoundError):
            surface = pg.Surface(ENEMY_SIZE, pg.SRCALPHA)
            pg.draw.ellipse(surface, ENEMY_COLOR, surface.get_rect())
            return surface

    def update(self) -> None:
        """
        敵機を降下させる
        画面外に出た場合はkill()を呼び出してグループから削除する
        """
        self.rect.y += ENEMY_SPEED
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

    def shoot(self, now: int, player_center: tuple[int, int]) -> Projectile | None:
        """
        プレイヤーの方向へ弾を発射する
        引数 now: 現在のゲーム経過時間
        引数 player_center: プレイヤーの中心座標タプル
        戻り値: 生成されたProjectileインスタンス、発射間隔に満たない場合はNone
        """
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
# ゲーム管理クラス
# ============================================================
class Game:
    """
    ゲーム全体を管理するクラス
    """
    def __init__(self) -> None:
        """
        ゲームの初期化と各Spriteグループの生成を行う
        """
        pg.init()
        pg.font.init()
        pg.display.set_caption(WINDOW_TITLE)

        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pg.time.Clock()
        self.running = True
        self.font = pg.font.SysFont(None, 28)

        self.background = self.load_background()
        self.player = Player()

        # オブジェクト管理をリストからGroupに変更
        self.enemies = pg.sprite.Group()
        self.player_bullets = pg.sprite.Group()
        self.enemy_bullets = pg.sprite.Group()
        self.items = pg.sprite.Group()

        self.last_enemy_spawn = pg.time.get_ticks()
        self.global_stun_end_time = 0 

    def load_background(self) -> pg.Surface | None:
        """
        背景画像を読み込む
        戻り値: 背景Surface、見つからない場合はNone
        """
        try:
            image = pg.image.load(BACKGROUND_IMAGE).convert()
            return pg.transform.scale(image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except (pg.error, FileNotFoundError):
            return None

    def handle_events(self) -> None:
        """
        キー入力などのイベントを処理する
        """
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_x:
                    self.use_item()

    def use_item(self) -> None:
        """
        ストックしているアイテムを使用し、効果を適用する
        """
        if self.player.stock_item is None:
            return

        item_type = self.player.stock_item
        self.player.stock_item = None
        now = pg.time.get_ticks()

        if item_type == ITEM_HEAL:
            self.player.hp = min(self.player.hp + 1, PLAYER_MAX_HP)
        elif item_type == ITEM_STUN:
            self.global_stun_end_time = now + 4000  
        elif item_type == ITEM_INVINCIBLE:
            self.player.invincible_end_time = now + 5000  
        elif item_type == ITEM_RAPID:
            self.player.rapid_fire_end_time = now + 5000  

    def update(self) -> None:
        """
        ゲーム内の全オブジェクトの状態を更新する
        """
        now = pg.time.get_ticks()
        keys = pg.key.get_pressed()

        self.player.update(keys)

        if keys[pg.K_SPACE]:
            bullet = self.player.shoot(now)
            if bullet is not None:
                self.player_bullets.add(bullet)

        is_stunned = now < self.global_stun_end_time

        if not is_stunned:
            if now - self.last_enemy_spawn >= ENEMY_SPAWN_INTERVAL:
                self.enemies.add(Enemy())
                self.last_enemy_spawn = now
            
            # 敵の更新と弾の発射処理
            self.enemies.update()
            for enemy in self.enemies:
                bullet = enemy.shoot(now, self.player.rect.center)
                if bullet is not None:
                    self.enemy_bullets.add(bullet)

        # 各Spriteグループのupdateメソッドを一括で呼び出す
        self.items.update()
        self.player_bullets.update()
        self.enemy_bullets.update()

        self.check_collisions(now)

    def check_collisions(self, now: int) -> None:
        """
        ゲーム内のすべての衝突判定を処理する
        引数 now: 現在のゲーム経過時間
        """
        # 主人公の弾と敵の当たり判定 (両方Trueにして同時削除)
        hits = pg.sprite.groupcollide(self.enemies, self.player_bullets, True, True)
        for enemy in hits.keys():
            if random.random() < ITEM_DROP_RATE:
                item_type = random.choice([ITEM_HEAL, ITEM_STUN, ITEM_INVINCIBLE, ITEM_RAPID])
                self.items.add(Item(enemy.rect.centerx, enemy.rect.centery, item_type))

        # 主人公と敵弾/敵本体の当たり判定 (無敵時間外のみ)
        if now >= self.player.invincible_end_time:
            bullet_hits = pg.sprite.spritecollide(self.player, self.enemy_bullets, True)
            enemy_hits = pg.sprite.spritecollide(self.player, self.enemies, True)
            
            if bullet_hits or enemy_hits:
                self.player.hp -= 1
                self.player.invincible_end_time = now + 1500  
                if self.player.hp <= 0:
                    print("GAME OVER: HPが0になりました。")
                    self.running = False

        # 主人公とアイテムの当たり判定 (拾うまではアイテムを消さないため False)
        item_hits = pg.sprite.spritecollide(self.player, self.items, False)
        for item in item_hits:
            if self.player.stock_item is None:
                self.player.stock_item = item.type
                item.kill() # アイテムをストックできた場合のみグループから削除

    def draw_ui(self, now: int) -> None:
        """
        UI(HPやアイテム、バフ効果)を描画する
        引数 now: 現在のゲーム経過時間
        """
        hp_text = self.font.render(f"HP: {self.player.hp} / {PLAYER_MAX_HP}", True, (255, 255, 255))
        self.screen.blit(hp_text, (10, 10))

        if self.player.stock_item is not None:
            item_name = ITEM_NAMES[self.player.stock_item]
            item_text = self.font.render(f"ITEM: {item_name} [Press X]", True, ITEM_COLORS[self.player.stock_item])
        else:
            item_text = self.font.render("ITEM: NONE", True, (150, 150, 150))
        self.screen.blit(item_text, (10, 40))

        y_offset = 70
        if now < self.player.invincible_end_time:
            text = self.font.render("INVINCIBLE ACTIVE!", True, ITEM_COLORS[ITEM_INVINCIBLE])
            self.screen.blit(text, (10, y_offset))
            y_offset += 25
        if now < self.player.rapid_fire_end_time:
            text = self.font.render("RAPID FIRE ACTIVE!", True, ITEM_COLORS[ITEM_RAPID])
            self.screen.blit(text, (10, y_offset))
            y_offset += 25
        if now < self.global_stun_end_time:
            text = self.font.render("ENEMY STUNNED!", True, ITEM_COLORS[ITEM_STUN])
            self.screen.blit(text, (10, y_offset))

    def draw(self) -> None:
        """
        ゲーム内のすべてのオブジェクトを画面に描画する
        """
        now = pg.time.get_ticks()

        if self.background is not None:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill((5, 8, 30))

        # Group クラスの draw メソッドで一括描画
        self.enemies.draw(self.screen)
        self.items.draw(self.screen)
        self.player_bullets.draw(self.screen)
        self.enemy_bullets.draw(self.screen)
            
        self.screen.blit(self.player.image, self.player.rect)
        self.draw_ui(now)
        pg.display.flip()

    def run(self) -> None:
        """
        ゲームのメインループを実行する
        """
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