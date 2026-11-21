const fs=require('node:fs'),vm=require('node:vm');
const files=['index.html','exams.html','exams/practice.html','memos.html','memos/detail.html','favorite.html','tools.html','templates.html'];
let count=0;
for(const file of files){
 const text=fs.readFileSync(file,'utf8');
 for(const match of text.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)){
  if(/\bsrc=|application\/json/.test(match[1]))continue;
  new vm.Script(match[2],{filename:file});count++;
 }
}
new vm.Script(fs.readFileSync('assets/app.js','utf8'),{filename:'assets/app.js'});
console.log(`Syntax OK: ${count+1} scripts in ${files.length} pages`);
