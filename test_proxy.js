const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  
  await page.evaluate(async () => {
      try {
          const res = await fetch('https://corsproxy.io/?https://query2.finance.yahoo.com/v1/finance/search?q=ZOMATO');
          const data = await res.json();
          console.log("SUCCESS:", !!data.quotes);
      } catch(e) {
          console.log("ERROR:", e.message);
      }
  });

  page.on('console', msg => console.log(msg.text()));
  
  await new Promise(r => setTimeout(r, 3000));
  await browser.close();
})();
