import { Activity, AlertOctagon, Gauge, Zap } from 'lucide-react'

export const categoryConfig = {
  normal: { label: '正常', english: 'Normal', color: '#1d9b6c', softColor: '#eaf8f2', icon: Activity },
  voltageSag: { label: '電壓驟降', english: 'Voltage Sag', color: '#7657d9', softColor: '#f0ecff', icon: Zap },
  loadSpike: { label: '負載突升', english: 'Load Spike', color: '#e7872c', softColor: '#fff3e6', icon: Gauge },
  severeFault: { label: '嚴重異常', english: 'Severe Fault', color: '#db4d61', softColor: '#ffedf0', icon: AlertOctagon },
}
export const predictionCycle = [
  {
    result: 'normal',
    displayLabel: '正常',
    confidence: 94.6,
    summary: '目前運行狀態穩定，未偵測到異常',
    probabilities: [
      { type: 'normal', value: 94.6 },
      { type: 'voltageSag', value: 2.1 },
      { type: 'loadSpike', value: 2.5 },
      { type: 'severeFault', value: 0.8 },
    ],
  },
  {
    result: 'loadSpike',
    displayLabel: '有疑慮',
    confidence: 87,
    summary: '偵測結果存在疑慮，請通知工程師',
    probabilities: [
      { type: 'normal', value: 6 },
      { type: 'voltageSag', value: 4 },
      { type: 'loadSpike', value: 87 },
      { type: 'severeFault', value: 3 },
    ],
  },
  {
    result: 'severeFault',
    displayLabel: '維修中',
    confidence: 78,
    summary: '設備目前進入維修處理狀態',
    probabilities: [
      { type: 'normal', value: 8 },
      { type: 'voltageSag', value: 6 },
      { type: 'loadSpike', value: 8 },
      { type: 'severeFault', value: 78 },
    ],
  },
]
export const recentEvents = [
  [1,'2025-06-03','10:45:32','loadSpike','1分32秒','中','medium','已結束','ended','瞬時電流高於近期基準值 18%'],
  [2,'2025-06-03','10:12:18','voltageSag','2分05秒','高','high','已結束','ended','三相電壓短暫低於安全閾值'],
  [3,'2025-06-03','09:47:05','loadSpike','0分48秒','中','medium','已結束','ended','風速變化造成發電負載快速上升'],
  [4,'2025-06-03','08:16:44','voltageSag','0分27秒','低','low','待確認','pending','電壓波動接近模型警戒範圍'],
  [5,'2025-06-03','07:32:19','severeFault','進行中','高','high','進行中','active','偵測到多項指標同步偏離正常區間'],
  [6,'2025-06-03','06:51:03','loadSpike','1分08秒','低','low','已結束','ended','啟動階段出現短暫負載峰值'],
  [7,'2025-06-03','05:23:57','voltageSag','0分41秒','中','medium','已結束','ended','併網電壓短時間下降後恢復'],
  [8,'2025-06-03','03:48:26','loadSpike','1分21秒','中','medium','已結束','ended','發電功率於陣風期間快速變化'],
  [9,'2025-06-03','02:14:11','voltageSag','0分35秒','低','low','待確認','pending','單相電壓出現輕微偏低'],
  [10,'2025-06-02','23:42:09','severeFault','2分18秒','高','high','已結束','ended','保護機制啟動並完成狀態復歸'],
].map(([id,date,time,type,duration,severity,severityKey,status,statusKey,description]) => ({ id,date,time,type,duration,severity,severityKey,status,statusKey,description }))
const historyRow = (id,date,time,result,confidence,normal,voltageSag,loadSpike,severeFault,status='已結束',statusKey='ended') => ({ id,date,time,result,confidence,probabilities:{ normal,voltageSag,loadSpike,severeFault },status,statusKey })
export const predictionHistory = [
  historyRow(1,'2025-06-03','10:58:42','normal',94.6,94.6,2.1,2.5,0.8,'監測中','monitoring'), historyRow(2,'2025-06-03','10:45:32','loadSpike',94.6,2.1,2.5,94.6,0.8),
  historyRow(3,'2025-06-03','10:12:18','voltageSag',92.8,3.2,92.8,2.7,1.3), historyRow(4,'2025-06-03','09:47:05','loadSpike',89.7,5.1,3.4,89.7,1.8),
  historyRow(5,'2025-06-03','09:15:41','normal',97.2,97.2,1.1,1.2,0.5), historyRow(6,'2025-06-03','08:16:44','voltageSag',85.4,7.8,85.4,4.6,2.2,'待確認','pending'),
  historyRow(7,'2025-06-03','07:32:19','severeFault',96.1,0.9,1.2,1.8,96.1,'已處理','ended'), historyRow(8,'2025-06-03','06:51:03','loadSpike',87.9,6.8,2.9,87.9,2.4),
  historyRow(9,'2025-06-03','05:54:30','normal',95.8,95.8,1.7,1.9,0.6), historyRow(10,'2025-06-03','05:23:57','voltageSag',91.3,4.2,91.3,3.1,1.4),
]

export const currentPrediction = predictionCycle[0]

