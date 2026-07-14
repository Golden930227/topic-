function Icon({ name, size = 22 }) {
  return (
    <svg className="app-icon" width={size} height={size} aria-hidden="true">
      <use href={`/icons.svg#${name}-icon`} />
    </svg>
  )
}

export default Icon
