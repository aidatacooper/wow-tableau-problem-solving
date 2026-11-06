const task=await taskSpace(6); const page=task.page('p1'); const fs=await import('node:fs/promises'); const dir='C:/Users/imgwho/ego/wow-acceptance-20261030-new/';
await fs.writeFile(dir+'2019.txt',await page.snapshot()); await page.screenshot({path:dir+'2019.png'});
await page.mouse.click(850,704,{label:'Select 2018 for multiselect'});
await page.keyboard.down('Control');
try {await page.mouse.click(790,789,{label:'Add year 2020 selection'});} finally {await page.keyboard.up('Control');}
console.log(await page.snapshot({scope:'subtree',root:'@279'}));
