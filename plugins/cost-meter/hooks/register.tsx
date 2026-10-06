import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'

import type { Usd } from '../types'
import { compare, formatUsd } from './compare'

const cost = atom({ plugin: 'cost-meter', key: 'usd' } as const, null as Usd)

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const result = await next(e)
    const usage = await $.session.usage()
    if (usage.cost) {
      await update($, cost, () => usage.cost!.usd)
    }

    return result
  })

  // Fires after every turn, once the session's cost ledger has moved.
  on('session.measure', async ($, e, next) => {
    if (e.cost) {
      const usd = e.cost.usd
      await update($, cost, () => usd)
    }

    return next(e)
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const usd = await read($, cost)
    if (e.props.hasSurvey || usd === null) {
      return next(e)
    }

    const { Text } = $.ui.resolve(e)

    return (
      <Text dimColor>
        💰 {formatUsd(usd)} · {compare(usd)}
      </Text>
    )
  })
}
