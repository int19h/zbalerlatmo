// Optional.   Show the copy icon when dragging over.  Seems to only work for chrome.
document.body.addEventListener('dragover', function(e) {
    e.stopPropagation();
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
});

// Get file data on drop
document.body.addEventListener('drop', function(e) {
  e.stopPropagation();
  e.preventDefault();
  var files = e.dataTransfer.files; // Array of all files

  for (var i=0, file; file=files[i]; i++) {
    var reader = new FileReader();
    reader.fileName = file.name.split(".")[0];
    reader.onload = function(e2) {
        // finished reading file data.
        var rand = Math.floor(Math.random() * 10000),
            font = e2.target.fileName+'-'+rand,
            css = '@font-face { font-family: "'+font+'"; src: url('+e2.target.result+') }',
            head = document.head || document.getElementsByTagName('head')[0],
            style = document.createElement('style');

        head.appendChild(style);

        style.type = 'text/css';
        if (style.styleSheet){
          // This is required for IE8 and below.
          style.styleSheet.cssText = css;
        } else {
          style.appendChild(document.createTextNode(css));
        }
        console.log("Updating font to "+e2.target.fileName+"-"+rand);
        var option = document.createElement('option');
        option.value = font;
        option.innerHTML = font;
        font_selector.appendChild(option);
        font_selector.value = font;
        history.replaceState(undefined, undefined, "#" + font_selector.value);
        updateFont(font);
    }

    reader.readAsDataURL(file); // start reading the file data.
  }
});