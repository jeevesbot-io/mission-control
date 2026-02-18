<template>
  <div class="usage-panel">
    <div v-if="store.usage" class="usage-content">
      <div class="model-row">
        <McIcon name="cpu" :size="14" />
        <span class="model-name">{{ store.usage.model.replace('anthropic/', '') }}</span>
        <ModelSwitcher />
      </div>
      <div v-for="tier in store.usage.tiers" :key="tier.label" class="tier-row">
        <div class="tier-header">
          <span class="tier-label">{{ tier.label }}</span>
          <span class="tier-pct" :class="pctClass(tier.percent)">{{ tier.percent }}%</span>
        </div>
        <div class="progress-track">
          <div
            class="progress-fill"
            :class="pctClass(tier.percent)"
            :style="{ width: `${tier.percent}%` }"
          />
        </div>
        <span class="tier-reset">resets in {{ tier.resetsIn }}</span>
      </div>
    </div>
    <div v-else-if="store.loading" class="usage-loading">Loading usage…</div>
    <div v-else class="usage-empty">No usage data available</div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useWarRoomStore } from '../store'
import McIcon from '@/components/ui/McIcon.vue'
import ModelSwitcher from './ModelSwitcher.vue'

const store = useWarRoomStore()

onMounted(() => {
  store.fetchUsage()
  store.fetchModels()
})

function pctClass(pct: number) {
  if (pct >= 80) return 'pct-danger'
  if (pct >= 50) return 'pct-warning'
  return 'pct-ok'
}
</script>

<style scoped>
.usage-panel {
  background: var(--mc-bg-surface);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: var(--mc-radius);
  padding: 1.25rem;
  max-width: 480px;
}

.model-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.model-name {
  font-family: var(--mc-font-mono);
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--mc-text);
  flex: 1;
}

.tier-row { margin-bottom: 0.9rem; }
.tier-row:last-child { margin-bottom: 0; }

.tier-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.35rem;
}
.tier-label {
  font-size: 0.75rem;
  color: var(--mc-text-muted);
}
.tier-pct {
  font-family: var(--mc-font-mono);
  font-size: 0.75rem;
  font-weight: 700;
}
.pct-ok      { color: var(--mc-success); }
.pct-warning { color: var(--mc-warning); }
.pct-danger  { color: var(--mc-danger);  }

.progress-track {
  height: 5px;
  background: rgba(255,255,255,0.08);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 0.25rem;
}
.progress-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 600ms ease;
}
.progress-fill.pct-ok      { background: var(--mc-success); }
.progress-fill.pct-warning { background: var(--mc-warning); }
.progress-fill.pct-danger  { background: var(--mc-danger); }

.tier-reset {
  font-size: 0.67rem;
  color: var(--mc-text-muted);
  font-family: var(--mc-font-mono);
}

.usage-loading, .usage-empty {
  color: var(--mc-text-muted);
  font-size: 0.8rem;
  text-align: center;
  padding: 1rem 0;
}
</style>
