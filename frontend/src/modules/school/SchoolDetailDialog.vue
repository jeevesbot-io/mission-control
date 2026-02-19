<script setup lang="ts">
import { computed } from 'vue'
import type { CalendarEvent, SchoolEmail, TodoistTask } from './store'

type ItemType = 'event' | 'email' | 'task'

const props = defineProps<{
  visible: boolean
  type: ItemType | null
  item: CalendarEvent | SchoolEmail | TodoistTask | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
}>()

const dialogVisible = computed({
  get: () => props.visible,
  set: (v) => emit('update:visible', v),
})

const title = computed(() => {
  if (!props.item || !props.type) return ''
  if (props.type === 'event') return (props.item as CalendarEvent).summary
  if (props.type === 'email') return (props.item as SchoolEmail).subject ?? 'No subject'
  return (props.item as TodoistTask).content
})

function formatDate(iso: string | null): string {
  if (!iso) return ''
  return new Date(iso).toLocaleString(undefined, {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatDateOnly(iso: string | null): string {
  if (!iso) return ''
  return new Date(iso + 'T00:00:00').toLocaleString(undefined, {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}
</script>

<template>
  <Teleport to="body">
    <div v-if="dialogVisible" class="sd-overlay" @click.self="dialogVisible = false">
      <div class="sd-dialog">
        <div class="sd-header">
          <span class="sd-type-badge">{{ type }}</span>
          <button class="sd-close" @click="dialogVisible = false">
            <i class="pi pi-times" />
          </button>
        </div>

        <h3 class="sd-title">{{ title }}</h3>

        <!-- Event details -->
        <template v-if="type === 'event' && item">
          <div class="sd-fields">
            <div class="sd-field" v-if="(item as CalendarEvent).child">
              <span class="sd-label">Child</span>
              <span class="sd-value">{{ (item as CalendarEvent).child }}</span>
            </div>
            <div class="sd-field" v-if="(item as CalendarEvent).all_day">
              <span class="sd-label">When</span>
              <span class="sd-value">All day — {{ formatDateOnly((item as CalendarEvent).start_date) }}</span>
            </div>
            <div class="sd-field" v-else-if="(item as CalendarEvent).start_datetime">
              <span class="sd-label">Start</span>
              <span class="sd-value">{{ formatDate((item as CalendarEvent).start_datetime) }}</span>
            </div>
            <div class="sd-field" v-if="!(item as CalendarEvent).all_day && (item as CalendarEvent).end_datetime">
              <span class="sd-label">End</span>
              <span class="sd-value">{{ formatDate((item as CalendarEvent).end_datetime) }}</span>
            </div>
          </div>
        </template>

        <!-- Email details -->
        <template v-if="type === 'email' && item">
          <div class="sd-fields">
            <div class="sd-field" v-if="(item as SchoolEmail).sender">
              <span class="sd-label">From</span>
              <span class="sd-value">{{ (item as SchoolEmail).sender }}</span>
            </div>
            <div class="sd-field" v-if="(item as SchoolEmail).child">
              <span class="sd-label">Child</span>
              <span class="sd-value">{{ (item as SchoolEmail).child }}</span>
            </div>
            <div class="sd-field" v-if="(item as SchoolEmail).school_id">
              <span class="sd-label">School</span>
              <span class="sd-value">{{ (item as SchoolEmail).school_id }}</span>
            </div>
            <div class="sd-field" v-if="(item as SchoolEmail).processed_at">
              <span class="sd-label">Received</span>
              <span class="sd-value">{{ formatDate((item as SchoolEmail).processed_at) }}</span>
            </div>
            <div class="sd-field sd-field--full" v-if="(item as SchoolEmail).preview">
              <span class="sd-label">Preview</span>
              <span class="sd-value sd-preview">{{ (item as SchoolEmail).preview }}</span>
            </div>
          </div>
        </template>

        <!-- Task details -->
        <template v-if="type === 'task' && item">
          <div class="sd-fields">
            <div class="sd-field" v-if="(item as TodoistTask).due_date">
              <span class="sd-label">Due</span>
              <span class="sd-value">{{ formatDateOnly((item as TodoistTask).due_date) }}</span>
            </div>
            <div class="sd-field sd-field--full" v-if="(item as TodoistTask).description">
              <span class="sd-label">Description</span>
              <span class="sd-value sd-preview">{{ (item as TodoistTask).description }}</span>
            </div>
          </div>
        </template>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.sd-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: sd-fade-in 0.15s ease-out;
}

@keyframes sd-fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

.sd-dialog {
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius);
  padding: 1.5rem;
  width: 90%;
  max-width: 520px;
  max-height: 80vh;
  overflow-y: auto;
  animation: sd-slide-up 0.2s ease-out;
}

@keyframes sd-slide-up {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}

.sd-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.sd-type-badge {
  font-family: var(--mc-font-mono);
  font-size: 0.65rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 0.15rem 0.5rem;
  border-radius: 99px;
  background: var(--mc-accent-subtle);
  color: var(--mc-accent);
}

.sd-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: none;
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  color: var(--mc-text-muted);
  cursor: pointer;
  transition: all var(--mc-transition-speed);
}

.sd-close:hover {
  border-color: var(--mc-border-strong);
  color: var(--mc-text);
}

.sd-title {
  font-family: var(--mc-font-display);
  font-size: 1.15rem;
  font-weight: 700;
  margin-bottom: 1.25rem;
  line-height: 1.3;
}

.sd-fields {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.sd-field {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
}

.sd-field--full {
  flex-direction: column;
  gap: 0.25rem;
}

.sd-label {
  font-family: var(--mc-font-mono);
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--mc-text-muted);
  min-width: 70px;
  flex-shrink: 0;
}

.sd-value {
  font-size: 0.875rem;
  color: var(--mc-text);
}

.sd-preview {
  font-size: 0.85rem;
  line-height: 1.5;
  color: var(--mc-text-muted);
  white-space: pre-wrap;
}
</style>
