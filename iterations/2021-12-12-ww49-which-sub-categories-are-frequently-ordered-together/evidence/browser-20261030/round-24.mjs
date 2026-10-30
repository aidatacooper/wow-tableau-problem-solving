const task=await taskSpace(6); const page=task.page('p1'); const fs=await import('node:fs/promises'); const dir='C:/Users/imgwho/ego/wow-acceptance-20261030-new/';
await fs.writeFile(dir+'ww49-chairs.txt',await page.snapshot()); await page.screenshot({path:dir+'ww49-chairs.png'});
await page.mouse.move(1200,450,{label:'Dismiss matrix tooltip'});
help('page.screenshot');
console.log(await page.evaluate(()=>[...document.querySelectorAll('iframe')].map(e=>({src:e.src,rect:e.getBoundingClientRect().toJSON()}))));
