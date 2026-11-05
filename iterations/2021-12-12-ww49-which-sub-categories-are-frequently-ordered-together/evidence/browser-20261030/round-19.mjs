const task=await taskSpace(6); const page=task.page('p1'); await page.click('@403',{label:'Open frequency matrix dashboard'}); console.log(await page.snapshot());
