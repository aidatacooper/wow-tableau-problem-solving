const task=await taskSpace(6); const page=task.page('p1'); const fs=await import('node:fs/promises'); const dir='C:/Users/imgwho/ego/wow-acceptance-20261030-new/';
await fs.writeFile(dir+'ww49-domain-before.txt',await page.snapshot());
await page.mouse.click(225,438,{label:'Select binders accessories mark'}); await page.mouse.move(1200,450,{label:'Inspect selected matrix domain'});
console.log((await page.snapshot()).slice(-2200));
