let socket = null;

export function connectWebSocket(url, onMessage) {
  socket = new WebSocket(url);

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onMessage(data);
  };

  socket.onerror = (error) => {
    console.error('WebSocket error:', error);
  };

  return socket;
}

export function disconnectWebSocket() {
  if (socket) {
    socket.close();
    socket = null;
  }
}
