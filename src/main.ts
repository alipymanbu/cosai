import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import App from './App.vue'
import router from './router'
import './index.css'
import { useDataStore } from './stores/DataStore'

const app = createApp(App)

const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)

app.use(pinia)
app.use(router)

app.mount('#app')

// 挂载 DataStore 到 window 对象，方便其他组件访问
declare global {
  interface Window {
    __VUE_DATA_STORE__: ReturnType<typeof useDataStore>
  }
}

window.__VUE_DATA_STORE__ = useDataStore()
