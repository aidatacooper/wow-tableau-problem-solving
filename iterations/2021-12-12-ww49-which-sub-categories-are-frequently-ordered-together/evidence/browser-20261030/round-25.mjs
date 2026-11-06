const task=await taskSpace(6); const page=task.page('p1');
await page.cdp('Emulation.setDeviceMetricsOverride',{width:1519,height:1150,deviceScaleFactor:1,mobile:false});
console.log(await page.screenshot({path:'C:/Users/imgwho/ego/wow-acceptance-20261030-new/ww49-domain-before.png'}));
