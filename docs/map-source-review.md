# ZombieModding: bezbednost i prenos mapa

Provera javnih stranica: **16. novembar 2026.** Paketi nisu preuzeti,
raspakovani, skenirani antivirusom ili pokrenuti. Ovo nije potvrda da je
neka datoteka bezbedna. Fal.ai nije korišćen.

## Zaključak

ZombieModding ima upotrebljive vizuelne reference, ali proverene objave nisu
biblioteka mapa spremnih za Panda3D. Ne preporučujemo njihove instalere kao
izvor za zamenu deset Breach Shift mapa. Za prenos su potrebni izvorna
geometrija, teksture i dozvola za distribuciju u samostalnoj igri.

## Šta je provereno

| Izvor | Nalaz | Značenje za projekat |
| --- | --- | --- |
| [Zvanični vodič](https://zombiemodding.com/index.php?topic=13227.0), odeljci 2.1–2.3 | Opisuje modove za Call of Duty: World at War, instalere i izuzetak od prethodne moderacije za određene autore. Stariji savet uključuje isključivanje SmartScreen zaštite. | Popularnost sajta ne potvrđuje sadržaj pojedinačnog paketa. Zaštitu računara ne isključujemo. |
| [Lab 7734, originalna objava iz 2018.](https://zombiemodding.com/index.php?topic=21395.0) | Navodi T4M, spoljne servise za preuzimanje, instalaciju u EXE formatu i komponente iz drugih igara. | Nije potvrđen samostalan izvorni paket ni licenca za našu igru. Ovo nije provera verzije **Revised** iz 2026. sa korisnikove slike. |
| [Zombie Revery](https://zombiemodding.com/index.php?topic=21761.0) | Autor opisuje napuštenu viktorijansku železničku stanicu, sopstvene modele i muziku iz Medal of Honor: Allied Assault. | Zanimljiv kandidat za upit o originalnoj arhitekturi. Muziku i ostale tuđe komponente ne podrazumevamo kao dozvoljene za prenos. |

Na pregledanim objavama nije pronađena izričita dozvola za distribuciju tih
mapa u Panda3D igri. Besplatno preuzimanje i navođenje autora sami po sebi
ne utvrđuju takvu dozvolu. Autor može odobriti samo prava kojima raspolaže.
Deo stranica za preuzimanje vratio je HTTP 403; zaštita sajta nije zaobilažena.

## Kada bi prenos bio moguć

Potreban je konkretan izvorni paket, npr. FBX/OBJ/glTF ili Blender scena,
sa svim potrebnim teksturama i uslovima korišćenja. Sama CoD instalacija ne
sadrži nužno takav izvoz. Ako dobijemo izvorne Radiant mape, potrebno je
posebno utvrditi dozvoljen i pouzdan način konverzije; ne obećavamo direktan
uvoz. CoD skripte, T4M i mod instaleri nisu deo Panda3D integracije.

Prvo se proverava poreklo, tačna verzija i licenca jedne mape. Zatim se
ispituje paket bez izvršavanja: spisak datoteka, SHA-256, antivirusna provera,
putanje u arhivi, preveliko raspakivanje, skripte i spoljne reference. Sumnjivi
paketi se odbijaju. Nema administratorskih instalacija, otvaranja portova ni
isključivanja Defender/SmartScreen zaštite. Privatne datoteke i ključevi se
ne šalju servisima za analizu.

Odobrena geometrija zatim ide u Blender sa onemogućenim automatskim
izvršavanjem skripti. Proveravaju se razmera, +Y napred, +Z gore, UV mape,
ugrađene teksture, privatne putanje i poligoni, pa se izvozi GLB. Čak i GLB
zahteva proveru pre uvoza; format sam po sebi nije garancija bezbednosti.

Za prvu probnu mapu moramo uskladiti vidljivu geometriju sa sudarima,
početnom pozicijom, izlazom, jezgrom i obema realnostima. Trenutna navigacija
zombija je ravanska, pa stepenice i više spratova zahtevaju dodatni rad.
Posle provere izgleda, kretanja i performansi sledi pojedinačna zamena ostalih
devet mapa. Pre izbora i provere izvora postojeće mape ostaju funkcionalne.

## Praktičan sledeći izbor

**Zombie Revery** je konkretan kandidat za razgovor sa autorom o izvozu
njegove originalne stanične arhitekture i tekstura, bez tuđe muzike i CoD
komponenti. Takav izvoz i dozvola još nisu dobijeni. Autor nije kontaktiran.
Ako izvor nije dostupan, biramo zaseban environment paket sa jasnom licencom
za samostalnu igru; ne pokušavamo da zamenu svih deset mapa izvedemo iz EXE
instalacije.
