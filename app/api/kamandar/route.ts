import {NextResponse} from "next/server";

const repoApi="https://api.github.com/repos/babakbadel/Tahlil/contents/data/raw";
const rawBase="https://raw.githubusercontent.com/babakbadel/Tahlil/main/data/raw/";

export async function GET(){
  try{
    const list=await fetch(repoApi,{headers:{"Accept":"application/vnd.github+json","User-Agent":"Tahlil-Kamandar-Dashboard"},cache:"no-store"});
    if(!list.ok) return NextResponse.json({status:"error",http_status:list.status,files:{}},{status:200});
    const entries=await list.json();
    const names=entries
      .filter((x:any)=>x.type==="file" && /^kamandar_.*\.json$/i.test(x.name))
      .map((x:any)=>x.name);
    const pairs=await Promise.all(names.map(async(name:string)=>{
      try{
        const r=await fetch(rawBase+name,{cache:"no-store"});
        return [name,r.ok?await r.json():{status:"missing",http_status:r.status}] as const;
      }catch(e){
        return [name,{status:"error",error:String(e)}] as const;
      }
    }));
    return NextResponse.json(
      {status:"ok",fetched_at:new Date().toISOString(),files:Object.fromEntries(pairs)},
      {headers:{"Cache-Control":"no-store"}}
    );
  }catch(e){
    return NextResponse.json({status:"error",error:String(e),files:{}},{status:200});
  }
}
