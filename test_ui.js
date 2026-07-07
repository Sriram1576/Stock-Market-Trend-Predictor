const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR:', err.message));
  page.on('requestfailed', req => console.log('REQUEST FAILED:', req.url()));

  await page.goto('http://localhost:8000/', { waitUntil: 'networkidle0' });
  
  // Wait a bit to let initial load finish
  await new Promise(r => setTimeout(r, 2000));
  
  await browser.close();
})();
