(: 
  q04 – HTML táblázat a körözött személyekből
  oszlopok: Név, Státusz, Kategória, Link
:)

declare namespace output = "http://www.w3.org/2010/xslt-xquery-serialization";
declare option output:method "html";

let $data := json-doc("../data/wanted.json")
let $persons := $data?*?*

return
<html>
  <head>
    <title>FBI Wanted Persons</title>
    <style><![CDATA[
      table { border-collapse: collapse; width: 100%; }
      th, td { border: 1px solid black; padding: 5px; text-align: left; }
      th { background-color: #f2f2f2; }
    ]]></style>
  </head>
  <body>
    <h1>FBI Wanted Persons List</h1>
    <table>
      <thead>
        <tr>
          <th>Név</th>
          <th>Státusz</th>
          <th>Kategória</th>
          <th>Link</th>
        </tr>
      </thead>
      <tbody>
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
            <tr>
              <td>{ $title }</td>
              <td>{ $status }</td>
              <td>{ $subjects }</td>
              <td><a href="{ $url }" target="_blank">Link</a></td>
            </tr>
        }
      </tbody>
    </table>
  </body>
</html>
