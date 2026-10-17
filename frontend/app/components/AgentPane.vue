<script setup lang="ts">
import type { AgentEvent } from '~/composables/useAgentRun'

const props = defineProps<{
  title: string
  subtitle: string
  tone: 'naive' | 'resilient'
  events: AgentEvent[]
}>()

const tokens = computed(() => {
  const last = [...props.events].reverse().find(e => e.t === 'tokens')
  return last ? (last.input ?? 0) + (last.output ?? 0) : 0
})

const verdict = computed(() => [...props.events].reverse().find(e => e.t === 'verdict'))

const HOOK_LABEL: Record<string, string> = {
  blocked: 'BLOQUEADO',
  rewrote: 'CORREGIDO',
  failover: 'FAILOVER',
  retry: 'REINTENTO',
  verified: 'VERIFICADO',
}

// Agent → customer replies arrive as steps prefixed "respuesta:" / "respuesta al cliente:" / "el cliente recibe:".
const REPLY = /^(respuesta(?: al cliente)?|el cliente recibe):\s*/i
const replyOf = (e: AgentEvent) => (e.t === 'step' && e.text ? REPLY.exec(e.text) : null)

const log = ref<HTMLElement | null>(null)
watch(() => props.events.length, async () => {
  await nextTick()
  if (log.value) log.value.scrollTop = log.value.scrollHeight
})
</script>

<template>
  <section class="pane" :class="tone">
    <div class="chrome">
      <span class="fname">{{ tone === 'naive' ? 'sin-esta-capa.log' : 'con-esta-capa.log' }}</span>
      <span class="badge">{{ tone === 'naive' ? 'sin la capa' : 'con la capa' }}</span>
    </div>
    <header>
      <h2>{{ title }}</h2>
      <p class="sub">{{ subtitle }}</p>
    </header>

    <div ref="log" class="log">
      <p v-if="!events.length" class="empty">Sin ejecutar todavía. Pulsa <b>Ejecutar demo</b>.</p>

      <template v-for="(e, i) in events" :key="i">
        <p v-if="e.t === 'phase'" class="phase">{{ e.title }}</p>

        <div v-else-if="replyOf(e)" class="reply">
          <span class="reply-tag">Respuesta del agente al usuario</span>
          <p>{{ e.text!.replace(REPLY, '') }}</p>
        </div>

        <p v-else-if="e.t === 'step'" class="step">{{ e.text }}</p>

        <p v-else-if="e.t === 'tool'" class="tool">
          <span class="chip">tool</span>
          <span class="tool-name">{{ e.name }}</span>
          <code>{{ JSON.stringify(e.args) }}</code>
        </p>

        <p v-else-if="e.t === 'hook'" class="hook" :class="e.action">
          <span class="chip">{{ HOOK_LABEL[e.action ?? ''] ?? e.action?.toUpperCase() }}</span>
          {{ e.why }}
        </p>
      </template>
    </div>

    <footer :class="{ ok: verdict?.ok, bad: verdict && !verdict.ok }">
      <span class="tokens">
        <b>{{ tokens.toLocaleString('es') }}</b> tokens
      </span>
      <span v-if="verdict" class="verdict">
        <span class="glyph">{{ verdict.ok ? '✓' : '✗' }}</span>
        {{ verdict.summary }}
      </span>
      <span v-else class="verdict pending">— sin veredicto aún</span>
    </footer>
  </section>
</template>

<style scoped>
.pane {
  display: flex;
  flex-direction: column;
  min-height: 34rem;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: var(--panel);
  box-shadow: var(--shadow);
  overflow: hidden;
}
.pane.naive { border-top: 3px solid var(--danger); }
.pane.resilient { border-top: 3px solid var(--ok); }

.chrome {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  padding: 0.55rem 1.2rem;
  background: var(--panel-2);
  border-bottom: 1px solid var(--line);
}
.chrome .fname { font-family: var(--font-mono); font-size: 0.72rem; color: var(--muted); }
.chrome .badge {
  margin-left: auto;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.15rem 0.6rem;
  border-radius: 999px;
}
.naive .badge { color: var(--danger); background: var(--danger-dim); }
.resilient .badge { color: var(--ok); background: var(--ok-dim); }

header { padding: 1rem 1.2rem 0.85rem; border-bottom: 1px solid var(--line); }
header h2 { margin: 0; font-family: var(--font-display); font-weight: 600; font-size: 1.1rem; }
.sub { margin: 0.3rem 0 0; font-size: 0.85rem; line-height: 1.5; color: var(--muted); }

.log {
  flex: 1;
  overflow-y: auto;
  padding: 1rem 1.2rem 1.1rem;
  background: var(--console);
  color: var(--fg);
  font-family: var(--font-mono);
  font-size: 0.84rem;
  line-height: 1.7;
}
.log p { margin: 0.3rem 0; overflow-wrap: anywhere; }
.empty { color: var(--muted-dim); font-style: italic; }
.empty b { color: var(--muted); }

.phase {
  margin-top: 1.1rem !important;
  padding-top: 0.55rem;
  border-top: 1px dashed var(--line);
  font-weight: 700;
}
.phase:first-child { margin-top: 0.2rem !important; border-top: 0; padding-top: 0; }
.step { color: var(--muted); padding-left: 0.9rem; position: relative; }
.step::before { content: "·"; position: absolute; left: 0; color: var(--muted-dim); }

.log .reply {
  margin: 0.7rem 0;
  padding: 0.7rem 0.9rem;
  border-radius: 10px;
  border: 1px solid var(--accent);
  border-left-width: 4px;
  background: var(--accent-dim);
}
.reply-tag {
  display: block;
  margin-bottom: 0.3rem;
  font-size: 0.64rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--accent);
}
.log .reply p { margin: 0; font-size: 0.92rem; line-height: 1.55; color: var(--fg); }

.tool-name { color: var(--accent); font-weight: 600; }
.tool code { color: var(--muted-dim); margin-left: 0.4rem; }

.chip {
  display: inline-block;
  padding: 0.05rem 0.45rem;
  margin-right: 0.45rem;
  border-radius: 6px;
  font-size: 0.64rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  background: var(--panel-2);
  color: var(--fg);
}
.tool .chip { background: var(--accent-dim); color: var(--accent); }
.hook { padding: 0.4rem 0.7rem; border-radius: 8px; }
.hook.blocked, .hook.retry { background: var(--danger-dim); }
.hook.rewrote, .hook.failover, .hook.verified { background: var(--ok-dim); }
.hook.blocked .chip, .hook.retry .chip { background: var(--danger); color: var(--on-solid); }
.hook.rewrote .chip, .hook.failover .chip, .hook.verified .chip { background: var(--ok); color: var(--on-solid); }

footer {
  display: flex;
  gap: 1rem;
  align-items: center;
  justify-content: space-between;
  padding: 0.8rem 1.2rem;
  border-top: 1px solid var(--line);
  background: var(--panel-2);
  font-family: var(--font-mono);
  font-size: 0.76rem;
}
footer.ok { background: var(--ok-dim); }
footer.bad { background: var(--danger-dim); }
.tokens { color: var(--muted); white-space: nowrap; }
.tokens b { color: var(--fg); }
.verdict { display: flex; align-items: center; gap: 0.4rem; text-align: right; font-weight: 500; color: var(--muted); }
footer.bad .verdict { color: var(--danger); }
footer.ok .verdict { color: var(--ok); }
.verdict.pending { color: var(--muted-dim); }
.glyph {
  display: inline-grid;
  place-items: center;
  width: 1.15rem; height: 1.15rem;
  border-radius: 50%;
  font-size: 0.72rem;
  font-weight: 700;
}
footer.bad .glyph { background: var(--danger); color: var(--on-solid); }
footer.ok .glyph { background: var(--ok); color: var(--on-solid); }
</style>
