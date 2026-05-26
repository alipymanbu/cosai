<template>
  <div class="tug"></div>
</template>
<script lang="ts">
import { defineComponent } from 'vue';
export default defineComponent({
  name: 'Tug'
});
</script>
<style scoped>
.tug {
  width: 100%;
  height: 100%;
  background-color: transparent;
}
.tug:hover {
  background-color: rgba(0, 0, 255, 0.2);
}
</style>