<template>
  <a-config-provider :locale="locale">
    <a-spin :spinning="$store.state.isSpin" :indicator="myIndicator" tip="Loading" size="large" wrapperClassName="fixed-spin">
      <router-view />
    </a-spin>
  </a-config-provider>
</template>

<script lang="ts">
import zhCN from 'ant-design-vue/es/locale/zh_CN';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';
import { h } from 'vue';

dayjs.locale('zh-cn');

export default {
  name: 'App',
  data() {
    return {
      locale: zhCN,
    }
  },
  computed: {
    myIndicator() {
      return h('svg', {
        class: 'anticon-spin',
        viewBox: '0 0 1024 1024',
        xmlns: 'http://www.w3.org/2000/svg'
      }, [
        h('path', {
          fill: 'currentColor',
          d: 'M512 64a32 32 0 0 1 32 32v192a32 32 0 0 1-64 0V96a32 32 0 0 1 32-32m0 640a32 32 0 0 1 32 32v192a32 32 0 1 1-64 0V736a32 32 0 0 1 32-32m448-192a32 32 0 0 1-32 32H736a32 32 0 1 1 0-64h192a32 32 0 0 1 32 32m-640 0a32 32 0 0 1-32 32H96a32 32 0 0 1 0-64h192a32 32 0 0 1 32 32M195.2 195.2a32 32 0 0 1 45.248 0L376.32 331.008a32 32 0 0 1-45.248 45.248L195.2 240.448a32 32 0 0 1 0-45.248m452.544 452.544a32 32 0 0 1 45.248 0L828.8 783.552a32 32 0 0 1-45.248 45.248L647.744 692.992a32 32 0 0 1 0-45.248M828.8 195.264a32 32 0 0 1 0 45.184L692.992 376.32a32 32 0 0 1-45.248-45.248l135.808-135.808a32 32 0 0 1 45.248 0m-452.544 452.48a32 32 0 0 1 0 45.248L240.448 828.8a32 32 0 0 1-45.248-45.248l135.808-135.808a32 32 0 0 1 45.248 0'
        })
      ]);
    }
  },
}
</script>

<style>
.fixed-spin .ant-spin {
  position: fixed !important;
  top: 50% !important;
  left: 50% !important;
  transform: translate(-50%, -50%) !important;
  z-index: 9999 !important;
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: center !important;
}
.fixed-spin .ant-spin-blur {
  pointer-events: none;
}
.fixed-spin .ant-spin-dot {
  font-size: 42px !important;
  width: 42px !important;
  height: 42px !important;
  position: static !important;
  inset-inline-start: auto !important;
  display: block !important;
  margin: 0 !important;
}
.fixed-spin .ant-spin svg {
  width: 42px !important;
  height: 42px !important;
  display: block !important;
  animation: loading-rotate 2s linear infinite;
}
.fixed-spin .ant-spin svg path {
  fill: #409eff !important;
}
.fixed-spin .ant-spin-text {
  color: #409eff !important;
  font-size: 14px !important;
  margin-top: 32px !important;
  padding-top: 0 !important;
}
@keyframes loading-rotate {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
