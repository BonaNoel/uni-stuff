xquery version "3.1";


(: 
Ez a lekérdezés egy körözött személy adatait XML formában állítja elő
és XSD alapján validálja az eredményt.
:)

import schema default element namespace "" at "../schemas/wanted_person.xsd";

let $data := json-doc("../data/wanted.json")
let $person := $data(1)(5)

return
validate {
  <wantedPerson>
    <uid>{ $person?uid }</uid>
    <title>{ $person?title }</title>
    <status>{ $person?status }</status>
    <sex>{ $person?sex }</sex>
    <nationality>{ $person?nationality }</nationality>
  </wantedPerson>
}
