type Item = { usd: number; label: string }

// Everyday price points, in US dollars, cheapest first.
const FIRST: Item = { usd: 0.05, label: 'פחות ממסטיק' }
const LAST: Item = { usd: 150, label: 'בערך קנייה בסופר' }
const ITEMS: ReadonlyArray<Item> = [
  FIRST,
  { usd: 0.5, label: 'בערך מסטיק' },
  { usd: 1.5, label: 'בערך בקבוק מים' },
  { usd: 4, label: 'בערך כוס קפה' },
  { usd: 8, label: 'בערך כריך' },
  { usd: 15, label: 'בערך כרטיס לקולנוע' },
  { usd: 30, label: 'בערך ארוחה במסעדה' },
  { usd: 60, label: 'בערך מילוי מיכל דלק' },
  LAST,
]

export function formatUsd(usd: number): string {
  return usd < 0.01 ? '$0.00' : `$${usd.toFixed(2)}`
}

export function compare(usd: number): string {
  if (usd < FIRST.usd) {
    return FIRST.label
  }
  if (usd > LAST.usd * 1.5) {
    return `בערך ${Math.round(usd / LAST.usd)} קניות בסופר`
  }

  // The item closest in price, on a ratio scale.
  const distance = (item: Item) => Math.abs(Math.log(usd / item.usd))
  let best = FIRST
  for (const item of ITEMS) {
    if (distance(item) < distance(best)) {
      best = item
    }
  }

  return best.label
}
