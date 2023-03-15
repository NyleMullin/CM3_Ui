
setInterval(function(){
var x = Math.floor((Math.random() * 100) + 1);
document.getElementById("result").setAttribute("style", "width:calc("+x+"% * 0.73)");
},1000);

`use strict`;
function refreshTime() {
  const timeDisplay = document.getElementById("time");
  const dateString = new Date().toLocaleString();
  const formattedString = dateString.replace(", ", " - ");
  timeDisplay.textContent = formattedString;
}
  setInterval(refreshTime, 1000);
