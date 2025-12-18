(: 
  q03 – JSON objektumot ad vissza, amely a körözött személyek
  subject kategóriáihoz tartozó darabszámokat tartalmazza.
:)

declare namespace output = "http://www.w3.org/2010/xslt-xquery-serialization";
declare option output:method "json";


let $data := json-doc("../data/wanted.json")

let $persons := $data?*?*

let $all-subjects :=
  for $p in $persons
  for $s in ($p?subjects?*)
  return $s

let $distinct-subjects := distinct-values($all-subjects)

return
map {
  "subjectStatistics" :
    array {
      for $s in $distinct-subjects
      order by $s
      return
        map {
          "subject" : $s,
          "count" :
            count(
              for $p in $persons
              where some $x in ($p?subjects?*) satisfies $x = $s
              return $p
            )
        }
    }
}
