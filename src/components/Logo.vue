<template>
  <div class="logo" v-if="logoLoaded" ref="logoRef">
    <img 
      :src="currentIcon" 
      alt="AI" 
      @load="handleLogoLoad" 
      @error="handleLogoError"
      @click="handleLogoClick"
    />
    <div class="toggle-btn" @click.stop="toggleLogoIcon">
      <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
        <path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/>
      </svg>
    </div>
    
    <FileMenu ref="fileMenuRef" @dialogStateChange="handleDialogStateChange" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useAiStore } from '@/stores/AiStore';
import { useDataStore } from '@/stores/DataStore';
import FileMenu from './FileMenu.vue';

const aiStore = useAiStore();
const dataStore = useDataStore();
const logoLoaded = ref(true);
const showAI = ref(true);
const logoRef = ref<HTMLElement | null>(null);
const fileMenuRef = ref<InstanceType<typeof FileMenu> | null>(null);

const toggleLogoIcon = () => {
  showAI.value = !showAI.value;
};

const handleLogoClick = () => {
  if (showAI.value) {
    aiStore.show();
  } else {
    if (fileMenuRef.value) {
      fileMenuRef.value.openMenu();
    }
  }
};

const currentIcon = computed(() => {
  return showAI.value ? '/ai.png' : '/文件.png';
});

const handleLogoLoad = () => {
  logoLoaded.value = true;
};

const handleLogoError = () => {
  logoLoaded.value = false;
};

const handleDialogStateChange = (isOpen: boolean) => {
  console.log('Dialog state changed:', isOpen);
};


</script>

<style scoped>
.logo {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  position: relative;
}

.logo img {
  width: 28px;
  height: 28px;
  object-fit: contain;
  transition: opacity 0.2s ease;
  margin-bottom: 4px;
}

.logo img:hover {
  opacity: 0.8;
}

.toggle-btn {
  width: 30px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-radius: 4px;
  transition: background-color 0.2s ease;
  color: #555;
  /* background: white; */
  /* border: 1px solid #e0e0e0; */
  
  &:hover {
    background-color: #e0e0e0;
  }
  
  svg {
    transition: transform 0.3s ease;
  }
}
</style>
