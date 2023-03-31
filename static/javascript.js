
setInterval(function(){
var x = Math.floor((Math.random() * 100) + 1);
document.getElementById("result").setAttribute("style", "width:calc("+x+"% * 0.73)");
},1000);

`use strict`;
function refreshTime() {
  const timeDisplay = document.getElementById("time");
  const dateString = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
  const formattedString = dateString.replace(", ", " - ");
  timeDisplay.textContent = formattedString;
}
  setInterval(refreshTime, 1000);


let i_drone = 0;
setInterval(function(){
  var drone_list = ['weak', 'low', 'medium', 'strong'];

  // document.getElementById("drone-link-icon").classList.remove("signal-icon", mylist[i]);

  document.getElementById("drone-link-icon").classList.add("signal-icon", drone_list[i_drone]);

  i_drone++;

  if (i_drone === 4){
    i_drone = 0;
  }
},1000);

let i_wifi = 0;
setInterval(function(){
  var wifi_list = ['waveStrength-1', 'waveStrength-2', 'waveStrength-3', 'waveStrength-4'];

  // document.getElementById("drone-link-icon").classList.remove("signal-icon", mylist[i]);

  document.getElementById("wifi-signal-strength").classList.add(wifi_list[i_wifi]);

  i_wifi++;
  
  if (i_wifi === 4){
    i_wifi = 0;
  }
},1000);
