<script setup lang="ts">
const route = useRoute()
const id = computed(() => String(route.params.id))
const demo = computed(() => demoById(id.value))

if (!demo.value) throw createError({ statusCode: 404, statusMessage: 'demo no encontrada' })

useHead({ title: () => `${id.value} — ${demo.value?.title}` })

const { events, running, error, start, paneEvents } = useAgentRun()
const naive = paneEvents('naive')
const resilient = paneEvents('resilient')

// --- Métricas de resultado (reusan lo que ya emite el backend: tokens + verdict) ---
type Ev = { t: string; input?: number; output?: number; ok?: boolean; summary?: string }
const lastTokens = (list: Ev[]) => {
  const e = [...list].reverse().find(x => x.t === 'tokens')
  return e ? (e.input ?? 0) + (e.output ?? 0) : 0
}
const lastVerdict = (list: Ev[]) => [...list].reverse().find(x => x.t === 'verdict')

const stats = computed(() => {
  const n = lastVerdict(naive.value as Ev[])
  const r = lastVerdict(resilient.value as Ev[])
  const nTok = lastTokens(naive.value as Ev[])
  const rTok = lastTokens(resilient.value as Ev[])
  return {
    ready: !!(n || r),
    naive: { ok: n?.ok, summary: n?.summary, tokens: nTok },
    resilient: { ok: r?.ok, summary: r?.summary, tokens: rTok },
    delta: rTok && nTok ? rTok - nTok : 0,
  }
})
const fmt = (n: number) => n.toLocaleString('es')

const config = useRuntimeConfig()
const replay = computed(() => String(config.public.replay) === '1' || route.query.replay === '1')
const clean = computed(() => route.query.clean === '1')
</script>

<template>
  <main v-if="demo">
    <NuxtLink to="/" class="back">← todas las capas</NuxtLink>

    <header class="head">
      <div class="head-text">
        <span class="id">demo {{ demo.id }} · {{ demo.layer }} · {{ demo.analogy }}</span>
        <h1>{{ demo.title }}</h1>

        <div class="prompt-sent">
          <span class="tag">Prompt enviado</span>
          <p><span class="caret" aria-hidden="true">▸</span>{{ demo.prompt }}</p>
        </div>

        <div class="callouts">
          <div class="callout failure">
            <span class="tag">El fallo</span>
            <p>{{ demo.failure }}</p>
          </div>
          <div class="callout fix">
            <span class="tag">El arreglo</span>
            <p>{{ demo.fix }}</p>
          </div>
        </div>
        <code class="primitive">{{ demo.primitive }}</code>
      </div>

      <button :disabled="running" @click="start(demo.id)">
        <span v-if="running" class="spin" aria-hidden="true"></span>
        {{ running ? 'Ejecutando…' : events.length ? 'Ejecutar otra vez' : 'Ejecutar demo' }}
      </button>
    </header>

    <p v-if="error" class="error">{{ error }}</p>

    <section v-if="stats.ready" class="scoreboard">
      <h2 class="sb-title">Resultado</h2>
      <div class="sb-grid">
        <div class="sb-cell" :class="{ bad: stats.naive.ok === false, ok: stats.naive.ok }">
          <span class="sb-label">Sin esta capa</span>
          <span class="sb-verdict">{{ stats.naive.ok === false ? '✗ FALLA' : stats.naive.ok ? '✓ RESISTE' : '—' }}</span>
          <span class="sb-sum">{{ stats.naive.summary }}</span>
          <span class="sb-tokens">{{ fmt(stats.naive.tokens) }} <em>tokens</em></span>
        </div>

        <div class="sb-cell" :class="{ bad: stats.resilient.ok === false, ok: stats.resilient.ok }">
          <span class="sb-label">Con esta capa</span>
          <span class="sb-verdict">{{ stats.resilient.ok === false ? '✗ FALLA' : stats.resilient.ok ? '✓ RESISTE' : '—' }}</span>
          <span class="sb-sum">{{ stats.resilient.summary }}</span>
          <span class="sb-tokens">
            {{ fmt(stats.resilient.tokens) }} <em>tokens</em>
            <span v-if="stats.delta" class="sb-delta">{{ stats.delta > 0 ? '+' : '' }}{{ fmt(stats.delta) }} vs sin la capa</span>
          </span>
        </div>
      </div>
    </section>

    <div class="panes">
      <AgentPane
        title="Sin esta capa"
        subtitle="El agente solo. Lo que pida el cliente, va."
        tone="naive"
        :events="naive"
      />
      <span class="vs" aria-hidden="true">vs</span>
      <AgentPane
        title="Con esta capa"
        subtitle="Mismo modelo, misma tarea, con la capa de QA puesta."
        tone="resilient"
        :events="resilient"
      />
    </div>

    <p v-if="replay && !clean" class="note">
      Resultado simulado: la secuencia está escrita a mano con los mismos eventos que emite el
      agente real, para grabar la demo sin llamar a ningún modelo.
    </p>
    <p v-else-if="!replay" class="note">
      Ejecuciones reales: el modelo corre en vivo sobre un agente de reembolsos con pedidos de
      prueba en memoria (A-1101 dentro de política, A-1002 fuera). Los tokens son medidos, no estimados.
    </p>
  </main>
</template>

<style scoped>
.back {
  display: inline-block;
  margin-bottom: 1.5rem;
  font-family: var(--font-mono);
  font-size: 0.74rem;
  letter-spacing: 0.04em;
  color: var(--muted);
  text-decoration: none;
}
.back:hover { color: var(--accent); }

.head {
  display: flex;
  gap: 2.5rem;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 2rem;
}
.head-text { min-width: 0; }
.id {
  font-family: var(--font-mono);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--accent);
}
h1 {
  margin: 0.4rem 0 1.25rem;
  font-family: var(--font-display);
  font-weight: 700;
  font-size: clamp(1.8rem, 3.4vw, 2.5rem);
  line-height: 1.08;
  letter-spacing: -0.015em;
}

/* prompt = the literal input, styled as a terminal line */
.prompt-sent {
  margin: 0 0 1rem;
  border-radius: 10px;
  border: 1px solid var(--line);
  background: var(--panel-2);
  overflow: hidden;
}
.prompt-sent .tag {
  display: block;
  padding: 0.5rem 0.9rem;
  border-bottom: 1px solid var(--line);
  font-family: var(--font-mono);
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--accent);
  background: var(--accent-dim);
}
.prompt-sent p {
  margin: 0;
  padding: 0.85rem 0.95rem;
  font-family: var(--font-mono);
  font-size: 0.88rem;
  line-height: 1.6;
  color: var(--fg);
}
.prompt-sent .caret { color: var(--accent); font-weight: 700; margin-right: 0.55rem; }

/* fallo / arreglo side by side — the red→green pair */
.callouts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.85rem;
}
.callout {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
  padding: 0.95rem 1.05rem;
  border-radius: 10px;
  border: 1px solid var(--line);
}
.callout p { margin: 0; line-height: 1.55; font-size: 0.92rem; color: var(--fg); }
.callout.failure { background: var(--danger-dim); border-color: color-mix(in srgb, var(--danger) 45%, transparent); }
.callout.fix { background: var(--ok-dim); border-color: color-mix(in srgb, var(--ok) 45%, transparent); }
.callout .tag {
  align-self: start;
  font-family: var(--font-mono);
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  white-space: nowrap;
}
.failure .tag { color: var(--danger); background: color-mix(in srgb, var(--danger) 18%, transparent); }
.fix .tag { color: var(--ok); background: color-mix(in srgb, var(--ok) 18%, transparent); }
@media (max-width: 620px) { .callouts { grid-template-columns: 1fr; } }

.primitive {
  display: inline-block;
  margin: 1rem 0 0;
  padding: 0.3rem 0.7rem;
  border-radius: 8px;
  background: var(--panel-2);
  border: 1px solid var(--line-soft);
  font-family: var(--font-mono);
  font-size: 0.72rem;
  color: var(--muted);
}
.head button { white-space: nowrap; display: inline-flex; align-items: center; gap: 0.55rem; }
.spin {
  width: 0.85rem; height: 0.85rem; border-radius: 50%;
  border: 2px solid color-mix(in srgb, var(--on-solid) 40%, transparent);
  border-top-color: var(--on-solid);
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.scoreboard { margin: 0 0 1.75rem; }
.sb-title {
  margin: 0 0 0.75rem;
  font-family: var(--font-mono);
  font-size: 0.72rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--muted);
}
.sb-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.sb-cell {
  display: grid;
  grid-template-rows: auto auto 1fr auto;
  gap: 0.5rem;
  padding: 1.15rem 1.3rem;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: var(--panel);
  color: var(--fg);
  box-shadow: var(--shadow);
}
.sb-cell.bad { border-color: var(--danger); box-shadow: inset 0 3px 0 var(--danger); }
.sb-cell.ok { border-color: var(--ok); box-shadow: inset 0 3px 0 var(--ok); }
.sb-label {
  font-family: var(--font-mono);
  font-size: 0.68rem;
  letter-spacing: 0.09em;
  text-transform: uppercase;
  color: var(--muted);
}
.sb-verdict {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 1.9rem;
  line-height: 1;
  letter-spacing: -0.01em;
}
.sb-cell.bad .sb-verdict { color: var(--danger); }
.sb-cell.ok .sb-verdict { color: var(--ok); }
.sb-sum { font-size: 0.92rem; line-height: 1.5; color: var(--fg); }
.sb-tokens {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.5rem 0.7rem;
  padding-top: 0.65rem;
  border-top: 1px solid var(--line);
  font-family: var(--font-mono);
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--fg);
}
.sb-tokens em { font-style: normal; font-weight: 400; font-size: 0.78rem; color: var(--muted); }
.sb-delta {
  font-weight: 400;
  font-size: 0.72rem;
  color: var(--muted);
  padding: 0.1rem 0.55rem;
  border-radius: 999px;
  background: var(--panel-2);
}

.panes {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: stretch;
  gap: 0.85rem;
}
.vs {
  align-self: center;
  font-family: var(--font-display);
  font-style: italic;
  font-size: 1.1rem;
  color: var(--muted-dim);
}
@media (max-width: 860px) {
  .head { flex-direction: column; gap: 1.25rem; }
  .panes { grid-template-columns: 1fr; }
  .sb-grid { grid-template-columns: 1fr; }
  .vs { justify-self: center; }
}

.error {
  margin: 0 0 1.25rem;
  padding: 0.85rem 1.1rem;
  border-radius: 10px;
  border: 1px solid var(--danger);
  background: var(--danger-dim);
  color: var(--danger);
  font-family: var(--font-mono);
  font-size: 0.82rem;
  overflow-wrap: anywhere;
}
.note {
  margin-top: 1.75rem;
  font-size: 0.78rem;
  line-height: 1.6;
  color: var(--muted-dim);
}
</style>
