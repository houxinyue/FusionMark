<template>
  <n-config-provider :theme="fusionMarkTheme" :theme-overrides="fusionMarkThemeOverrides">
    <n-message-provider>
      <n-dialog-provider>
        <n-loading-bar-provider>
          <div class="app">
            <AppHeader />
            <main class="main">
              <router-view />
            </main>
            <AppFooter />
          </div>
        </n-loading-bar-provider>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import AppHeader from '@/components/layout/AppHeader.vue'
import AppFooter from '@/components/layout/AppFooter.vue'
import { fusionMarkTheme, fusionMarkThemeOverrides } from '@/theme/naiveTheme'
</script>

<style scoped>
.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: transparent;
}

.main {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
</style>
