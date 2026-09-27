"use client";

import {useEffect,useMemo,useState} from "react";

type Any=Record<string,any>;

const titleMap:Record<string,string>={
  kamandar_market_report:"گزارش بازار",
  kamandar_indices:"شاخص‌ها و breadth",
  kamandar_stocks:"سهام",
  kamandar_funds:"صندوق‌ها",
  kamandar_options:"اختیارها",
  kamandar_baskets:"سبدها",
  kamandar_options_top_put:"Top Put",
  kamandar_services_crawl:"خدمات و صفحات کماندار",
};

function flat(v:any):any[]{
  if(v==null)return[];
  if(Array.isArray(v))return v.flatMap(flat);
  if(typeof v==="object")return Object.values(v).flatMap(flat);
  return[v];
}
function strings(v:any){return flat(v).filter(x=>typeof x==="string") as string[]}
function numbers(v:any){return flat(v).filter(x=>typeof x==="number"&&Number.isFinite(x)) as number[]}
function titleOf(name:string){return titleMap[name.replace(/\.json$/,"")]||name.replace(/^kamandar_/,"").replace(/_/g," ")}
function fmt(n:any){
  if(typeof n!=="number"||!Number.isFinite(n))return String(n??"—");
  return new Intl.NumberFormat("fa-IR",{maximumFractionDigits:2}).format(n);
}
function collectRecords(v:any,out:any[]=[]):any[]{
  if(Array.isArray(v)){for(const x of v)collectRecords(x,out);return out}
  if(v&&typeof v==="object"){
    const keys=Object.keys(v);
    if(keys.some(k=>/date|time|timestamp|symbol|ticker|name|title|value|price|volume|index|change|status|url/i.test(k))) out.push(v);
    for(const x of Object.values(v)) collectRecords(x,out);
  }
  return out;
}
function meaningfulLines(v:any){
  return [...new Set(strings(v)
    .flatMap(s=>s.split(/[\n.!؟]+/))
    .map(s=>s.trim())
    .filter(s=>s.length>18))]
    .filter(s=>/شاخص|هم.?وزن|مثبت|منفی|صف|پول|ورود|خروج|ارزش|حجم|بازده|رشد|افت|معامله|نماد|اختیار|صندوق|بازار|فرابورس|بزرگ|عرضه|تقاضا|سفارش|زمان|تاریخ/i.test(s))
    .slice(0,40);
}
function servicePages(v:any){
  const all=collectRecords(v);
  const seen=new Set<string>();
  return all.filter(x=>{
    const u=x.url||x.final_url||x.link;
    if(!u||typeof u!=="string"||seen.has(u))return false;
    seen.add(u);return true;
  }).slice(0,200);
}

export default function App(){
  const[data,setData]=useState<Any>({});
  const[loading,setLoading]=useState(true);
  const[tab,setTab]=useState("all");

  useEffect(()=>{
    fetch("/api/kamandar",{cache:"no-store"})
      .then(r=>r.json()).then(x=>setData(x.files||{})).finally(()=>setLoading(false));
  },[]);

  const files=Object.keys(data);
  const datasets=files.filter(x=>x.startsWith("kamandar_"));
  const selected=tab==="all"?null:data[tab];

  const overview=useMemo(()=>{
    const all=datasets.flatMap(x=>[data[x]]);
    const ns=numbers(all);
    const text=strings(all).join(" ");
    const pos=(text.match(/مثبت|positive|صف خرید|ورود|رشد|افزایش/gi)||[]).length;
    const neg=(text.match(/منفی|negative|صف فروش|خروج|افت|کاهش/gi)||[]).length;
    const urls=new Set<string>();
    for(const d of all) for(const r of collectRecords(d)){
      const u=r.url||r.final_url||r.link;
      if(typeof u==="string"&&/^https?:/i.test(u))urls.add(u);
    }
    return {ns:ns.length,pos,neg,urls:urls.size};
  },[data,datasets]);

  const important=useMemo(()=>meaningfulLines(selected||data),[selected,data]);
  const pages=useMemo(()=>servicePages(data.kamandar_services_crawl),[data.kamandar_services_crawl]);
  const latest=useMemo(()=>{
    const all=strings(data);
    const dates=all.filter(x=>/202\d[-/]\d\d[-/]\d\d|\d\d\d\d[-/]\d\d[-/]\d\d/.test(x));
    return [...new Set(dates)].slice(-8).reverse();
  },[data]);

  return <main className="wrap" dir="rtl">
    <header className="hero">
      <div>
        <div className="eyebrow">BABIMIND • KAMANDAR INTELLIGENCE</div>
        <h1 className="title">داشبورد کامل داده‌های کماندار</h1>
        <div className="muted">داده خام ریپو Tahlil → استخراج → دسته‌بندی → شواهد قابل ردیابی</div>
      </div>
      <div className="sourceBox">
        <b>{loading?"در حال دریافت…":"اتصال به ریپو برقرار است"}</b>
        <span>{datasets.length} فایل کماندار · {overview.urls} لینک/صفحه · {new Date().toLocaleTimeString("fa-IR")}</span>
      </div>
    </header>

    <section className="grid">
      <div className="card"><div className="muted">سیگنال‌های مثبت</div><div className="metric">{fmt(overview.pos)}</div></div>
      <div className="card"><div className="muted">سیگنال‌های منفی</div><div className="metric">{fmt(overview.neg)}</div></div>
      <div className="card"><div className="muted">مقادیر عددی استخراج‌شده</div><div className="metric">{fmt(overview.ns)}</div></div>
      <div className="card"><div className="muted">داده‌های کماندار در ریپو</div><div className="metric">{fmt(datasets.length)}</div></div>
    </section>

    <nav className="tabs">
      <button className={"tab "+(tab==="all"?"active":"")} onClick={()=>setTab("all")}>نمای کلی</button>
      {datasets.map(x=><button className={"tab "+(tab===x?"active":"")} onClick={()=>setTab(x)} key={x}>{titleOf(x)}</button>)}
    </nav>

    <section className="section">
      <div className="sectionHead"><h2>{tab==="all"?"چه چیزهایی از کماندار در دسترس است؟":titleOf(tab)}</h2><span className="pill">{selected?"داده خام + استخراج": "همه منابع"}</span></div>
      {tab==="all" ? <div className="datasetGrid">
        {datasets.map(x=>{
          const d=data[x]; const rec=collectRecords(d); const ns=numbers(d);
          return <button className="dataset" onClick={()=>setTab(x)} key={x}>
            <b>{titleOf(x)}</b><span>{rec.length.toLocaleString("fa-IR")} رکورد ساختاریافته</span><span>{ns.length.toLocaleString("fa-IR")} مقدار عددی</span>
          </button>
        })}
      </div> : <div className="split">
        <div className="card">
          <h3>اتفاقات و نکات قابل استخراج</h3>
          {important.length?important.map((x,i)=><div className="event" key={i}>{x}</div>):<div className="muted">برای این بخش هنوز متن قابل‌استخراج کافی وجود ندارد.</div>}
        </div>
        <div className="card">
          <h3>تاریخ‌های موجود در داده</h3>
          {latest.length?latest.map(x=><div className="row" key={x}><span>{x}</span><span className="pill">evidence</span></div>):<div className="muted">تاریخ صریح پیدا نشد.</div>}
        </div>
      </div>}
    </section>

    <section className="section">
      <div className="sectionHead"><h2>صفحات و لینک‌های کشف‌شده کماندار</h2><span className="pill">{pages.length.toLocaleString("fa-IR")} مورد</span></div>
      <div className="pageList">
        {pages.length?pages.map((p:any,i)=><div className="pageItem" key={i}>
          <div><b>{p.title||p.name||p.url||"صفحه کماندار"}</b><div className="muted">{p.final_url||p.url||p.link}</div></div>
          <span className="status">{p.status??p.http_status??"—"}</span>
        </div>):<div className="card">فایل crawl هنوز داده صفحه‌ای ندارد یا در ریپو موجود نیست.</div>}
      </div>
    </section>

    <section className="section">
      <div className="sectionHead"><h2>داده خام همین بخش</h2><span className="pill">بدون حذف evidence</span></div>
      <pre className="raw">{JSON.stringify(selected||data,null,2)}</pre>
    </section>

    <footer className="footer">
      کماندار منبع ثانویه است. اعداد حساس بازار باید با TSE/TSETMC و منابع رسمی cross-check شوند. این صفحه داده را از فایل‌های موجود در ریپو Tahlil می‌خواند؛ اگر GitHub Actions فایل جدید commit کند، با deployment/revalidation بعدی در سایت دیده می‌شود.
    </footer>
  </main>;
}
