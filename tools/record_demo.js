const path = require('path');

const corePath = process.env.PW_CORE;
if (!corePath) {
  throw new Error('缺少 PW_CORE 环境变量');
}
const { chromium } = require(corePath);

(async () => {
  const browser = await chromium.launch({ headless: true, channel: 'msedge' });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    recordVideo: {
      dir: path.resolve('output/playwright/video'),
      size: { width: 1440, height: 900 }
    }
  });
  const page = await context.newPage();

  await page.goto('http://localhost:5000/');
  await page.waitForTimeout(1000);
  await page.getByRole('textbox', { name: '账号（英文或数字）' }).fill('demo');
  await page.getByRole('textbox', { name: '密码（英文或数字）' }).fill('demo123');
  await page.getByRole('button', { name: '登 录' }).click();
  await page.waitForTimeout(1800);

  await page.getByRole('button', { name: '错题录入' }).click();
  await page.waitForTimeout(1300);
  await page.getByRole('button', { name: '错题库' }).click();
  await page.waitForTimeout(1300);
  await page.getByRole('button', { name: /复习模式/ }).click();
  await page.waitForTimeout(1500);
  await page.getByRole('button', { name: '薄弱分析' }).click();
  await page.waitForTimeout(2200);
  await page.getByRole('button', { name: '知识图谱' }).click();
  await page.waitForTimeout(1600);
  await page.getByRole('button', { name: '树图' }).click();
  await page.waitForTimeout(1300);
  await page.getByRole('button', { name: '旭日图' }).click();
  await page.waitForTimeout(1300);
  await page.getByRole('button', { name: '分层导图' }).click();
  await page.waitForTimeout(1200);
  await page.getByRole('button', { name: '统计报表' }).click();
  await page.waitForTimeout(1600);
  await page.getByRole('button', { name: '学科设置' }).click();
  await page.waitForTimeout(1300);
  await page.getByRole('button', { name: '账号设置' }).click();
  await page.waitForTimeout(1300);
  await page.getByRole('button', { name: '关闭' }).last().click();
  await page.getByRole('button', { name: '模型与 OCR 配置' }).click();
  await page.waitForTimeout(1300);
  await page.getByRole('button', { name: '关闭' }).last().click();
  await page.getByRole('button', { name: '首页' }).click();
  await page.waitForTimeout(1800);

  const video = page.video();
  await context.close();
  await browser.close();
  if (video) {
    console.log('视频保存路径:', await video.path());
  }
})();
