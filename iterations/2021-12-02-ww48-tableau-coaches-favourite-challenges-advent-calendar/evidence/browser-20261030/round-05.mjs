const task=await taskSpace(6); const page=task.page('p1'); const fs=await import('node:fs/promises');
await fs.writeFile('C:/Users/imgwho/ego/wow-acceptance-20261030-new/day24.txt',await page.snapshot());
await page.screenshot({path:'C:/Users/imgwho/ego/wow-acceptance-20261030-new/day24.png'});
await page.mouse.move(326,260,{label:'Hover Christmas star'});
console.log(await page.snapshot({scope:'subtree',root:'@279'}));
