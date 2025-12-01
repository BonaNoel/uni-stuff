(: Ez a lekérdezés beolvas egy FBI JSON forrást (pl. data/fbi_raw_page1.json vagy data/fbi_wanted.json) és XML formátumban adja vissza az összes személyt. A kimenet `persons` gyökérelemet ad, majd validate strict { ... } használatával ellenőrzi az eredményt a hozzá tartozó XSD szerint. :) 

declare option output:method "xml";

(: Beállítás: itt helyi fájlra mutatunk, de ha a processor támogatja, a json-doc URL-t is használhatod. :)
let $json := json-doc('data/fbi_raw_page1.json')
let $items := $json?items?*

let $xml :=
  <persons>{
    for $it in $items return
      <person>
        <uid>{ $it?uid }</uid>
        <name>{ $it?title }</name>
        <nationality>{ $it?nationality }</nationality>
      </person>
  }</persons>

(: A validate használatához schema-aware processzor szükséges (pl. Oxygen + Saxon-EE). Állítsd be, hogy a `schemas/persons.xsd` betöltődjön a projekt schema komponensei közé a futtatáskor. :)
return validate strict { $xml }
