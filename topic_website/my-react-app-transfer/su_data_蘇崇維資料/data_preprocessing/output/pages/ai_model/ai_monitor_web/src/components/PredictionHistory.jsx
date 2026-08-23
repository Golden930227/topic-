import { BrainCircuit } from 'lucide-react'
import SectionHeader from './SectionHeader'

export default function PredictionHistory({ history, categories }) {
  const visibleHistory = history.slice(0, 10)
  return (
    <section className="panel">
      <SectionHeader icon={BrainCircuit} title="近10筆歷史AI結果" subtitle="模型分類判斷與各類別機率紀錄" action={<span className="record-count">最近更新 {history[0].time}</span>} />
      <div className="table-scroll"><table className="history-table"><thead><tr><th>判斷時間</th><th>AI 判斷結果</th><th>Confidence</th><th>正常</th><th>電壓驟降</th><th>負載突升</th><th>嚴重異常</th><th>狀態</th></tr></thead><tbody>
        {visibleHistory.map((record) => { const category = categories[record.result]; const Icon = category.icon; const maxValue = Math.max(...Object.values(record.probabilities)); return <tr key={record.id}><td className="date-cell"><strong>{record.date}</strong><span>{record.time}</span></td><td><span className="type-label" style={{ '--category': category.color, '--category-bg': category.softColor }}><Icon size={16} />{category.label}</span></td><td><strong className="confidence-number">{record.confidence.toFixed(1)}%</strong></td>{Object.entries(record.probabilities).map(([type, value]) => <td key={type}><span className={value === maxValue ? 'probability-peak' : 'probability-muted'} style={value === maxValue ? { '--category': categories[type].color, '--category-bg': categories[type].softColor } : undefined}>{value.toFixed(1)}%</span></td>)}<td><span className={`pill status-${record.statusKey}`}><i />{record.status}</span></td></tr> })}
      </tbody></table></div>
    </section>
  )
}
