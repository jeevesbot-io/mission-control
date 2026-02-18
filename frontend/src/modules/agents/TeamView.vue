<template>
  <div class="team-view">
    <div class="team-header mb-4">
      <h3>Digital Organization</h3>
      <p class="subtitle">Agent hierarchy, roles, and responsibilities</p>
    </div>

    <!-- Org Chart -->
    <Panel header="Team Structure" class="org-panel mb-4">
      <OrganizationChart :value="orgData" class="org-chart">
        <template #default="slotProps">
          <div class="org-node" :class="`org-node-${slotProps.node.type}`">
            <div class="org-node-icon">
              <i :class="slotProps.node.icon"></i>
            </div>
            <div class="org-node-content">
              <div class="org-node-name">{{ slotProps.node.label }}</div>
              <div class="org-node-role">{{ slotProps.node.role }}</div>
              <Tag
                v-if="slotProps.node.status"
                :value="slotProps.node.status"
                :severity="getStatusSeverity(slotProps.node.status)"
                class="mt-2"
                size="small"
              />
            </div>
          </div>
        </template>
      </OrganizationChart>
    </Panel>

    <!-- Agent Roster -->
    <Panel header="Agent Roster" class="roster-panel mb-4">
      <DataTable
        :value="agents"
        :loading="loading"
        stripedRows
        size="small"
        :paginator="agents.length > 10"
        :rows="10"
        :rowClass="getRowClass"
      >
        <Column field="id" header="Agent" sortable>
          <template #body="slotProps">
            <div class="agent-cell">
              <span class="agent-avatar" :style="{ backgroundColor: getAgentColor(slotProps.data.id) }">
                {{ getAgentInitials(slotProps.data.id) }}
              </span>
              <span>{{ slotProps.data.id }}</span>
            </div>
          </template>
        </Column>
        <Column field="role" header="Role" sortable />
        <Column field="model" header="Model" sortable>
          <template #body="slotProps">
            <code class="model-badge">{{ slotProps.data.model }}</code>
          </template>
        </Column>
        <Column field="workspace" header="Workspace" sortable>
          <template #body="slotProps">
            <span class="workspace-path">{{ getWorkspaceName(slotProps.data.workspace) }}</span>
          </template>
        </Column>
        <Column field="allowedAgents" header="Can Spawn" sortable>
          <template #body="slotProps">
            <Tag
              v-for="agentId in slotProps.data.allowedAgents"
              :key="agentId"
              :value="agentId"
              class="mr-1"
              severity="secondary"
              size="small"
            />
            <span v-if="!slotProps.data.allowedAgents || slotProps.data.allowedAgents.length === 0" class="text-muted">None</span>
          </template>
        </Column>
        <Column field="status" header="Status">
          <template #body="slotProps">
            <Tag
              :value="slotProps.data.status"
              :severity="getStatusSeverity(slotProps.data.status)"
            />
          </template>
        </Column>
      </DataTable>
    </Panel>

    <!-- Responsibilities Matrix -->
    <Panel header="Responsibilities" class="responsibilities-panel">
      <div class="responsibilities-grid">
        <Card v-for="agent in agentsWithRoles" :key="agent.id" class="responsibility-card">
          <template #title>
            <div class="responsibility-header">
              <span class="agent-avatar-small" :style="{ backgroundColor: getAgentColor(agent.id) }">
                {{ getAgentInitials(agent.id) }}
              </span>
              {{ agent.id }}
            </div>
          </template>
          <template #subtitle>
            {{ agent.role }}
          </template>
          <template #content>
            <ul class="responsibility-list">
              <li v-for="(resp, idx) in agent.responsibilities" :key="idx">
                <i class="pi pi-check-circle mr-2"></i>
                {{ resp }}
              </li>
            </ul>
            <div v-if="agent.skills && agent.skills.length > 0" class="skills-section mt-3">
              <strong>Skills:</strong>
              <div class="skills-tags mt-2">
                <Tag
                  v-for="skill in agent.skills"
                  :key="skill"
                  :value="skill"
                  severity="info"
                  size="small"
                  class="mr-1 mb-1"
                />
              </div>
            </div>
          </template>
        </Card>
      </div>
    </Panel>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import Panel from 'primevue/panel'
import OrganizationChart from 'primevue/organizationchart'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Card from 'primevue/card'
import Tag from 'primevue/tag'

interface Agent {
  id: string
  role: string
  model: string
  workspace: string
  allowedAgents?: string[]
  status: string
  responsibilities?: string[]
  skills?: string[]
}

const loading = ref(false)

// Organizational structure
const orgData = ref({
  label: 'Jeeves',
  type: 'lead',
  role: 'Personal Assistant & System Coordinator',
  icon: 'pi pi-home',
  status: 'active',
  children: [
    {
      label: 'Matron',
      type: 'specialist',
      role: 'School Communications',
      icon: 'pi pi-graduation-cap',
      status: 'active',
    },
    {
      label: 'The Archivist',
      type: 'specialist',
      role: 'Memory Curator',
      icon: 'pi pi-book',
      status: 'active',
    },
    {
      label: 'The Curator',
      type: 'specialist',
      role: 'Media Library Manager',
      icon: 'pi pi-video',
      status: 'active',
    },
    {
      label: 'The Foundry',
      type: 'team',
      role: 'Autonomous Builder',
      icon: 'pi pi-cog',
      status: 'scheduled',
      children: [
        { label: 'Scout', type: 'worker', role: 'Trend Discovery', icon: 'pi pi-search', status: 'active' },
        { label: 'Spec Writer', type: 'worker', role: 'Specifications', icon: 'pi pi-file-edit', status: 'active' },
        { label: 'Builder', type: 'worker', role: 'Implementation', icon: 'pi pi-wrench', status: 'active' },
      ],
    },
  ],
})

// Agent roster with full details
const agents = ref<Agent[]>([
  {
    id: 'main',
    role: 'System Coordinator',
    model: 'claude-sonnet-4-5',
    workspace: '/Users/jeeves/.openclaw/workspace',
    allowedAgents: ['matron', 'archivist', 'curator', 'foundry-blacksmith'],
    status: 'active',
  },
  {
    id: 'matron',
    role: 'School Communications Agent',
    model: 'claude-sonnet-4-5',
    workspace: '/Users/jeeves/.openclaw/workspace-matron',
    allowedAgents: ['archivist'],
    status: 'active',
  },
  {
    id: 'archivist',
    role: 'Memory Curator',
    model: 'claude-sonnet-4-5',
    workspace: '/Users/jeeves/.openclaw/workspace',
    allowedAgents: [],
    status: 'active',
  },
  {
    id: 'curator',
    role: 'Media Library Manager',
    model: 'claude-sonnet-4-5',
    workspace: '/Users/jeeves/.openclaw/workspace',
    allowedAgents: [],
    status: 'on-demand',
  },
  {
    id: 'foundry-blacksmith',
    role: 'Build Coordinator',
    model: 'claude-opus-4-6',
    workspace: '/Users/jeeves/.openclaw/workspace-foundry-blacksmith',
    allowedAgents: ['foundry-scout', 'foundry-spec', 'foundry-builder'],
    status: 'scheduled',
  },
  {
    id: 'foundry-scout',
    role: 'Trend Scout',
    model: 'claude-haiku-4',
    workspace: '/Users/jeeves/.openclaw/workspace-foundry-scout',
    allowedAgents: [],
    status: 'scheduled',
  },
  {
    id: 'foundry-spec',
    role: 'Specification Writer',
    model: 'claude-sonnet-4-5',
    workspace: '/Users/jeeves/.openclaw/workspace-foundry-spec',
    allowedAgents: [],
    status: 'scheduled',
  },
  {
    id: 'foundry-builder',
    role: 'MVP Builder',
    model: 'claude-opus-4-6',
    workspace: '/Users/jeeves/.openclaw/workspace-foundry-builder',
    allowedAgents: [],
    status: 'scheduled',
  },
])

// Agents with detailed responsibilities
const agentsWithRoles = computed(() => [
  {
    id: 'main',
    role: 'Personal Assistant & System Coordinator',
    responsibilities: [
      'Primary interface for all user interactions',
      'Coordinate sub-agent dispatching',
      'Memory management and recall',
      'Proactive task monitoring via heartbeats',
      'System administration and configuration',
    ],
    skills: ['web-search', 'email', 'calendar', 'reminders', 'all-tools'],
  },
  {
    id: 'matron',
    role: 'School Communications Agent',
    responsibilities: [
      'Monitor school email inbox',
      'Parse and classify school communications',
      'Extract events and deadlines',
      'Create calendar entries and tasks',
      'Daily digest and urgent alerts',
    ],
    skills: ['himalaya', 'gog-calendar', 'postgres', 'pdf-extraction'],
  },
  {
    id: 'archivist',
    role: 'Memory Curator',
    responsibilities: [
      'Process conversation history every 3 hours',
      'Extract significant items from sessions',
      'Maintain daily memory files',
      'Consolidate and curate MEMORY.md',
      'Pattern detection for automation',
      'Obsidian vault maintenance',
    ],
    skills: ['memory-search', 'obsidian-cli', 'sessions-history'],
  },
  {
    id: 'curator',
    role: 'Media Library Manager',
    responsibilities: [
      'Search and add movies to Radarr',
      'Search and add TV shows to Sonarr',
      'Trigger quality upgrades',
      'Weekly viewing recommendations',
      'Library health audits',
    ],
    skills: ['radarr-api', 'sonarr-api', 'plex-integration'],
  },
  {
    id: 'foundry',
    role: 'Autonomous Overnight Builder',
    responsibilities: [
      'Scan trending topics (X, Reddit, HN, ProductHunt)',
      'Score buildability and select one trend',
      'Write technical specifications',
      'Spawn coding agent to build MVP',
      'Deliver morning briefing with repo',
    ],
    skills: ['bird', 'web-search', 'aider', 'github', 'multi-agent-coordination'],
  },
])

function getStatusSeverity(status: string): string {
  const severityMap: Record<string, string> = {
    active: 'success',
    scheduled: 'info',
    'on-demand': 'secondary',
    idle: 'secondary',
    error: 'danger',
  }
  return severityMap[status] || 'secondary'
}

function getAgentColor(agentId: string): string {
  const colors: Record<string, string> = {
    main: '#3b82f6',
    matron: '#f97316',
    archivist: '#8b5cf6',
    curator: '#ec4899',
    'foundry-blacksmith': '#14b8a6',
    'foundry-scout': '#06b6d4',
    'foundry-spec': '#10b981',
    'foundry-builder': '#84cc16',
  }
  return colors[agentId] || '#6b7280'
}

function getAgentInitials(agentId: string): string {
  if (agentId === 'main') return 'J'
  return agentId
    .split('-')
    .map((w) => w[0].toUpperCase())
    .join('')
    .slice(0, 2)
}

function getWorkspaceName(workspace: string): string {
  return workspace.split('/').pop() || workspace
}

function getRowClass(data: Agent) {
  return data.status === 'active' ? 'row-active' : ''
}
</script>

<style scoped>
.team-view {
  padding: 2rem;
}

.team-header h3 {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
}

.subtitle {
  color: var(--text-color-secondary);
  margin: 0;
}

/* Org Chart */
.org-chart {
  overflow-x: auto;
}

.org-node {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: var(--surface-card);
  border: 1px solid var(--surface-border);
  border-radius: 8px;
  min-width: 200px;
}

.org-node-lead {
  border-color: var(--blue-500);
  background: linear-gradient(135deg, var(--surface-card) 0%, rgba(59, 130, 246, 0.1) 100%);
}

.org-node-specialist {
  border-color: var(--orange-500);
}

.org-node-team {
  border-color: var(--teal-500);
}

.org-node-worker {
  border-color: var(--surface-300);
}

.org-node-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 3rem;
  height: 3rem;
  border-radius: 50%;
  background: var(--primary-color);
  color: white;
  font-size: 1.5rem;
}

.org-node-content {
  flex: 1;
}

.org-node-name {
  font-weight: 600;
  font-size: 1.1rem;
}

.org-node-role {
  font-size: 0.85rem;
  color: var(--text-color-secondary);
  margin-top: 0.25rem;
}

/* Agent Roster */
.agent-cell {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.agent-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  color: white;
  font-weight: 600;
  font-size: 0.8rem;
}

.agent-avatar-small {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 50%;
  color: white;
  font-weight: 600;
  font-size: 0.7rem;
  margin-right: 0.5rem;
}

.model-badge {
  background: var(--surface-100);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
}

.workspace-path {
  font-family: monospace;
  font-size: 0.85rem;
  color: var(--text-color-secondary);
}

.text-muted {
  color: var(--text-color-secondary);
  font-style: italic;
}

.row-active {
  background: rgba(34, 197, 94, 0.05) !important;
}

/* Responsibilities */
.responsibilities-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.responsibility-card {
  height: 100%;
}

.responsibility-header {
  display: flex;
  align-items: center;
  font-size: 1.1rem;
}

.responsibility-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.responsibility-list li {
  display: flex;
  align-items: flex-start;
  padding: 0.5rem 0;
  color: var(--text-color);
}

.responsibility-list li i {
  color: var(--green-500);
  margin-top: 0.1rem;
}

.skills-section {
  padding-top: 1rem;
  border-top: 1px solid var(--surface-border);
}

.skills-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}
</style>
