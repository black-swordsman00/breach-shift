"""Create a local review gallery from actual Blender renders and game balance."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from breach_shift.combat.catalog import WEAPON_ORDER, WEAPON_SPECS
from breach_shift.enemies.catalog import ZOMBIE_ORDER, ZOMBIE_SPECS


HTML = r'''<!doctype html>
<html lang="sr-Latn"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Breach Shift · Model workshop</title>
<style>
:root{color-scheme:dark;--bg:#090d11;--panel:#111820;--line:#26323b;--muted:#92a0a8;--orange:#ee9258;--text:#e9ecec}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 'Segoe UI',system-ui,sans-serif}button,a{font:inherit}button{cursor:pointer}a{color:var(--orange)}
header,main,footer{max-width:1240px;margin:auto;padding:24px 32px}header{display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--line)}
.brand{font-size:24px;font-weight:800;letter-spacing:5px}.brand span{color:var(--orange)}.eyebrow{color:var(--muted);font-size:11px;letter-spacing:3px;text-transform:uppercase}.tag{border:1px solid var(--line);padding:7px 12px;border-radius:4px;color:var(--muted);font-size:12px}
h1{font-size:32px;line-height:1.2;margin:8px 0 12px;letter-spacing:-1px}p{color:var(--muted);max-width:660px}.tabs{display:flex;gap:8px;margin:22px 0 16px;flex-wrap:wrap}button,.source{background:var(--panel);border:1px solid var(--line);color:var(--text);border-radius:5px;padding:9px 15px;text-decoration:none}button:hover,.source:hover{border-color:var(--orange)}button[aria-pressed=true]{background:#30231c;border-color:var(--orange);color:#ffc39b}.outline{margin-left:auto}
.hero{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(280px,1fr);border:1px solid var(--line);border-radius:9px;overflow:hidden;background:var(--panel)}
.stage{background:#070a0d;min-height:510px;display:flex;justify-content:center;align-items:center}.stage img{width:100%;height:510px;object-fit:contain}.details{padding:35px 32px;display:flex;flex-direction:column;justify-content:center}.details h2{font-size:38px;line-height:1.15;margin:10px 0 20px}.metrics{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:8px 0 28px}.metric{border-top:1px solid var(--line);padding-top:10px}.metric b{display:block;font-size:28px;font-weight:500}.metric span{color:var(--muted);font-size:12px;letter-spacing:1px}.source{display:inline-block;align-self:flex-start;margin:0 0 10px}.sound{width:100%;max-width:310px;height:35px;margin-top:12px}.hint{font-size:12px;color:var(--muted);margin-top:15px}
.cards{display:flex;overflow-x:auto;gap:10px;padding:18px 0 8px;scrollbar-color:#43515b #111820}.card{min-width:112px;padding:7px 8px 10px;text-align:left}.card img{display:block;width:96px;height:112px;object-fit:contain;background:#080b0e;border-radius:3px}.card strong{display:block;font-size:13px;margin-top:7px}.card small{color:var(--muted);font-size:11px}footer{color:var(--muted);font-size:12px;border-top:1px solid var(--line);margin-top:20px}dialog{max-width:96vw;background:#10161c;border:1px solid #43515b;border-radius:7px;padding:18px}dialog::backdrop{background:#000c}dialog img{display:block;max-width:90vw;max-height:75vh;object-fit:contain}.dialogbar{display:flex;gap:10px;align-items:center;justify-content:space-between;margin-bottom:15px}.dialogbar strong{margin-right:20px}
@media(max-width:720px){header,main,footer{padding:18px}.brand{font-size:17px;letter-spacing:3px}.tag{display:none}.hero{grid-template-columns:1fr}.stage,.stage img{height:420px;min-height:0}.details{padding:24px}.details h2{font-size:30px}.outline{margin-left:0}h1{font-size:27px}}
</style>
<header><div class="brand">BREACH <span>SHIFT</span></div><span class="tag">10 ZOMBIJA / 4 ORUŽJA</span></header>
<main><div class="eyebrow">Pregled modela · Blender</div><h1>Izaberi sledeći detalj.</h1><p>Ovo su renderi stvarnih 3D modela. Izaberi lik ili oružje, uporedi statistike i otvori njegov Blender izvor za dalji dizajn.</p>
<nav class="tabs" aria-label="Vrsta modela"><button id="zombies" aria-pressed="true">Zombiji</button><button id="weapons" aria-pressed="false">Oružje</button><button class="outline" id="engine">Pogledaj u igri ↗</button></nav>
<section class="hero" aria-label="Izabrani model"><div class="stage"><img id="main-image" alt=""></div><div class="details"><div class="eyebrow" id="design"></div><h2 id="name"></h2><div class="metrics" id="metrics"></div><a class="source" id="blend">Otvori Blender fajl ↗</a><div class="hint">Primer zvuka</div><audio class="sound" id="audio" controls preload="none"></audio><div class="hint">Blender 4.5 LTS · teksture sačuvane u fajlu</div></div></section>
<div class="cards" id="cards" aria-label="Dostupni modeli"></div>
</main><footer>Prva anatomska Blender iteracija. Koncept slike ostaju vizuelni cilj; detaljna skeletna animacija i završna obrada mapa tek slede. <a href="../../docs/blender-workshop.md">Radni tok i izvori</a></footer>
<dialog id="captures"><div class="dialogbar"><strong>Panda3D · stvarni prikaz</strong><button data-capture="zombie-roster.png">Zombiji</button><button data-capture="weapons.png">Oružje</button><button data-capture="gameplay.png">Gameplay</button><button id="close-captures" aria-label="Zatvori pregled">✕</button></div><img id="capture-image" src="zombie-roster.png" alt="Modeli prikazani u igri"></dialog>
<script>
const data=__DATA__;let category='zombies',selected=0;
function choose(index){selected=index;const model=data[category][index];document.getElementById('main-image').src=model.image;document.getElementById('main-image').alt=model.name+' — Blender render';document.getElementById('name').textContent=model.name;document.getElementById('design').textContent=model.design;document.getElementById('metrics').innerHTML=model.metrics.map(m=>'<div class="metric"><b>'+m.value+'</b><span>'+m.label+'</span></div>').join('');document.getElementById('blend').href=model.blend;const sound=document.getElementById('audio');sound.pause();sound.src=model.audio;document.querySelectorAll('.card').forEach((card,i)=>card.setAttribute('aria-pressed',String(i===index)));}
function show(group){category=group;for(const id of ['zombies','weapons'])document.getElementById(id).setAttribute('aria-pressed',String(id===group));const cards=document.getElementById('cards');cards.replaceChildren();data[group].forEach((model,i)=>{const button=document.createElement('button');button.className='card';button.setAttribute('aria-label',model.name);button.innerHTML='<img src="'+model.image+'" alt="" loading="lazy"><strong>'+model.name+'</strong><small>'+model.summary+'</small>';button.onclick=()=>choose(i);cards.append(button)});choose(0)}
document.getElementById('zombies').onclick=()=>show('zombies');document.getElementById('weapons').onclick=()=>show('weapons');document.getElementById('engine').onclick=()=>document.getElementById('captures').showModal();document.getElementById('close-captures').onclick=()=>document.getElementById('captures').close();for(const button of document.querySelectorAll('[data-capture]'))button.onclick=()=>document.getElementById('capture-image').src=button.dataset.capture;show('zombies');
</script></html>'''


def main():
    data = {"zombies": [], "weapons": []}
    for kind in ZOMBIE_ORDER:
        spec = ZOMBIE_SPECS[kind]
        design = json.loads((ROOT / "assets/designs/characters" / (kind.value + ".json")).read_text())
        data["zombies"].append({"name": kind.value.title(), "design": design["name"],
            "image": f"characters/{kind.value}.png", "blend": f"../blender/characters/{kind.value}.blend",
            "audio": "../../breach_shift/data/audio/growl_1.wav", "summary": f"{spec.health} HP",
            "metrics": [{"value": spec.health, "label": "HP"}, {"value": spec.damage, "label": "DAMAGE"},
                        {"value": f"{spec.speed} m/s", "label": "BRZINA"}, {"value": f"{spec.height} m", "label": "VISINA"}]})
    for kind in WEAPON_ORDER:
        spec = WEAPON_SPECS[kind]
        data["weapons"].append({"name": spec.name, "design": "Breach Shift · originalni model",
            "image": f"weapons/{kind.value}.png", "blend": f"../blender/weapons/{kind.value}.blend",
            "audio": f"../../breach_shift/data/audio/{kind.value}.wav", "summary": f"{spec.damage} DMG",
            "metrics": [{"value": spec.damage, "label": "DAMAGE PO HICU"}, {"value": spec.magazine_size, "label": "KAPACITET OKVIRA"},
                        {"value": f"{spec.reload_time}s", "label": "PUNJENJE"}, {"value": spec.pellets, "label": "PROJEKTILA PO HICU"}]})
    path = ROOT / "assets/previews/gallery.html"
    path.write_text(HTML.replace("__DATA__", json.dumps(data, ensure_ascii=False)), encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
