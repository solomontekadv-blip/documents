import { expect, test } from 'claude-code/testing'

import { compare, formatUsd } from './compare'

test('formats dollars to cents', async () => {
  expect(formatUsd(0)).toBe('$0.00')
  expect(formatUsd(1.234)).toBe('$1.23')
})

test('compares to the closest everyday item', async () => {
  expect(compare(0.01)).toBe('פחות ממסטיק')
  expect(compare(4.2)).toBe('בערך כוס קפה')
  expect(compare(14)).toBe('בערך כרטיס לקולנוע')
  expect(compare(600)).toBe('בערך 4 קניות בסופר')
})
