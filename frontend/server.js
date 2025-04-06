const express = require('express');
const path = require('path');
const app = express();
const PORT = 8081;

// Serve static files
app.use(express.static(__dirname));

// Handle all routes
app.get('*', (req, res) => {
  // Determine which HTML file to serve based on the URL path
  const url = req.url;
  
  if (url === '/' || url === '/index.html') {
    res.sendFile(path.join(__dirname, 'index.html'));
  } else if (url.endsWith('.html')) {
    res.sendFile(path.join(__dirname, url));
  } else {
    // Default to index.html for unknown routes
    res.sendFile(path.join(__dirname, 'index.html'));
  }
});

app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}/`);
}); 