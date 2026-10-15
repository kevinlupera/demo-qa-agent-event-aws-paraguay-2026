export default defineNuxtConfig({
  compatibilityDate: '2025-07-01',
  devtools: { enabled: false },
  // Allow Cloudflare quick-tunnel hosts (leading dot = any *.trycloudflare.com subdomain)
  vite: { server: { allowedHosts: ['.trycloudflare.com'] } },
  app: { head: { htmlAttrs: { lang: 'es' } } },
  runtimeConfig: {
    // Set AGENT_RUNTIME_ARN to hit the deployed AgentCore Runtime. Leave it empty and the
    // server route falls back to a local `python app.py` on LOCAL_AGENT_URL — same events,
    // no AWS round-trip, which is what you want while building the demo.
    agentRuntimeArn: '',
    awsRegion: 'us-west-2',
    localAgentUrl: 'http://localhost:8080/invocations',
    maxRunsPerVisitor: '20',
    // NUXT_REPLAY=1 streams simulated fixtures instead of calling the agent (for recording).
    replay: '',
    public: {
      // NUXT_PUBLIC_REPLAY=1 shows the REPLAY badge and forwards ?replay=1 on the run request.
      replay: '',
    },
  },
})
