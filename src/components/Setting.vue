<template>
  <div class="app-container">
    <Sidebar />
    <Capsule />
  </div>
</template>

<script lang="ts">
  import Sidebar from './Sidebar.vue'
  import Capsule from './Capsule.vue'
  
  export default {
    name: 'Setting',
    components: {
      Sidebar,
      Capsule,
 
    }
  }
</script>

<style scoped>
.app-container {
  height: 100%;
  display: flex;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  min-height: 100vh;
}
</style>