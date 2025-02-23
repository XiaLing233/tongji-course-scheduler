<template>
    <a-layout-header class="flex flex-row justify-between items-center" style="background-color: #f6f8fa">
        <div class="bg-[url(../assets/logo.png)] bg-cover bg-center h-10 w-95"></div>
        <div class="float-right flex flex-row space-x-4">
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

<script>
import { ExportOutlined, GithubOutlined, CalendarOutlined, LinkOutlined, ReadOutlined } from '@ant-design/icons-vue';
import { codesToJsonForCSV, jsonToCSV, downloadCSV } from '@/utils/csvRelated';
import { codesToJsonForXLS, jsonToXLS, downloadXLS } from '@/utils/xlsRelated';
import { errorNotify } from '@/utils/errorNotify';

export default {
    components: {
        ExportOutlined,
        GithubOutlined,
        ReadOutlined,
        LinkOutlined,
        CalendarOutlined
    },
    methods: {
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
