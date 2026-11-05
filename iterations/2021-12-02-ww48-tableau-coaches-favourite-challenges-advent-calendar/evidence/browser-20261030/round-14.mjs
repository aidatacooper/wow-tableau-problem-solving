const task=await taskSpace(6); const page=task.page('p1');
await page.mouse.click(950,746,{label:'Clear selected year marks'});
console.log(await page.snapshot({scope:'subtree',root:'@279'}));
