xquery version "3.1";

(: 
Ez a lekérdezés letölti az FBI körözési lista adatait az API-ból,
és egyetlen JSON tömbbe egyesíti az összes körözött személyt. data/wanted.json
:)


declare namespace output = "http://www.w3.org/2010/xslt-xquery-serialization";
declare namespace map = "http://www.w3.org/2005/xpath-functions/map";
declare namespace array = "http://www.w3.org/2005/xpath-functions/array";

declare option output:method "json";
declare option output:indent "yes";
declare option output:omit-xml-declaration "yes";

declare function local:fetch-page($page as xs:integer) {
  let $url :=
    concat("https://api.fbi.gov/wanted/v1/list?page=", $page)
  let $json := json-doc($url)
  return $json?items
};

let $pages := 1 to 5

let $all-items :=
  for $p in $pages
  let $items := local:fetch-page($p)
  for $item in $items
  return $item

return
array {
  for $item in $all-items
  return $item
}

