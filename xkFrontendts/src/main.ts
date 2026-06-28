import './assets/base.css'

import { createApp } from 'vue'
import store from './store'
import Antd from 'ant-design-vue';
import App from './App.vue'
import router from './router'

const app = createApp(App);

app.use(Antd).use(store).use(router).mount('#app')
