<template>
  <div v-if="store.availableTags.length" class="tag-filter">
    <span class="filter-label">Tags:</span>
    <button
      v-for="tag in store.availableTags"
      :key="tag"
      class="tag-btn"
      :class="{ active: store.filterTags.includes(tag) }"
      @click="toggleTag(tag)"
    >
      {{ tag }}
    </button>
    <button
      v-if="store.filterTags.length"
      class="clear-btn"
      @click="store.setTagFilter([])"
    >
      clear
    </button>
  </div>
</template>

<script setup lang="ts">
import { useWarRoomStore } from '../store'

const store = useWarRoomStore()

function toggleTag(tag: string) {
  const current = store.filterTags
  if (current.includes(tag)) {
    store.setTagFilter(current.filter((t) => t !== tag))
  } else {
    store.setTagFilter([...current, tag])
  }
}
</script>

<style scoped>
.tag-filter {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  align-items: center;
}

.filter-label {
  font-size: 0.7rem;
  color: var(--mc-text-muted);
  font-family: var(--mc-font-mono);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.tag-btn {
  padding: 2px 8px;
  border-radius: 20px;
  font-size: 0.68rem;
  font-family: var(--mc-font-mono);
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.04);
  color: var(--mc-text-muted);
  cursor: pointer;
  transition: all var(--mc-transition-speed);
}
.tag-btn:hover { background: rgba(255,255,255,0.08); color: var(--mc-text); }
.tag-btn.active {
  border-color: var(--mc-accent);
  background: var(--mc-accent-subtle);
  color: var(--mc-accent);
}

.clear-btn {
  font-size: 0.65rem;
  color: var(--mc-danger);
  background: none;
  border: none;
  cursor: pointer;
  font-family: var(--mc-font-mono);
  padding: 0 4px;
}
</style>
