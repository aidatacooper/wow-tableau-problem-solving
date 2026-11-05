const task=await taskSpace(6); const page=task.page('p1'); const fs=await import('node:fs/promises'); const dir='C:/Users/imgwho/ego/wow-acceptance-20261030-new/';
await fs.writeFile(dir+'star.txt',await page.snapshot()); await page.screenshot({path:dir+'star.png'});
console.log(await page.mouse.click(850,704,{label:'Select year 2018 bar'}));
console.log(await page.snapshot({scope:'subtree',root:'@279'}));
