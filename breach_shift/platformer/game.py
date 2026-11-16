"""Panda3D window used solely for orthographic 2D cards, input and sound."""
from math import atan2, degrees, exp, sin

from direct.gui.DirectGui import DirectButton, DirectFrame
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import (ClockObject, GraphicsWindow, KeyboardButton, OrthographicLens,
                         TextNode, WindowProperties, loadPrcFileData)

from breach_shift.audio.bank import SoundBank
from breach_shift.combat.catalog import WEAPON_SPECS
from breach_shift.enemies.catalog import ZOMBIE_SPECS
from breach_shift.platformer.scenery import SideScenery, glow_texture, line, quad
from breach_shift.platformer.session import Controls, SideSession
from breach_shift.platformer.sprites import SpriteLibrary
from breach_shift.world.reality import Reality


class SideHUD:
    def __init__(self, game):
        self.game = game
        self.root = game.aspect2d.attachNewNode("game-hud")
        self.panels = []
        self._text_cache = {}
        self.top = self.panel(game.a2dTopLeft, (.035,0,-.035), (0,1.32,-.215,0))
        self.title = self.text(self.top, "BREACH SHIFT", (.035,-.055), .047, (.53,.92,.87,1))
        self.sector = self.text(self.top, "", (.035,-.105), .036)
        self.objective = self.text(self.top, "", (.035,-.155), .029)
        self.enemies = self.text(self.top, "", (.035,-.193), .027, (.55,.66,.68,1))
        self.vitals = self.panel(game.a2dTopRight, (-.035,0,-.035), (-.8,0,-.215,0))
        self.health = self.text(self.vitals, "100", (-.755,-.093), .072, (.6,.95,.82,1))
        self.text(self.vitals, "VITALS", (-.23,-.052), .026, (.49,.67,.67,1))
        self.health_bar = DirectFrame(parent=self.vitals, frameColor=(.26,.83,.68,1),
                                      frameSize=(0,.71,0,.012), pos=(-.755,0,-.126))
        self.stance = self.text(self.vitals, "", (-.755,-.184), .028, (.58,.7,.72,1))
        self.shift_panel = self.panel(game.a2dBottomLeft, (.035,0,.035), (0,1.21,0,.19))
        self.reality = self.text(self.shift_panel, "", (.035,.128), .041, (.45,.9,.86,1))
        self.shift = self.text(self.shift_panel, "", (.035,.083), .027)
        self.shift_bar = DirectFrame(parent=self.shift_panel, frameColor=(.36,.83,.8,1),
                                     frameSize=(0,1.12,0,.008), pos=(.035,0,.053))
        self.text(self.shift_panel, "F1 CONTROLS    ESC PAUSE", (.035,.019), .023, (.46,.61,.64,1))
        self.ammo_panel = self.panel(game.a2dBottomRight, (-.035,0,.035), (-1.02,0,0,.215))
        self.weapon = self.text(self.ammo_panel, "", (-.975,.166), .028, (.63,.77,.79,1))
        self.ammo = self.text(self.ammo_panel, "", (-.975,.077), .077)
        self.reload = self.text(self.ammo_panel, "", (-.975,.027), .026, (.72,.81,.76,1))
        self.notice = OnscreenText(parent=self.root, text="", pos=(0,-.64), scale=.033,
                                  fg=(.8,.88,.87,1), align=TextNode.ACenter, mayChange=True,
                                  shadow=(0,0,0,1), shadowOffset=(.05,.05))
        self.notice.textNode.setWordwrap(70)
        self.boss_root = self.root.attachNewNode("boss-hud")
        self.boss_text = self.text(self.boss_root, "THE WARDEN", (-.58,.88), .028, (.9,.59,.59,1))
        DirectFrame(parent=self.boss_root, frameColor=(.08,.035,.04,.95), frameSize=(-.6,.6,.825,.845))
        self.boss_bar = DirectFrame(parent=self.boss_root, frameColor=(.85,.25,.32,1),
                                    frameSize=(0,1.2,0,.02), pos=(-.6,0,.825))
        self.help = self.panel(self.root, (0,0,0), (-.96,.96,-.58,.6))
        self.text(self.help, "BREACH SHIFT  /  CONTROLS", (-.87,.47), .052, (.5,.9,.86,1))
        help_text = ("A / D or Arrows     Move left / right\n"
                     "Mouse + Left click   Aim / shoot\n"
                     "Space / W / Up      Jump; press twice for double jump\n"
                     "C / Ctrl / Down     Hold to crouch\n"
                     "R                   Reload\n"
                     "1 / 2 / 3 / 4       Pistol / SMG / rifle / shotgun\n"
                     "Shift               Change reality\n"
                     "E                   Recover core / extract\n"
                     "T                   Retry sector / restart range\n"
                     "M                   Toggle sound\n"
                     "Esc                 Pause / resume\n"
                     "F1                  Close this panel")
        self.text(self.help, help_text, (-.86,.34), .035)
        self.help.hide()
        self.pause = self.panel(self.root, (0,0,0), (-.7,.7,-.57,.54))
        self.text(self.pause, "PAUSED", (-.23,.36), .08, (.53,.92,.87,1))
        for title, z, command in (("RESUME", .12, game.toggle_pause),
                                   ("RETRY SECTOR", -.1, game.restart_sector),
                                   ("QUIT", -.32, game.userExit)):
            DirectButton(parent=self.pause, text=title, scale=.055, pos=(0,0,z),
                         frameSize=(-8,8,-1.15,1.5), frameColor=(.12,.24,.25,1),
                         text_fg=(.86,.94,.93,1), relief=0, command=command)
        self.pause.hide()

    def panel(self, parent, position, bounds):
        panel = DirectFrame(parent=parent, frameColor=(.025,.047,.058,.94),
                            frameSize=bounds, pos=position)
        self.panels.append(panel)
        return panel

    def text(self, parent, value, position, scale, color=(.84,.9,.9,1)):
        return OnscreenText(parent=parent, text=value, pos=position, scale=scale, fg=color,
                            align=TextNode.ALeft, mayChange=True)

    def set_text(self, node, text):
        if self._text_cache.get(id(node)) != text:
            node.setText(text)
            self._text_cache[id(node)] = text

    def update(self, session):
        self.set_text(self.sector, f"{session.level.number:02} / 10   {session.level.name.upper()}")
        if session.training:
            self.set_text(self.objective, f"HITS {session.statistics.hits} / {session.statistics.shots}   ACCURACY {session.statistics.accuracy:.0f}%")
        elif session.progress.complete:
            self.set_text(self.objective, "CAMPAIGN COMPLETE  /  T: PLAY AGAIN")
        elif not session.progress.core_collected:
            distance = abs(session.player.x - session.level.core[0])
            self.set_text(self.objective, f"CORE: BREACH  /  {distance:.0f}m  /  E TO RECOVER")
        else:
            self.set_text(self.objective, "EXTRACT IN NORMAL  /  E AT THE EXIT")
        wave = "RIFT SEALED" if session.director.sealed else f"WAVE IN {session.director.remaining:.0f}s"
        self.set_text(self.enemies, f"INFECTED {session.alive}    " + ("PRACTICE" if session.training else wave))
        self.set_text(self.health, str(session.health.current))
        self.health_bar.setSx(max(.001,session.health.current/session.health.maximum))
        jumps = max(0,2-session.jumps_used)
        self.set_text(self.stance, ("CROUCHING" if session.crouching else "AIRBORNE" if not session.player.grounded else "STANDING") + f"  /  JUMPS {jumps}")
        self.set_text(self.reality, session.reality.state.value.upper() + " REALITY")
        ready = session.reality.remaining(session.now)
        self.set_text(self.shift, "SHIFT READY" if ready == 0 else f"SHIFT RECHARGING  {ready:.1f}s")
        self.shift_bar.setSx(max(.001,1-ready/max(.001,session.reality.cooldown)))
        self.set_text(self.weapon, f"0{list(session.arsenal.weapons).index(session.arsenal.selected)+1}  {session.weapon.name.upper()}")
        self.weapon.setFg(WEAPON_SPECS[session.arsenal.selected].color)
        self.set_text(self.ammo, f"{session.weapon.ammo:02}  /  {session.weapon.reserve_ammo:03}")
        self.set_text(self.reload, f"RELOADING {session.reload_progress*100:.0f}%" if session.weapon.is_reloading
                      else "R: RELOAD" if session.weapon.ammo < session.weapon.magazine_size else "MAGAZINE READY")
        self.set_text(self.notice, session.notice if session.now < session.notice_until else "")
        bosses = [enemy for enemy in session.enemies.values() if enemy.kind.value == "warden" and enemy.health > 0]
        if bosses:
            self.boss_root.show()
            self.boss_bar.setSx(max(.001,bosses[0].health/bosses[0].maximum))
            self.set_text(self.boss_text, f"THE WARDEN  /  {int(bosses[0].health)} HP")
        else:
            self.boss_root.hide()

    def destroy(self):
        for panel in self.panels:
            panel.destroy()
        self.root.removeNode()


class SideViewGame(ShowBase):
    def __init__(self, *, level=1, training=False, headless=False):
        loadPrcFileData("breach-shift-2d", "win-size 1280 720\nwindow-title Breach Shift - 2D\ntextures-power-2 none\nshow-frame-rate-meter false")
        self.headless = headless
        if headless:
            loadPrcFileData("2d-preview", "audio-library-name null\nsync-video false")
        super().__init__(windowType="offscreen" if headless else None)
        self.clock = ClockObject.getGlobalClock()
        self.disableMouse()
        self.setBackgroundColor(.025,.04,.055)
        self.lens = OrthographicLens()
        self.lens.setNearFar(.1,100)
        self.cam.node().setLens(self.lens)
        self.camera.setY(-50)
        self.library = SpriteLibrary(self.loader)
        self.session = SideSession(level=level, training=training)
        self.audio = SoundBank(self.loader, enabled=not headless)
        self.world_root = self.render.attachNewNode("2d-world")
        self.scenery = None
        self.enemies = {}
        self.pickup_nodes = {}
        self.weapon_sprite = None
        self.previous_revision = -1
        self.accumulator = 0.0
        self.paused = False
        self.edges = set()
        self.fire_held = False
        self.selected_slot = None
        self.camera_x, self.camera_z = 10.0, 4.2
        self.death_elapsed = 0.0
        self.aim = (14,1.2)
        self.view_width = 32.0
        self.effects = self.world_root.attachNewNode("effects")
        self.reticle = self.world_root.attachNewNode("reticle")
        for points in (((-.2,0),(-.07,0)),((.07,0),(.2,0)),((0,-.2),(0,-.07)),((0,.07),(0,.2))):
            line(self.reticle, points, (.7,.98,.92,1), width=1.5, order=80)
        self.player_sprite = self.library.sprite(self.world_root,"player",order=40)
        self.flash = quad(self.world_root,-.5,-.5,1,1,(1,.64,.2,.9),order=55,texture=glow_texture())
        self.hud = SideHUD(self)
        self._bind_input()
        self._rebuild()
        self.render_scene(0)
        self.taskMgr.add(self.update_frame,"side-view-frame")
        self._cursor(False)

    def _cursor(self, visible):
        if isinstance(self.win, GraphicsWindow):
            properties = WindowProperties()
            properties.setCursorHidden(not visible)
            self.win.requestProperties(properties)

    def _edge(self, action):
        self.edges.add(action)

    def _fire(self, pressed):
        self.fire_held = pressed
        if pressed:
            self.edges.add("fire_pressed")

    def _select(self, slot):
        self.selected_slot = slot

    def _bind_input(self):
        for prefix in ("", "shift-", "control-", "shift-control-", "control-shift-"):
            for key, action in (("space","jump"),("w","jump"),("arrow_up","jump"),
                                ("r","reload"),("e","interact")):
                self.accept(prefix+key,self._edge,[action])
            self.accept(prefix+"mouse1",self._fire,[True])
            self.accept(prefix+"mouse1-up",self._fire,[False])
            self.accept(prefix+"t",self.restart_sector)
            self.accept(prefix+"escape",self.toggle_pause)
            self.accept(prefix+"f1",self.toggle_help)
            self.accept(prefix+"m",self.audio.toggle)
            for slot in range(4):
                self.accept(prefix+str(slot+1),self._select,[slot])
        self.accept("shift",self._edge,["shift"])
        self.accept("control-shift",self._edge,["shift"])

    def set_paused(self, paused):
        self.paused = paused
        self.edges.clear()
        self.fire_held = False
        self.selected_slot = None
        self.accumulator = 0
        self.hud.pause.show() if paused else self.hud.pause.hide()
        self._cursor(paused)
        if paused:
            self.audio.stop_all()

    def toggle_pause(self):
        self.hud.help.hide()
        self.set_paused(not self.paused)

    def toggle_help(self):
        if self.hud.help.isHidden():
            self.set_paused(True)
            self.hud.pause.hide()
            self.hud.help.show()
        else:
            self.hud.help.hide()
            self.set_paused(False)

    def restart_sector(self):
        self.session.restart()
        self.audio.stop_all()
        self.hud.help.hide()
        self.set_paused(False)
        self._rebuild()

    def _controls(self):
        watcher = self.mouseWatcherNode
        down = lambda key: watcher is not None and watcher.isButtonDown(key)
        left = down(KeyboardButton.asciiKey("a")) or down(KeyboardButton.left())
        right = down(KeyboardButton.asciiKey("d")) or down(KeyboardButton.right())
        crouch = down(KeyboardButton.asciiKey("c")) or down(KeyboardButton.control()) or down(KeyboardButton.down())
        controls = Controls(move=int(right)-int(left),aim=self.aim,fire=self.fire_held,crouch=crouch,
                            slot=self.selected_slot,**{action:action in self.edges
                            for action in ("jump","shift","interact","reload","fire_pressed")})
        self.edges.clear()
        self.selected_slot = None
        return controls

    def _rebuild(self):
        if self.scenery is not None:
            self.scenery.destroy()
        self.scenery = SideScenery(self.world_root,self.session.level,self.library)
        for sprite in self.enemies.values():
            sprite.node.removeNode()
        for node in self.pickup_nodes.values():
            node.removeNode()
        self.enemies.clear()
        self.pickup_nodes.clear()
        self.previous_revision = self.session.revision
        self.camera_x = max(10,min(self.session.level.width-10,self.session.player.x+5))
        self.camera_z = 4.2
        self.death_elapsed = 0

    def _update_weapon(self):
        name = self.session.arsenal.selected.value
        if self.weapon_sprite is None or self.weapon_sprite.entry["file"] != name+".png":
            if self.weapon_sprite is not None:
                self.weapon_sprite.node.removeNode()
            self.weapon_sprite = self.library.sprite(self.world_root,name,order=43)
        session = self.session
        x, z = session.player.x, session.player.z+session.player.height*.72
        angle = max(-85,min(85,degrees(atan2(self.aim[1]-z,abs(self.aim[0]-x)+.001))))
        reload_angle = sin(session.reload_progress*3.14159)*35 if session.weapon.is_reloading else 0
        self.weapon_sprite.node.setPos(x+session.facing*.12,0,z)
        self.weapon_sprite.node.setSx(session.facing)
        self.weapon_sprite.node.setR((-angle+reload_angle)*session.facing)
        if not session.health.is_alive:
            self.weapon_sprite.node.hide()
        else:
            self.weapon_sprite.node.show()
        flash = session.now-session.shot_at < .055
        self.flash.show() if flash else self.flash.hide()
        self.flash.setPos(x+session.facing*.83,0,z)

    def render_scene(self, dt):
        session = self.session
        if self.previous_revision != session.revision:
            self._rebuild()
        aspect = max(.5,self.getAspectRatio())
        self.view_width = 14.4*aspect
        self.lens.setFilmSize(self.view_width,14.4)
        target_x = max(10,min(session.level.width-10,session.player.x+session.facing*4.5))
        target_z = 4.2+max(0,session.player.z-3)*.55
        blend = 1-exp(-5*max(0,dt))
        self.camera_x += (target_x-self.camera_x)*blend
        self.camera_z += (target_z-self.camera_z)*blend
        self.camera.setPos(self.camera_x,-50,self.camera_z)
        self.camera.setHpr(0,0,0)
        if self.mouseWatcherNode is not None and self.mouseWatcherNode.hasMouse() and not self.headless:
            mouse = self.mouseWatcherNode.getMouse()
            self.aim = (self.camera_x+mouse.x*self.view_width/2,self.camera_z+mouse.y*7.2)
        self.reticle.setPos(self.aim[0],0,self.aim[1])
        self.reticle.hide() if self.paused else self.reticle.show()
        self.scenery.update(session,self.camera_x)
        if not session.health.is_alive:
            self.death_elapsed += 0 if self.paused else dt
            state,frame = "death",min(7,int(self.death_elapsed*8))
        elif session.weapon.is_reloading:
            state,frame = "reload",min(7,int(session.reload_progress*8))
        elif session.crouching:
            state,frame = "crouch",int(session.player_phase*8) if abs(session.player.vx)>.1 else 0
        elif not session.player.grounded:
            state,frame = "jump",0
        elif abs(session.player.vx)>.1:
            state,frame = "walk",int(session.player_phase*8)
        else:
            state,frame = "idle",int(session.now*3)
        self.player_sprite.set_frame(state,frame)
        self.player_sprite.node.setPos(session.player.x,0,session.player.z)
        self.player_sprite.node.setSx(session.facing)
        hurt = session.now-session.damage_at < .12
        self.player_sprite.node.setColorScale(1,.5 if hurt else 1,.5 if hurt else 1,1)
        for identifier in set(self.enemies)-set(session.enemies):
            self.enemies.pop(identifier).node.removeNode()
        for identifier,enemy in session.enemies.items():
            if identifier not in self.enemies:
                self.enemies[identifier] = self.library.sprite(self.world_root,enemy.kind.value,order=35)
            sprite = self.enemies[identifier]
            sprite.node.setPos(enemy.body.x,0,enemy.body.z)
            sprite.node.setSx(enemy.facing)
            if enemy.dead_at is not None:
                sprite.set_frame("death",min(7,int((session.now-enemy.dead_at)*8)))
            elif session.now-enemy.attack_at < .65:
                sprite.set_frame("attack",min(7,int((session.now-enemy.attack_at)*12)))
            elif abs(enemy.body.vx)>.05:
                sprite.set_frame("walk",int(enemy.phase*8))
            else:
                sprite.set_frame("idle",int(session.now*3))
            alpha = .28 if enemy.kind.value=="stalker" and session.reality.state is Reality.NORMAL else 1
            hurt = session.now-enemy.damaged_at < .12
            sprite.node.setColorScale(1,.4 if hurt else 1,.4 if hurt else 1,alpha)
        self._update_weapon()
        self._effects()
        self.hud.update(session)
        for cue,x,z in session.events:
            distance = abs(x-session.player.x)
            self.audio.play(cue,volume=.75/(1+distance*.08),now=session.now)
        session.events.clear()

    def _effects(self):
        for child in self.effects.getChildren():
            child.removeNode()
        session = self.session
        for trace in session.traces:
            if trace.kind=="shot":
                line(self.effects,[trace.start,trace.end],(1,.8,.4,.8),width=1.4,order=50)
            else:
                x,z = trace.start
                quad(self.effects,x-.24,z-.24,.48,.48,(.8,.12,.13,.8),order=51,texture=self.scenery.glow)
        for projectile in session.projectiles:
            quad(self.effects,projectile.x-.25,projectile.z-.25,.5,.5,(.4,1,.25,.9),order=50,texture=self.scenery.glow)
        for enemy in session.enemies.values():
            if enemy.health>0 and session.now-enemy.damaged_at<2.5:
                x,z = enemy.body.x,enemy.body.z+enemy.body.height+.15
                quad(self.effects,x-.4,z,.8,.04,(.1,.15,.15,1),order=48)
                quad(self.effects,x-.4,z,.8*enemy.health/enemy.maximum,.04,ZOMBIE_SPECS[enemy.kind].color,order=49)
            if enemy.windup_until is not None:
                x,z = enemy.body.x,enemy.body.z
                quad(self.effects,x-4.5,z+.02,9,.09,(1,.25,.12,.8),order=46)
        present = {pickup.identifier for pickup in session.pickups}
        for identifier in set(self.pickup_nodes)-present:
            self.pickup_nodes.pop(identifier).removeNode()
        for pickup in session.pickups:
            if pickup.identifier not in self.pickup_nodes:
                node = self.world_root.attachNewNode("ammo")
                quad(node,-.22,0,.44,.25,WEAPON_SPECS[pickup.kind].color,order=32)
                quad(node,-.12,.06,.24,.12,(.18,.24,.15,1),order=33)
                self.pickup_nodes[pickup.identifier] = node
            self.pickup_nodes[pickup.identifier].setPos(pickup.x,0,pickup.z+.1+sin(session.now*3)*.045)

    def update_frame(self, task):
        dt = min(self.clock.getDt(),.1)
        if not self.headless and isinstance(self.win,GraphicsWindow) and not self.win.getProperties().getForeground():
            if not self.paused:
                self.set_paused(True)
        if not self.paused:
            self.accumulator += max(0,dt)
            while self.accumulator >= 1/120:
                self.session.step(self._controls(),1/120)
                self.accumulator -= 1/120
        self.render_scene(dt)
        return Task.cont

    def destroy(self):
        if hasattr(self,"audio"):
            self.audio.stop_all()
        if hasattr(self,"hud"):
            self.hud.destroy()
        super().destroy()
