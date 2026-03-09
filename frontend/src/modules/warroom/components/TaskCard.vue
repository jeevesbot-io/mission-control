<template>
  <div
    class="task-card"
    :class="[`priority-${task.priority}`, { 'is-done': task.status === 'done', 'is-in-progress': task.status === 'in-progress', 'is-blocked': blocked }]"
    :style="projectAccentStyle"
    :data-task-id="task.id"
    @click="$emit('click', task)"
  >
    <div class="task-card-header">
      <ProjectBadge v-if="project" :project="project" />
      <span v-if="blocked" class="blocked-badge" title="Blocked by dependencies">
        <i class="pi pi-lock" style="font-size: 0.6rem"></i>
      </span>
      <span v-if="task.status === 'in-progress'" class="status-dot" title="In progress" />
    </div>

    <p class="task-title">{{ task.title }}</p>

    <p v-if="task.description" class="task-description">{{ task.description }}</p>

    <!-- Result / error for done tasks -->
    <div v-if="task.status === 'done' && (task.result || task.error)" class="task-result">
      <span v-if="task.error" class="result-error">{{ task.error }}</span>
      <span v-else-if="task.result" class="result-ok">{{ task.result }}</span>
    </div>

    <div class="task-footer">
      <span class="priority-pill" :class="`priority-pill-${task.priority}`">{{ task.priority }}</span>
      <span v-if="task.skill" class="meta-chip">{{ task.skill }}</span>
      <span v-if="task.references?.length" class="meta-chip">{{ task.references.length }} ref{{ task.references.length !== 1 ? 's' : '' }}</span>
      <span v-if="task.schedule && task.schedule !== 'asap'" class="meta-chip schedule">
        {{ scheduleLabel }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useWarRoomStore } from '../store'
import type { Task } from '../store'
import ProjectBadge from './ProjectBadge.vue'

const COLOR_MAP: Record<string, string> = {
  purple: 'rgba(167,139,250,0.5)',
  pink:   'rgba(244,114,182,0.5)',
  green:  'rgba(52,211,153,0.5)',
  blue:   'rgba(96,165,250,0.5)',
  amber:  'rgba(251,191,36,0.5)',
  indigo: 'rgba(129,140,248,0.5)',
  red:    'rgba(248,113,113,0.5)',
  orange: 'rgba(251,146,60,0.5)',
  cyan:   'rgba(34,211,238,0.5)',
  yellow: 'rgba(253,224,71,0.5)',
}

const props = defineProps<{ task: Task }>()
defineEmits<{ (e: 'click', task: Task): void }>()

const store = useWarRoomStore()

const project = computed(() => props.task.project
  ? store.projects.find((p) => p.id === props.task.project) ?? null
  : null,
)

const blocked = computed(() => store.isTaskBlocked(props.task))

const projectAccentStyle = computed(() => {
  if (!project.value) return {}
  const color = COLOR_MAP[project.value.color] ?? COLOR_MAP['amber']
  return { '--card-accent': color }
})

const scheduleLabel = computed(() => {
  const s = props.task.schedule
  if (!s || s === 'asap') return ''
  if (s === 'next-heartbeat') return '⟳ heartbeat'
  try {
    return new Date(s).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  } catch {
    return s
  }
})
</script>

<style scoped>
.task-card {
  background: var(--mc-bg-elevated);
  border: 1px solid var(--mc-border);
  border-left: 3px solid var(--card-accent, var(--mc-color-amber-accent));
  border-radius: var(--mc-radius-sm);
  padding: 0.75rem;
  cursor: pointer;
  transition: background var(--mc-transition-speed), transform var(--mc-transition-speed), border-color var(--mc-transition-speed);
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.task-card:hover {
  background: var(--mc-bg-hover);
  border-color: var(--mc-border-strong);
  transform: translateY(-1px);
}
.task-card.is-in-progress {
  animation: mc-pulse-subtle 2s ease-in-out infinite;
}
.task-card.is-done {
  opacity: 0.65;
}
.task-card.is-blocked {
  opacity: 0.55;
  border-left-color: var(--mc-color-red-accent);
}

.task-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 18px;
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--mc-accent);
  flex-shrink: 0;
  animation: mc-glow-pulse 1.5s ease-in-out infinite;
}

.task-title {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--mc-text);
  line-height: 1.35;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.task-description {
  font-size: 0.72rem;
  color: var(--mc-text-muted);
  line-height: 1.4;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.task-result {
  font-size: 0.7rem;
  font-family: var(--mc-font-mono);
  border-radius: 4px;
  padding: 4px 6px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.result-ok {
  color: var(--mc-success);
}
.result-error {
  color: var(--mc-danger);
}

.task-footer {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 2px;
}

.priority-pill {
  font-size: 0.6rem;
  font-family: var(--mc-font-mono);
  font-weight: 700;
  text-transform: uppercase;
  padding: 1px 5px;
  border-radius: 3px;
  letter-spacing: 0.05em;
}
.priority-pill-low    { background: var(--mc-bg-hover); color: var(--mc-text-muted); }
.priority-pill-medium { background: var(--mc-color-blue-bg); color: var(--mc-color-blue); }
.priority-pill-high   { background: var(--mc-color-amber-bg); color: var(--mc-color-amber); }
.priority-pill-urgent { background: var(--mc-color-red-bg); color: var(--mc-color-red); }

.meta-chip {
  font-size: 0.6rem;
  font-family: var(--mc-font-mono);
  color: var(--mc-text-muted);
  background: var(--mc-bg-inset);
  border: 1px solid var(--mc-border);
  padding: 1px 5px;
  border-radius: 3px;
}
.schedule {
  color: var(--mc-warning);
}

.blocked-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--mc-color-red-bg);
  color: var(--mc-color-red);
}
</style>
