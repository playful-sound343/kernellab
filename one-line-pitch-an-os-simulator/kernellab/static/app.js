const experiments = {
  cpu: { label: "CPU scheduling", algorithms: ["fcfs", "sjf", "srtf", "round_robin", "priority"], params: { quantum: 2, processes: [{pid:"P1",arrival:0,burst:7,priority:2},{pid:"P2",arrival:2,burst:4,priority:1},{pid:"P3",arrival:4,burst:1,priority:3}] } },
  memory: { label: "Memory allocation", algorithms: ["first_fit", "best_fit", "worst_fit", "buddy"], params: { blocks:[100,500,200,300,600], requests:[212,417,112,426] }, buddy: { memory_size:1024, requests:[64,120,200,300] } },
  vm: { label: "Virtual memory", algorithms: ["fifo", "lru", "clock", "optimal"], params: { frames:3, references:[1,2,3,4,1,2,5,1,2,3,4,5] } },
  deadlock: { label: "Deadlock", algorithms: ["bankers", "wait_for_dfs"], params: { available:[3,3,2], maximum:[[7,5,3],[3,2,2],[9,0,2],[2,2,2],[4,3,3]], allocation:[[0,1,0],[2,0,0],[3,0,2],[2,1,1],[0,0,2]] }, wait_for_dfs: { graph:{P1:["P2"],P2:["P3"],P3:["P1"]} } },
  sync: { label: "Synchronization", algorithms: ["producer_consumer", "dining_philosophers"], params: { buffer_size:3, operations:["produce","produce","consume","consume","consume"] }, dining_philosophers: { rounds:3, philosophers:5 } }
};
const moduleSelect = document.querySelector('#module'), algorithmSelect = document.querySelector('#algorithm'), paramsField = document.querySelector('#params');
Object.entries(experiments).forEach(([key, value]) => moduleSelect.add(new Option(value.label, key)));
function setParams() { const experiment = experiments[moduleSelect.value]; paramsField.value = JSON.stringify(experiment[algorithmSelect.value] || experiment.params, null, 2); }
function setWorkload() { const experiment = experiments[moduleSelect.value]; algorithmSelect.replaceChildren(...experiment.algorithms.map(a => new Option(a.replaceAll('_',' '), a))); setParams(); }
moduleSelect.addEventListener('change', setWorkload); algorithmSelect.addEventListener('change', setParams); setWorkload();
let chart;
async function refreshHistory() {
  const runs = await (await fetch(`/history?module=${moduleSelect.value}`)).json();
  document.querySelector('#history').innerHTML = runs.length ? `<table><tr><th>Algorithm</th><th>Key metric</th><th>Created</th></tr>${runs.map(r => { const entry = Object.entries(r.metrics)[0] || ['-', '-']; return `<tr><td>${r.algorithm}</td><td>${entry[0]}: ${Number(entry[1]).toFixed(2)}</td><td>${new Date(r.created_at).toLocaleTimeString()}</td></tr>` }).join('')}</table>` : 'No stored runs for this module.';
}
document.querySelector('#run').onclick = async () => {
  let params; try { params = JSON.parse(paramsField.value); } catch { document.querySelector('#output').textContent = 'Workload JSON is invalid.'; return; }
  const workload = { module: moduleSelect.value, algorithm: algorithmSelect.value, params };
  const response = await fetch('/run', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(workload)});
  const data = await response.json(); if (!response.ok) { document.querySelector('#output').textContent = data.detail || 'Experiment failed.'; return; }
  document.querySelector('#output').textContent = JSON.stringify(data.details, null, 2);
  const entries = Object.entries(data.metrics);
  chart?.destroy(); chart = new Chart(document.querySelector('#metrics'), {type:'bar', data:{labels:entries.map(x=>x[0]), datasets:[{label:data.algorithm, data:entries.map(x=>x[1]), backgroundColor:'#65d6ad'}]}, options:{plugins:{legend:{display:false}}}});
  refreshHistory();
};
moduleSelect.addEventListener('change', refreshHistory);
refreshHistory();
