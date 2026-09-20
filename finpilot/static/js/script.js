
let DATA=null, TX=[], categoryChart=null;

document.querySelectorAll(".nav-item").forEach(btn=>{
  btn.addEventListener("click",()=>{
    document.querySelectorAll(".nav-item").forEach(x=>x.classList.remove("active"));
    document.querySelectorAll(".section").forEach(x=>x.classList.remove("active"));
    btn.classList.add("active");
    const sec=document.getElementById(btn.dataset.section);
    sec.classList.add("active");
    document.getElementById("page-title").textContent=btn.querySelector("span").textContent;
    if(btn.dataset.section==="transactions") renderTransactions();
  });
});

async function loadDashboard(){
  const month=document.getElementById("month").value;
  const r=await fetch("/api/dashboard?month="+month); DATA=await r.json();
  TX=DATA.transactions||[];
  const date=new Date(month+"-01T00:00:00");
  document.getElementById("hero-title").textContent=date.toLocaleString("en-US",{month:"long",year:"numeric"});
  document.getElementById("income").textContent=money(DATA.income);
  document.getElementById("expenses").textContent=money(DATA.expenses);
  document.getElementById("savings").textContent=money(DATA.savings);
  document.getElementById("savingRate").textContent=DATA.savings_rate+"% savings rate";
  const totalBudget=DATA.budgets.reduce((s,x)=>s+x.budget,0), totalSpent=DATA.budgets.reduce((s,x)=>s+x.spent,0);
  document.getElementById("budgetUsed").textContent=(totalBudget?(totalSpent/totalBudget*100):0).toFixed(1)+"%";
  document.getElementById("pulse").textContent=pulse(DATA.savings_rate,DATA.budgets);
  renderChart(); renderInsights(); renderBudgets(); renderChanges(); renderRecurring(); renderUnusual(); renderGoals();
}
function money(v){return "₹"+Number(v||0).toLocaleString("en-IN",{maximumFractionDigits:0})}
function pulse(rate,budgets){let over=budgets.filter(x=>x.percent>100).length;if(rate>=20&&over===0)return"Healthy";if(rate>=10)return"Watch";return"Review"}
function renderChart(){
  const ctx=document.getElementById("categoryChart");
  if(categoryChart)categoryChart.destroy();
  categoryChart=new Chart(ctx,{type:"doughnut",data:{labels:DATA.categories.map(x=>x.category),datasets:[{data:DATA.categories.map(x=>x.amount),borderWidth:0}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"right",labels:{font:{size:10},boxWidth:10}}},cutout:"70%"}});
}
function renderInsights(){document.getElementById("insights").innerHTML=DATA.insights.map(x=>`<div class="insight">${x}</div>`).join("")}
function renderBudgets(){
  const html=DATA.budgets.map(b=>`<div class="bar-row"><div class="bar-top"><span>${b.category}</span><b>${money(b.spent)} / ${money(b.budget)}</b></div><div class="bar-bg"><div class="bar-fill ${b.percent>100?'over':''}" style="width:${Math.min(b.percent,100)}%"></div></div></div>`).join("");
  document.getElementById("budgetHealth").innerHTML=html||'<div class="empty">No budgets configured.</div>';
  document.getElementById("budgetCards").innerHTML=DATA.budgets.map(b=>`<div class="mini-card"><h3>${b.category}</h3><div class="big">${money(b.spent)}</div><div class="muted">${b.percent.toFixed(0)}% used · ${b.remaining>=0?money(b.remaining)+" remaining":money(Math.abs(b.remaining))+" over"}</div></div>`).join("");
}
function renderChanges(){
  document.getElementById("changes").innerHTML=DATA.changes.slice(0,6).map(c=>`<div class="change-row"><span>${c.category}</span><b class="${c.change>0?'up':'down'}">${c.change>0?'+':''}${money(c.change)}</b></div>`).join("")||'<div class="empty">Not enough history.</div>';
}
function renderTransactions(){
  if(!DATA)return;
  const q=(document.getElementById("search")?.value||"").toLowerCase(), type=document.getElementById("typeFilter")?.value||"";
  const rows=TX.filter(x=>(!type||x.type===type)&&(`${x.description} ${x.category}`.toLowerCase().includes(q)));
  document.getElementById("txBody").innerHTML=rows.map(x=>`<tr><td>${x.date}</td><td><b>${x.description}</b></td><td><span class="tag">${x.category}</span></td><td class="${x.type==='income'?'income-tag':'expense-tag'}">${x.type}</td><td><b>${x.type==='income'?'+':'−'}${money(x.amount)}</b></td></tr>`).join("")||'<tr><td colspan="5" class="empty">No transactions found.</td></tr>';
}
function renderRecurring(){
  document.getElementById("recurringGrid").innerHTML=DATA.recurring.map(x=>`<div class="mini-card"><h3>${x.description}</h3><div class="big">${money(x.average)}</div><div class="muted">${x.category} · detected ${x.occurrences} time(s) · last ${x.last_date}</div></div>`).join("")||'<div class="empty">No recurring payments detected.</div>';
}
function renderUnusual(){
  document.getElementById("unusual").innerHTML=DATA.unusual.map(x=>`<div class="change-row"><span><b>${x.description}</b><br><small>${x.date} · ${x.category}</small></span><b class="warning">${money(x.amount)}</b></div>`).join("")||'<div class="empty">No unusually large transactions detected this month.</div>';
}
function renderGoals(){
  document.getElementById("goalsGrid").innerHTML=DATA.goals.map(g=>{
    const pct=Math.min(g.saved/g.target*100,100);
    return `<div class="mini-card"><h3>${g.name}</h3><div class="big">${money(g.saved)} <span class="muted">of ${money(g.target)}</span></div><div class="bar-bg"><div class="bar-fill" style="width:${pct}%"></div></div><p class="muted">${pct.toFixed(1)}% funded · ${money(Math.max(g.target-g.saved,0))} remaining</p><p class="muted">Deadline: ${g.deadline||"Not set"}</p></div>`
  }).join("")||'<div class="empty">No goals yet.</div>';
}
async function uploadCSV(){
  const f=document.getElementById("file").files[0]; if(!f)return;
  const fd=new FormData(); fd.append("file",f);
  const r=await fetch("/api/upload",{method:"POST",body:fd}), d=await r.json();
  toast(d.message||d.error); if(!d.error)loadDashboard();
}
async function saveBudget(){
  const category=document.getElementById("budgetCategory").value.trim(), amount=document.getElementById("budgetAmount").value;
  if(!category||!amount)return toast("Enter a category and amount.");
  const r=await fetch("/api/budgets",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({category,amount})});
  toast((await r.json()).message); loadDashboard();
}
async function saveGoal(){
  const name=document.getElementById("goalName").value.trim(), target=document.getElementById("goalTarget").value;
  if(!name||!target)return toast("Enter a goal name and target.");
  await fetch("/api/goals",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name,target,saved:document.getElementById("goalSaved").value||0,deadline:document.getElementById("goalDeadline").value})});
  toast("Goal created."); loadDashboard();
}
function setQ(q){document.getElementById("question").value=q;askQuestion()}
async function askQuestion(){
  const q=document.getElementById("question").value.trim(); if(!q)return;
  const chat=document.getElementById("chat"); chat.innerHTML+=`<div class="user msg"><b>You</b><p>${escapeHTML(q)}</p></div>`;
  document.getElementById("question").value="";
  const r=await fetch("/api/ask",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({question:q})}), d=await r.json();
  chat.innerHTML+=`<div class="bot msg"><b>FinPilot</b><p>${escapeHTML(d.answer)}</p></div>`; chat.scrollTop=chat.scrollHeight;
}
function escapeHTML(s){return s.replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]))}
async function resetDemo(){await fetch("/api/reset",{method:"POST"});toast("Demo data restored.");loadDashboard()}
function toast(t){const x=document.getElementById("toast");x.textContent=t;x.classList.add("show");setTimeout(()=>x.classList.remove("show"),2600)}
loadDashboard();
