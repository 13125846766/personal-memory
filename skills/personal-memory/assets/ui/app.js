'use strict';
const $ = id => document.getElementById(id);
const token = document.querySelector('meta[name="memory-token"]').content;
const topics = {identity:'个人信息',education:'教育经历',preferences:'偏好习惯',personality:'性格自述',relationships:'情感经历',goals:'目标计划'};
const kinds = {'user-stated':'本人陈述','user-confirmed-interpretation':'本人确认','tentative':'待核实推测'};
let profile='default', view='all', records=[], editing=null, requestVersion=0, busy=false;
function toast(message){ $('toast').textContent=message; $('toast').hidden=false; clearTimeout(toast.timer); toast.timer=setTimeout(()=>$('toast').hidden=true,6500); }
async function api(path, data){
  const response=await fetch('/api/'+path,{method:data?'POST':'GET',headers:{'X-Memory-Token':token,...(data?{'Content-Type':'application/json'}:{})},...(data?{body:JSON.stringify({profile,...data})}:{})});
  const result=await response.json(); if(!response.ok)throw new Error(result.error||'操作失败'); return result;
}
function node(tag, text, cls){const element=document.createElement(tag); if(text!==undefined)element.textContent=text;if(cls)element.className=cls;return element;}
function action(text, fn, cls){const b=node('button',text,cls);b.type='button';b.addEventListener('click',()=>run(fn));return b;}
async function run(fn){if(busy)return;busy=true;try{await fn();}catch(e){toast(e.message);}finally{busy=false;}}
function showText(title,text,hint=''){ $('text-title').textContent=title;$('text-output').value=text;$('text-hint').textContent=hint;$('text-dialog').showModal(); }
function confirmAction(title,message){return new Promise(resolve=>{const dialog=$('confirm-dialog');$('confirm-title').textContent=title;$('confirm-message').textContent=message;dialog.returnValue='cancel';dialog.addEventListener('close',()=>resolve(dialog.returnValue==='yes'),{once:true});dialog.showModal();});}
async function refresh(){
  const serial=++requestVersion;
  const selectedProfile=profile;
  const params=new URLSearchParams({profile:selectedProfile,q:$('search').value,topic:$('topic').value,sensitive:$('sensitive').checked?'1':'0'});
  const [items,stats,profiles]=await Promise.all([api('records?'+params),api('doctor?profile='+encodeURIComponent(selectedProfile)),api('profiles?profile='+encodeURIComponent(selectedProfile))]);
  if(serial!==requestVersion||profile!==selectedProfile)return;
  records=items;$('total').textContent=stats.count;$('confirmed-count').textContent=stats.active;
  // Aggregate counts come from the full profile, including hidden sensitive records.
  $('pending-count').textContent=stats.pending;$('expired-count').textContent=stats.expired;
  $('profile').replaceChildren(...profiles.map(p=>{const option=node('option',p);option.value=p;return option;}));$('profile').value=profile;
  $('legacy').hidden=!stats.old_markdown.length;$('legacy').textContent=stats.old_markdown.length?'发现旧版 Markdown 档案：'+stats.old_markdown.join('、')+'。它们尚未合并；请在聊天中调用 skill 整理迁移。':'';
  render();
}
function render(){
  const selected=records.filter(r=>view==='all'||(view==='expired'?r.expired:r.status===view&&!r.expired));
  $('view-label').textContent={all:'全部记忆',active:'已确认',pending:'待确认',expired:'已过期'}[view];
  $('result-count').textContent=selected.length+' 条可见记录';$('records').replaceChildren();$('empty').hidden=selected.length>0;
  if(!selected.length){$('empty').querySelector('h3').textContent=records.length?'这里暂时没有符合条件的记录':'从一件值得记住的小事开始';}
  for(const record of selected){
    const card=node('article',undefined,'card'),head=node('div',undefined,'card-head');
    head.append(node('span',topics[record.topic],'topic'),node('span',record.expired?'已过期':record.status==='pending'?'待确认':'已确认','status '+record.status));
    card.append(head,node('p',record.statement),node('div','来源：'+record.source,'source'));
    const bottom=node('div',undefined,'card-bottom'),buttons=node('div',undefined,'card-actions');
    bottom.append(node('small',kinds[record.kind]+(record.sensitivity==='sensitive'?' · 敏感':'')+(record.expires?' · 至 '+record.expires:'')));
    if(record.status==='pending'&&record.kind!=='tentative'&&!record.expired)buttons.append(action('确认',async()=>{await api('update',{id:record.id,version:record.version,record:{status:'active'}});await refresh();toast('已确认');}));
    buttons.append(action('编辑',()=>openEditor(record)),action('历史',async()=>{const history=await api('history',{id:record.id});showText('修正历史',history.length?history.map(r=>'版本 '+r.version+' · '+r.updated+'\n'+r.statement+'\n来源：'+r.source).join('\n\n'):'还没有修正记录。','删除此条记忆时，会一并删除这些旧版本。');}),action('删除',async()=>{
      if(!await confirmAction('删除这条记忆？','将删除此条记忆及其修正历史，无法在本工具中撤销。旧聊天、系统备份及你已导出的副本不会一并删除。'))return;
      await api('forget',{id:record.id});await refresh();toast('已删除此条记忆及其修正历史。');
    },'delete'));
    bottom.append(buttons);card.append(bottom);$('records').append(card);
  }
}
function openEditor(record=null){editing=record;$('editor-title').textContent=record?'修正记忆':'添加记忆';for(const field of ['statement','source','expires','key'])$(field).value=record?.[field]||'';$('edit-topic').value=record?.topic||'preferences';$('kind').value=record?.kind||'user-stated';$('status').value=record?.status||'active';$('edit-sensitivity').value=record?.sensitivity||'ordinary';$('editor').showModal();$('statement').focus();}
$('editor-form').addEventListener('submit',event=>{event.preventDefault();run(async()=>{
  const record={topic:$('edit-topic').value,statement:$('statement').value,kind:$('kind').value,source:$('source').value||'本人填写；原始日期未知',expires:$('expires').value,key:$('key').value,status:$('status').value,sensitivity:$('edit-sensitivity').value};
  const result=await api(editing?'update':'add',{record,...(editing?{id:editing.id,version:editing.version}:{})});$('editor').close();await refresh();toast(result.duplicate?'已存在相同记录，没有重复保存。':result.conflict?'发现同一字段的不同记录，已放入待确认。':'已保存到本机。');
});});
document.querySelectorAll('[data-close]').forEach(button=>button.addEventListener('click',()=>$(button.dataset.close).close()));
$('add').addEventListener('click',()=>openEditor());$('empty-add').addEventListener('click',()=>openEditor());
document.querySelectorAll('[data-view]').forEach(button=>button.addEventListener('click',()=>{view=button.dataset.view;document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('active',b===button));render();}));
$('profile').addEventListener('change',()=>{profile=$('profile').value;records=[];render();refresh().catch(e=>toast(e.message));});
$('new-profile').addEventListener('click',()=>{$('profile-name').value='';$('profile-dialog').showModal();});
$('profile-form').addEventListener('submit',event=>{event.preventDefault();profile=$('profile-name').value;$('profile-dialog').close();records=[];render();refresh().catch(e=>toast(e.message));});
let searchTimer;$('search').addEventListener('input',()=>{clearTimeout(searchTimer);searchTimer=setTimeout(()=>refresh().catch(e=>toast(e.message)),200);});
for(const id of ['topic','sensitive'])$(id).addEventListener('change',()=>refresh().catch(e=>toast(e.message)));
$('capsule').addEventListener('click',()=>run(async()=>{const result=await api('capsule',{query:$('search').value,topics:$('topic').value?[$('topic').value]:[],sensitive:$('sensitive').checked,budget:3000});showText('可带走的上下文卡片',result.text,'仅包含已确认、未过期的记忆；敏感记录遵循当前显示开关。'+result.included+' 条已选，'+result.omitted+' 条因长度省略。复制到其他 AI 后，接收方会看到这些内容。');}));
$('copy').addEventListener('click',()=>run(async()=>{try{await navigator.clipboard.writeText($('text-output').value);toast('已复制。');}catch{$('text-output').focus();$('text-output').select();toast('请按 Ctrl+C 或 Cmd+C 复制选中文字。');}}));
$('import').addEventListener('click',()=>$('import-file').click());
$('import-file').addEventListener('change',()=>run(async()=>{const file=$('import-file').files[0];try{if(!file)return;if(file.size>8*1024*1024)throw new Error('文件不能超过 8 MiB。');const payload=JSON.parse(await file.text());if(!await confirmAction('导入到 '+profile+'？','导入的记录会全部进入待确认，确认后才参与上下文调用。不会覆盖现有记录。'))return;const results=await api('import',{payload});await refresh();toast('已导入 '+results.filter(r=>!r.duplicate).length+' 条，跳过 '+results.filter(r=>r.duplicate).length+' 条重复。');}finally{$('import-file').value='';}}));
$('export').addEventListener('click',()=>run(async()=>{if(!await confirmAction('导出此档案？','将下载此档案全部当前记录，包括隐藏的敏感记录和待确认记录。导出是未加密 JSON，不含修正历史。请保存到私人位置，避免云盘和公开仓库。'))return;const result=await api('export',{});const url=URL.createObjectURL(new Blob([JSON.stringify(result,null,2)],{type:'application/json'}));const anchor=node('a');anchor.href=url;anchor.download='personal-memory-'+profile+'.json';anchor.click();setTimeout(()=>URL.revokeObjectURL(url),1000);toast('已导出，请妥善保管这个明文副本。');}));
$('health').addEventListener('click',()=>run(async()=>showText('档案检查',JSON.stringify(await api('doctor?profile='+encodeURIComponent(profile)),null,2),'过期内容不会被上下文卡片选中；删除导出副本需另行处理。')));
refresh().catch(e=>toast('连接失败：'+e.message));
