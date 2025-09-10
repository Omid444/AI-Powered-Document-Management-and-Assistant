

console.log("✅ dashboard.js loaded!");

let navLock = false;
let currentNavAbort = null;

function getToken(){ return localStorage.getItem("access_token"); }
function lockNav(){ navLock = true; document.body.style.pointerEvents="none"; }
function unlockNav(){ navLock = false; document.body.style.pointerEvents=""; }

async function fetchWithAuth(url, signal){
  const token = getToken();
  if(!token){ alert("No token found. Please login."); location.href="/"; throw new Error("No token"); }
  const res = await fetch(url, { headers:{Authorization:`Bearer ${token}`}, signal });
  if(res.status===401||res.status===403){ alert("Session expired. Please login again."); localStorage.removeItem("access_token"); location.href="/"; throw new Error("Unauthorized"); }
  if(!res.ok) throw new Error("HTTP "+res.status);
  return res.text();
}
function replaceDocument(html){ document.open(); document.write(html); document.close(); }

async function go(url, pushPath){
  if(navLock) return;
  if(currentNavAbort) currentNavAbort.abort();
  currentNavAbort = new AbortController();
  lockNav();
  try{
    const html = await fetchWithAuth(url, currentNavAbort.signal);
    replaceDocument(html);
    try{ if(pushPath && location.pathname!==pushPath) history.pushState({}, "", pushPath); }catch{}
  } finally { unlockNav(); }
}

window.mylog = function(evt){ evt?.preventDefault?.(); evt?.stopPropagation?.(); go("/account","/account"); };
window.goDashboard = function(evt){ evt?.preventDefault?.(); evt?.stopPropagation?.(); go("/dashboard","/dashboard"); };

document.addEventListener("click",(e)=>{
  const aDash = e.target.closest('a[href="/dashboard"], #dashboard-link');
  if(aDash){ e.preventDefault(); e.stopPropagation(); window.goDashboard(); return; }
  const aHome = e.target.closest('a[href="/account"], #home-link');
  if(aHome){ e.preventDefault(); e.stopPropagation(); window.mylog(); }
}, true);
