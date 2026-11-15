import { AlertTriangle } from 'lucide-react'
import SectionHeader from './SectionHeader'

export default function RecentEvents({ events, categories }) {
  const visibleEvents = events.slice(0, 10)
  return <section className="panel">
    <SectionHeader icon={AlertTriangle} title="近10筆異常事件" subtitle="實機偵測到的設備狀態變化" action={<span className="record-count">共 {visibleEvents.length} 筆</span>} />
    <div className="table-scroll"><table className="events-table"><thead><tr><th>發生時間</th><th>異常類型</th><th>狀態</th><th>描述</th></tr></thead><tbody>
      {visibleEvents.map(event=>{ const category=categories[event.type]; const Icon=category.icon; return <tr key={event.id}>
        <td className="date-cell">{event.time}</td>
        <td><span className="type-label" style={{'--category':category.color,'--category-bg':category.softColor}}><Icon size={16} />{category.label}</span></td>
        <td><span className={`pill status-${event.statusKey}`}><i />{event.status}</span></td><td className="description-cell">{event.description}</td>
      </tr>})}
    </tbody></table></div>
  </section>
}
