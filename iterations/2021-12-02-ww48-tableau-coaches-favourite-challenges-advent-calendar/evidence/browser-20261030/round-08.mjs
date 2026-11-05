const task=await taskSpace(6); const page=task.page('p1');
await page.mouse.click(770,746,{label:'Select year 2019 bar'});
console.log(await page.snapshot({scope:'subtree',root:'@279'}));
