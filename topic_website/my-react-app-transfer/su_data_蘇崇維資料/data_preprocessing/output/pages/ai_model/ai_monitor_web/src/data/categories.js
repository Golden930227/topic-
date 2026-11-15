import { Activity, AlertOctagon, Gauge, Zap } from 'lucide-react'

export const categoryConfig = {
  normal: { label: '正常', english: 'Normal', color: '#1d9b6c', softColor: '#eaf8f2', icon: Activity },
  voltageSag: { label: '電壓驟降', english: 'Voltage Sag', color: '#7657d9', softColor: '#f0ecff', icon: Zap },
  loadSpike: { label: '負載突升', english: 'Load Spike', color: '#e7872c', softColor: '#fff3e6', icon: Gauge },
  severeFault: { label: '嚴重異常', english: 'Severe Fault', color: '#db4d61', softColor: '#ffedf0', icon: AlertOctagon },
}
