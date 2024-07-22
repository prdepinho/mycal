
console.log('loop loaded');

setInterval(function() {
  console.log('loop');
  postMessage();
}, 1000);
