interface PageGuideItem {
  description: string
  title: string
}

interface PageGuideProps {
  items: PageGuideItem[]
  label: string
}

export function PageGuide({ items, label }: PageGuideProps) {
  return (
    <ol className="page-guide" aria-label={label}>
      {items.map((item, index) => (
        <li key={item.title}>
          <span>{String(index + 1).padStart(2, '0')}</span>
          <div>
            <strong>{item.title}</strong>
            <small>{item.description}</small>
          </div>
        </li>
      ))}
    </ol>
  )
}
