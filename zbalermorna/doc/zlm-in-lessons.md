# Zbalermorna in lessons

Preview:

![Example](img/zlm-in-lessons-ex.png)

You can easily translate all of the Lojban in [la gleki's The Crash Course](https://mw.lojban.org/papri/The_Crash_Course_(a_draft)) with [this extension](https://chrome.google.com/webstore/detail/custom-javascript-for-web/ddbjnfjiigjmcpcpkmhogomapikjbjdk) and this javascript:

```js
document.querySelectorAll("body")[0].innerHTML += 
  "<style>" +
  "  @import url(//jackhumbert.github.io/zbalermorna/assets/css/fonts.css);" +
  "  .cjs-zlm {" +
  "    font-weight: 400!important;" + 
  "    font-family: 'crisa';" + 
  "    font-size: 24px;" +
  "  }" +
  "</style>";

function formatUnicode (point) {
  return String.fromCodePoint(point);
}

const UNICODE_START = 0xED80;
const lerfu_index = "ptkflscmx.' 1234bdgvrzjn`-,~    aeiouy          AEIOUY";

function latinToZbalermornaUnicode(c) {
  if (c.codePointAt(0) >= 0xED80) {
    return c;
  }
  if (c == " ")
    return " ";
  if (c == "h")
    c = "'";
  if (lerfu_index.indexOf(c) >= 0)
    return formatUnicode(UNICODE_START + lerfu_index.indexOf(c));
  else if (lerfu_index.indexOf(c.toLowerCase()) >= 0)
    return formatUnicode(UNICODE_START + lerfu_index.indexOf(c.toLowerCase()));
  if (c == "\n")
    return "\n";
  if (c == "\t")
    return "\t";
  return "";
}

function zlmArray(s) {
  var zlm = "", latin = "", tag = false;
  for (const c of s) {
    if (c == "<")
      tag = true;
    
    if (tag) {
     zlm += c; 
    } else {
      zlm += latinToZbalermornaUnicode(c);
      latin += c;
    }
    
    if (c == ">")
      tag = false;
  }
  return {
    "latin": latin,
    "zlm": zlm,
  };
}

document.querySelectorAll("b").forEach(function(b) {
  var t = zlmArray(b.innerHTML);
  b.innerHTML = "<span title=\"" + t.latin + "\" class='cjs-zlm'>" + t.zlm + "</span>";
});
```