type ForcesPanelProps = {
  bullish: string[];
  bearish: string[];
};

export function ForcesPanel({ bullish, bearish }: ForcesPanelProps) {
  return (
    <section className="panel forces-grid">
      <div className="force-column">
        <span className="eyebrow">Bullish pressure</span>
        <ul className="tag-list">
          {bullish.map((item) => (
            <li key={item} className="tag bullish">
              {item}
            </li>
          ))}
        </ul>
      </div>
      <div className="force-column">
        <span className="eyebrow">Bearish pressure</span>
        <ul className="tag-list">
          {bearish.map((item) => (
            <li key={item} className="tag bearish">
              {item}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

