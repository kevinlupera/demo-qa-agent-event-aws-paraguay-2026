export interface AgentEvent {
  t: 'phase' | 'step' | 'tool' | 'hook' | 'tokens' | 'verdict' | 'error' | 'done'
  pane?: 'naive' | 'resilient'
  text?: string
  title?: string
  name?: string
  args?: Record<string, unknown>
  action?: string
  why?: string
  input?: number
  output?: number
  ok?: boolean
  summary?: string
  message?: string
}

/** Streams one scenario run. The server sends SSE; we only ever render AgentEvents. */
export function useAgentRun() {
  const route = useRoute()
  const events = ref<AgentEvent[]>([])
  const running = ref(false)
  const error = ref('')

  const paneEvents = (pane: 'naive' | 'resilient') =>
    computed(() => events.value.filter(e => e.pane === pane))

  async function start(demo: string, guard = true) {
    if (running.value) return
    events.value = []
    error.value = ''
    running.value = true

    try {
      // ?replay=1 on the page URL is forwarded to the server route (replay without env vars).
      const url = route.query.replay === '1' ? '/api/run?replay=1' : '/api/run'
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ demo, guard }),
      })
      if (!response.ok || !response.body) {
        throw new Error(`El agente respondio ${response.status}: ${await response.text()}`)
      }

      const reader = response.body.pipeThrough(new TextDecoderStream()).getReader()
      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += value

        let newline
        while ((newline = buffer.indexOf('\n')) >= 0) {
          const line = buffer.slice(0, newline).trim()
          buffer = buffer.slice(newline + 1)
          if (!line.startsWith('data:')) continue
          const raw = line.slice(5).trim()
          if (!raw) continue
          try {
            const event = JSON.parse(raw) as AgentEvent
            if (event.t === 'error') error.value = event.message ?? 'error desconocido'
            events.value = [...events.value, event]
          } catch {
            // a partial or non-JSON keepalive frame; ignore it
          }
        }
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      running.value = false
    }
  }

  return { events, running, error, start, paneEvents }
}
