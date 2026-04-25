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
    data() {
        return {
            // updateTime: ''
        }
    },
    mounted() {
        this.getUpdateTime();
    },
    methods: {
        waitForSpinEnd(): Promise<void> {
            return new Promise((resolve) => {
                if (!this.$store.state.isSpin) {
                    resolve();
                    return;
                }
                const unwatch = this.$watch(() => this.$store.state.isSpin, (newVal) => {
                    if (!newVal) {
                        unwatch();
                        resolve();
                    }
                });
            });
        },
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
                    // 数据过期，调用智能同步逻辑
                    // 不在这里设置 isDataOutdated=true，由 handleSmartSync 根据用户选择决定
                    await this.handleSmartSync();
                }
            }
            catch (error: unknown) {
                const err = error as { response?: { data?: { msg?: string } } };
                errorNotify(err.response?.data?.msg || '获取更新时间失败');
            }
        },
        async handleSmartSync() {
            try {
                // 确保从 localStorage 加载课程数据
                this.$store.commit("loadSolidify");
                
                const stagedCourses = this.$store.state.commonLists.stagedCourses;
                const selectedCourses = this.$store.state.commonLists.selectedCourses;
                const calendarId = this.$store.state.majorSelected.calendarId;
                
                // 获取专业信息（用于判断 isExclusive）
                // 注意：majorSelected.major 实际上存储的是专业代码 (code)
                const majorInfo = this.$store.state.majorSelected.grade && this.$store.state.majorSelected.major
                    ? {
                        grade: this.$store.state.majorSelected.grade,
                        code: this.$store.state.majorSelected.major  // major 字段存储的是 code
                    }
                    : undefined;

                console.log("stagedCourses:", stagedCourses);
                console.log("selectedCourses:", selectedCourses);
                console.log("calendarId:", calendarId);

                // 如果没有课程，提示用户直接更新时间
                if (stagedCourses.length === 0 && selectedCourses.length === 0) {
                    this.$store.commit("syncLatestData");  // 静默更新时间
                    return;
                }

                console.log("majorInfo:", majorInfo);

                // 获取最新课程信息
                const latestCourses = await fetchLatestCourseInfo(calendarId, stagedCourses, selectedCourses, majorInfo);

                // 检测课程变更
                const syncResult = detectCourseChanges(
                    stagedCourses,
                    latestCourses,
                    selectedCourses,
                    this.$store.state.occupied
                );

                if (!syncResult.hasChanges) {
                    // 没有变更，静默更新时间
                    this.$store.commit("setUpdateTime", this.$store.state.latestUpdateTime);
                    this.$store.commit("setDataOutdated", false);
                    console.log("数据已更新但课程无变化，已自动同步时间");
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

                    await this.waitForSpinEnd();
                    successNotify(`已自动更新 ${stagedOnlyChanges.length} 门备选课程信息`);
                }

                // 2. 如果有已选变更，弹窗确认
                if (selectedChanges.length > 0) {
                    await this.waitForSpinEnd();
                    Modal.confirm({
                        title: '检测到课程变更',
                        icon: createVNode(ExclamationCircleOutlined),
                        content: createVNode('div', { style: { maxHeight: '500px', overflow: 'auto' } },
                            renderSyncChanges(selectedChanges)
                        ),
                        width: 700,
                        okText: '立即同步',
                        okType: 'primary',
                        cancelText: '稍后处理',
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

                                await this.waitForSpinEnd();
                                successNotify('同步成功！');
                            } catch (error) {
                                console.error('同步失败:', error);
                                await this.waitForSpinEnd();
                                errorNotify('同步失败，请稍后重试');
                            }
                        },
                        onCancel: () => {
                            // 用户拒绝同步，显示底部红色同步按钮作为降级入口
                            this.$store.commit("setDataOutdated", true);
                            console.log("用户选择稍后处理课程同步");
                        }
                    });
                } else {
                    // 没有需要用户确认的已选变更（可能已静默更新待选），标记为已同步
                    this.$store.commit("setDataOutdated", false);
                }

            } catch (error) {
                console.error('智能同步失败:', error);

                // 降级方案：提供清除缓存选项
                await this.waitForSpinEnd();
                Modal.confirm({
                    title: '数据过期提示',
                    icon: createVNode(ExclamationCircleOutlined),
                    content: '检测到后端课程数据已更新，但无法自动同步课程信息。您可以选择清除缓存并使用最新数据，或稍后手动同步。',
                    okText: '清除缓存',
                    okType: 'danger',
                    cancelText: '稍后处理',
                    onOk: async () => {
                        this.$store.commit("syncLatestData");
                        await this.waitForSpinEnd();
                        successNotify("缓存已清除，请重新选择课程");
                    }
                });
            }
        }
    }
}
</script>