const task=await taskSpace(6); const page=task.page('p1'); await page.mouse.move(169,326,{label:'Hover accessories NONE cell'}); console.log(await page.snapshot({scope:'subtree',root:'@420'}));
