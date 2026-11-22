import assert from 'node:assert/strict'
import {test} from 'node:test'
import {readdir,readFile} from 'node:fs/promises'
import path from 'node:path'
import {pathToFileURL,fileURLToPath} from 'node:url'
import {createRequire} from 'node:module'
import {transformWithOxc} from 'vite'
import {createElement} from 'react'
import {renderToStaticMarkup} from 'react-dom/server'
const require=createRequire(import.meta.url)
const root=fileURLToPath(new URL('..',import.meta.url))
const dir=(await readdir(root,{withFileTypes:true})).find(x=>x.isDirectory()&&x.name.startsWith('su_data_')).name
const filename=path.join(root,dir,'data_preprocessing/output/pages/cnn_monitor/cnn_monitor_web/src/components/RecentMeasurementsTable.jsx')
const {code}=await transformWithOxc(await readFile(filename,'utf8'),filename,{jsx:{runtime:'automatic'}})
const runtime=pathToFileURL(require.resolve('react/jsx-runtime')).href
const moduleCode=code.replaceAll('"react/jsx-runtime"',JSON.stringify(runtime)).replaceAll("'react/jsx-runtime'",JSON.stringify(runtime))
const {default:Table}=await import('data:text/javascript;base64,'+Buffer.from(moduleCode).toString('base64'))
for(const count of [0,23,50,80]) test(`table and badge show ${Math.min(count,50)} of ${count} available rows`,()=>{
 const measurements=Array.from({length:count},(_,i)=>({id:String(i),time:`TIME_${i}`}))
 const html=renderToStaticMarkup(createElement(Table,{measurements}))
 const body=html.match(/<tbody>([\s\S]*?)<\/tbody>/)[1]
 assert.equal((body.match(/<tr(?:\s|>)/g)||[]).length,Math.min(count,50))
 assert.ok(html.includes(`monitor-record-count">${Math.min(count,50)} `))
 assert.ok(html.includes('最近 50 筆直流發電機量測紀錄'))
 if(count) {
  const times=[...body.matchAll(/<td>TIME_(\d+)<\/td>/g)].map(x=>Number(x[1]))
  assert.equal(times[0],count-1)
  assert.equal(times.at(-1),Math.max(0,count-50))
  assert.equal(measurements[0].id,'0')
 }
})
