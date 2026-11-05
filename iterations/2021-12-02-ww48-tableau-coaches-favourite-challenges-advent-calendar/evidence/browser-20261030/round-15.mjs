const task=await taskSpace(6); const page=task.page('p1'); const fs=await import('node:fs/promises'); const dir='C:/Users/imgwho/ego/wow-acceptance-20261030-new/';
await fs.writeFile(dir+'clear.txt',await page.snapshot()); await page.screenshot({path:dir+'clear.png'});
const popup=page.waitForEvent('popup',{timeout:15000});
console.log(await page.mouse.click(245,373,{label:'Open day one challenge'}));
try {const p=await popup; console.log({popup:p.label,url:await p.url()}); await fs.writeFile(dir+'url-action.json',JSON.stringify({url:await p.url(),label:p.label,time:new Date().toISOString()})); await p.screenshot({path:dir+'challenge-popup.png'}); await p.close();}catch(e){console.log(String(e));}
console.log(await task.tabs());
