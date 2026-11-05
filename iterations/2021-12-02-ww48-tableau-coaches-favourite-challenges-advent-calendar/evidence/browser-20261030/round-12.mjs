const task=await taskSpace(6); const page=task.page('p1'); const fs=await import('node:fs/promises'); const dir='C:/Users/imgwho/ego/wow-acceptance-20261030-new/';
await fs.writeFile(dir+'multiselect.txt',await page.snapshot()); await page.screenshot({path:dir+'multiselect.png'});
await page.mouse.click(950,746,{label:'Clear year bar selection'});
console.log(await page.snapshot({scope:'subtree',root:'@279'}));
