export default function SectionHeader({ icon: Icon, title, subtitle, action }) {
  return <div className="section-header"><div className="section-heading"><span className="section-icon"><Icon size={21} aria-hidden="true" /></span><div><h2>{title}</h2><p>{subtitle}</p></div></div>{action}</div>
}
