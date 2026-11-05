const task=await taskSpace(6); const page=task.page('p1');
await page.keyboard.down('Control'); try{await page.mouse.click(790,789,{label:'Control select 2020 bar'});}finally{await page.keyboard.up('Control');}
await page.mouse.move(1100,500,{label:'Move away from selection'});
console.log(await page.snapshot({scope:'subtree',root:'@279'}));
