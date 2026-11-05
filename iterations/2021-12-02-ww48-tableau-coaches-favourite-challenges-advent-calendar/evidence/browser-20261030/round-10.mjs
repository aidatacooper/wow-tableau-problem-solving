const task=await taskSpace(6); const page=task.page('p1'); const dir='C:/Users/imgwho/ego/wow-acceptance-20261030-new/';
await page.mouse.move(1100,500,{label:'Dismiss bar tooltip'});
console.log(await page.screenshot({path:dir+'multiselect-attempt.png'}));
