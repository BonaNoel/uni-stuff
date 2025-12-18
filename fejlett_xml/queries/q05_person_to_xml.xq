(: 
  q05 – Wanted persons XML létrehozása és validálása XSD-vel
:)

import schema namespace wp="http://example.com/wanted"
  at "../schemas/wanted.xsd";

declare namespace output = "http://www.w3.org/2010/xslt-xquery-serialization";
declare option output:method "xml";

(: A lekérdezés többi része ugyanaz :)
let $data := json-doc("../data/wanted.json")
let $persons := $data?*?*

return
<wantedPersons xmlns="http://example.com/wanted">
{
  for $p in $persons
  let $title := if (exists($p?title)) then $p?title else ""
  let $status := if (exists($p?status)) then $p?status else "NA"
  let $subjects := if (exists($p?subjects)) then
      string-join(
        for $s in $p?subjects
        return if ($s instance of xs:string) then $s else ""
      , ", ")
    else ""
  let $url := if (exists($p?url)) then $p?url else "#"
  return
    <wp:wantedPerson>
      <title>{ $title }</title>
      <status>{ $status }</status>
      { if ($subjects != "") then <subjects>{ $subjects }</subjects> else () }
      <url>{ $url }</url>
    </wp:wantedPerson>
}
</wantedPersons>
