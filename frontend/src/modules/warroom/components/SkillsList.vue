<template>
  <div class="skills-list">
    <!-- Stats bar -->
    <div class="skills-stats">
      <span>{{ skills.length }} total</span>
      <span>{{ enabledCount }} enabled</span>
      <span>{{ managedCount }} managed</span>
      <span>{{ workspaceCount }} workspace</span>
    </div>

    <!-- Search -->
    <InputText v-model="search" placeholder="Search skills…" class="skills-search" />

    <!-- Managed section -->
    <div v-if="managedSkills.length" class="skill-section">
      <h3 class="section-heading">Managed</h3>
      <div v-for="skill in managedSkills" :key="skill.id" class="skill-row">
        <SkillCard
          :skill="skill"
          @toggle="toggleSkill"
          @delete="null"
        />
      </div>
    </div>

    <!-- Workspace section -->
    <div class="skill-section">
      <h3 class="section-heading">Workspace</h3>
      <div v-for="skill in workspaceSkills" :key="skill.id" class="skill-row">
        <SkillCard
          :skill="skill"
          :deletable="true"
          @toggle="toggleSkill"
          @delete="deleteSkill"
        />
      </div>

      <!-- Create new skill -->
      <div class="create-skill">
        <button class="btn-create" @click="showCreate = !showCreate">
          <McIcon name="sparkles" :size="14" />
          New skill
        </button>
        <div v-if="showCreate" class="create-form">
          <InputText v-model="createForm.name" placeholder="skill-name (slug)" />
          <InputText v-model="createForm.description" placeholder="Description" />
          <Textarea v-model="createForm.instructions" placeholder="Instructions (markdown)…" :rows="4" />
          <div class="create-actions">
            <button class="btn-secondary" @click="showCreate = false">Cancel</button>
            <button class="btn-primary" :disabled="!createForm.name.trim()" @click="submitCreate">Create</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="store.loading" class="loading-msg">Loading skills…</div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, ref } from 'vue'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import { useWarRoomStore } from '../store'
import type { Skill } from '../store'
import McIcon from '@/components/ui/McIcon.vue'
import { useApi } from '@/composables/useApi'

const store = useWarRoomStore()
const api = useApi()

// SkillCard sub-component — must be in <script setup> to be in template scope
const SkillCard = defineComponent({
  props: {
    skill: { type: Object as () => Skill, required: true },
    deletable: { type: Boolean, default: false },
  },
  emits: ['toggle', 'delete'],
  setup(props, { emit }) {
    const expanded = ref(false)
    const content = ref('')
    const innerApi = useApi()

    async function loadContent() {
      if (!expanded.value) { expanded.value = true; return }
      if (content.value) { expanded.value = false; return }
      try {
        const data = await innerApi.get<{ content: string }>(`/api/warroom/skills/${props.skill.id}/content`)
        content.value = data.content
      } catch {
        content.value = '# Error loading content'
      }
    }

    return () =>
      h('div', { class: 'skill-card' }, [
        h('div', { class: 'skill-card-main' }, [
          h('button', {
            class: ['toggle-btn', props.skill.enabled ? 'enabled' : 'disabled'],
            onClick: () => emit('toggle', props.skill.id, !props.skill.enabled),
            title: props.skill.enabled ? 'Disable' : 'Enable',
          }, props.skill.enabled ? '●' : '○'),
          h('div', { class: 'skill-info', onClick: loadContent, style: 'cursor:pointer' }, [
            h('span', { class: 'skill-name' }, props.skill.name),
            props.skill.description ? h('span', { class: 'skill-desc' }, props.skill.description) : null,
          ]),
          h('span', { class: ['source-badge', `source-${props.skill.source}`] }, props.skill.source),
          props.deletable
            ? h('button', {
                class: 'delete-btn',
                onClick: () => emit('delete', props.skill.id),
              }, '✕')
            : null,
        ]),
        expanded.value && content.value
          ? h('pre', { class: 'skill-content' }, content.value)
          : null,
      ])
  },
})

const search = ref('')
const showCreate = ref(false)
const createForm = ref({ name: '', description: '', instructions: '' })

const skills = computed(() => store.skills)
const enabledCount = computed(() => skills.value.filter((s) => s.enabled).length)
const managedCount = computed(() => skills.value.filter((s) => s.source === 'managed').length)
const workspaceCount = computed(() => skills.value.filter((s) => s.source === 'workspace').length)

const filtered = computed(() => {
  const q = search.value.toLowerCase()
  if (!q) return skills.value
  return skills.value.filter((s) =>
    s.name.toLowerCase().includes(q) || s.description.toLowerCase().includes(q),
  )
})

const managedSkills = computed(() => filtered.value.filter((s) => s.source === 'managed'))
const workspaceSkills = computed(() => filtered.value.filter((s) => s.source === 'workspace'))

onMounted(() => store.fetchSkills())

async function toggleSkill(id: string, enabled: boolean) {
  await store.toggleSkill(id, enabled)
}

async function deleteSkill(id: string) {
  if (confirm('Delete this workspace skill?')) {
    await store.deleteSkill(id)
  }
}

async function submitCreate() {
  if (!createForm.value.name.trim()) return
  await store.createSkill(createForm.value)
  createForm.value = { name: '', description: '', instructions: '' }
  showCreate.value = false
}
</script>


<style scoped>
.skills-list { display: flex; flex-direction: column; gap: 1rem; }

.skills-stats {
  display: flex;
  gap: 1rem;
  font-size: 0.73rem;
  font-family: var(--mc-font-mono);
  color: var(--mc-text-muted);
}

.skills-search { width: 100%; max-width: 320px; }

.skill-section { display: flex; flex-direction: column; gap: 0.4rem; }

.section-heading {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--mc-text-muted);
  font-family: var(--mc-font-mono);
  margin: 0 0 0.3rem;
}

:deep(.skill-card) {
  background: var(--mc-bg-surface);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: var(--mc-radius-sm);
  overflow: hidden;
}
:deep(.skill-card-main) {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.6rem 0.75rem;
}
:deep(.toggle-btn) {
  font-size: 1.1rem;
  background: none;
  border: none;
  cursor: pointer;
  flex-shrink: 0;
  width: 20px;
}
:deep(.toggle-btn.enabled)  { color: var(--mc-success); }
:deep(.toggle-btn.disabled) { color: var(--mc-text-muted); }
:deep(.skill-info) { flex: 1; display: flex; flex-direction: column; gap: 2px; }
:deep(.skill-name) { font-size: 0.82rem; font-weight: 600; color: var(--mc-text); }
:deep(.skill-desc) { font-size: 0.72rem; color: var(--mc-text-muted); }
:deep(.source-badge) {
  font-size: 0.6rem;
  font-family: var(--mc-font-mono);
  font-weight: 700;
  text-transform: uppercase;
  padding: 2px 6px;
  border-radius: 3px;
  flex-shrink: 0;
}
:deep(.source-managed)   { background: rgba(251,146,60,0.15); color: #fb923c; }
:deep(.source-workspace) { background: rgba(52,211,153,0.15); color: #34d399; }
:deep(.delete-btn) {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--mc-danger);
  font-size: 0.85rem;
  padding: 2px 4px;
}
:deep(.skill-content) {
  font-size: 0.72rem;
  font-family: var(--mc-font-mono);
  color: var(--mc-text-muted);
  background: rgba(0,0,0,0.2);
  padding: 0.75rem;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 200px;
  overflow-y: auto;
  border-top: 1px solid rgba(255,255,255,0.06);
}

.create-skill { margin-top: 0.5rem; }
.btn-create {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 5px 12px;
  font-size: 0.78rem;
  border: 1px dashed rgba(255,255,255,0.15);
  background: none;
  color: var(--mc-accent);
  border-radius: var(--mc-radius-sm);
  cursor: pointer;
  transition: background var(--mc-transition-speed);
}
.btn-create:hover { background: var(--mc-accent-subtle); }

.create-form {
  margin-top: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.75rem;
  background: var(--mc-bg-surface);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: var(--mc-radius-sm);
}

.create-actions { display: flex; gap: 0.5rem; justify-content: flex-end; }

.btn-primary {
  padding: 5px 14px; border-radius: var(--mc-radius-sm);
  background: var(--mc-accent); color: #fff; font-weight: 600; font-size: 0.78rem;
  border: none; cursor: pointer;
}
.btn-primary:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-secondary {
  padding: 5px 14px; border-radius: var(--mc-radius-sm);
  background: rgba(255,255,255,0.06); color: var(--mc-text); font-size: 0.78rem;
  border: 1px solid rgba(255,255,255,0.1); cursor: pointer;
}

.loading-msg { color: var(--mc-text-muted); font-size: 0.8rem; }
</style>
