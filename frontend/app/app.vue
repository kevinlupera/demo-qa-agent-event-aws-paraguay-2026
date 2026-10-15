<script setup lang="ts">
// Replay = simulated fixtures, not a live run. The badge keeps that honest; ?clean=1 hides it
// for screen recording.
const route = useRoute()
const config = useRuntimeConfig()
const replay = computed(() => String(config.public.replay) === '1' || route.query.replay === '1')
const showBadge = computed(() => replay.value && route.query.clean !== '1')
</script>

<template>
  <div class="shell">
    <header class="topbar">
      <NuxtLink to="/" class="brand">
        <span class="mark" aria-hidden="true"></span>
        QA para agentes de IA
        <span class="route">agente de reembolsos</span>
      </NuxtLink>
      <span v-if="showBadge" class="replay-badge">Replay · resultado simulado</span>
    </header>
    <NuxtPage />
  </div>
</template>

<style>
/* Neutral light theme with a dark variant. Semantic colors only mark pass / fail. */
:root {
  --bg: #f8fafc;
  --panel: #ffffff;
  --panel-2: #f1f5f9;
  --line: #e2e8f0;
  --line-soft: #eef2f6;
  --console: #ffffff;
  --console-line: #e2e8f0;
  --fg: #0f172a;
  --muted: #475569;
  --muted-dim: #64748b;
  --ok: #15803d;
  --ok-dim: rgba(21, 128, 61, 0.1);
  --danger: #b91c1c;
  --danger-dim: rgba(185, 28, 28, 0.08);
  --accent: #4f46e5;
  --accent-dim: rgba(79, 70, 229, 0.1);
  --on-solid: #ffffff;
  --shadow: 0 1px 2px rgba(15, 23, 42, 0.06);

  --font-display: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --font-body: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0b1120;
    --panel: #111827;
    --panel-2: #1a2333;
    --line: #273244;
    --line-soft: #1f2937;
    --console: #111827;
    --console-line: #273244;
    --fg: #e5e7eb;
    --muted: #a3acba;
    --muted-dim: #8b95a5;
    --ok: #4ade80;
    --ok-dim: rgba(74, 222, 128, 0.12);
    --danger: #f87171;
    --danger-dim: rgba(248, 113, 113, 0.12);
    --accent: #818cf8;
    --accent-dim: rgba(129, 140, 248, 0.14);
    --on-solid: #0b1120;
    --shadow: none;
  }
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; background: var(--bg); }
body {
  margin: 0;
  background: var(--bg);
  color: var(--fg);
  font-family: var(--font-body);
  font-size: 17px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}
a { color: inherit; }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

.shell { max-width: 1280px; margin: 0 auto; padding: 2rem 2rem 4rem; }

.topbar { margin-bottom: 2.5rem; display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
.replay-badge {
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.25rem 0.7rem;
  border-radius: 999px;
  color: var(--accent);
  background: var(--accent-dim);
}
.brand {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 0.9rem;
  font-weight: 600;
  text-decoration: none;
  color: var(--fg);
}
.brand .mark { width: 0.6rem; height: 0.6rem; border-radius: 50%; background: var(--accent); }
.brand .route {
  font-weight: 400;
  color: var(--muted);
  padding-left: 0.6rem;
  border-left: 1px solid var(--line);
}

button {
  font-family: var(--font-body);
  font-size: 0.95rem;
  cursor: pointer;
  border: 1px solid transparent;
  border-radius: 8px;
  padding: 0.6rem 1.25rem;
  background: var(--accent);
  color: var(--on-solid);
  font-weight: 600;
  transition: filter 0.12s ease;
}
button:hover:not(:disabled) { filter: brightness(1.08); }
button:disabled { opacity: 0.6; cursor: progress; }
</style>
