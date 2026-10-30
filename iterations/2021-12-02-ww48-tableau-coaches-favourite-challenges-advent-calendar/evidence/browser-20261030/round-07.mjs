const task=await taskSpace(6); const page=task.page('p1'); const fs=await import('node:fs/promises'); const dir='C:/Users/imgwho/ego/wow-acceptance-20261030-new/';
await fs.writeFile(dir+'2018.txt',await page.snapshot()); console.log(await page.screenshot({path:dir+'2018.png'}));
