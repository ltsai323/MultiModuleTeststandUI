// you cannot use https
//const socket = io.connect("http://127.0.0.1:5001");
// connect at the same ip and port
const socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

// send request to server
setInterval(() => {
  socket.emit("soctest");
}, 2000 );

// read feedback after request sent
socket.on('soctest_response', (data) => {
  document.getElementById('server-data').innerText = data.data;
});
