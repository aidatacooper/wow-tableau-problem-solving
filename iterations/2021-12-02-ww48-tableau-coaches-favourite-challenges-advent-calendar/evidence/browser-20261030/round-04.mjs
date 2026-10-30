const task=await taskSpace(6); const page=task.page('p1');
console.log(await page.mouse.move(571,761,{label:'Hover day twenty four'}));
console.log(await page.snapshot({scope:'subtree',root:'@279'}));
