<template>
  <div class="app-container">
    <!-- 市场概览 -->
    <el-row :gutter="20" class="market-overview">
      <el-col :span="6" v-for="index in marketIndices" :key="index.code">
        <el-card class="index-card">
          <div class="index-info">
            <div class="index-name">{{ index.name }}</div>
            <div class="index-value" :class="getPriceClass(index.pct_chg)">
              {{ index.current }}
            </div>
            <div class="index-change" :class="getPriceClass(index.pct_chg)">
              {{ formatChange(index.change) }} ({{ formatPercent(index.pct_chg) }})
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 热门股票 -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>今日涨幅榜</span>
              <el-button text @click="refreshHotStocks">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </template>
          <el-table
            :data="hotStocks"
            style="width: 100%"
            size="small"
            @row-click="goToStock"
            :row-style="{cursor: 'pointer'}"
          >
            <el-table-column prop="name" label="股票" width="80" />
            <el-table-column prop="close" label="现价" width="70" align="right">
              <template #default="scope">
                <span :class="getPriceClass(scope.row.pct_chg)">
                  {{ scope.row.close }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="pct_chg" label="涨幅" width="80" align="right">
              <template #default="scope">
                <span :class="getPriceClass(scope.row.pct_chg)">
                  {{ formatPercent(scope.row.pct_chg) }}
                </span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 实时新闻 -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>市场新闻</span>
              <el-button text @click="refreshNews">
                <el-icon><Refresh /></el-icon>
                更多
              </el-button>
            </div>
          </template>
          <div class="news-list">
            <div
              v-for="news in latestNews"
              :key="news.id"
              class="news-item"
              @click="viewNews(news)"
            >
              <div class="news-title">{{ news.title }}</div>
              <div class="news-meta">
                <span class="news-source">{{ news.source }}</span>
                <span class="news-time">{{ formatTime(news.publish_time) }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 我的自选股 -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>我的自选</span>
              <el-button text @click="goToWatchlist">
                <el-icon><Setting /></el-icon>
                管理
              </el-button>
            </div>
          </template>
          <div class="watchlist" v-if="watchlist.length">
            <div
              v-for="stock in watchlist"
              :key="stock.ts_code"
              class="watchlist-item"
              @click="goToStock(stock)"
            >
              <div class="stock-name">{{ stock.name }}</div>
              <div class="stock-price">
                <span :class="getPriceClass(stock.pct_chg)">
                  {{ stock.current_price }}
                </span>
                <span :class="getPriceClass(stock.pct_chg)" class="stock-change">
                  {{ formatPercent(stock.pct_chg) }}
                </span>
              </div>
            </div>
          </div>
          <div v-else class="empty-watchlist">
            <el-empty description="还没有添加自选股" />
            <el-button type="primary" @click="goToStockList">去选股</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 市场走势图表 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>大盘走势</span>
              <el-radio-group v-model="chartPeriod" size="small" @change="updateChart">
                <el-radio-button label="1D">日线</el-radio-button>
                <el-radio-button label="5D">5日</el-radio-button>
                <el-radio-button label="1M">月线</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <v-chart
            class="market-chart"
            :option="marketChartOption"
            :loading="chartLoading"
            autoresize
          />
        </el-card>
      </el-col>

      <!-- 涨跌分布 -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>涨跌分布</span>
          </template>
          <div class="market-stats">
            <div class="stat-item up">
              <div class="stat-number">{{ marketStats.up_count }}</div>
              <div class="stat-label">上涨</div>
            </div>
            <div class="stat-item down">
              <div class="stat-number">{{ marketStats.down_count }}</div>
              <div class="stat-label">下跌</div>
            </div>
            <div class="stat-item flat">
              <div class="stat-number">{{ marketStats.flat_count }}</div>
              <div class="stat-label">平盘</div>
            </div>
          </div>
          
          <!-- 资金流向 -->
          <div class="money-flow">
            <h4>资金流向</h4>
            <div class="flow-item">
              <span>主力净流入:</span>
              <span class="flow-value" :class="moneyFlow.main_flow > 0 ? 'price-up' : 'price-down'">
                {{ formatMoney(moneyFlow.main_flow) }}
              </span>
            </div>
            <div class="flow-item">
              <span>散户净流入:</span>
              <span class="flow-value" :class="moneyFlow.retail_flow > 0 ? 'price-up' : 'price-down'">
                {{ formatMoney(moneyFlow.retail_flow) }}
              </span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快捷操作 -->
    <el-card style="margin-top: 20px;">
      <template #header>
        <span>快捷操作</span>
      </template>
      <el-row :gutter="20">
        <el-col :span="4">
          <div class="quick-action" @click="goToStockList">
            <el-icon size="30"><TrendCharts /></el-icon>
            <div>股票列表</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="quick-action" @click="goToMarketNews">
            <el-icon size="30"><Document /></el-icon>
            <div>市场资讯</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="quick-action" @click="goToPortfolio">
            <el-icon size="30"><Wallet /></el-icon>
            <div>我的持仓</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="quick-action" @click="goToTradeHistory">
            <el-icon size="30"><List /></el-icon>
            <div>交易记录</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="quick-action" @click="goToRiskManagement">
            <el-icon size="30"><Warning /></el-icon>
            <div>风险管理</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="quick-action" @click="goToDataAnalysis">
            <el-icon size="30"><DataAnalysis /></el-icon>
            <div>数据分析</div>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script>
import { use } from "echarts/core"
import { CanvasRenderer } from "echarts/renderers"
import { LineChart, BarChart } from "echarts/charts"
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from "echarts/components"
import VChart from "vue-echarts"
import {
  Refresh,
  Setting,
  TrendCharts,
  Document,
  Wallet,
  List,
  Warning,
  DataAnalysis
} from '@element-plus/icons-vue'
import {
  getHotStocks,
  getLatestNews,
  getMarketOverview,
  getStockKlineData
} from '@/api/stock'
import wsService from '@/utils/websocket'

use([
  CanvasRenderer,
  LineChart,
  BarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

export default {
  name: 'StockDashboard',
  components: {
    VChart,
    Refresh,
    Setting,
    TrendCharts,
    Document,
    Wallet,
    List,
    Warning,
    DataAnalysis
  },
  data() {
    return {
      loading: false,
      chartLoading: false,
      chartPeriod: '1D',
      marketIndices: [],
      hotStocks: [],
      latestNews: [],
      watchlist: [],
      marketStats: {
        up_count: 0,
        down_count: 0,
        flat_count: 0
      },
      moneyFlow: {
        main_flow: 0,
        retail_flow: 0
      },
      marketChartData: [],
      refreshTimer: null
    }
  },
  computed: {
    marketChartOption() {
      if (!this.marketChartData || !Array.isArray(this.marketChartData) || !this.marketChartData.length) {
        return {}
      }
      
      // 过滤和验证数据
      const validData = this.marketChartData.filter(item => 
        item && 
        typeof item === 'object' && 
        item.date && 
        item.close != null && 
        !isNaN(parseFloat(item.close))
      )
      
      if (validData.length === 0) {
        return {}
      }
      
      const dates = validData.map(item => item.date)
      const values = validData.map(item => parseFloat(item.close))
      
      return {
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: dates
        },
        yAxis: {
          type: 'value',
          scale: true
        },
        series: [
          {
            name: '大盘走势',
            type: 'line',
            data: values.filter(val => val != null && !isNaN(val)),
            smooth: true,
            symbol: 'none',
            lineStyle: {
              color: '#1890ff',
              width: 2
            },
            areaStyle: {
              color: {
                type: 'linear',
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [
                  { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
                  { offset: 1, color: 'rgba(24, 144, 255, 0)' }
                ]
              }
            }
          }
        ]
      }
    }
  },
  async created() {
    await this.loadDashboardData()
    this.startAutoRefresh()
    this.initWebSocket()
  },
  beforeUnmount() {
    this.stopAutoRefresh()
    this.disconnectWebSocket()
  },
  methods: {
    async loadDashboardData() {
      this.loading = true
      try {
        await Promise.all([
          this.getHotStocksList(),
          this.getLatestNewsList(),
          this.getMarketChartData(),
          this.loadWatchlist()
        ])
      } catch (error) {
        console.error('加载仪表板数据失败:', error)
      } finally {
        this.loading = false
      }
    },
    async getHotStocksList() {
      try {
        const response = await getHotStocks({ limit: 10 })
        console.log('热门股票响应:', response.data) // 调试日志
        if (response.data.code === 200) {
          this.hotStocks = response.data.data || []
          console.log('热门股票数据:', this.hotStocks) // 调试日志
        }
      } catch (error) {
        console.error('获取热门股票失败:', error)
        this.$message.error('获取热门股票失败，请检查网络连接')
      }
    },
    async getLatestNewsList() {
      try {
        const response = await getLatestNews({ limit: 8 })
        if (response.data.code === 200) {
          this.latestNews = response.data.data
        }
      } catch (error) {
        console.error('获取最新新闻失败:', error)
        this.$message.error('获取最新新闻失败，请检查网络连接')
      }
    },
    async getMarketChartData() {
      this.chartLoading = true
      try {
        // 获取上证指数数据作为大盘走势
        const response = await getStockKlineData('000001.SH', {
          period: 'daily',
          limit: this.chartPeriod === '1D' ? 30 : this.chartPeriod === '5D' ? 5 : 30
        })
        
        console.log('大盘数据响应:', response.data) // 调试日志
        
        if (response.data.code === 200 && response.data.data) {
          // 处理K线数据格式
          const klineData = response.data.data.kline_data || []
          
          if (klineData.length === 0) {
            throw new Error('返回的K线数据为空')
          }
          
          // 转换为大盘走势图所需的格式
          this.marketChartData = klineData.map(item => ({
            date: item.date,
            close: item.close,
            open: item.open,
            high: item.high,
            low: item.low,
            volume: item.volume,
            change: item.change,
            pct_chg: item.pct_chg
          }))
          
          console.log('处理后的大盘数据:', this.marketChartData) // 调试日志
        } else {
          throw new Error(response.data.msg || '获取大盘数据失败')
        }
      } catch (error) {
        console.error('获取市场图表数据失败:', error)
        this.$message.error(`获取市场图表数据失败: ${error.message}`)
        this.marketChartData = []
      } finally {
        this.chartLoading = false
      }
    },
    
    loadWatchlist() {
      const saved = localStorage.getItem('stock_watchlist')
      if (saved) {
        this.watchlist = JSON.parse(saved)
      } else {
        this.watchlist = []
      }
    },
    async refreshHotStocks() {
      await this.getHotStocksList()
      this.$message.success('已刷新今日涨幅榜')
    },
    async refreshNews() {
      this.$router.push('/stock/news')
    },
    updateChart() {
      this.getMarketChartData()
    },
    startAutoRefresh() {
      this.refreshTimer = setInterval(() => {
        this.getHotStocksList()
        this.getMarketChartData()
      }, 30000) // 30秒刷新一次
    },
    stopAutoRefresh() {
      if (this.refreshTimer) {
        clearInterval(this.refreshTimer)
        this.refreshTimer = null
      }
    },
    goToStock(stock) {
      this.$router.push(`/stock/detail/${stock.ts_code}`)
    },
    viewNews(news) {
      this.$router.push(`/stock/news/${news.id}`)
    },
    goToStockList() {
      this.$router.push('/stock/list')
    },
    goToWatchlist() {
      this.$router.push('/stock/watchlist')
    },
    goToMarketNews() {
      this.$router.push('/stock/news')
    },
    goToPortfolio() {
      this.$router.push('/stock/portfolio')
    },
    goToTradeHistory() {
      this.$router.push('/stock/history')
    },
    goToRiskManagement() {
      this.$router.push('/stock/risk')
    },
    goToDataAnalysis() {
      this.$router.push('/stock/analysis')
    },
    getPriceClass(pctChg) {
      if (!pctChg) return ''
      return pctChg > 0 ? 'price-up' : pctChg < 0 ? 'price-down' : ''
    },
    formatChange(value) {
      if (!value) return '--'
      const formatted = parseFloat(value).toFixed(2)
      return value > 0 ? `+${formatted}` : formatted
    },
    formatPercent(value) {
      if (!value) return '--'
      const formatted = parseFloat(value).toFixed(2)
      return value > 0 ? `+${formatted}%` : `${formatted}%`
    },
    formatTime(timeStr) {
      if (!timeStr) return ''
      return timeStr.substring(5, 16) // 提取月-日 时:分
    },
    formatMoney(value) {
      if (!value) return '0'
      const absValue = Math.abs(value)
      if (absValue >= 100000000) {
        return (value / 100000000).toFixed(2) + '亿'
      } else if (absValue >= 10000) {
        return (value / 10000).toFixed(2) + '万'
      }
      return value.toLocaleString()
    },
    
    // WebSocket 相关方法
    async initWebSocket() {
      try {
        await wsService.connect()
        
        // 添加消息处理器
        wsService.addMessageHandler('market_data', this.handleMarketData)
        wsService.addMessageHandler('realtime_data', this.handleRealtimeData)
        wsService.addMessageHandler('news_update', this.handleNewsUpdate)
        
        // 订阅热门股票实时数据
        if (this.hotStocks.length > 0) {
          const tsCodes = this.hotStocks.map(stock => stock.ts_code)
          wsService.subscribe(tsCodes)
        }
        
        console.log('WebSocket连接并订阅成功')
      } catch (error) {
        console.error('WebSocket连接失败:', error)
        this.$message.warning('实时数据连接失败，将使用定时刷新模式')
      }
    },
    
    disconnectWebSocket() {
      // 移除消息处理器
      wsService.removeMessageHandler('market_data', this.handleMarketData)
      wsService.removeMessageHandler('realtime_data', this.handleRealtimeData) 
      wsService.removeMessageHandler('news_update', this.handleNewsUpdate)
    },
    
    handleMarketData(data) {
      // 处理市场概况数据
      if (data.indices) {
        this.marketIndices = data.indices
      }
      if (data.market_stats) {
        this.marketStats = data.market_stats
      }
      if (data.hot_stocks) {
        this.hotStocks = data.hot_stocks
      }
    },
    
    handleRealtimeData(data) {
      // 处理实时股票数据，更新热门股票列表中的价格
      if (Array.isArray(data)) {
        data.forEach(stockData => {
          const index = this.hotStocks.findIndex(stock => stock.ts_code === stockData.ts_code)
          if (index !== -1) {
            this.hotStocks[index] = {
              ...this.hotStocks[index],
              current_price: stockData.current_price,
              change: stockData.change,
              pct_chg: stockData.pct_chg
            }
          }
        })
      }
    },
    
    handleNewsUpdate(data) {
      // 处理新闻更新
      if (data.type === 'new_news' && Array.isArray(data.news)) {
        // 将新闻插入到列表前面，保持最新的在顶部
        this.latestNews = [...data.news, ...this.latestNews].slice(0, 8)
        this.$message.info('收到新的市场资讯')
      }
    }
  }
}
</script>

<style scoped>
.app-container {
  padding: 20px;
}

.market-overview {
  margin-bottom: 20px;
}

.index-card {
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.index-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.index-info {
  padding: 10px 0;
}

.index-name {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.index-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 5px;
}

.index-change {
  font-size: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.news-list {
  max-height: 300px;
  overflow-y: auto;
}

.news-item {
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background-color 0.3s;
}

.news-item:hover {
  background-color: #f5f5f5;
}

.news-title {
  font-size: 14px;
  line-height: 1.4;
  margin-bottom: 5px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.news-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #999;
}

.watchlist {
  max-height: 300px;
  overflow-y: auto;
}

.watchlist-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background-color 0.3s;
}

.watchlist-item:hover {
  background-color: #f5f5f5;
}

.stock-name {
  font-size: 14px;
  font-weight: bold;
}

.stock-price {
  text-align: right;
}

.stock-change {
  display: block;
  font-size: 12px;
  margin-top: 2px;
}

.empty-watchlist {
  text-align: center;
  padding: 20px 0;
}

.market-chart {
  width: 100%;
  height: 300px;
}

.market-stats {
  display: flex;
  justify-content: space-around;
  margin-bottom: 20px;
}

.stat-item {
  text-align: center;
}

.stat-number {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 12px;
  color: #666;
}

.stat-item.up .stat-number {
  color: #f56c6c;
}

.stat-item.down .stat-number {
  color: #67c23a;
}

.stat-item.flat .stat-number {
  color: #909399;
}

.money-flow h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #333;
}

.flow-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 13px;
}

.flow-value {
  font-weight: bold;
}

.quick-action {
  text-align: center;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s;
  border-radius: 8px;
}

.quick-action:hover {
  background-color: #f0f9ff;
  transform: translateY(-2px);
}

.quick-action div {
  margin-top: 8px;
  font-size: 14px;
  color: #333;
}

.price-up {
  color: #dd4b39; /* AdminLTE的红色 */
}

.price-down {
  color: #00a65a; /* AdminLTE的绿色 */
}
</style>