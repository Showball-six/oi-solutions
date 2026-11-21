const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
let core;
try {
  const page = fs.readFileSync('exams/practice.html','utf8');
  const context = {};
  vm.runInNewContext(page.match(/<script id="exam-core">([\s\S]*?)<\/script>/)[1], context);
  core = context.ExamCore;
} catch {}
function getCore(){ assert.ok(core, '答题核心尚未实现'); return core; }
const paper = {id:'test', version:'v1', questions:[
  {uid:'q1',type:'multi_choice',score:4,answer:'BD',gradable:true},
  {uid:'q2',type:'judge',score:2,answer:'False',gradable:true},
  {uid:'q3',type:'fill',score:3,answer:'42',gradable:true},
  {uid:'q4',type:'program',score:25,answer:'',gradable:false},
  {uid:'q5',type:'choice',score:2,answer:'',gradable:false}
]};
test('多选顺序无关但必须完全匹配',()=>{
  const c=getCore(); assert.equal(c.grade(paper,{q1:['D','B']}).score,4);
  assert.equal(c.grade(paper,{q1:['B']}).score,0);
  assert.equal(c.grade(paper,{q1:['A','B','D']}).score,0);
});
test('判断、填空与客观题满分口径',()=>{
  const result=getCore().grade(paper,{q1:['B','D'],q2:'False',q3:' 42 ',q4:'code'});
  assert.equal(result.score,9);assert.equal(result.max,9);assert.equal(result.results.q4,null);
});
test('空答案不被视为正确，未答判错',()=>{
  const result=getCore().grade(paper,{});assert.equal(result.score,0);assert.equal(result.results.q5,null);assert.equal(result.results.q2,false);
});
test('修订版隔离与损坏记录恢复',()=>{
  const c=getCore();assert.equal(c.restore(paper,{version:'old',answers:{q1:['B','D']}}),null);
  assert.equal(c.restore(paper,{version:'v1',answers:'broken'}),null);
  assert.equal(c.restore(paper,{version:'v1',answers:{q2:'False'},deadline:12}).answers.q2,'False');
});
test('截止时间不依赖页面刷新且不显示负数',()=>{
  const c=getCore();assert.equal(c.remaining(90000,30000),60);assert.equal(c.remaining(90000,100000),0);
});
test('旧标签不能撤销另一标签的计时、交卷和重新练习',()=>{
 const c=getCore();assert.equal(typeof c.merge,'function');
 const old={version:'v1',attempt:'a',answers:{q2:'False'},submitted:false,deadline:null};
 const timed={...old,deadline:90000};
 assert.equal(c.merge(paper,old,timed,'q2').deadline,90000);
 const submitted={...timed,submitted:true};
 assert.equal(c.merge(paper,old,submitted,'q2').submitted,true);
 const reset={...old,attempt:'b',answers:{}};
 assert.equal(c.merge(paper,old,reset,'q2').attempt,'b');
});
