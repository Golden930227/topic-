import { AlertTriangle, Clock3 } from 'lucide-react'
import SectionHeader from './SectionHeader'

export default function RecentEvents({ events, categories }) {
  const visibleEvents = events.slice(0, 10)
  return (
    <section className="panel">
      <SectionHeader icon={AlertTriangle} title="近10筆異常事件" subtitle="近期偵測到的設備狀態變化" action={<span className="record-count">共 {visibleEvents.length} 筆</span>} />
      <div className="table-scroll"><table><thead><tr><th>發生時間</th><th>異常類型</th><th>持續時間</th><th>嚴重程度</th><th>狀態</th><th>描述</th></tr></thead><tbody>
        {visibleEvents.map((event) => { const category = categories[event.type]; const Icon = category.icon; return <tr key={event.id}><td className="date-cell"><strong>{event.date}</strong><span>{event.time}</span></td><td><span className="type-label" style={{ '--category': category.color, '--category-bg': category.softColor }}><Icon size={16} />{category.label}</span></td><td><span className="duration"><Clock3 size={14} />{event.duration}</span></td><td><span className={`pill severity-${event.severityKey}`}>{event.severity}</span></td><td><span className={`pill status-${event.statusKey}`}><i />{event.status}</span></td><td className="description-cell">{event.description}</td></tr> })}
      </tbody></table></div>
    </section>
  )
}
