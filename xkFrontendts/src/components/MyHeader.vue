<template>
    <a-layout-header class="flex flex-row justify-between items-center" style="background-color: #f6f8fa">
        <div class="bg-[url(../assets/myLogo.png)] bg-cover bg-center h-10 w-50"></div>
        <div class="float-right flex flex-row space-x-4">
            <div v-if="$store.state.flags.isDataOutdated">
                <a-button type="primary" danger @click="syncData">
                    <div class="flex flex-row space-x-2 items-center">
                        <p>同步最新数据</p>
                        <div><SyncOutlined /></div>
                    </div>
                </a-button>
            </div>
            <div>
                <a-dropdown>
                    <template #overlay>
                        <a-menu class="text-center">
                        <a-menu-item key="wakeUp" @click="wakeUpCSV">
                            <div class="flex flex-row space-x-2 items-center">
                                <p>WakeUp 课程表支持的 csv 格式</p>
                                <p><a href="https://www.wakeup.fun/" target="_blank">[官网]</a></p>
                            </div>
                        </a-menu-item>
                        <a-menu-item key="excel" @click="helpExcel">
                            <p>辅助选课的 xls 文件</p>
                        </a-menu-item>
                        </a-menu>
                    </template>
                    <a-button>
                        <div class="flex flex-row space-x-2 items-center">
                            <p>导出为</p>
                            <div><ExportOutlined /></div>
                        </div>
                    </a-button>
                </a-dropdown>
            </div>
            <div>
                <a-button @click="readTheDocs">
                    <div class="flex flex-row space-x-2 items-center">
                        <p>帮助文档</p>
                        <div><ReadOutlined /></div>
                    </div>
                </a-button>
            </div>
            <div>
                <a-dropdown>
                    <template #overlay>
                        <a-menu class="text-center">
                        <a-menu-item key="tongji">
                            <a href="https://1.tongji.edu.cn" target="_blank">1 系统</a>
                        </a-menu-item>
                        <a-menu-item key="wlc">
                            <a href="https://1.tongji.icu" target="_blank">乌龙茶</a>
                        </a-menu-item>
                        <a-menu-item key="github">
                            <div class="flex flex-row space-x-2 items-center">
                                <div><GithubOutlined /></div>
                                <div><a href="https://github.com/XiaLing233/tongji-course-scheduler" target="_blank" style="color: inherit">项目仓库</a></div>
                            </div>
                        </a-menu-item>
                        </a-menu>
                    </template>
                    <a-button>
                        <div class="flex flex-row space-x-2 items-center">
                            <p>友情链接</p>
                            <div><LinkOutlined /></div>
                        </div>

                    </a-button>
                </a-dropdown>
            </div>
        </div>
    </a-layout-header>
</template>

<script lang="ts">
import { ExportOutlined, GithubOutlined, CalendarOutlined, LinkOutlined, ReadOutlined, SyncOutlined, ExclamationCircleOutlined } from '@ant-design/icons-vue';
import { codesToJsonForCSV, jsonToCSV, downloadCSV } from '@/utils/csvRelated';
import { codesToJsonForXLS, jsonToXLS, downloadXLS } from '@/utils/xlsRelated';
import { errorNotify, successNotify } from '@/utils/notify';
import { Modal } from 'ant-design-vue';
import { createVNode } from 'vue';

export default {
    components: {
        ExportOutlined,
        GithubOutlined,
        ReadOutlined,
        LinkOutlined,
        CalendarOutlined,
        SyncOutlined
    },
    methods: {
        syncData() {
            Modal.confirm({
                title: '确认同步最新数据',
                icon: createVNode(ExclamationCircleOutlined),
                content: '同步最新数据后，您当前选择的所有课程将被清空，此操作不可恢复。确定要继续吗？',
                okText: '确定同步',
                okType: 'danger',
                cancelText: '取消',
                onOk: () => {
                    this.$store.commit("syncLatestData");
                    successNotify("已同步最新数据，请重新选择课程");
                },
                onCancel: () => {
                    console.log("User cancelled data sync");
                }
            });
        },
        wakeUpCSV() {
            const csv = codesToJsonForCSV(this.$store.state.commonLists.selectedCourses, this.$store.state.commonLists.stagedCourses);
            const csvString = jsonToCSV(csv);
            downloadCSV(csvString);
        },
        helpExcel() {
            const xls = codesToJsonForXLS(this.$store.state.commonLists.selectedCourses, this.$store.state.commonLists.stagedCourses);
            const xlsBlob = jsonToXLS(xls);
            downloadXLS(xlsBlob);
        },
        readTheDocs() {
            errorNotify("敬请期待");
        }
    }
}
</script>
