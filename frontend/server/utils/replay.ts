import demo00 from '../fixtures/demo00.json'
import demo01 from '../fixtures/demo01.json'
import demo02 from '../fixtures/demo02.json'
import demo03 from '../fixtures/demo03.json'
import demo04 from '../fixtures/demo04.json'

interface Frame {
  delayMs: number
  event: { t: string; pane?: string; [key: string]: unknown }
}

// Simulated runs: same event vocabulary as the real backend, hand-written, no model involved.
const FIXTURES: Record<string, Frame[]> = {
  '00': demo00,
  '01': demo01,
  '02': demo02,
  '03': demo03,
  '04': demo04,
}

/** Streams a fixture as SSE, honouring each frame's delay. `guard=false` drops the resilient pane. */
export function replayStream(demo: string, guard: boolean): ReadableStream<Uint8Array> {
  const frames = (FIXTURES[demo] ?? []).filter(f => guard || f.event.pane !== 'resilient')
  const encoder = new TextEncoder()
  let timer: ReturnType<typeof setTimeout> | undefined

  return new ReadableStream<Uint8Array>({
    start(controller) {
      let i = 0
      const next = () => {
        if (i >= frames.length) return controller.close()
        const frame = frames[i++]!
        timer = setTimeout(() => {
          controller.enqueue(encoder.encode(`data: ${JSON.stringify(frame.event)}\n\n`))
          next()
        }, frame.delayMs)
      }
      next()
    },
    cancel() {
      clearTimeout(timer)
    },
  })
}
