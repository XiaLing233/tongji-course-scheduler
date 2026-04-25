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
                                <p><a href="https://www.wakeup.fun/" target="_blank" @click.stop>[官网]</a></p>
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
                        <a-menu-item key="courseSystem">
                            <a href="https://tongji.xialing.icu" target="_blank">课程检索</a>
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
import { ExportOutlined, GithubOutlined, LinkOutlined, ReadOutlined, SyncOutlined, ExclamationCircleOutlined } from '@ant-design/icons-vue';
import { codesToJsonForCSV, jsonToCSV, downloadCSV } from '@/utils/csvRelated';
import { codesToJsonForXLS, jsonToXLS, downloadXLS } from '@/utils/xlsRelated';
import { errorNotify, successNotify } from '@/utils/notify';
import { Modal } from 'ant-design-vue';
import { createVNode } from 'vue';
import {
    fetchLatestCourseInfo,
    detectCourseChanges,
    applyCourseSync,
    rebuildOccupiedAndTimeTable
} from '@/utils/courseSync';
import { renderSyncChanges } from '@/utils/syncRender';
import { insertOccupied } from '@/utils/courseManipulate';
import type { occupyCell, courseOnTable } from '@/utils/myInterface';

export default {
    components: {
        ExportOutlined,
        GithubOutlined,
        ReadOutlined,
        LinkOutlined,
        SyncOutlined
    },
    methods: {
        async syncData() {
            try {
                // 获取当前的stagedCourses和selectedCourses
                const stagedCourses = this.$store.state.commonLists.stagedCourses;
                const selectedCourses = this.$store.state.commonLists.selectedCourses;
                const calendarId = this.$store.state.majorSelected.calendarId;

                if (!calendarId) {
                    errorNotify('未选择学期，无法同步');
                    return;
                }

                if (stagedCourses.length === 0 && selectedCourses.length === 0) {
                    // 没有课程，直接同步时间即可
                    Modal.confirm({
                        title: '确认同步最新数据',
                        icon: createVNode(ExclamationCircleOutlined),
                        content: '当前没有已选课程，确认同步更新时间？',
                        okText: '确定',
                        okType: 'primary',
                        cancelText: '取消',
                        onOk: () => {
                            this.$store.commit("syncLatestData");
                            successNotify("已同步最新数据");
                        }
                    });
                    return;
                }

                // 获取专业信息（用于判断 isExclusive）
                // 注意：majorSelected.major 实际上存储的是专业代码 (code)
                const majorInfo = this.$store.state.majorSelected.grade && this.$store.state.majorSelected.major
                    ? {
                        grade: this.$store.state.majorSelected.grade,
                        code: this.$store.state.majorSelected.major  // major 字段存储的是 code
                    }
                    : undefined;

                // 显示加载中
                this.$store.commit("setIsSpin", true);

                // 从后端获取最新课程信息
                const latestCourses = await fetchLatestCourseInfo(calendarId, stagedCourses, selectedCourses, majorInfo);

                // 检测课程变更
                const syncResult = detectCourseChanges(
                    stagedCourses,
                    latestCourses,
                    selectedCourses,
                    this.$store.state.occupied
                );

                this.$store.commit("setIsSpin", false);

                if (!syncResult.hasChanges) {
                    // 没有变更，直接更新时间
                    Modal.info({
                        title: '课程已是最新',
                        content: '所有课程信息均为最新版本，已自动更新同步时间。',
                        okText: '确定',
                        onOk: () => {
                            this.$store.commit("setUpdateTime", this.$store.state.latestUpdateTime);
                            this.$store.commit("setDataOutdated", false);
                            successNotify("已更新同步时间");
                        }
                    });
                    return;
                }

                // 拆分为已选变更和仅待选变更
                const selectedChanges = syncResult.changes.filter(c =>
                    selectedCourses.some((code: string) => code.startsWith(c.courseCode))
                );
                const stagedOnlyChanges = syncResult.changes.filter(c =>
                    !selectedCourses.some((code: string) => code.startsWith(c.courseCode))
                );

                // 1. 静默应用仅待选变更
                if (stagedOnlyChanges.length > 0) {
                    const { newStagedCourses, newSelectedCodes } = applyCourseSync(
                        stagedOnlyChanges,
                        stagedCourses,
                        selectedCourses,
                        latestCourses
                    );

                    const { occupied: newOccupied, timeTableData: newTimeTableData } = rebuildOccupiedAndTimeTable(
                        newSelectedCodes,
                        newStagedCourses
                    );

                    this.$store.commit("smartSyncCourses", {
                        newStagedCourses,
                        newSelectedCodes,
                        newOccupied,
                        newTimeTableData
                    });

                    successNotify(`已自动更新 ${stagedOnlyChanges.length} 门备选课程信息`);
                }

                // 2. 如果有已选变更，弹窗确认
                if (selectedChanges.length > 0) {
                    Modal.confirm({
                        title: '课程同步',
                        icon: createVNode(ExclamationCircleOutlined),
                        content: renderSyncChanges(selectedChanges),
                        width: 700,
                        bodyStyle: { maxHeight: '500px', overflow: 'auto' },
                        okText: '确认同步',
                        okType: 'primary',
                        cancelText: '取消',
                        onOk: async () => {
                            try {
                                // 使用最新的 store 状态（可能已被 stagedOnly 更新过）
                                const currentStaged = this.$store.state.commonLists.stagedCourses;
                                const currentSelected = this.$store.state.commonLists.selectedCourses;

                                const { newStagedCourses, newSelectedCodes } = applyCourseSync(
                                    selectedChanges,
                                    currentStaged,
                                    currentSelected,
                                    latestCourses
                                );

                                const { occupied: newOccupied, timeTableData: newTimeTableData } = rebuildOccupiedAndTimeTable(
                                    newSelectedCodes,
                                    newStagedCourses
                                );

                                this.$store.commit("smartSyncCourses", {
                                    newStagedCourses,
                                    newSelectedCodes,
                                    newOccupied,
                                    newTimeTableData
                                });

                                successNotify('同步成功！');
                            } catch (error) {
                                console.error('同步失败:', error);
                                errorNotify('同步失败，请重试');
                            }
                        },
                        onCancel: () => {
                            // 用户拒绝同步，保持底部红色按钮显示
                            this.$store.commit("setDataOutdated", true);
                            console.log("User cancelled smart sync");
                        }
                    });
                }

            } catch (error) {
                this.$store.commit("setIsSpin", false);
                console.error('获取课程信息失败:', error);
                
                // 如果获取失败，提供降级选项：清空所有课程
                Modal.confirm({
                    title: '无法获取最新课程信息',
                    icon: createVNode(ExclamationCircleOutlined),
                    content: '无法从服务器获取最新课程信息。您可以选择清空所有课程并同步，或稍后重试。',
                    okText: '清空并同步',
                    okType: 'danger',
                    cancelText: '稍后重试',
                    onOk: () => {
                        this.$store.commit("syncLatestData");
                        successNotify("已清空课程并同步最新数据");
                    }
                });
            }
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
            window.open('/docs/', '_blank');
        }
    }
}
</script>
