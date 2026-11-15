import { useEffect, useState } from 'react'
import { formatTaipei } from './liveData.js'
import './archived-data.css'

const value = (number, digits=2) => number == null ? '未提供' : Number(number).toFixed(digits)

export default function ArchivedData({ kind, getToken, apiBase='' }) {
  const [state,setState]=useState({records:[],events:[],error:'',loading:true})
  useEffect(()=>{
    let active=true
    let timer
    let controller
    const load=async()=>{
      controller=new AbortController()
      const timeout=setTimeout(()=>controller.abort(),10000)
      try {
        if (!getToken) throw new Error('請先登入')
        const response=await fetch(`${apiBase}/api/${kind}?archive=true`,{headers:{Authorization:`Bearer ${await getToken()}`},credentials:'include',signal:controller.signal})
        if(!response.ok) throw new Error('舊資料暫時無法讀取')
        const data=await response.json()
        if(active)setState({records:data.records || [],events:data.events || [],error:'',loading:false})
      }catch(error){if(active)setState(previous=>({...previous,error:error.message,loading:false}))}
      finally{clearTimeout(timeout);if(active)timer=setTimeout(load,30000)}
    }
    load()
    return()=>{active=false;clearTimeout(timer);controller?.abort()}
  },[kind,getToken,apiBase])
  return <section className="archived-data" aria-label="舊資料">
    <h2>舊資料（超過 10 分鐘）</h2>
    <p>依取樣／判斷時間分類；既有非即時來源及時間未確認的紀錄也保留在此。</p>
    {state.loading && <p>正在讀取舊資料…</p>}
    {state.error && <p role="status">{state.error}</p>}
    {!state.loading && !state.records.length && !state.error && <p>目前沒有舊資料。</p>}
    {!!state.records.length && <>
      <p>最近 {state.records.length} 筆 · 台灣時間</p>
      <div className="archive-table-scroll"><table><thead><tr>
        <th>{kind==='cnn'?'取樣時間':'判斷時間'}</th>
        {kind==='cnn'?<><th>電壓 V</th><th>電流 A</th><th>功率 W</th><th>轉速 rpm</th></>:<><th>判斷結果</th><th>信心度</th></>}
      </tr></thead><tbody>{state.records.map(row=><tr key={row.measurement_uid || row.prediction_uid}>
        <td>{formatTaipei(kind==='cnn'?row.measurement_time:row.prediction_time)}</td>
        {kind==='cnn'?<><td>{value(row.vout2)}</td><td>{value(row.ids)}</td><td>{value(row.load_power_est)}</td><td>{value(row.rpm,0)}</td></>:<><td>{row.final_result || row.predicted_class_zh || '未提供'}</td><td>{row.confidence==null?'未提供':`${(Number(row.confidence)*100).toFixed(1)}%`}</td></>}
      </tr>)}</tbody></table></div>
    </>}
    {kind==='ai' && !!state.events.length && <>
      <h3>舊異常事件</h3><div className="archive-table-scroll"><table><thead><tr><th>發生時間</th><th>異常類型</th><th>狀態</th><th>描述</th></tr></thead>
        <tbody>{state.events.map(row=><tr key={row.event_uid}><td>{formatTaipei(row._time?.occurredAt)}</td><td>{row.class_name_zh || row.class_key || '未提供'}</td><td>已確認</td><td>{row.class_name_zh || '未提供'}</td></tr>)}</tbody>
      </table></div>
    </>}
  </section>
}
