# Concept generation prompts

Generated with the built-in `image_gen` tool through the imagegen skill. No CLI/API fallback was used. These images are design proposals; production meshes, rigs and game integration are separate work.

## 1. Original character lineup

Output: [zombies-v1.png](./characters/zombies-v1.png)

```text
Use case: stylized-concept.
Project: BREACH SHIFT, an offline first-person zombie survival game in Panda3D. This is concept art for future game assets, not an existing screenshot.
Art direction: cohesive, production-plausible mid-budget stylized 3D game art, angular mid-poly geometry, restrained hand-painted roughness and surface wear, detailed enough to feel atmospheric but forms simple enough to turn into practical game assets. Adult grounded survival-horror, readable silhouettes, desaturated industrial concrete, worn steel, muted olive cloth. Normal reality uses cool teal-grey light and occasional warm industrial lamps. Breach reality uses violet fissures and purple emissive energy without turning everything purple. No gore, no exposed organs, no excessive blood, no cartoon smiles, no photoreal photographic look, no AAA movie-poster treatment, no watermarks, no third-party game logos. Carefully controlled lighting with visible subjects and traversable spaces.
Asset type: character model design sheet, wide landscape canvas.
Primary request: create a polished 3D character concept sheet showing FIVE DISTINCT ZOMBIE MODELS from this game, left to right WALKER, RUNNER, BRUTE, ARMORED, WARDEN. Each is a complete single full-body character, head and feet visible, separated by breathing room, all viewed from matching three-quarter front angle on a plain dark grey studio floor with faint contact shadows. Use a coherent shared art style and convincing human proportions except the bulky mutants. Readable silhouettes are essential for gameplay. Walker is an infected maintenance worker in torn olive workwear, pallid skin, slow slumped stance. Runner is lean and sinewy in a faded yellow-grey tracksuit, pitched forward with long limbs and dynamic posture. Brute is a much broader muscular infected laborer with heavy asymmetrical shoulders and rust-brown torn work clothing, about a head taller than the Walker. Armored is an infected riot-security guard wearing battered blue-grey protective plates and a damaged visor, mostly human-sized with a broad armored silhouette. Warden is the largest boss, massive humanoid with naturally fused dark angular armor plates, dim violet fractures across shoulders and chest, no weapon, no tentacles, no ornate fantasy crown. Distinguish identities through proportions, posture and costume rather than just color. Place a small clean uppercase title "BREACH SHIFT" and subtitle "CHARACTER CONCEPTS" in a restrained top margin, with one legible model name underneath each figure. Treat the five names as exact labels. No extra captions, stats, charts, or UI. The overall feel should be an actual artist's 3D model proposal that a small indie team could implement.
```

## 2. Character revision: female Runner and greater variety

Output: [zombies-v2-female-runner.png](./characters/zombies-v2-female-runner.png)

Edit target: the original character lineup above.

```text
Use case: precise-object-edit.
Asset type: revised 3D zombie character concept sheet for BREACH SHIFT.
Input image 1 is the EDIT TARGET: the previous five-zombie model lineup. Preserve its polished grounded stylized 3D medium, full-body five-figure composition, dark grey studio background, contact shadows, legible title, lighting quality, and left-to-right labels exactly WALKER, RUNNER, BRUTE, ARMORED, WARDEN. The user likes this overall visual direction.
Primary requested changes: increase distinct facial identities, body proportions, clothing and personality across the five zombie designs, and give ONE zombie type a clearly ADULT FEMALE MODEL. Make RUNNER the female type.
WALKER: older male, visibly gaunt angular elderly face with sparse grey hair beneath his cap, stooped posture, one drooping shoulder, faded olive maintenance uniform, believable infection without gore.
RUNNER: clearly adult female infected athlete, roughly 30 years old, lean muscular athletic build, recognizable adult female face, short uneven dark bob or messy short ponytail, forward hunting stance; distressed charcoal and faded mustard sports jacket, practical full-length track trousers and running shoes, modest practical clothing. Not a pinup or beauty portrait: she is a threatening fast infected enemy with a distinct female identity and readable lean silhouette. Keep her full body visible and separated from the neighboring figures.
BRUTE: broader stocky male laborer, thick neck, heavily muscled squat torso, flattened broad nose, asymmetrical heavy arms, bald or very short buzz-cut head, rust-orange ruined workwear and heavy boots. His face must not look like the Walker's face enlarged.
ARMORED: broad armored riot guard whose identity is mostly obscured by a battered helmet and cracked dark visor, visibly protective blue-grey plates and practical boots. Different head silhouette from the unhelmeted zombies.
WARDEN: tallest mutated humanoid boss with angular naturally fused dark armor plates and restrained violet glowing fractures, elongated stern craggy face with no human hair, distinct anatomy and immense shoulders. Keep original concept recognizable.
Constraints: keep every head, hand and foot inside frame; no overlapping characters; all five names remain correctly spelled; consistent 3D art style and scale; no new sixth character, no new abilities, no large weapons, no blood splatter or exposed organs, no nudity, no extra paragraphs or labels. This is a visual DESIGN PROPOSAL, not a finished rigged 3D asset.
```

## 3. Fortress courtyard — approved visual direction

Output: [01-fortress-courtyard.png](./environments/01-fortress-courtyard.png)

Reference image: [user-supplied fortress](../references/environments/fortress-courtyard-reference.png). The user approved the generated fortress appearance on 2026-11-16. Its assignment to the first campaign map is a proposed implementation choice.

```text
Use case: stylized-concept.
Asset type: photorealistic survival-horror FPS environment art proposal for BREACH SHIFT, landscape image, wide screen-filling composition.
Input image 1 is a REFERENCE IMAGE for atmosphere and architectural motifs only: a snowy nighttime fortress courtyard. The user wants one map to be similar in feel, while the remaining game locations will be grounded realistic horror. Create an ORIGINAL MAP VIEW informed by this reference, not an exact reconstruction.
Primary request: a terrifying yet believable abandoned STONE FORTRESS COURTYARD at night in winter, presented at first-person human eye height about 1.7m as if looking into an explorable game level. A broad snow-covered cobbled courtyard is enclosed by weathered medieval fortress walls. A cylindrical stone tower with a damaged clock or circular window is the principal landmark in the middle distance; a narrow pointed-roof watchtower and steep exterior stairs rise along the left; an elevated stone balustrade and another flight of steps frame the right foreground; a vaulted archway opens into deep darkness toward the back. Distant jagged snowy mountains and clouds obscure parts of the moon. Do not reproduce reference composition exactly: offset the main tower, add a clearly connected lateral stone arcade and a small quarantined service annex integrated into the old masonry.
Style and rendering: HIGHLY REALISTIC GAME ENVIRONMENT, physically based stone and aged wood materials, natural scale, rough mortar, frost in cracks, powdery snow and ice, believable wrought iron, subtle realistic volumetric moonbeams and windblown snow. Emphasize realistic tangible construction, no chunky simplified low-poly forms, no cartoon or painterly rendering.
Lighting and fear: cold desaturated blue moonlight, sparse dim amber window light, one failing utility lamp, drifting low fog and threatening unlit archways. The player can read the central combat space and the staircase treads. Include at most TWO SMALL DISTANT INFECTED HUMAN SILHOUETTES, barely emerging from a far archway, creating dread rather than a crowd. No gore needed. The space should feel abandoned and dangerous, not festive or a fantasy postcard.
Gameplay composition: a broad traversable loop with side routes and practical low stone cover, no huge impassable chasm, no excessive foreground clutter. This is the proposed normal-reality appearance, so retain a mostly realistic environment with no saturated purple flood; at most a tiny faint violet seam behind one remote sealed doorway to hint at Breach.
Constraints: one coherent scene; no split panels, no montage, no HUD, no crosshair, no weapon or foreground hands, no labels, no watermarks, no studio logos. This is a concept proposal rather than a claim about currently implemented game graphics.
```

## 4. Realistic hospital isolation wing

Output: [08-isolation-ward.png](./environments/08-isolation-ward.png)

```text
Use case: stylized-concept.
Asset type: highly realistic survival-horror first-person game environment concept for BREACH SHIFT, LEVEL 8 "ISOLATION WARD". Wide landscape image, one single coherent scene. This is a proposal for future map art, not a current game screenshot.
Primary request: an EXTREMELY EERIE, PHYSICALLY BELIEVABLE ABANDONED HOSPITAL ISOLATION WING AT NIGHT, seen at human first-person eye height about 1.7m, looking from a wide ruined nurses' station hub into several connected wards and corridors. Grounded contemporary medical architecture, realistic proportions, painfully convincing decay and abandonment.
Scene and composition: a scuffed L-shaped nurses' desk with shattered wired-glass partition at the left creates low combat cover; an abandoned wheeled hospital bed with rumpled faded bedding sits off the route on the right; dirty cream-and-pale-sage tile, cracked terrazzo floor with small puddles and realistic reflections, peeling walls, sagging ceiling panels, exposed cables, a partly open observation room, a curtain hanging still in a deep doorway. A T-junction beyond the hub gives two readable escape lanes. The central route is wide and traversable rather than blocked by debris. A partly closed fire door at the far end and a long window into a dark patient ward provide landmarks. There is ONE distant unmistakably adult human-like infected silhouette, partly obscured by hanging translucent ward curtains; no visible mutilation, gore or bodies. Its small scale and uncertain visibility should create strong dread.
Rendering: photorealistic modern horror-game environment art, physically based materials and natural wear, convincing cloth, tarnished steel, aged glass, grime and water. Rich realistic microtexture where visible, but coherent art direction and architecture. No low-poly stylization, no cartoon shapes, no glossy clean sci-fi laboratory.
Lighting: extremely tense and dim yet intentionally readable. A weak cold-green fluorescent fixture over the nurses' station, a tiny distant dull red emergency lamp around a corner, cold moonlight through tall broken windows, drifting dust motes in shafts of light, deep shadow inside adjoining rooms. Use plausible light bounce so nearby floor, cover and doorframes remain visible. No uniformly black image. There may be a VERY SUBTLE thin violet seam around one sealed door as a Breach hint, but the overall scene must feel realistic and grounded, not a purple fantasy room.
Mood: oppressive silence, infection aftermath, isolation, anticipation that something is moving in the corridor. Make it frightening through space, light and uncertainty rather than graphic violence.
Constraints: single environment view, no insets, no panels, no title, no labels, no large readable signage, no HUD or crosshair, no weapon or hands, no watermarks or franchise logos, no extra characters. This should look like an artist's ambitious realistic FPS map target with practical combat spaces.
```