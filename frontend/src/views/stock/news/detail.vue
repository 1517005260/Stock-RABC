<template>
  <div class="app-container">
    <el-card v-loading="loading">
      <!-- 返回按钮 -->
      <div class="back-button">
        <el-button @click="$router.go(-1)">
          <el-icon><ArrowLeft /></el-icon>
          返回新闻列表
        </el-button>
      </div>

      <!-- 新闻头部 -->
      <div class="news-header">
        <h1 class="news-title">{{ newsDetail.title }}</h1>
        <div class="news-meta">
          <span class="news-source">{{ newsDetail.source }}</span>
          <span class="news-time">{{ formatTime(newsDetail.publish_time) }}</span>
          <span class="news-views">阅读量: {{ newsDetail.views || 0 }}</span>
          <span class="news-category">{{ getCategoryLabel(newsDetail.category) }}</span>
        </div>
      </div>

      <!-- 新闻操作 -->
      <div class="news-actions">
        <el-button @click="shareNews">
          <el-icon><Share /></el-icon>
          分享
        </el-button>
        <el-button @click="collectNews">
          <el-icon><Star /></el-icon>
          {{ isCollected ? '已收藏' : '收藏' }}
        </el-button>
        <el-button v-if="newsDetail.source_url || newsDetail.url" @click="openOriginal">
          <el-icon><Link /></el-icon>
          查看原文
        </el-button>
      </div>

      <!-- 新闻内容 -->
      <div class="news-content">
        <div v-if="newsDetail.content" v-html="newsDetail.content"></div>
        <div v-else class="no-content">
          <p>{{ newsDetail.summary || '暂无详细内容' }}</p>
          <el-button v-if="newsDetail.source_url || newsDetail.url" type="primary" @click="openOriginal">
            点击查看原文
          </el-button>
        </div>
      </div>

      <!-- 相关标签 -->
      <div v-if="newsDetail.tags && newsDetail.tags.length" class="news-tags">
        <span class="tags-label">相关标签:</span>
        <el-tag
          v-for="tag in newsDetail.tags"
          :key="tag"
          class="tag-item"
          @click="searchByTag(tag)"
        >
          {{ tag }}
        </el-tag>
      </div>

      <!-- 相关股票 -->
      <div v-if="relatedStocks.length" class="related-stocks">
        <h3>相关股票</h3>
        <el-row :gutter="16">
          <el-col :span="8" v-for="stock in relatedStocks" :key="stock.ts_code">
            <el-card class="stock-card" @click="goToStock(stock)">
              <div class="stock-info">
                <div class="stock-name">{{ stock.name }}</div>
                <div class="stock-code">{{ stock.ts_code }}</div>
                <div class="stock-price" :class="getPriceClass(stock.pct_chg)">
                  {{ stock.current_price }}
                </div>
                <div class="stock-change" :class="getPriceClass(stock.pct_chg)">
                  {{ formatPercent(stock.pct_chg) }}
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 相关新闻 -->
      <div v-if="relatedNews.length" class="related-news">
        <h3>相关新闻</h3>
        <div class="related-news-list">
          <div
            v-for="news in relatedNews"
            :key="news.id"
            class="related-news-item"
            @click="viewRelatedNews(news)"
          >
            <div class="related-news-title">{{ news.title }}</div>
            <div class="related-news-meta">
              <span>{{ news.source }}</span>
              <span>{{ formatTime(news.publish_time) }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script>
import { ArrowLeft, Share, Star, Link } from '@element-plus/icons-vue'
import { getNewsDetail, getLatestNews } from '@/api/stock'

export default {
  name: 'NewsDetail',
  components: {
    ArrowLeft,
    Share,
    Star,
    Link
  },
  data() {
    return {
      loading: false,
      newsDetail: {},
      relatedNews: [],
      relatedStocks: [],
      isCollected: false
    }
  },
  async created() {
    await this.loadNewsDetail()
    this.checkIfCollected()
  },
  methods: {
    async loadNewsDetail() {
      this.loading = true
      try {
        const newsId = this.$route.params.id
        
        // 尝试从API获取新闻详情
        try {
          const response = await getNewsDetail(newsId)
          if (response.data.code === 200) {
            this.newsDetail = response.data.data
          } else {
            throw new Error('API返回错误')
          }
        } catch (apiError) {
          console.warn('API获取失败:', apiError)
          this.$message.error('新闻不存在或无法获取')
          return
        }

        // 获取相关新闻
        await this.loadRelatedNews()
        
        // 获取相关股票（基于新闻标签或关键词）
        this.loadRelatedStocks()

      } catch (error) {
        console.error('加载新闻详情失败:', error)
        this.$message.error('加载新闻详情失败')
      } finally {
        this.loading = false
      }
    },
    async loadRelatedNews() {
      try {
        const response = await getLatestNews({ limit: 5 })
        if (response.data.code === 200) {
          this.relatedNews = response.data.data.filter(news => news.id !== this.newsDetail.id)
        }
      } catch (error) {
        console.error('获取相关新闻失败:', error)
        this.relatedNews = []
      }
    },
    loadRelatedStocks() {
      this.relatedStocks = []
    },
    checkIfCollected() {
      const collected = JSON.parse(localStorage.getItem('collected_news') || '[]')
      this.isCollected = collected.some(item => item.id === this.newsDetail.id)
    },
    shareNews() {
      if (navigator.share) {
        navigator.share({
          title: this.newsDetail.title,
          text: this.newsDetail.summary,
          url: window.location.href
        })
      } else {
        navigator.clipboard.writeText(`${this.newsDetail.title} - ${window.location.href}`)
        this.$message.success('链接已复制到剪贴板')
      }
    },
    collectNews() {
      const collected = JSON.parse(localStorage.getItem('collected_news') || '[]')
      
      if (this.isCollected) {
        // 取消收藏
        const filtered = collected.filter(item => item.id !== this.newsDetail.id)
        localStorage.setItem('collected_news', JSON.stringify(filtered))
        this.isCollected = false
        this.$message.success('已取消收藏')
      } else {
        // 添加收藏
        collected.unshift(this.newsDetail)
        localStorage.setItem('collected_news', JSON.stringify(collected))
        this.isCollected = true
        this.$message.success('收藏成功')
      }
    },
    openOriginal() {
      const url = this.newsDetail.source_url || this.newsDetail.url
      if (url) {
        window.open(url, '_blank', 'noopener,noreferrer')
      } else {
        this.$message.warning('该新闻暂无原文链接')
      }
    },
    searchByTag(tag) {
      this.$router.push({
        path: '/stock/news',
        query: { keyword: tag }
      })
    },
    goToStock(stock) {
      this.$router.push(`/stock/detail/${stock.ts_code}`)
    },
    viewRelatedNews(news) {
      this.$router.push(`/stock/news/${news.id}`)
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
    getPriceClass(pctChg) {
      if (!pctChg) return ''
      return pctChg > 0 ? 'price-up' : pctChg < 0 ? 'price-down' : ''
    },
    formatPercent(value) {
      if (!value) return '--'
      const formatted = parseFloat(value).toFixed(2)
      return value > 0 ? `+${formatted}%` : `${formatted}%`
    },
    formatTime(timeStr) {
      if (!timeStr) return ''
      const date = new Date(timeStr)
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    }
  }
}
</script>

<style scoped>
.app-container {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.back-button {
  margin-bottom: 20px;
}

.news-header {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 2px solid #f0f0f0;
}

.news-title {
  font-size: 28px;
  font-weight: bold;
  line-height: 1.4;
  margin-bottom: 15px;
  color: #333;
}

.news-meta {
  display: flex;
  gap: 20px;
  font-size: 14px;
  color: #666;
  flex-wrap: wrap;
}

.news-source {
  color: #1890ff;
  font-weight: 500;
}

.news-category {
  background-color: #f0f0f0;
  padding: 2px 8px;
  border-radius: 4px;
}

.news-actions {
  margin-bottom: 30px;
  display: flex;
  gap: 10px;
}

.news-content {
  font-size: 16px;
  line-height: 1.8;
  color: #333;
  margin-bottom: 30px;
}

.news-content :deep(p) {
  margin-bottom: 16px;
}

.no-content {
  text-align: center;
  padding: 40px 20px;
  color: #666;
}

.news-tags {
  margin-bottom: 30px;
  padding: 20px;
  background-color: #f9f9f9;
  border-radius: 8px;
}

.tags-label {
  font-weight: bold;
  margin-right: 10px;
  color: #333;
}

.tag-item {
  margin-right: 8px;
  margin-bottom: 5px;
  cursor: pointer;
}

.related-stocks,
.related-news {
  margin-top: 40px;
  padding-top: 20px;
  border-top: 1px solid #f0f0f0;
}

.related-stocks h3,
.related-news h3 {
  margin-bottom: 20px;
  font-size: 18px;
  color: #333;
}

.stock-card {
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 16px;
}

.stock-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stock-info {
  text-align: center;
}

.stock-name {
  font-weight: bold;
  margin-bottom: 5px;
}

.stock-code {
  font-size: 12px;
  color: #999;
  margin-bottom: 8px;
}

.stock-price {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 3px;
}

.stock-change {
  font-size: 14px;
}

.related-news-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.related-news-item {
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background-color 0.3s;
}

.related-news-item:hover {
  background-color: #f9f9f9;
}

.related-news-title {
  font-size: 14px;
  font-weight: bold;
  margin-bottom: 5px;
  color: #333;
}

.related-news-meta {
  font-size: 12px;
  color: #999;
  display: flex;
  gap: 15px;
}

.price-up {
  color: #dd4b39;
}

.price-down {
  color: #00a65a;
}
</style>