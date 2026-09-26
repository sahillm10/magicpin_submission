const localtunnel = require('localtunnel');

(async () => {
  try {
    const tunnel = await localtunnel({ port: 8080 });
    console.log('PUBLIC_URL:' + tunnel.url);
    tunnel.on('close', () => {
      console.log('tunnel closed');
    });
    tunnel.on('error', (err) => {
      console.error('tunnel error:', err);
    });
  } catch (err) {
    console.error('Failed to start tunnel:', err);
  }
})();
