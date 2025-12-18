(: 
  q08 – Publikus JSON nézet a körözött személyekről
  Csak a legfontosabb mezők kerülnek kiírásra
:)

declare namespace output = "http://www.w3.org/2010/xslt-xquery-serialization";
declare option output:method "json";
declare option output:indent "yes";

let $data := json-doc("../data/wanted.json")
let $persons := $data?*?*

return
array {
  for $p in $persons
  return
    map {
      "uid" : $p?uid,
      "title" : $p?title,
      "status" : if (exists($p?status)) then $p?status else "UNKNOWN",
      "publication" : $p?publication,
      "subjects" :
        if (exists($p?subjects))
        then array { for $s in $p?subjects return $s }
        else array {},
      "url" : $p?url
    }
}
