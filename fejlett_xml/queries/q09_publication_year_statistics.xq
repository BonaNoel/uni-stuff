(: 
  q09 – Körözések száma évenként a publication dátum alapján
:)

declare namespace output = "http://www.w3.org/2010/xslt-xquery-serialization";
declare option output:method "json";
declare option output:indent "yes";

let $data := json-doc("../data/wanted.json")
let $persons := $data?*?*

let $years :=
  for $p in $persons
  where exists($p?publication)
  let $year := xs:integer(substring($p?publication, 1, 4))
  group by $year
  order by $year
  return
    map {
      "year" : $year,
      "count" : count($p)
    }

return
array { $years }
