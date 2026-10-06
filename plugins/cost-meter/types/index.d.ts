export type Usd = number | null

declare module 'claude-code' {
  interface PluginState {
    'cost-meter': { usd: Usd }
  }
}
