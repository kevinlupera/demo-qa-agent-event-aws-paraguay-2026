<script setup lang="ts">
useHead({ title: 'QA para agentes de IA — 5 capas en vivo' })
</script>

<template>
  <main>
    <section class="hero">
      <p class="kicker">Cinco capas de QA · en vivo</p>
      <h1>Tu agente pasó todos los tests.<br><em>Y acaba de regalar el dinero de la empresa.</em></h1>
      <p class="lede">
        Un agente de soporte con una sola tool peligrosa: <b>issue_refund</b>, la que mueve dinero.
        Cinco capas de QA lo blindan, igual que en un aeropuerto. Elige una y córrela tú mismo: verás
        el agente <b>sin esa capa</b> y <b>con esa capa</b>, lado a lado.
      </p>
    </section>

    <ol class="cards">
      <li v-for="demo in DEMOS" :key="demo.id">
        <NuxtLink :to="`/demo/${demo.id}`">
          <div class="card-top">
            <span class="id">{{ demo.id }}</span>
            <h2>{{ demo.title }}</h2>
            <span class="layer">{{ demo.layer }}</span>
            <span class="go" aria-hidden="true">→</span>
          </div>

          <p class="analogy">{{ demo.analogy }}</p>

          <p class="row failure">
            <span class="tag">Falla</span>
            {{ demo.failure }}
          </p>
          <p class="row fix">
            <span class="tag">Arreglo</span>
            {{ demo.fix }}
          </p>

          <code class="primitive">{{ demo.primitive }}</code>
        </NuxtLink>
      </li>
    </ol>
  </main>
</template>

<style scoped>
.hero { margin: 0 0 3rem; max-width: 62ch; }
.kicker {
  margin: 0 0 1rem;
  font-family: var(--font-mono);
  font-size: 0.72rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--accent);
}
h1 {
  margin: 0 0 1.1rem;
  font-family: var(--font-display);
  font-weight: 700;
  font-size: clamp(2rem, 4.6vw, 3.1rem);
  line-height: 1.05;
  letter-spacing: -0.015em;
}
h1 em { font-style: normal; color: var(--accent); }
.lede { margin: 0; color: var(--muted); font-size: 1.02rem; line-height: 1.65; }
.lede b { color: var(--fg); font-weight: 600; }

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(20rem, 1fr));
  gap: 1rem;
  list-style: none;
  margin: 0;
  padding: 0;
  counter-reset: none;
}
.cards a {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  height: 100%;
  padding: 1.4rem 1.4rem 1.25rem;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: var(--panel);
  box-shadow: var(--shadow);
  text-decoration: none;
  position: relative;
  overflow: hidden;
  transition: border-color 0.16s, transform 0.16s;
}
.cards a:hover { border-color: var(--accent); }
.cards a:hover .go { transform: translateX(3px); opacity: 1; }

.card-top { display: flex; align-items: baseline; gap: 0.7rem; }
.id {
  font-family: var(--font-mono);
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--accent);
}
.card-top h2 {
  margin: 0;
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 1.18rem;
  line-height: 1.2;
  flex: 1;
}
.layer {
  font-family: var(--font-mono);
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  color: var(--accent);
  background: var(--accent-dim);
  white-space: nowrap;
}
.analogy { margin: -0.2rem 0 0; color: var(--accent); font-weight: 700; font-size: 0.95rem; }
.go { color: var(--muted-dim); opacity: 0.6; transition: transform 0.16s, opacity 0.16s; }

.row {
  margin: 0;
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.6rem;
  font-size: 0.86rem;
  line-height: 1.5;
  color: var(--muted);
}
.tag {
  align-self: start;
  font-family: var(--font-mono);
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: 0.15rem 0.45rem;
  border-radius: 999px;
  white-space: nowrap;
}
.failure .tag { color: var(--danger); background: var(--danger-dim); }
.fix .tag { color: var(--ok); background: var(--ok-dim); }
.fix { color: var(--fg); }

.primitive {
  margin-top: auto;
  padding-top: 0.75rem;
  border-top: 1px dashed var(--line);
  font-family: var(--font-mono);
  font-size: 0.7rem;
  line-height: 1.5;
  color: var(--muted-dim);
}
</style>
