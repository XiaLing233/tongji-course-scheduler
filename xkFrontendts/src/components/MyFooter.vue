<template>
    <a-layout>
        <a-layout-footer>
            <div class="text-center">
                <p>基于 <a href="https://github.com/me-shaon/GLWTPL" target="_blank" >GLWTPL</a> 开源</p>
                <p>数据来源：<a href="https://1.tongji.edu.cn" target="_blank">同济大学教学管理信息系统</a></p>
                <p>当前学期数据的更新时间：{{ $store.state.updateTime }}</p>
            </div>
        </a-layout-footer>
    </a-layout>
</template>

<script lang="ts">
import { errorNotify, successNotify } from '@/utils/notify';
import { isUpToDate } from '@/utils/misc';
import axios from 'axios';
import { Modal } from 'ant-design-vue';
import { ExclamationCircleOutlined } from '@ant-design/icons-vue';
import { createVNode } from 'vue';

export default {
    data() {
        return {
            // updateTime: ''
        }
    },
    mounted() {
        this.getUpdateTime();
    },
    methods: {
        async getUpdateTime() {
            try {
                const res = await axios({
                    method: 'get',
                    url: '/api/getLatestUpdateTime'
                });

                this.$store.commit("loadSolidifyTime");
                this.$store.commit("setLatestUpdateTime", res.data.data);

                if (this.$store.state.updateTime === '') {
                    // 初次加载，不弹窗
                    this.$store.commit("syncLatestData");
                    return;
                }
                else if (isUpToDate(this.$store.state.updateTime, res.data.data)) {
                    this.$store.commit("setDataOutdated", false);
                    return;
                }
                else {
                    this.$store.commit("setDataOutdated", true);
                    // 弹出确认框
                    Modal.confirm({
                        title: '数据过期提示',
                        icon: createVNode(ExclamationCircleOutlined),
                        content: '检测到后端课程数据已更新，您当前选择的课程基于旧版本数据。是否清除缓存并使用最新数据？',
                        okText: '清除缓存',
                        cancelText: '保留旧数据',
                        onOk: () => {
                            // 二次确认
                            Modal.confirm({
                                title: '确认清除缓存',
                                icon: createVNode(ExclamationCircleOutlined),
                                content: '清除缓存后，您当前选择的所有课程将被清空，此操作不可恢复。确定要继续吗？',
                                okText: '确定清除',
                                okType: 'danger',
                                cancelText: '取消',
                                onOk: () => {
                                    this.$store.commit("syncLatestData");
                                    successNotify("缓存已清除，请重新选择课程");
                                },
                                onCancel: () => {
                                    console.log("User cancelled cache clearing");
                                }
                            });
                        },
                        onCancel: () => {
                            console.log("User chose to keep old data");
                        }
                    });
                    console.log("Outdated!")
                }
                // this.updateTime = res.data.data;
            }
            catch (error: any) {
                // console.log("error:", error);
                errorNotify(error.response.data.msg);
            }
        }
    }
}
</script>