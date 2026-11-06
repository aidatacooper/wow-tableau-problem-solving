const task=await taskSpace(6); const page=task.page('p1');
await page.goto('https://10ax.online.tableau.com/#/site/cooperwh/workbooks/3098104');
console.log(await page.snapshot());
