(: Ez a lekérdezés előállít egy JSON tömböt, amely minden letöltött lap `items` mezőjéből összegyűjti a körözöttek objektumait. A kimenet JSON formátumú. :) 
(: Szerkeszthető: módosítsd a $pages értékét a letöltött oldalak számához. Ha Oxygen + Saxon-EE-t használsz, a `json-doc()` URL-ről is működhet; itt alapértelmezetten a helyi `data/` fájlokat használjuk. :)
xquery version "3.1";

declare option output:method "json";

(: --- Konfiguráció: hány lapot dolgozunk fel (állítsd be) --- :)
let $pages := 1 to 3

(: Összegyűjtjük az összes 'items' objektumot a megadott oldalakból. A JSON-forrás fájlok nevei: data/fbi_raw_page1.json, data/fbi_raw_page2.json, ... :) 
let $allItems := for $p in $pages
                 let $path := concat('data/fbi_raw_page', $p, '.json')
                 let $doc := try { json-doc($path) } catch * { () }
                 return $doc?items?*

return array { for $it in $allItems return $it }
