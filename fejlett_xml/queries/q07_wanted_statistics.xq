(: 
  q07 – Wanted persons statisztikák XML formátumban
:)

import schema namespace ws="http://example.com/wanted/statistics"
  at "../schemas/wanted-statistics.xsd";

declare namespace output = "http://www.w3.org/2010/xslt-xquery-serialization";
declare option output:method "xml";

let $data := json-doc("../data/wanted.json")
let $persons := $data?*?*

let $total := count($persons)

let $statuses :=
  for $p in $persons
  let $s := if (exists($p?status)) then $p?status else "UNKNOWN"
  group by $s
  order by $s
  return
    <ws:status name="{$s}" count="{count($p)}"/>

let $distinct-status-count := count(distinct-values(
  for $p in $persons
  return if (exists($p?status)) then $p?status else "UNKNOWN"
))

let $rewarded :=
  count(
    for $p in $persons
    where exists($p?reward_text) and normalize-space($p?reward_text) != ""
    return $p
  )

let $seeking-info :=
  count(
    for $p in $persons
    where exists($p?subjects)
      and (some $s in $p?subjects satisfies $s = "Seeking Information")
    return $p
  )

return
<wantedStatistics xmlns="http://example.com/wanted/statistics">
  <totalPersons>{ $total }</totalPersons>
  <distinctStatuses>{ $distinct-status-count }</distinctStatuses>
  <rewardedPersons>{ $rewarded }</rewardedPersons>
  <seekingInformationPersons>{ $seeking-info }</seekingInformationPersons>

  <statusBreakdown>
    { $statuses }
  </statusBreakdown>
</wantedStatistics>
