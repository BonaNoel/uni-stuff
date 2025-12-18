(: 
  q06 – Körözött személyek státusz szerinti csoportosítása XML formátumban
:)

import schema namespace ws="http://example.com/wanted/status"
  at "../schemas/wanted-by-status.xsd";

declare namespace output = "http://www.w3.org/2010/xslt-xquery-serialization";
declare option output:method "xml";

let $data := json-doc("../data/wanted.json")
let $persons := $data?*?*

return
<wantedByStatus xmlns="http://example.com/wanted/status">
{
  for $p in $persons
  let $status := if (exists($p?status)) then $p?status else "UNKNOWN"
  group by $status
  order by $status
  return
    <ws:status name="{$status}" count="{count($p)}">
    {
      for $person in $p
      let $title := if (exists($person?title)) then $person?title else ""
      let $url := if (exists($person?url)) then $person?url else "#"
      return
        <person>
          <title>{ $title }</title>
          <url>{ $url }</url>
        </person>
    }
    </ws:status>
}
</wantedByStatus>
