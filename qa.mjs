export default async function run(page) {
  await page.waitForTimeout(20000);
  const info = await page.evaluate(() => ({
    catches: document.getElementById('sCatches').textContent,
    status: document.getElementById('status').textContent,
    labelsOnScreen: document.querySelectorAll('.catch').length,
  }));
  await page.screenshot({ path: 'e:\\Project\\WebCrawler\\shot.png' });
  return info;
}
