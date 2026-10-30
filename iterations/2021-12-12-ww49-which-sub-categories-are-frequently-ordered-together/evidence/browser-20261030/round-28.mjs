const task=await taskSpace(6); const page=task.page('p1'); const fs=await import('node:fs/promises'); const dir='C:/Users/imgwho/ego/wow-acceptance-20261030-new/';
await page.cdp('Emulation.setDeviceMetricsOverride',{width:1519,height:1150,deviceScaleFactor:1,mobile:false});
await fs.writeFile(dir+'ww49-cleared.txt',await page.snapshot()); await page.screenshot({path:dir+'ww49-cleared.png'});
await page.cdp('Emulation.clearDeviceMetricsOverride',{});
