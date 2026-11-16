"""Anchored campaign panels with clear combat, objective and reload feedback."""
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import CardMaker, TextNode, TransparencyAttrib


INK = (.86,.92,.91,1)
MUTED = (.52,.65,.67,1)
MINT = (.35,.85,.72,1)
RED = (.96,.32,.25,1)


def card(parent, name, frame, color):
    maker=CardMaker(name)
    maker.setFrame(*frame)
    node=parent.attachNewNode(maker.generate())
    node.setColor(*color)
    node.setTransparency(TransparencyAttrib.MAlpha)
    node.setBin('fixed',0)
    node.setDepthTest(False)
    node.setDepthWrite(False)
    return node


def text(parent, name, position, scale=.032, color=INK, align=TextNode.ALeft):
    node=OnscreenText(text='',parent=parent,pos=position,scale=scale,fg=color,
                      align=align,mayChange=True,shadow=(0,0,0,.5))
    node.setName(name)
    node.setBin('fixed',2)
    return node


def panel(parent, name, x, z, width, height, accent=MINT):
    root=parent.attachNewNode(name)
    root.setPos(x,0,z)
    card(root,name+'-background',(0,width,-height,0),(.018,.029,.035,.88))
    card(root,name+'-accent',(0,.005,-height,0),accent)
    return root


class CampaignHUD:
    def __init__(self, game):
        self.mission=panel(game.a2dTopLeft,'mission-panel',.045,-.045,1.02,.33)
        self.title=text(self.mission,'mission-title',(.025,-.055),.036)
        self.objective=text(self.mission,'mission-objective',(.025,-.12),.035)
        self.vitals=panel(game.a2dTopRight,'vitals-panel',-.66,-.045,.615,.235)
        self.health=text(self.vitals,'health-number',(.025,-.085),.071)
        self.health_label=text(self.vitals,'health-label',(.58,-.075),.025,MUTED,TextNode.ARight)
        self.health_label.setText('VITALS')
        card(self.vitals,'health-track',(.025,.58,-.13,-.115),(.15,.22,.24,1))
        self.health_fill=card(self.vitals,'health-value',(0,.555,-.13,-.115),MINT)
        self.health_fill.setX(.025)
        self.status=text(self.vitals,'combat-status',(.025,-.185),.026,MUTED)
        self.phase=panel(game.a2dBottomLeft,'reality-panel',.045,.23,.71,.18)
        self.phase_name=text(self.phase,'reality-name',(.025,-.06),.038,MINT)
        self.phase_hint=text(self.phase,'reality-hint',(.025,-.115),.026,MUTED)
        self.weapon=panel(getattr(game,'a2dBottomRight',game.aspect2d),
                          'ammo-panel',-.71,.29,.665,.24)
        self.weapon_name=text(self.weapon,'weapon-name',(.025,-.047),.028,MUTED)
        self.ammo=text(self.weapon,'ammo-count',(.025,-.135),.079)
        self.reserve=text(self.weapon,'reserve-count',(.62,-.13),.035,MUTED,TextNode.ARight)
        self.reload_hint=text(self.weapon,'reload-hint',(.025,-.2),.025,MUTED)
        self.reload_track=card(self.weapon,'reload-track',(.025,.62,-.225,-.215),(.15,.22,.24,1))
        self.reload_fill=card(self.weapon,'reload-progress',(0,.595,-.225,-.215),MINT)
        self.reload_fill.setX(.025)
        self.notice_panel=panel(game.aspect2d,'notice-panel',-.96,-.58,1.92,.14)
        self.notice=text(self.notice_panel,'notice',(.96,-.055),.029,INK,TextNode.ACenter)
        self.notice.textNode.setWordwrap(62)
        self.help=panel(game.aspect2d,'controls-panel',-.8,.5,1.6,.77)
        self.controls=text(self.help,'controls',(.045,-.075),.038)
        self.controls.setText('BREACH SHIFT / CONTROLS\n\nWASD   Move     |     Mouse   Look\n'
                              'LMB   Fire       |     R   Reload\n1 - 4   Select weapon\n'
                              'Space   Jump / double jump\nC / Ctrl   Hold crouch\n'
                              'Shift   Change reality     |     E   Interact\n'
                              'T   Retry     |     M   Sound     |     Esc   Exit\n\nF1   Close controls')
        self.help.hide()
        self.help_hint=text(game.aspect2d,'help-hint',(0,-.955),.026,INK,TextNode.ACenter)
        self.help_hint.setText('F1  CONTROLS')
        self.boss=panel(game.aspect2d,'boss-health-panel',-.55,.945,1.1,.105,RED)
        self.boss_label=text(self.boss,'boss-label',(.55,-.038),.026,INK,TextNode.ACenter)
        card(self.boss,'boss-track',(.025,1.075,-.085,-.07),(.2,.1,.1,1))
        self.boss_fill=card(self.boss,'boss-health',(0,1.05,-.085,-.07),RED)
        self.boss_fill.setX(.025)
        self.boss.hide()
        self.result=panel(game.aspect2d,'result-panel',-.7,.2,1.4,.34)
        self.result_title=text(self.result,'result-title',(.7,-.11),.065,INK,TextNode.ACenter)
        self.result_action=text(self.result,'result-action',(.7,-.23),.036,MUTED,TextNode.ACenter)
        self.result.hide()

    def toggle_help(self):
        self.help.show() if self.help.isHidden() else self.help.hide()

    def update(self, game):
        level=game.levels[game.progress.level_index]
        self.title.setText(f'{level.number:02d} / {len(game.levels):02d}   {level.name.upper()}')
        hp=game.player_health
        color=RED if hp.current<=25 else MINT
        self.health.setText(f'{hp.current:03d}')
        self.health.setFg(color)
        self.health_fill.setSx(max(0,hp.current/hp.maximum))
        self.health_fill.setColor(*color)
        crouched=getattr(game,'stance',None) and game.stance.is_crouching
        self.status.setText(f'{"CROUCHED" if crouched else "STANDING"}   /   THREATS {game.enemies_remaining:02d}')
        cooldown=game.reality.remaining(game.clock.getFrameTime())
        self.phase_name.setText(game.reality.state.value.upper())
        self.phase_name.setFg((.77,.55,1,1) if game.reality.state.value=='Breach' else MINT)
        self.phase_hint.setText(f'SHIFT   {cooldown:.1f}s' if cooldown else 'SHIFT   READY')
        self.notice_panel.show() if game.clock.getFrameTime()<game.notice_until else self.notice_panel.hide()
        bosses=[z for z in game.zombies.values() if z.kind.value=='warden' and z.health>0
                and (z.root.getPos()-game.player.getPos()).length()<32]
        if bosses:
            boss=min(bosses,key=lambda z:(z.root.getPos()-game.player.getPos()).length())
            self.boss_label.setText(f'WARDEN   /   {boss.health} HP')
            self.boss_fill.setSx(boss.health/boss.max_health)
            self.boss.show()
        else:
            self.boss.hide()
        self.set_weapon(game.weapon,game.arsenal.selected,game.weapon_view.reload_progress)
        if game.progress.complete or not hp.is_alive:
            self.result_title.setText('CAMPAIGN COMPLETE' if game.progress.complete else 'YOU DIED')
            self.result_title.setFg(MINT if game.progress.complete else RED)
            self.result_action.setText('T   PLAY AGAIN' if game.progress.complete else 'T   RETRY THIS MAP')
            self.result.show()
        else:
            self.result.hide()

    def set_weapon(self, weapon, kind, progress=0):
        slot=list(type(kind)).index(kind)+1
        self.weapon_name.setText(f'0{slot}   {weapon.name.upper()}')
        self.ammo.setText(f'{weapon.ammo:02d}')
        self.ammo.setFg(RED if weapon.ammo==0 else INK)
        self.reserve.setText(f'/ {weapon.reserve_ammo:03d}')
        hint='RELOADING' if weapon.is_reloading else ('R   RELOAD' if weapon.ammo<weapon.magazine_size and weapon.reserve_ammo else 'MAGAZINE READY')
        if weapon.ammo==0 and weapon.reserve_ammo==0:
            hint='NO AMMUNITION'
        self.reload_hint.setText(hint)
        self.reload_fill.setSx(max(0,min(1,progress)))
        for node in (self.reload_track,self.reload_fill):
            node.show() if weapon.is_reloading else node.hide()
