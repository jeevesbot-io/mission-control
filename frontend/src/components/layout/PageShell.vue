<template>
  <div class="page-shell">
    <slot />
  </div>
</template>

<style scoped>
.page-shell {
  padding: var(--mc-page-padding);
  height: 100%;
  animation: mc-fade-up 0.35s ease-out;
}
</style>
