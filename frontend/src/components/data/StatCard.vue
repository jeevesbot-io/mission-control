<script setup lang="ts">
defineProps<{
  icon: string
  value: string | number
  label: string
  trend?: { value: string; direction: 'up' | 'down' }
}>()
</script>

<template>
  <div class="stat-card">
    <!-- Top edge accent -->
    <div class="stat-card__accent" />

    <div class="stat-card__content">
      <div class="stat-card__header">
        <div class="stat-card__icon-box">
          <span class="stat-card__icon">{{ icon }}</span>
        </div>
        <div v-if="trend" class="stat-card__trend" :class="`stat-card__trend--${trend.direction}`">
          <i :class="trend.direction === 'up' ? 'pi pi-arrow-up-right' : 'pi pi-arrow-down-right'" />
          {{ trend.value }}
        </div>
      </div>
      <div class="stat-card__data">
        <span class="stat-card__value">{{ value }}</span>
        <span class="stat-card__label">{{ label }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stat-card {
  position: relative;
  background: var(--mc-bg-surface);
  backdrop-filter: var(--mc-glass-blur);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius);
  overflow: hidden;
  transition:
    border-color var(--mc-transition-speed),
    box-shadow var(--mc-transition-speed),
    transform var(--mc-transition-speed);
}

.stat-card:hover {
  border-color: var(--mc-border-strong);
  box-shadow: var(--mc-shadow-glow);
  transform: translateY(-2px);
}

/* Top edge gradient bar */
.stat-card__accent {
  height: 2px;
  background: linear-gradient(to right, var(--mc-accent), transparent 80%);
  opacity: 0.5;
  transition: opacity var(--mc-transition-speed);
}

.stat-card:hover .stat-card__accent {
  opacity: 1;
}

.stat-card__content {
  padding: 1.25rem;
}

.stat-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.stat-card__icon-box {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: var(--mc-accent-subtle);
  border: 1px solid var(--mc-border);
  border-radius: 10px;
  font-size: 1.25rem;
}

.stat-card__trend {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-family: var(--mc-font-mono);
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
}

.stat-card__trend--up {
  color: var(--mc-success);
  background: color-mix(in srgb, var(--mc-success) 10%, transparent);
}

.stat-card__trend--down {
  color: var(--mc-danger);
  background: color-mix(in srgb, var(--mc-danger) 10%, transparent);
}

.stat-card__trend i {
  font-size: 0.625rem;
}

.stat-card__data {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.stat-card__value {
  font-family: var(--mc-font-display);
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  line-height: 1.1;
}

.stat-card__label {
  font-size: 0.8125rem;
  color: var(--mc-text-muted);
  font-weight: 400;
  letter-spacing: 0.01em;
}
</style>
