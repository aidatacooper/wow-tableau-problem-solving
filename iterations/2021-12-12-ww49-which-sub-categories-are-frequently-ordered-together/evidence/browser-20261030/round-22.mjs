const task=await taskSpace(6); const page=task.page('p1'); const fs=await import('node:fs/promises'); const dir='C:/Users/imgwho/ego/wow-acceptance-20261030-new/';
await fs.writeFile(dir+'ww49-none.txt',await page.snapshot()); await page.screenshot({path:dir+'ww49-none.png'});
await page.mouse.move(225,438,{label:'Hover binders accessories pair'}); console.log(await page.snapshot({scope:'subtree',root:'@420'}));
