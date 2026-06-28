import './assets/base.css'

const APP_VERSION = '2.0'
if (localStorage.getItem('app_version') !== APP_VERSION) {
    localStorage.clear()
    localStorage.setItem('app_version', APP_VERSION)
}

import { createApp } from 'vue'
import store from './store'
import Antd from 'ant-design-vue';
import App from './App.vue'
import router from './router'

const app = createApp(App);

app.use(Antd).use(store).use(router).mount('#app')
