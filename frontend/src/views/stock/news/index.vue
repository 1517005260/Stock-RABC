<template>
  <div class="app-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>股票新闻</span>
          <div class="header-actions">
            <!-- 管理员操作按钮 -->
            <div v-if="isAdmin" class="admin-actions">
              <el-button
                type="success"
                @click="fetchLatestNews"
                :loading="fetchingNews"
                size="small"
              >
                <el-icon><Download /></el-icon>
                爬取最新新闻
              </el-button>
            </div>
            <el-button type="primary" @click="refreshNews">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-row :gutter="20" class="search-bar">
        <el-col :span="8">
          <el-input
            v-model="searchKeyword"
            placeholder="请输入搜索关键词"
            @keyup.enter="searchNews"
          >
            <template #append>
              <el-button @click="searchNews">
                <el-icon><Search /></el-icon>
              </el-button>
            </template>
          </el-input>
        </el-col>
        <el-col :span="6">
          <el-select v-model="selectedCategory" placeholder="选择分类" @change="searchNews">
            <el-option label="全部" value="" />
            <el-option label="公司新闻" value="company" />
            <el-option label="行业动态" value="industry" />
            <el-option label="政策法规" value="policy" />
            <el-option label="财经评论" value="comment" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            @change="searchNews"
          />
        </el-col>
      </el-row>

      <!-- 新闻列表 -->
      <div class="news-list" v-loading="loading">
        <div
          v-for="news in newsList"
          :key="news.id"
          class="news-item"
          @click="viewNews(news)"
        >
          <div class="news-content">
            <div class="news-title">
              {{ news.title }}
              <!-- 原文链接可用标识 -->
              <el-tag
                v-if="news.source_url || news.url"
                type="success"
                size="small"
                class="original-link-tag"
              >
                可查看原文
              </el-tag>
            </div>
            <div class="news-summary">{{ news.summary || '暂无摘要' }}</div>
            <div class="news-meta">
              <span class="news-source">{{ news.source }}</span>
              <span class="news-category">{{ getCategoryLabel(news.category) }}</span>
              <span class="news-time">{{ formatTime(news.publish_time) }}</span>
              <span class="news-views">阅读: {{ news.views || 0 }}</span>
            </div>
          </div>
          <div class="news-actions">
            <!-- 查看原文按钮 -->
            <el-button
              v-if="news.source_url || news.url"
              type="primary"
              size="small"
              @click.stop="openOriginalNews(news)"
            >
              <el-icon><Link /></el-icon>
              查看原文
            </el-button>

            <!-- 管理员删除按钮 -->
            <el-button
              v-if="isAdmin"
              text
              type="danger"
              @click.stop="confirmDeleteNews(news)"
              size="small"
            >
              <el-icon><Delete /></el-icon>
              删除
            </el-button>

            <!-- 普通用户操作 -->
            <el-button text @click.stop="shareNews(news)">
              <el-icon><Share /></el-icon>
              分享
            </el-button>
            <el-button text @click.stop="collectNews(news)">
              <el-icon><Star /></el-icon>
              收藏
            </el-button>
          </div>
        </div>

        <!-- 空状态 -->
        <el-empty v-if="!loading && !newsList.length" description="暂无新闻数据" />
      </div>

      <!-- 分页 -->
      <el-pagination
        v-if="total > 0"
        class="pagination"
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </el-card>
  </div>
</template>

<script>
import { Refresh, Search, Share, Star, Download, Delete, Link } from '@element-plus/icons-vue'
import { getLatestNews } from '@/api/stock'
import { fetchLatestNews as fetchNewsAPI, deleteNews as deleteNewsAPI } from '@/api/trading'

export default {
  name: 'StockNews',
  components: {
    Refresh,
    Search,
    Share,
    Star,
    Download,
    Delete,
    Link
  },
  data() {
    return {
      loading: false,
      fetchingNews: false,
      searchKeyword: '',
      selectedCategory: '',
      dateRange: null,
      newsList: [],
      currentPage: 1,
      pageSize: 20,
      total: 0
    }
  },
  computed: {
    // 检查是否是管理员
    isAdmin() {
      const currentUser = JSON.parse(sessionStorage.getItem('currentUser') || '{}')
      const userRoles = currentUser.roles || ''
      return userRoles.includes('超级管理员') || userRoles.includes('管理员')
    }
  },
  async created() {
    await this.loadNews()
  },
  methods: {
    async loadNews() {
      this.loading = true
      try {
        const params = {
          page: this.currentPage,
          limit: this.pageSize,
          keyword: this.searchKeyword,
          category: this.selectedCategory
        }

        if (this.dateRange && this.dateRange.length === 2) {
          params.start_date = this.dateRange[0].toISOString().split('T')[0]
          params.end_date = this.dateRange[1].toISOString().split('T')[0]
        }

        const response = await getLatestNews(params)
        if (response.data.code === 200) {
          this.newsList = response.data.data
          this.total = response.data.total || this.newsList.length
        }
      } catch (error) {
        console.error('获取新闻失败:', error)
        this.$message.error('获取新闻失败，请检查网络连接')
        this.newsList = []
        this.total = 0
      } finally {
        this.loading = false
      }
    },
    async searchNews() {
      this.currentPage = 1
      await this.loadNews()
    },
    async refreshNews() {
      await this.loadNews()
      this.$message.success('新闻已刷新')
    },
    handleSizeChange(size) {
      this.pageSize = size
      this.currentPage = 1
      this.loadNews()
    },
    handleCurrentChange(page) {
      this.currentPage = page
      this.loadNews()
    },
    viewNews(news) {
      if (news.source_url || news.url) {
        // 如果有外部链接，打开新窗口
        this.openOriginalNews(news)
      } else {
        // 否则跳转到内部详情页
        this.$router.push(`/stock/news/${news.id}`)
      }
    },

    openOriginalNews(news) {
      const url = news.source_url || news.url
      if (url) {
        // 在新标签页中打开原文链接
        window.open(url, '_blank', 'noopener,noreferrer')

        // 可选：记录点击统计
        this.trackNewsClick(news)
      } else {
        this.$message.warning('该新闻暂无原文链接')
      }
    },

    trackNewsClick(news) {
      // 增加阅读计数（可选功能）
      try {
        const clickedNews = JSON.parse(localStorage.getItem('clicked_news') || '[]')
        const existingIndex = clickedNews.findIndex(item => item.id === news.id)

        if (existingIndex >= 0) {
          clickedNews[existingIndex].clickCount = (clickedNews[existingIndex].clickCount || 0) + 1
          clickedNews[existingIndex].lastClicked = new Date().toISOString()
        } else {
          clickedNews.unshift({
            id: news.id,
            title: news.title,
            clickCount: 1,
            lastClicked: new Date().toISOString()
          })
        }

        // 保持最近100条点击记录
        if (clickedNews.length > 100) {
          clickedNews.splice(100)
        }

        localStorage.setItem('clicked_news', JSON.stringify(clickedNews))
      } catch (error) {
        console.warn('记录点击统计失败:', error)
      }
    },
    shareNews(news) {
      // 分享功能
      if (navigator.share) {
        navigator.share({
          title: news.title,
          text: news.summary,
          url: news.url || window.location.href
        })
      } else {
        // 复制到剪贴板
        navigator.clipboard.writeText(`${news.title} - ${news.url || window.location.href}`)
        this.$message.success('链接已复制到剪贴板')
      }
    },
    collectNews(news) {
      // 收藏功能
      const collected = JSON.parse(localStorage.getItem('collected_news') || '[]')
      const exists = collected.find(item => item.id === news.id)
      
      if (!exists) {
        collected.unshift(news)
        localStorage.setItem('collected_news', JSON.stringify(collected))
        this.$message.success('收藏成功')
      } else {
        this.$message.info('已经收藏过了')
      }
    },
    getCategoryLabel(category) {
      const categoryMap = {
        company: '公司新闻',
        industry: '行业动态',
        policy: '政策法规',
        comment: '财经评论'
      }
      return categoryMap[category] || '其他'
    },
    formatTime(timeStr) {
      if (!timeStr) return ''
      const date = new Date(timeStr)
      const now = new Date()
      const diff = now - date

      if (diff < 60000) { // 小于1分钟
        return '刚刚'
      } else if (diff < 3600000) { // 小于1小时
        return Math.floor(diff / 60000) + '分钟前'
      } else if (diff < 86400000) { // 小于1天
        return Math.floor(diff / 3600000) + '小时前'
      } else {
        return timeStr.substring(5, 16) // MM-DD HH:mm
      }
    },

    // 管理员功能方法

    // 爬取最新新闻
    async fetchLatestNews() {
      if (!this.isAdmin) {
        this.$message.error('权限不足')
        return
      }

      this.fetchingNews = true
      try {
        const response = await fetchNewsAPI({
          limit: 20
        })

        if (response.data.code === 200) {
          const savedCount = response.data.data?.saved_count || 0
          this.$message.success(response.data.msg || `成功爬取并保存了 ${savedCount} 条新闻`)

          // 刷新新闻列表
          await this.loadNews()
        } else {
          this.$message.warning(response.data.msg || '爬取新闻失败')
        }
      } catch (error) {
        console.error('爬取新闻失败:', error)
        this.$message.error('爬取新闻失败，请检查网络连接')
      } finally {
        this.fetchingNews = false
      }
    },

    // 确认删除新闻
    confirmDeleteNews(news) {
      if (!this.isAdmin) {
        this.$message.error('权限不足')
        return
      }

      this.$confirm(
        `确定要删除新闻"${news.title}"吗？删除后无法恢复。`,
        '删除确认',
        {
          confirmButtonText: '确定删除',
          cancelButtonText: '取消',
          type: 'warning',
          dangerouslyUseHTMLString: true
        }
      ).then(async () => {
        await this.deleteNews(news.id)
      }).catch(() => {
        // 用户取消删除
      })
    },

    // 删除新闻
    async deleteNews(newsId) {
      try {
        const response = await deleteNewsAPI(newsId)

        if (response.data.code === 200) {
          this.$message.success('新闻删除成功')
          // 刷新新闻列表
          await this.loadNews()
        } else {
          this.$message.error(response.data.msg || '删除新闻失败')
        }
      } catch (error) {
        console.error('删除新闻失败:', error)
        this.$message.error('删除新闻失败，请检查网络连接')
      }
    }
  }
}
</script>

<style scoped>
.app-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.admin-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-bar {
  margin-bottom: 20px;
}

.news-list {
  min-height: 400px;
}

.news-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px 0;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background-color 0.3s;
}

.news-item:hover {
  background-color: #f9f9f9;
}

.news-content {
  flex: 1;
  margin-right: 20px;
}

.news-title {
  font-size: 16px;
  font-weight: bold;
  line-height: 1.4;
  margin-bottom: 8px;
  color: #333;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.original-link-tag {
  flex-shrink: 0;
}

.news-summary {
  font-size: 14px;
  color: #666;
  line-height: 1.5;
  margin-bottom: 10px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.news-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #999;
}

.news-source {
  color: #1890ff;
  font-weight: 500;
}

.news-category {
  background-color: #f0f0f0;
  padding: 2px 6px;
  border-radius: 4px;
}

.news-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 120px;
}

.news-actions .el-button {
  width: 100%;
}

.news-actions .el-button--primary {
  margin-bottom: 8px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>