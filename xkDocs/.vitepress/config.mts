import { defineConfig } from 'vitepress'

// https://vitepress.vuejs.org/config/app-configs
export default defineConfig({
  title: "同济排课助手",
  description: "同济大学选课辅助工具文档",
  base: '/docs/',
  lang: 'zh-CN',
  
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: '首页', link: '/' },
      { text: '用户指南', link: '/user/' },
      { text: '开发者文档', link: '/developer/' }
    ],

    sidebar: {
      '/user/': [
        {
          text: '用户指南',
          collapsed: false,
          items: [
            { text: '概述', link: '/user/' },
            { text: '选择基本信息', link: '/user/major' },
            { text: '选择课程', link: '/user/opt' },
            { text: '导出与其他工具', link: '/user/export' },
            { text: '课程信息同步', link: '/user/sync' }
          ]
        }
      ],
      '/developer/': [
        {
          text: '开发者文档',
          collapsed: false,
          items: [
            { text: '概述', link: '/developer/' },
            { text: '如何构建', link: '/developer/how2build' },
            { text: '如何开发', link: '/developer/how2dev' }
          ]
        }
      ]
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/XiaLing233/tongji-course-scheduler' }
    ],

    editLink: {
      pattern: 'https://github.com/XiaLing233/tongji-course-scheduler/edit/master/xkDocs/docs/:path',
      text: '在 GitHub 上编辑此页'
    },

    lastUpdated: {
      text: '最后更新于',
      formatOptions: {
        dateStyle: 'short',
        timeStyle: 'medium'
      }
    },

    search: {
      provider: 'local',
      options: {
        translations: {
          button: {
            buttonText: '搜索文档',
            buttonAriaLabel: '搜索文档'
          },
          modal: {
            noResultsText: '无法找到相关结果',
            resetButtonTitle: '清除查询条件',
            footer: {
              selectText: '选择',
              navigateText: '切换',
              closeText: '关闭'
            }
          }
        }
      }
    },

    docFooter: {
      prev: '上一页',
      next: '下一页'
    },

    outline: [2, 3],
    
    outlineTitle: '页面导航',

    returnToTopLabel: '回到顶部',
    sidebarMenuLabel: '菜单',
    darkModeSwitchLabel: '主题',
    lightModeSwitchTitle: '切换到浅色模式',
    darkModeSwitchTitle: '切换到深色模式'
  }
})