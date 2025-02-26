<template>
    <a-layout>
        <a-layout-footer>
            <div class="text-center">
                <p>基于 <a href="https://github.com/me-shaon/GLWTPL" target="_blank" >GLWTPL</a> 开源</p>
                <p>数据来源：<a href="https://1.tongji.edu.cn" target="_blank">同济大学教学管理信息系统</a></p>
                <p>当前学期数据的更新时间：{{ updateTime }}</p>
            </div>
        </a-layout-footer>
    </a-layout>
</template>

<script lang="ts">
import { errorNotify } from '@/utils/errorNotify';
import axios from 'axios';

export default {
    data() {
        return {
            updateTime: ''
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
                this.updateTime = res.data.data;
            }
            catch (error: any) {
                // console.log("error:", error);
                errorNotify(error.response.data.msg);
            }
        }
    }
}
</script>