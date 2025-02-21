import './assets/base.css'

import { createApp } from 'vue'
import store from './store'
import Antd from 'ant-design-vue';
import App from './App.vue'

const app = createApp(App);

app.use(Antd).use(store).mount('#app')
