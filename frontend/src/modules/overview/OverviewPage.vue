<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useApi } from '@/composables/useApi'
import PageShell from '@/components/layout/PageShell.vue'
import StatCard from '@/components/data/StatCard.vue'
import Badge from '@/components/ui/Badge.vue'

const api = useApi()
const health = ref<{ status: string; version: string } | null>(null)

onMounted(async () => {
  try {
    health.value = await api.get('/api/health')
  } catch {
    // API not available yet
  }
})
</script>

<template>
  <PageShell>
    <div class="overview">
      <!-- Hero section -->
      <div class="overview__hero">
        <div class="overview__hero-left">
          <h2 class="overview__greeting">Good evening, Commander</h2>
          <p class="overview__subtitle">All systems operational. Here's your status report.</p>
        </div>
        <div class="overview__hero-right">
          <Badge
            :variant="health?.status === 'ok' ? 'success' : 'warning'"
            :label="health?.status === 'ok' ? 'ALL SYSTEMS GO' : 'CONNECTING...'"
          />
        </div>
      </div>

      <!-- Stat grid -->
      <section class="overview__section">
        <h3 class="overview__section-title">System Telemetry</h3>
        <div class="overview__stats mc-stagger">
          <StatCard icon="&#x1f7e2;" :value="health?.status ?? '—'" label="Backend Status" />
          <StatCard icon="&#x1f4e6;" :value="health?.version ?? '—'" label="Build Version" />
          <StatCard icon="&#x1f9e0;" value="—" label="Memory Files" />
          <StatCard icon="&#x1f916;" value="—" label="Agent Runs (24h)" />
        </div>
      </section>

      <!-- Quick access -->
      <section class="overview__section">
        <h3 class="overview__section-title">Quick Access</h3>
        <div class="overview__grid mc-stagger">
          <div class="overview__card overview__card--ghost">
            <span class="overview__card-icon">&#x1f4dd;</span>
            <span class="overview__card-label">Memory Module</span>
            <span class="overview__card-hint">Coming in Phase 3</span>
          </div>
          <div class="overview__card overview__card--ghost">
            <span class="overview__card-icon">&#x1f393;</span>
            <span class="overview__card-label">School Dashboard</span>
            <span class="overview__card-hint">Coming in Phase 5</span>
          </div>
          <div class="overview__card overview__card--ghost">
            <span class="overview__card-icon">&#x26a1;</span>
            <span class="overview__card-label">Agent Live Feed</span>
            <span class="overview__card-hint">Coming in Phase 4</span>
          </div>
        </div>
      </section>
    </div>
  </PageShell>
</template>

<style scoped>
.overview {
  max-width: 1100px;
}

/* Hero */
.overview__hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1.5rem;
  margin-bottom: 2.5rem;
  animation: mc-fade-up 0.4s ease-out;
}

.overview__greeting {
  font-family: var(--mc-font-display);
  font-size: 1.75rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  line-height: 1.2;
}

.overview__subtitle {
  color: var(--mc-text-muted);
  margin-top: 0.375rem;
  font-size: 0.9375rem;
}

@media (max-width: 640px) {
  .overview__hero {
    flex-direction: column;
    gap: 0.75rem;
  }
}

/* Sections */
.overview__section {
  margin-bottom: 2.25rem;
}

.overview__section-title {
  font-family: var(--mc-font-mono);
  font-size: 0.6875rem;
  font-weight: 600;
  color: var(--mc-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.12em;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--mc-border);
}

/* Stat grid */
.overview__stats {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
  gap: 1rem;
}

/* Quick access grid */
.overview__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 1rem;
}

.overview__card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 2rem 1.5rem;
  background: var(--mc-bg-surface);
  backdrop-filter: var(--mc-glass-blur);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius);
  text-align: center;
  transition:
    border-color var(--mc-transition-speed),
    background var(--mc-transition-speed);
}

.overview__card--ghost {
  border-style: dashed;
  opacity: 0.65;
}

.overview__card--ghost:hover {
  opacity: 0.85;
  border-color: var(--mc-border-strong);
}

.overview__card-icon {
  font-size: 1.75rem;
}

.overview__card-label {
  font-family: var(--mc-font-display);
  font-weight: 600;
  font-size: 0.9375rem;
}

.overview__card-hint {
  font-family: var(--mc-font-mono);
  font-size: 0.6875rem;
  color: var(--mc-text-muted);
  letter-spacing: 0.04em;
}
</style>
