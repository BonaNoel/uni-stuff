Projekt scaffolding a fejlett XML házi feladathoz

Fájl- és mappastruktúra

- queries/: Az XQuery lekérdezések (.xq) — minden feladat külön fájlban.
- data/: Bemeneti JSON fájlok (példák és letöltött raw fájlok).
- schemas/: XML sémák az XML kimenetek validálásához (.xsd).
- output/: Itt gyűjtheted a futtatott eredményeket.

Első lépések (Oxygen használata)

1) Ha Oxygen-t használsz (ahogy említetted), akkor az Oxygen XQuery szerkesztője és beépített futtatómotorja (Saxon) kényelmes: a szerkesztőben megadhatod a schema fájlokat a projekt beállításaiban, és Saxon-EE esetén működik a `validate strict { ... }` kifejezés.

2) A `queries/01_fetch_fbi_json.xq` példa úgy van megírva, hogy helyi fájlokból (`data/fbi_raw_page1.json`, stb.) gyűjti az `items` tömböt. Könnyen módosítható, hogy közvetlenül az API-ról olvasson (`json-doc('https://api.fbi.gov/wanted/v1/list?page=1')`) ha a futtató környezet engedi.

Futtatás (fish shell példák)

# Lokális JSON letöltése (ha szeretnéd frissíteni a mintát):
mkdir -p data
curl -s "https://api.fbi.gov/wanted/v1/list?page=1" -o data/fbi_raw_page1.json

# XQuery futtatása Saxon (ha van saxon-he.jar a projektben):
java -cp saxon-he.jar net.sf.saxon.Query -q:queries/01_fetch_fbi_json.xq -o:output/fbi_wanted.json

# XML kimenet és validate (Saxon-EE vagy Oxygen schema-aware konfigurációt igényel):
java -cp saxon-ee.jar net.sf.saxon.Query -q:queries/02_json_to_persons_xml.xq -o:output/persons.xml

Megjegyzés a validate használatáról

A `validate strict { ... }` XQuery konstrukcióhoz schema-aware processzorra van szükség. Oxygen + Saxon-EE használata esetén helyezd el a `schemas` mappát a projekt sémái közé (Project > Schema Settings), vagy futtasd a lekérdezést Saxon-EE-vel, amelyhez a `saxon-ee.jar` szükséges. Saxon-HE alapból nem támogat minden schema-aware funkciót.

Következő lépések, amit javaslok:
- Megírom a maradék XQuery sablonokat (összesen 10), vagy először szeretnéd, hogy készítsek néhány konkrét lekérdezést (XML kimenet + validate, JSON kimenet, HTML riport)?
