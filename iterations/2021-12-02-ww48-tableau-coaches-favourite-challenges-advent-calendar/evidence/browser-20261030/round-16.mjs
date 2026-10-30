const task=await taskSpace(6); const page=task.page('p1'); const fs=await import('node:fs/promises'); const dir='C:/Users/imgwho/ego/wow-acceptance-20261030-new/';
await page.mouse.move(1100,400,{label:'Inspect ornament selection colors'});
await fs.writeFile(dir+'no-grey.txt',await page.snapshot()); await page.screenshot({path:dir+'no-grey.png'});
