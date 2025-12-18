(: 
  q10 – TOP 5 subject a körözési listában előfordulás szerint
:)

declare namespace output = "http://www.w3.org/2010/xslt-xquery-serialization";
declare option output:method "json";
declare option output:indent "yes";

let $data := json-doc("../data/wanted.json")
let $persons := $data?*?*

let $subjects :=
  for $p in $persons
  where exists($p?subjects)
  for $s in $p?subjects
  group by $s
  let $count := count($p)
  order by $count descending
  return
    map {
      "subject" : $s,
      "count" : $count
    }

return
array {
  subsequence($subjects, 1, 5)
}
