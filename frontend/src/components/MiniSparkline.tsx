type MiniSparklineProps = {
  values: number[];
};

export function MiniSparkline({ values }: MiniSparklineProps) {
  if (!values.length) {
    return null;
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const pts = values.map((value, index) => {
    const x = (index / (values.length - 1 || 1)) * 100;
    const y = 100 - ((value - min) / range) * 100;
    return { x, y };
  });

  function catmullRom2bezier(points: { x: number; y: number }[]) {
    if (points.length === 1) return `M ${points[0].x},${points[0].y}`;
    let d = `M ${points[0].x},${points[0].y}`;
    for (let i = 0; i < points.length - 1; i++) {
      const p0 = points[i - 1] || points[i];
      const p1 = points[i];
      const p2 = points[i + 1];
      const p3 = points[i + 2] || p2;

      const cp1x = p1.x + (p2.x - p0.x) / 6;
      const cp1y = p1.y + (p2.y - p0.y) / 6;
      const cp2x = p2.x - (p3.x - p1.x) / 6;
      const cp2y = p2.y - (p3.y - p1.y) / 6;

      d += ` C ${cp1x},${cp1y} ${cp2x},${cp2y} ${p2.x},${p2.y}`;
    }
    return d;
  }

  const pathD = catmullRom2bezier(pts);

  return (
    <svg className="sparkline" viewBox="0 0 100 100" preserveAspectRatio="none">
      <path
        d={pathD}
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

