<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { RouterLink } from 'vue-router'
import { useAgentsStore } from './store'
import { useWebSocket } from '@/composables/useWebSocket'
import type { AgentInfo } from './store'
import PageShell from '@/components/layout/PageShell.vue'
import McIcon from '@/components/ui/McIcon.vue'
import { getAgentIconName } from '@/composables/useIcons'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import Dialog from 'primevue/dialog'
import TeamView from './TeamView.vue'

// ── Agent group definitions ───────────────────────────────────────────────────
interface AgentGroup {
  id: string
  label: string
  orchestrator?: string // if set, first row in group is the parent/orchestrator
  members: string[]     // all agent IDs in this group
  collapsed: boolean
}

const GROUPS: AgentGroup[] = [
  {
    id: 'core',
    label: 'Core',
    members: ['main', 'matron', 'archivist', 'curator'],
    collapsed: false,
  },
  {
    id: 'job-search',
    label: 'Job Search',
    orchestrator: 'coordinator',
    members: ['coordinator', 'market-intel', 'app-tracker', 'cv-tailor', 'cover-letter', 'interview-prep', 'networking'],
    collapsed: true,
  },
  {
    id: 'foundry',
    label: 'The Foundry',
    orchestrator: 'foundry-blacksmith',
    members: ['foundry-blacksmith', 'foundry-scout', 'foundry-spec', 'foundry-builder', 'portfolio-curator'],
    collapsed: true,
  },
  {
    id: 'tier2',
    label: 'On-Demand',
    members: ['researcher', 'strategist', 'builder', 'scribe', 'designer', 'consultant'],
    collapsed: false,
  },
  {
    id: 'board',
    label: 'The Board',
    orchestrator: 'board-chair',
    members: ['board-chair', 'board-contrarian', 'board-risk', 'board-quant', 'board-stakeholder', 'board-strategy', 'board-ops'],
    collapsed: true,
  },
  {
    id: 'dev',
    label: 'Dev Swarm',
    orchestrator: 'dev-lead',
    members: ['dev-lead', 'dev-recon', 'dev-spec', 'dev-impl', 'dev-gate', 'dev-verify', 'dev-shipper'],
    collapsed: true,
  },
  {
    id: 'design',
    label: 'Design Studio',
    orchestrator: 'design-cd',
    members: ['design-cd', 'design-ui', 'design-copy', 'design-social', 'design-guard', 'design-qa'],
    collapsed: true,
  },
  {
    id: 'marketing',
    label: 'Marketing',
    orchestrator: 'mktg-director',
    members: ['mktg-director', 'mktg-pulse', 'mktg-strat', 'mktg-quill', 'mktg-canvas', 'mktg-herald', 'mktg-gauge', 'mktg-outpost'],
    collapsed: true,
  },
]

// Make groups reactive
const groups = ref<AgentGroup[]>(GROUPS.map(g => ({ ...g })))

// ── Store & websocket ─────────────────────────────────────────────────────────
const store = useAgentsStore()
const { subscribe } = useWebSocket()
const activeTab = ref(0)
const triggering = ref<string | null>(null)

// ── Trigger modal ─────────────────────────────────────────────────────────────
const triggerModal = ref(false)
const triggerTarget = ref<string | null>(null)
const triggerPrompt = ref('')
const triggerError = ref('')
const triggerSuccess = ref('')

function openTriggerModal(agentId: string) {
  triggerTarget.value = agentId
  triggerPrompt.value = ''
  triggerError.value = ''
  triggerSuccess.value = ''
  triggerModal.value = true
}

async function confirmTrigger() {
  if (!triggerTarget.value) return
  triggering.value = triggerTarget.value
  triggerError.value = ''
  triggerSuccess.value = ''
  const ok = await store.triggerAgent(triggerTarget.value, triggerPrompt.value)
  triggering.value = null
  if (ok) {
    triggerSuccess.value = `✓ ${triggerTarget.value} triggered successfully`
    await store.fetchAgents()
    setTimeout(() => { triggerModal.value = false }, 1500)
  } else {
    triggerError.value = 'Failed to trigger agent — check gateway connection'
  }
}

onMounted(() => {
  store.fetchAgents()
  store.fetchStats()
  store.fetchCron()
  subscribe('agents:activity', (data) => {
    store.addActivity(data as { event: string; agent_id: string; message: string })
    store.fetchAgents()
    store.fetchStats()
  })
})

// ── Agent lookup map ──────────────────────────────────────────────────────────
const agentMap = computed(() => {
  const m = new Map<string, AgentInfo>()
  for (const a of store.agents) m.set(a.agent_id, a)
  return m
})

// Any agents not covered by the groups go into an "Ungrouped" bucket
const ungroupedAgents = computed(() => {
  const covered = new Set(GROUPS.flatMap(g => g.members))
  return store.agents.filter(a => !covered.has(a.agent_id))
})

// ── Helpers ───────────────────────────────────────────────────────────────────
function toggleGroup(g: AgentGroup) {
  g.collapsed = !g.collapsed
}

function levelVariant(level: string | null): 'ok' | 'warn' | 'err' | 'muted' {
  if (!level) return 'muted'
  if (level === 'info') return 'ok'
  if (level === 'warning') return 'warn'
  if (level === 'error') return 'err'
  return 'muted'
}

function formatRelative(iso: string | null): string {
  if (!iso) return '—'
  const now = Date.now()
  const then = new Date(iso).getTime()
  const diff = now - then
  const mins = Math.round(diff / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.round(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.round(hours / 24)
  return `${days}d ago`
}

// kept for compatibility — modal is now preferred path
async function handleTrigger(agentId: string) {
  openTriggerModal(agentId)
}

function healthColor(rate: number): string {
  if (rate >= 90) return 'var(--mc-success)'
  if (rate >= 70) return 'var(--mc-warning)'
  return 'var(--mc-danger)'
}

// Summary stats for a group header (active count, any warnings)
function groupSummary(g: AgentGroup) {
  let active = 0, warned = 0, total = 0
  for (const id of g.members) {
    const a = agentMap.value.get(id)
    if (a) {
      total++
      if (a.warning_count > 0) warned++
      if (a.last_activity) {
        const age = Date.now() - new Date(a.last_activity).getTime()
        if (age < 86400000) active++ // active within 24h
      }
    }
  }
  return { active, warned, total, registered: g.members.length }
}
</script>

<template>
  <PageShell>
    <div class="ag">

      <!-- ── Page header ─────────────────────────────────────── -->
      <header class="ag__header">
        <div>
          <h2 class="ag__title">Agents</h2>
          <p class="ag__sub">Fleet status · logs · dispatch</p>
        </div>
      </header>

      <Tabs :value="activeTab" @update:value="(v: number) => activeTab = v">
        <TabList>
          <Tab :value="0">Fleet</Tab>
          <Tab :value="1">Team</Tab>
        </TabList>

        <TabPanels>

          <!-- ── Fleet tab ─────────────────────────────────── -->
          <TabPanel :value="0">
            <div class="ag__fleet">

              <!-- Stat strip -->
              <div class="ag__stats mc-stagger" v-if="store.stats">
                <div class="ag__stat">
                  <div class="ag__stat-icon" style="--ic: var(--mc-accent)">
                    <McIcon name="bot" :size="15" />
                  </div>
                  <div class="ag__stat-body">
                    <span class="ag__stat-val">{{ store.stats.unique_agents }}</span>
                    <span class="ag__stat-lbl">Logged agents</span>
                  </div>
                </div>
                <div class="ag__stat">
                  <div class="ag__stat-icon" style="--ic: var(--mc-info)">
                    <McIcon name="activity" :size="15" />
                  </div>
                  <div class="ag__stat-body">
                    <span class="ag__stat-val">{{ store.stats.entries_24h }}</span>
                    <span class="ag__stat-lbl">Entries today</span>
                  </div>
                </div>
                <div class="ag__stat">
                  <div class="ag__stat-icon" style="--ic: var(--mc-success)">
                    <McIcon name="heart-pulse" :size="15" />
                  </div>
                  <div class="ag__stat-body">
                    <span class="ag__stat-val" :style="{ color: healthColor(store.stats.health_rate) }">
                      {{ store.stats.health_rate }}%
                    </span>
                    <span class="ag__stat-lbl">Health</span>
                  </div>
                </div>
                <div class="ag__stat">
                  <div class="ag__stat-icon" style="--ic: var(--mc-warning)">
                    <McIcon name="alert-triangle" :size="15" />
                  </div>
                  <div class="ag__stat-body">
                    <span class="ag__stat-val">{{ store.stats.warning_count }}</span>
                    <span class="ag__stat-lbl">Warnings</span>
                  </div>
                </div>
              </div>

              <!-- ── Agent groups ─────────────────────────────── -->
              <div class="ag__groups">

                <div
                  v-for="group in groups"
                  :key="group.id"
                  class="ag__group"
                >
                  <!-- Group header row -->
                  <button
                    class="ag__group-header"
                    @click="toggleGroup(group)"
                  >
                    <McIcon
                      :name="group.collapsed ? 'chevron-right' : 'chevron-down'"
                      :size="14"
                      class="ag__group-chevron"
                    />
                    <span class="ag__group-label">{{ group.label }}</span>

                    <!-- Orchestrator badge if present -->
                    <span v-if="group.orchestrator" class="ag__group-orch mc-mono">
                      via {{ group.orchestrator }}
                    </span>

                    <!-- Member count -->
                    <span class="ag__group-count mc-mono">{{ group.members.length }}</span>

                    <!-- Warning indicator -->
                    <span
                      v-if="groupSummary(group).warned > 0"
                      class="ag__group-warn"
                      :title="`${groupSummary(group).warned} agent(s) with warnings`"
                    >
                      <McIcon name="alert-triangle" :size="12" />
                      {{ groupSummary(group).warned }}
                    </span>
                  </button>

                  <!-- Agent rows (collapsible) -->
                  <Transition name="ag-expand">
                    <div v-if="!group.collapsed" class="ag__group-body">

                      <!-- Column headers (once per group) -->
                      <div class="ag__row ag__row--head">
                        <span></span><!-- icon -->
                        <span>Agent</span>
                        <span>Status</span>
                        <span>Last message</span>
                        <span>Entries</span>
                        <span>Last seen</span>
                        <span></span><!-- actions -->
                      </div>

                      <div
                        v-for="(memberId, idx) in group.members"
                        :key="memberId"
                        class="ag__row"
                        :class="{
                          'ag__row--orchestrator': memberId === group.orchestrator,
                          'ag__row--sub': memberId !== group.orchestrator && group.orchestrator,
                        }"
                      >
                        <!-- Icon -->
                        <McIcon
                          :name="getAgentIconName(memberId)"
                          :size="14"
                          class="ag__row-icon"
                        />

                        <!-- Name -->
                        <div class="ag__row-name-cell">
                          <span v-if="memberId !== group.orchestrator && group.orchestrator" class="ag__row-indent" />
                          <RouterLink :to="`/agents/${memberId}`" class="ag__row-link">
                            {{ memberId }}
                          </RouterLink>
                        </div>

                        <!-- Status badge -->
                        <div>
                          <span
                            v-if="agentMap.get(memberId)"
                            class="ag__level-badge"
                            :class="`ag__level-badge--${levelVariant(agentMap.get(memberId)!.last_level)}`"
                          >
                            {{ agentMap.get(memberId)!.last_level ?? 'no data' }}
                          </span>
                          <span v-else class="ag__level-badge ag__level-badge--muted">no data</span>
                        </div>

                        <!-- Last message -->
                        <span class="ag__row-msg">
                          {{ agentMap.get(memberId)?.last_message ?? '—' }}
                        </span>

                        <!-- Entry count -->
                        <span class="ag__row-num mc-mono">
                          {{ agentMap.get(memberId)?.total_entries ?? '—' }}
                        </span>

                        <!-- Last seen -->
                        <span class="ag__row-time mc-mono">
                          {{ formatRelative(agentMap.get(memberId)?.last_activity ?? null) }}
                        </span>

                        <!-- Actions -->
                        <div class="ag__row-actions">
                          <RouterLink
                            v-if="agentMap.get(memberId)?.warning_count"
                            :to="{ path: `/agents/${memberId}`, query: { level: 'warning' } }"
                            class="ag__warn-link"
                            :title="`${agentMap.get(memberId)!.warning_count} warnings`"
                          >
                            <McIcon name="alert-triangle" :size="12" />
                            {{ agentMap.get(memberId)!.warning_count }}
                          </RouterLink>
                          <button
                            class="ag__trigger-btn"
                            :disabled="triggering === memberId"
                            :title="`Trigger ${memberId}`"
                            @click="handleTrigger(memberId)"
                          >
                            <McIcon
                              :name="triggering === memberId ? 'loader' : 'zap'"
                              :size="13"
                            />
                          </button>
                        </div>
                      </div>
                    </div>
                  </Transition>
                </div>

                <!-- Ungrouped agents (catch-all) -->
                <div v-if="ungroupedAgents.length > 0" class="ag__group">
                  <div class="ag__group-header ag__group-header--plain">
                    <McIcon name="help-circle" :size="14" class="ag__group-chevron" />
                    <span class="ag__group-label">Ungrouped</span>
                    <span class="ag__group-count mc-mono">{{ ungroupedAgents.length }}</span>
                  </div>
                  <div class="ag__group-body">
                    <div class="ag__row ag__row--head">
                      <span></span>
                      <span>Agent</span>
                      <span>Status</span>
                      <span>Last message</span>
                      <span>Entries</span>
                      <span>Last seen</span>
                      <span></span>
                    </div>
                    <div v-for="agent in ungroupedAgents" :key="agent.agent_id" class="ag__row">
                      <McIcon :name="getAgentIconName(agent.agent_id)" :size="14" class="ag__row-icon" />
                      <RouterLink :to="`/agents/${agent.agent_id}`" class="ag__row-link">{{ agent.agent_id }}</RouterLink>
                      <span class="ag__level-badge" :class="`ag__level-badge--${levelVariant(agent.last_level)}`">{{ agent.last_level ?? 'no data' }}</span>
                      <span class="ag__row-msg">{{ agent.last_message ?? '—' }}</span>
                      <span class="ag__row-num mc-mono">{{ agent.total_entries }}</span>
                      <span class="ag__row-time mc-mono">{{ formatRelative(agent.last_activity) }}</span>
                      <div class="ag__row-actions">
                        <button class="ag__trigger-btn" :disabled="triggering === agent.agent_id" @click="handleTrigger(agent.agent_id)">
                          <McIcon :name="triggering === agent.agent_id ? 'loader' : 'zap'" :size="13" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Cron schedule -->
              <div class="ag__card" v-if="store.cronJobs.length > 0">
                <div class="ag__card-header">
                  <McIcon name="clock" :size="14" class="ag__card-hicon" />
                  <span class="ag__card-htitle">Cron Schedule</span>
                  <span class="ag__badge mc-mono">{{ store.cronJobs.length }}</span>
                </div>
                <div class="ag__cron-table">
                  <div v-for="job in store.cronJobs" :key="job.agent_id" class="ag__cron-row">
                    <span class="ag__cron-dot" :class="job.enabled ? 'ag__cron-dot--on' : 'ag__cron-dot--off'" />
                    <span class="ag__cron-agent mc-mono">{{ job.agent_id }}</span>
                    <span class="ag__cron-schedule mc-mono">{{ job.schedule }}</span>
                    <span class="ag__cron-status" :class="job.enabled ? 'ag__cron-status--on' : 'ag__cron-status--off'">
                      {{ job.enabled ? 'active' : 'disabled' }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- Live activity -->
              <div class="ag__card" v-if="store.activityFeed.length > 0">
                <div class="ag__card-header">
                  <McIcon name="zap" :size="14" class="ag__card-hicon" />
                  <span class="ag__card-htitle">Live Activity</span>
                  <span class="ag__live-dot" />
                </div>
                <div class="ag__feed">
                  <div v-for="(event, i) in store.activityFeed.slice(0, 15)" :key="i" class="ag__feed-row">
                    <span class="ag__feed-agent mc-mono">{{ event.agent_id }}</span>
                    <span class="ag__feed-msg">{{ event.message }}</span>
                    <span class="ag__feed-time mc-mono">{{ formatRelative(event.timestamp ?? null) }}</span>
                  </div>
                </div>
              </div>

              <div v-if="store.error" class="ag__error">
                <McIcon name="alert-circle" :size="14" />
                {{ store.error }}
              </div>

            </div>
          </TabPanel>

          <!-- ── Team tab ───────────────────────────────────── -->
          <TabPanel :value="1">
            <TeamView />
          </TabPanel>

        </TabPanels>
      </Tabs>
    </div>
  </PageShell>

  <!-- ── Trigger modal ───────────────────────────────────── -->
  <Dialog v-model:visible="triggerModal" modal :closable="true" :style="{ width: '480px' }">
    <template #header>
      <div class="trig__header">
        <McIcon name="zap" :size="16" class="trig__header-icon" />
        <span>Trigger Agent</span>
        <span class="trig__agent-id mc-mono">{{ triggerTarget }}</span>
      </div>
    </template>

    <div class="trig__body">
      <label class="trig__label">Prompt <span class="trig__label-hint">(optional — leave blank for default heartbeat)</span></label>
      <textarea
        v-model="triggerPrompt"
        class="trig__textarea"
        rows="4"
        placeholder="e.g. Run your daily checks and report any anomalies…"
        @keydown.ctrl.enter="confirmTrigger"
      />

      <div v-if="triggerError" class="trig__error">
        <McIcon name="alert-circle" :size="14" />
        {{ triggerError }}
      </div>
      <div v-if="triggerSuccess" class="trig__success">
        <McIcon name="check-circle" :size="14" />
        {{ triggerSuccess }}
      </div>
    </div>

    <template #footer>
      <div class="trig__footer">
        <button class="trig__btn trig__btn--cancel" @click="triggerModal = false">Cancel</button>
        <button
          class="trig__btn trig__btn--confirm"
          :disabled="!!triggering"
          @click="confirmTrigger"
        >
          <McIcon :name="triggering ? 'loader' : 'zap'" :size="14" />
          {{ triggering ? 'Triggering…' : 'Trigger' }}
        </button>
      </div>
    </template>
  </Dialog>
</template>

<style scoped>
.ag {
  max-width: 1100px;
  display: flex;
  flex-direction: column;
  gap: 0;
}

/* ── Header ──────────────────────────────────────────────── */
.ag__header {
  margin-bottom: 1.25rem;
  animation: mc-fade-up 0.35s ease-out;
}
.ag__title {
  font-size: 1.5rem;
  font-weight: 600;
  letter-spacing: -0.02em;
}
.ag__sub {
  margin-top: 0.2rem;
  font-size: 0.8rem;
  color: var(--mc-text-muted);
}

/* ── Fleet wrapper ───────────────────────────────────────── */
.ag__fleet {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding-top: 1rem;
}

/* ── Stat strip ──────────────────────────────────────────── */
.ag__stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
}
@media (max-width: 600px) { .ag__stats { grid-template-columns: repeat(2, 1fr); } }

.ag__stat {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem 1rem;
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius);
  transition: border-color var(--mc-transition-speed);
}
.ag__stat:hover { border-color: var(--mc-border-strong); }

.ag__stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: var(--mc-radius-sm);
  background: color-mix(in srgb, var(--ic, var(--mc-accent)) 12%, transparent);
  color: var(--ic, var(--mc-accent));
  flex-shrink: 0;
}
.ag__stat-body { display: flex; flex-direction: column; gap: 0.1rem; }
.ag__stat-val {
  font-size: 1.25rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1;
}
.ag__stat-lbl {
  font-size: 0.68rem;
  color: var(--mc-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

/* ── Groups ──────────────────────────────────────────────── */
.ag__groups {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.ag__group {
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius);
  overflow: hidden;
}

.ag__group-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.7rem 1rem;
  background: var(--mc-bg-elevated);
  border: none;
  border-bottom: 1px solid transparent;
  color: var(--mc-text);
  cursor: pointer;
  text-align: left;
  transition: background var(--mc-transition-fast), border-color var(--mc-transition-fast);
}
.ag__group-header:hover { background: var(--mc-bg-hover); }
.ag__group-header--plain { cursor: default; }

.ag__group-chevron { color: var(--mc-text-muted); flex-shrink: 0; }

.ag__group-label {
  font-size: 0.825rem;
  font-weight: 600;
  flex: 1;
}

.ag__group-orch {
  font-size: 0.65rem;
  color: var(--mc-text-muted);
}

.ag__group-count {
  font-size: 0.65rem;
  color: var(--mc-text-muted);
  background: var(--mc-bg-inset);
  padding: 0.15rem 0.45rem;
  border-radius: var(--mc-radius-full);
  border: 1px solid var(--mc-border);
}

.ag__group-warn {
  display: flex;
  align-items: center;
  gap: 0.2rem;
  font-size: 0.65rem;
  color: var(--mc-warning);
}

/* ── Agent rows ──────────────────────────────────────────── */
.ag__group-body {
  display: flex;
  flex-direction: column;
}

.ag__row {
  display: grid;
  grid-template-columns: 20px 200px 80px 1fr 60px 90px 80px;
  align-items: center;
  gap: 0.625rem;
  padding: 0.5rem 1rem;
  border-bottom: 1px solid var(--mc-border);
  transition: background var(--mc-transition-fast);
}
.ag__row:last-child { border-bottom: none; }

.ag__row--head {
  font-size: 0.65rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--mc-text-muted);
  background: color-mix(in srgb, var(--mc-bg-elevated) 60%, transparent);
  padding-top: 0.4rem;
  padding-bottom: 0.4rem;
  border-bottom: 1px solid var(--mc-border);
}

.ag__row--orchestrator {
  background: color-mix(in srgb, var(--mc-accent) 4%, transparent);
}

.ag__row--sub {}

.ag__row:not(.ag__row--head):hover { background: var(--mc-bg-hover); }

.ag__row-icon { color: var(--mc-text-muted); justify-self: center; }

.ag__row-name-cell {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  min-width: 0;
}

.ag__row-indent {
  display: inline-block;
  width: 14px;
  height: 1px;
  border-left: 1px solid var(--mc-border-strong);
  border-bottom: 1px solid var(--mc-border-strong);
  margin-right: 2px;
  flex-shrink: 0;
  align-self: center;
}

.ag__row-link {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--mc-text);
  text-decoration: none;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  transition: color var(--mc-transition-fast);
}
.ag__row-link:hover { color: var(--mc-accent); }

/* Level badge */
.ag__level-badge {
  display: inline-block;
  font-size: 0.62rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 0.12rem 0.45rem;
  border-radius: var(--mc-radius-full);
}
.ag__level-badge--ok   { color: var(--mc-success); background: color-mix(in srgb, var(--mc-success) 12%, transparent); }
.ag__level-badge--warn { color: var(--mc-warning); background: color-mix(in srgb, var(--mc-warning) 12%, transparent); }
.ag__level-badge--err  { color: var(--mc-danger);  background: color-mix(in srgb, var(--mc-danger)  12%, transparent); }
.ag__level-badge--muted { color: var(--mc-text-muted); background: var(--mc-bg-elevated); }

.ag__row-msg  { font-size: 0.75rem; color: var(--mc-text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ag__row-num  { font-size: 0.72rem; color: var(--mc-text-muted); }
.ag__row-time { font-size: 0.7rem;  color: var(--mc-text-muted); }

.ag__row-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.375rem;
}

.ag__warn-link {
  display: flex; align-items: center; gap: 0.2rem;
  font-size: 0.65rem; color: var(--mc-warning);
  text-decoration: none; transition: opacity var(--mc-transition-fast);
}
.ag__warn-link:hover { opacity: 0.7; }

.ag__trigger-btn {
  display: flex; align-items: center; justify-content: center;
  width: 28px; height: 28px;
  background: var(--mc-accent-subtle);
  border: 1px solid color-mix(in srgb, var(--mc-accent) 40%, transparent);
  border-radius: var(--mc-radius-sm);
  color: var(--mc-accent);
  cursor: pointer;
  transition: background var(--mc-transition-fast), color var(--mc-transition-fast), border-color var(--mc-transition-fast), box-shadow var(--mc-transition-fast);
}
.ag__trigger-btn:hover {
  background: var(--mc-accent);
  border-color: var(--mc-accent);
  color: #000;
  box-shadow: 0 0 8px var(--mc-accent-glow);
}
.ag__trigger-btn:disabled { opacity: 0.35; cursor: not-allowed; }

/* ── Expand animation ────────────────────────────────────── */
.ag-expand-enter-active,
.ag-expand-leave-active {
  transition: max-height 0.22s ease, opacity 0.18s ease;
  overflow: hidden;
  max-height: 2000px;
}
.ag-expand-enter-from,
.ag-expand-leave-to {
  max-height: 0;
  opacity: 0;
}

/* ── Card (cron, feed) ───────────────────────────────────── */
.ag__card {
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius);
  overflow: hidden;
}
.ag__card-header {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--mc-border);
  background: var(--mc-bg-elevated);
}
.ag__card-hicon { color: var(--mc-text-muted); }
.ag__card-htitle { font-size: 0.8rem; font-weight: 600; flex: 1; }
.ag__badge {
  font-size: 0.65rem; color: var(--mc-text-muted);
  background: var(--mc-bg-inset); padding: 0.15rem 0.45rem;
  border-radius: var(--mc-radius-full); border: 1px solid var(--mc-border);
}
.ag__live-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--mc-success);
  box-shadow: 0 0 6px color-mix(in srgb, var(--mc-success) 60%, transparent);
  animation: mc-pulse-subtle 2s ease-in-out infinite;
}

.ag__cron-table { display: flex; flex-direction: column; }
.ag__cron-row {
  display: grid;
  grid-template-columns: 12px 180px 1fr auto;
  align-items: center; gap: 0.75rem;
  padding: 0.55rem 1rem;
  border-bottom: 1px solid var(--mc-border);
  transition: background var(--mc-transition-fast);
}
.ag__cron-row:last-child { border-bottom: none; }
.ag__cron-row:hover { background: var(--mc-bg-hover); }
.ag__cron-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.ag__cron-dot--on  { background: var(--mc-success); box-shadow: 0 0 4px color-mix(in srgb, var(--mc-success) 50%, transparent); }
.ag__cron-dot--off { background: var(--mc-text-muted); opacity: 0.4; }
.ag__cron-agent   { font-size: 0.78rem; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ag__cron-schedule { font-size: 0.75rem; color: var(--mc-text-muted); }
.ag__cron-status  { font-size: 0.65rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; padding: 0.12rem 0.45rem; border-radius: var(--mc-radius-full); }
.ag__cron-status--on  { color: var(--mc-success); background: color-mix(in srgb, var(--mc-success) 12%, transparent); }
.ag__cron-status--off { color: var(--mc-text-muted); background: var(--mc-bg-elevated); }

.ag__feed { display: flex; flex-direction: column; max-height: 260px; overflow-y: auto; }
.ag__feed-row {
  display: grid; grid-template-columns: 160px 1fr auto;
  align-items: center; gap: 0.75rem;
  padding: 0.45rem 1rem; border-bottom: 1px solid var(--mc-border);
  transition: background var(--mc-transition-fast);
}
.ag__feed-row:last-child { border-bottom: none; }
.ag__feed-row:hover { background: var(--mc-bg-hover); }
.ag__feed-agent { font-size: 0.72rem; color: var(--mc-accent); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ag__feed-msg   { font-size: 0.75rem; color: var(--mc-text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ag__feed-time  { font-size: 0.68rem; color: var(--mc-text-muted); white-space: nowrap; }

.ag__error {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: color-mix(in srgb, var(--mc-danger) 8%, transparent);
  border: 1px solid color-mix(in srgb, var(--mc-danger) 25%, transparent);
  border-radius: var(--mc-radius-sm);
  color: var(--mc-danger); font-size: 0.825rem;
}

/* ── Trigger modal ───────────────────────────────────────── */
.trig__header {
  display: flex; align-items: center; gap: 0.5rem;
}
.trig__header-icon { color: var(--mc-accent); }
.trig__agent-id {
  font-size: 0.75rem;
  color: var(--mc-text-muted);
  background: var(--mc-bg-inset);
  padding: 0.1rem 0.5rem;
  border-radius: var(--mc-radius-full);
  border: 1px solid var(--mc-border);
  margin-left: 0.25rem;
}

.trig__body { display: flex; flex-direction: column; gap: 0.75rem; }

.trig__label {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--mc-text);
}
.trig__label-hint {
  font-size: 0.72rem;
  color: var(--mc-text-muted);
  font-weight: 400;
}

.trig__textarea {
  width: 100%;
  background: var(--mc-bg-inset);
  border: 1px solid var(--mc-border-input);
  border-radius: var(--mc-radius-sm);
  color: var(--mc-text);
  font-family: var(--mc-font-body);
  font-size: 0.85rem;
  padding: 0.625rem 0.75rem;
  resize: vertical;
  min-height: 90px;
  transition: border-color var(--mc-transition-speed), box-shadow var(--mc-transition-speed);
  line-height: 1.5;
}
.trig__textarea:focus {
  outline: none;
  border-color: var(--mc-accent);
  box-shadow: 0 0 0 3px var(--mc-accent-glow);
}
.trig__textarea::placeholder { color: var(--mc-text-muted); opacity: 0.6; }

.trig__error {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.6rem 0.75rem;
  background: color-mix(in srgb, var(--mc-danger) 10%, transparent);
  border: 1px solid color-mix(in srgb, var(--mc-danger) 25%, transparent);
  border-radius: var(--mc-radius-sm);
  color: var(--mc-danger); font-size: 0.8rem;
}
.trig__success {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.6rem 0.75rem;
  background: color-mix(in srgb, var(--mc-success) 10%, transparent);
  border: 1px solid color-mix(in srgb, var(--mc-success) 25%, transparent);
  border-radius: var(--mc-radius-sm);
  color: var(--mc-success); font-size: 0.8rem;
}

.trig__footer { display: flex; justify-content: flex-end; gap: 0.5rem; }

.trig__btn {
  display: flex; align-items: center; gap: 0.375rem;
  padding: 0.5rem 1rem;
  border-radius: var(--mc-radius-sm);
  font-size: 0.825rem; font-weight: 500;
  cursor: pointer;
  transition: background var(--mc-transition-fast), color var(--mc-transition-fast), box-shadow var(--mc-transition-fast);
}
.trig__btn--cancel {
  background: transparent;
  border: 1px solid var(--mc-border);
  color: var(--mc-text-muted);
}
.trig__btn--cancel:hover { background: var(--mc-bg-hover); color: var(--mc-text); }

.trig__btn--confirm {
  background: var(--mc-accent);
  border: 1px solid var(--mc-accent);
  color: #000;
  font-weight: 600;
}
.trig__btn--confirm:hover { box-shadow: 0 0 10px var(--mc-accent-glow); }
.trig__btn--confirm:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
