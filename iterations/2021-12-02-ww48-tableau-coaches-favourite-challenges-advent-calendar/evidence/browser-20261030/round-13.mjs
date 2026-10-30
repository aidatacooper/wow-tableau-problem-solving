const task=await taskSpace(6); const page=task.page('p1');
await page.keyboard.press('Escape'); await page.mouse.move(1100,400,{label:'Dismiss selection tooltip'});
console.log(await page.screenshot({path:'C:/Users/imgwho/ego/wow-acceptance-20261030-new/pre-clear.png'}));
