
const { chromium } = require('playwright');
const OUT = 'output/playwright/screenshots/';
(async () => {
  const browser = await chromium.launch({ headless: true, channel: 'msedge' });
  const ctx = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    deviceScaleFactor: 1,
    serviceWorkers: 'block'
  });
  const page = await ctx.newPage();
  const errs = [];
  page.on('pageerror', e => errs.push(e.message));
  page.on('console', m => { if (m.type()==='error' && !m.text().includes('401')) errs.push(m.text()); });

  await page.goto('http://127.0.0.1:5000/', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2500);
  await page.fill('input[placeholder*="账号"]', 'demo');
  await page.fill('input[placeholder*="密码"]', 'demo123');
  await page.click('button:has-text("登")');
  await page.waitForTimeout(7000);

  const shots = [
    ['01_dashboard.png', '首页'],
    ['06_review.png', '复习模式'],
    ['07_weak.png', '薄弱分析'],
    ['11_report.png', '统计报表'],
  ];
  for (const [file, nav] of shots) {
    await page.click('button:has-text("' + nav + '")');
    await page.waitForTimeout(5000);
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(600);
    await page.screenshot({ path: OUT + file, fullPage: true });
    const dim = await page.evaluate(() => document.body.scrollHeight);
    console.log('shot', file, 'contentHeight=' + dim);
  }
  console.log('errors:', JSON.stringify(errs.slice(0, 5)));
  await browser.close();
})().catch(e => { console.error('FAILED:', e && e.message); process.exit(1); });
