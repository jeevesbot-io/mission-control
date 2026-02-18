<template>
  <div class="soul-editor">
    <!-- File tab switcher -->
    <div class="file-tabs">
      <button
        v-for="f in FILES"
        :key="f"
        class="file-tab"
        :class="{ active: activeFile === f, dirty: dirtyFiles.has(f) }"
        @click="switchFile(f)"
      >
        {{ f }}
        <span v-if="dirtyFiles.has(f)" class="dirty-dot" title="Unsaved changes" />
      </button>
    </div>

    <div class="editor-body">
      <!-- Main editor pane -->
      <div class="editor-pane">
        <div v-if="loading" class="editor-loading">Loading…</div>
        <Textarea
          v-else
          v-model="drafts[activeFile]"
          class="soul-textarea"
          :rows="28"
          :placeholder="`Edit ${activeFile}…`"
          @input="markDirty"
        />
        <div class="editor-actions">
          <span v-if="saveError" class="save-error">{{ saveError }}</span>
          <button class="btn-secondary" :disabled="!dirtyFiles.has(activeFile)" @click="resetFile">Reset</button>
          <button class="btn-primary" :disabled="!dirtyFiles.has(activeFile) || saving" @click="saveFile">
            {{ saving ? 'Saving…' : 'Save' }}
          </button>
        </div>
      </div>

      <!-- Side panel: templates (SOUL.md only) + history -->
      <div v-if="activeFile === 'SOUL.md'" class="side-panel">
        <div class="side-tabs">
          <button class="side-tab" :class="{ active: sideTab === 'templates' }" @click="sideTab = 'templates'">Templates</button>
          <button class="side-tab" :class="{ active: sideTab === 'history' }" @click="loadHistory(); sideTab = 'history'">History</button>
        </div>

        <!-- Templates -->
        <div v-if="sideTab === 'templates'" class="side-content">
          <div
            v-for="tpl in templates"
            :key="tpl.name"
            class="template-card"
            :class="{ expanded: expandedTemplate === tpl.name }"
          >
            <div class="template-header" @click="toggleTemplate(tpl.name)">
              <span class="template-name">{{ tpl.name }}</span>
              <span class="template-toggle">{{ expandedTemplate === tpl.name ? '▲' : '▼' }}</span>
            </div>
            <p v-if="tpl.description" class="template-desc">{{ tpl.description }}</p>
            <div v-if="expandedTemplate === tpl.name" class="template-preview">
              <pre>{{ tpl.content.slice(0, 300) }}{{ tpl.content.length > 300 ? '…' : '' }}</pre>
              <button class="btn-apply" @click="applyTemplate(tpl.content)">Apply Template</button>
            </div>
          </div>
          <div v-if="!templates.length" class="side-empty">No templates available.</div>
        </div>

        <!-- History -->
        <div v-if="sideTab === 'history'" class="side-content">
          <div v-if="historyLoading" class="side-empty">Loading history…</div>
          <div v-else-if="!history.length" class="side-empty">No history yet.</div>
          <div
            v-else
            v-for="(entry, idx) in history"
            :key="idx"
            class="history-entry"
            :class="{ selected: previewIdx === idx }"
            @click="previewHistory(idx)"
          >
            <span class="history-time">{{ formatAge(entry.savedAt) }}</span>
            <span class="history-len">{{ entry.content.length }} chars</span>
          </div>
          <div v-if="previewIdx !== null" class="history-preview">
            <pre>{{ history[previewIdx].content.slice(0, 500) }}{{ history[previewIdx].content.length > 500 ? '…' : '' }}</pre>
            <div class="history-actions">
              <button class="btn-secondary" @click="previewIdx = null">Dismiss</button>
              <button class="btn-primary" @click="revertHistory(previewIdx)">Revert to this</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Side panel: history only for other files -->
      <div v-else class="side-panel">
        <div class="side-tabs">
          <button class="side-tab active" @click="loadHistory(); sideTab = 'history'">History</button>
        </div>
        <div class="side-content">
          <div v-if="historyLoading" class="side-empty">Loading history…</div>
          <div v-else-if="!history.length" class="side-empty">No history yet.</div>
          <div
            v-else
            v-for="(entry, idx) in history"
            :key="idx"
            class="history-entry"
            :class="{ selected: previewIdx === idx }"
            @click="previewHistory(idx)"
          >
            <span class="history-time">{{ formatAge(entry.savedAt) }}</span>
            <span class="history-len">{{ entry.content.length }} chars</span>
          </div>
          <div v-if="previewIdx !== null && history[previewIdx]" class="history-preview">
            <pre>{{ history[previewIdx].content.slice(0, 500) }}{{ history[previewIdx].content.length > 500 ? '…' : '' }}</pre>
            <div class="history-actions">
              <button class="btn-secondary" @click="previewIdx = null">Dismiss</button>
              <button class="btn-primary" @click="revertHistory(previewIdx!)">Revert to this</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import Textarea from 'primevue/textarea'
import { useApi } from '@/composables/useApi'

type FileName = 'SOUL.md' | 'IDENTITY.md' | 'USER.md' | 'AGENTS.md'

const FILES: FileName[] = ['SOUL.md', 'IDENTITY.md', 'USER.md', 'AGENTS.md']

interface HistoryEntry { savedAt: string; content: string }
interface SoulTemplate { name: string; description: string; content: string }

const api = useApi()

const activeFile = ref<FileName>('SOUL.md')
const drafts = reactive<Record<FileName, string>>({
  'SOUL.md': '', 'IDENTITY.md': '', 'USER.md': '', 'AGENTS.md': '',
})
const originals = reactive<Record<FileName, string>>({
  'SOUL.md': '', 'IDENTITY.md': '', 'USER.md': '', 'AGENTS.md': '',
})
const dirtyFiles = ref<Set<FileName>>(new Set())
const loading = ref(false)
const saving = ref(false)
const saveError = ref('')

const sideTab = ref<'templates' | 'history'>('templates')
const templates = ref<SoulTemplate[]>([])
const expandedTemplate = ref<string | null>(null)
const history = ref<HistoryEntry[]>([])
const historyLoading = ref(false)
const previewIdx = ref<number | null>(null)

async function loadFile(name: FileName) {
  loading.value = true
  try {
    const data = await api.get<{ content: string }>(`/api/warroom/workspace-file?name=${name}`)
    drafts[name] = data.content
    originals[name] = data.content
    dirtyFiles.value.delete(name)
  } catch {
    drafts[name] = ''
    originals[name] = ''
  } finally {
    loading.value = false
  }
}

async function switchFile(name: FileName) {
  activeFile.value = name
  if (!originals[name]) await loadFile(name)
  // reset history panel state on file switch
  history.value = []
  previewIdx.value = null
  sideTab.value = name === 'SOUL.md' ? 'templates' : 'history'
}

function markDirty() {
  dirtyFiles.value = new Set([...dirtyFiles.value, activeFile.value])
}

function resetFile() {
  drafts[activeFile.value] = originals[activeFile.value]
  dirtyFiles.value.delete(activeFile.value)
  dirtyFiles.value = new Set(dirtyFiles.value)
}

async function saveFile() {
  saving.value = true
  saveError.value = ''
  try {
    await api.put(`/api/warroom/workspace-file?name=${activeFile.value}`, { content: drafts[activeFile.value] })
    originals[activeFile.value] = drafts[activeFile.value]
    dirtyFiles.value.delete(activeFile.value)
    dirtyFiles.value = new Set(dirtyFiles.value)
  } catch (e: unknown) {
    saveError.value = e instanceof Error ? e.message : 'Save failed'
  } finally {
    saving.value = false
  }
}

async function loadHistory() {
  if (historyLoading.value) return
  historyLoading.value = true
  previewIdx.value = null
  try {
    history.value = await api.get<HistoryEntry[]>(`/api/warroom/workspace-file/history?name=${activeFile.value}`)
  } catch {
    history.value = []
  } finally {
    historyLoading.value = false
  }
}

function previewHistory(idx: number) {
  previewIdx.value = previewIdx.value === idx ? null : idx
}

async function revertHistory(idx: number) {
  if (!confirm('Revert to this version? Current content will be saved as a new history entry first.')) return
  try {
    const data = await api.post<{ content: string }>(`/api/warroom/workspace-file/revert?name=${activeFile.value}`, { index: idx })
    drafts[activeFile.value] = data.content
    originals[activeFile.value] = data.content
    dirtyFiles.value.delete(activeFile.value)
    dirtyFiles.value = new Set(dirtyFiles.value)
    previewIdx.value = null
    history.value = []
  } catch (e: unknown) {
    alert(e instanceof Error ? e.message : 'Revert failed')
  }
}

async function loadTemplates() {
  try {
    templates.value = await api.get<SoulTemplate[]>('/api/warroom/soul/templates')
  } catch {
    templates.value = []
  }
}

function toggleTemplate(name: string) {
  expandedTemplate.value = expandedTemplate.value === name ? null : name
}

function applyTemplate(content: string) {
  if (dirtyFiles.value.has('SOUL.md') && !confirm('Apply template? This will replace your current draft.')) return
  drafts['SOUL.md'] = content
  dirtyFiles.value = new Set([...dirtyFiles.value, 'SOUL.md' as FileName])
}

function formatAge(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const m = Math.floor(diff / 60000)
  if (m < 1) return 'just now'
  if (m < 60) return `${m}m ago`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h ago`
  return `${Math.floor(h / 24)}d ago`
}

onMounted(async () => {
  await loadFile('SOUL.md')
  await loadTemplates()
})
</script>

<style scoped>
.soul-editor { display: flex; flex-direction: column; gap: 0.75rem; height: 100%; }

.file-tabs {
  display: flex;
  gap: 0.25rem;
  border-bottom: 1px solid rgba(255,255,255,0.08);
  padding-bottom: 0;
}

.file-tab {
  position: relative;
  padding: 0.45rem 1rem;
  font-size: 0.78rem;
  font-family: var(--mc-font-mono);
  background: none;
  border: 1px solid transparent;
  border-bottom: none;
  border-radius: var(--mc-radius-sm) var(--mc-radius-sm) 0 0;
  cursor: pointer;
  color: var(--mc-text-muted);
  transition: color var(--mc-transition-speed), background var(--mc-transition-speed);
  display: flex;
  align-items: center;
  gap: 0.35rem;
}
.file-tab:hover { color: var(--mc-text); background: rgba(255,255,255,0.04); }
.file-tab.active {
  color: var(--mc-text);
  background: var(--mc-bg-surface);
  border-color: rgba(255,255,255,0.08);
  border-bottom-color: var(--mc-bg-surface);
  margin-bottom: -1px;
}

.dirty-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--mc-accent);
  flex-shrink: 0;
}

.editor-body {
  display: flex;
  gap: 1rem;
  flex: 1;
  min-height: 0;
}

.editor-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-width: 0;
}

.editor-loading {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--mc-text-muted);
  font-size: 0.8rem;
}

:deep(.soul-textarea) {
  width: 100%;
  font-family: var(--mc-font-mono);
  font-size: 0.78rem;
  line-height: 1.6;
  resize: vertical;
  flex: 1;
}

.editor-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  justify-content: flex-end;
}

.save-error {
  flex: 1;
  font-size: 0.75rem;
  color: var(--mc-danger);
}

.side-panel {
  width: 260px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: var(--mc-radius-sm);
  background: var(--mc-bg-surface);
  overflow: hidden;
}

.side-tabs {
  display: flex;
  border-bottom: 1px solid rgba(255,255,255,0.08);
}

.side-tab {
  flex: 1;
  padding: 0.45rem;
  font-size: 0.73rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--mc-text-muted);
  transition: color var(--mc-transition-speed), background var(--mc-transition-speed);
}
.side-tab:hover { color: var(--mc-text); background: rgba(255,255,255,0.04); }
.side-tab.active { color: var(--mc-accent); background: var(--mc-accent-subtle); }

.side-content {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.side-empty {
  color: var(--mc-text-muted);
  font-size: 0.75rem;
  text-align: center;
  padding: 1rem 0;
}

/* Templates */
.template-card {
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: var(--mc-radius-sm);
  overflow: hidden;
}
.template-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0.6rem;
  cursor: pointer;
  transition: background var(--mc-transition-speed);
}
.template-header:hover { background: rgba(255,255,255,0.04); }
.template-name { font-size: 0.78rem; font-weight: 600; color: var(--mc-text); }
.template-toggle { font-size: 0.6rem; color: var(--mc-text-muted); }
.template-desc {
  font-size: 0.7rem;
  color: var(--mc-text-muted);
  padding: 0 0.6rem 0.4rem;
  margin: 0;
}
.template-preview {
  border-top: 1px solid rgba(255,255,255,0.06);
}
.template-preview pre {
  font-size: 0.65rem;
  font-family: var(--mc-font-mono);
  color: var(--mc-text-muted);
  padding: 0.5rem 0.6rem;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 120px;
  overflow-y: auto;
}
.btn-apply {
  display: block;
  width: 100%;
  padding: 0.4rem;
  background: var(--mc-accent-subtle);
  border: none;
  border-top: 1px solid rgba(255,255,255,0.06);
  color: var(--mc-accent);
  font-size: 0.73rem;
  font-weight: 600;
  cursor: pointer;
  transition: background var(--mc-transition-speed);
}
.btn-apply:hover { background: var(--mc-accent); color: #fff; }

/* History */
.history-entry {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.4rem 0.6rem;
  border-radius: var(--mc-radius-sm);
  cursor: pointer;
  border: 1px solid transparent;
  transition: background var(--mc-transition-speed);
}
.history-entry:hover { background: rgba(255,255,255,0.04); }
.history-entry.selected { background: var(--mc-accent-subtle); border-color: var(--mc-accent); }
.history-time { font-size: 0.72rem; color: var(--mc-text); }
.history-len { font-size: 0.65rem; color: var(--mc-text-muted); font-family: var(--mc-font-mono); }

.history-preview {
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: var(--mc-radius-sm);
  overflow: hidden;
  margin-top: 0.25rem;
}
.history-preview pre {
  font-size: 0.65rem;
  font-family: var(--mc-font-mono);
  color: var(--mc-text-muted);
  padding: 0.5rem;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 120px;
  overflow-y: auto;
}
.history-actions {
  display: flex;
  gap: 0.4rem;
  padding: 0.4rem;
  border-top: 1px solid rgba(255,255,255,0.06);
  background: rgba(0,0,0,0.1);
  justify-content: flex-end;
}

/* Reused buttons */
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
.btn-secondary:disabled { opacity: 0.4; cursor: not-allowed; }
</style>
