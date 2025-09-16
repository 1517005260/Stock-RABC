<template>
  <div class="app-container">
    <!-- 返回按钮和操作按钮 -->
    <div class="header-actions">
      <el-button @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        返回股票列表
      </el-button>

      <div class="stock-actions">
        <el-button
          :type="isInWatchlist ? 'danger' : 'warning'"
          @click="toggleWatchlist"
          :loading="watchlistLoading"
        >
          <el-icon>
            <StarFilled v-if="isInWatchlist" />
            <Star v-else />
          </el-icon>
          {{ isInWatchlist ? '取消自选' : '加入自选' }}
        </el-button>
      </div>
    </div>

    <!-- 股票基本信息 -->
    <div class="stock-info" v-if="stockDetail" v-loading="loading">
      <el-row :gutter="20">
        <el-col :span="12">
          <div class="info-panel">
            <h2 class="stock-name">
              {{ stockDetail.name }} ({{ stockDetail.symbol }})
              <span class="ts-code">{{ stockDetail.ts_code }}</span>
            </h2>
            <div class="price-info">
              <span class="current-price" :class="getPriceClass(stockDetail.pct_chg)">
                ¥{{ stockDetail.current_price || '--' }}
              </span>
              <div class="change-info">
                <span :class="getPriceClass(stockDetail.pct_chg)">
                  {{ formatChange(stockDetail.change) }} 
                  ({{ formatPercent(stockDetail.pct_chg) }})
                </span>
              </div>
            </div>
          </div>
        </el-col>
        <el-col :span="12">
          <div class="trading-info">
            <el-row :gutter="10">
              <el-col :span="12">
                <div class="info-item">
                  <span class="label">开盘:</span>
                  <span class="value">{{ stockDetail.open_price || '--' }}</span>
                </div>
                <div class="info-item">
                  <span class="label">最高:</span>
                  <span class="value price-up">{{ stockDetail.high_price || '--' }}</span>
                </div>
                <div class="info-item">
                  <span class="label">买一价:</span>
                  <span class="value price-down">{{ stockDetail.bid_price || '--' }}</span>
                </div>
                <div class="info-item">
                  <span class="label">成交量:</span>
                  <span class="value">{{ formatVolume(stockDetail.volume) }}</span>
                </div>
              </el-col>
              <el-col :span="12">
                <div class="info-item">
                  <span class="label">昨收:</span>
                  <span class="value">{{ stockDetail.pre_close || '--' }}</span>
                </div>
                <div class="info-item">
                  <span class="label">最低:</span>
                  <span class="value price-down">{{ stockDetail.low_price || '--' }}</span>
                </div>
                <div class="info-item">
                  <span class="label">卖一价:</span>
                  <span class="value price-up">{{ stockDetail.ask_price || '--' }}</span>
                </div>
                <div class="info-item">
                  <span class="label">成交额:</span>
                  <span class="value">{{ formatAmount(stockDetail.amount) }}</span>
                </div>
              </el-col>
            </el-row>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 主要内容区 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 左侧：K线图 -->
      <el-col :span="16">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>{{ stockDetail?.name || '' }} - {{ chartMode === 'kline' ? 'K线图' : '实时股价' }}</span>
              <div class="chart-actions">
                <el-button 
                  :type="chartMode === 'kline' ? 'primary' : ''"
                  size="small" 
                  @click="switchToKline"
                >
                  股票日K
                </el-button>
                <el-button 
                  :type="chartMode === 'realtime' ? 'primary' : ''"
                  size="small" 
                  @click="switchToRealtime"
                  :disabled="!isMarketOpen"
                >
                  实时股价
                </el-button>
                <el-button
                  type="success"
                  size="small"
                  @click="openTradeDialog"
                  :disabled="!isMarketOpen"
                >
                  {{ isMarketOpen ? '买入' : '闭市中' }}
                </el-button>
              </div>
            </div>
          </template>
          
          <!-- K线图模式 -->
          <KlineChart 
            v-if="chartMode === 'kline'"
            :ts-code="tsCode" 
            :stock-name="stockDetail?.name || ''"
            chart-height="450px"
          />
          
          <!-- 实时股价图模式 -->
          <div v-else-if="chartMode === 'realtime'" class="realtime-chart">
            <v-chart
              class="realtime-chart-container"
              :option="realtimeChartOption"
              :loading="realtimeLoading"
              autoresize
            />
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：股权占比 -->
      <el-col :span="8">
        <el-card class="holders-card">
          <template #header>
            <span>股权占比</span>
          </template>
          
          <!-- 使用持股信息饼图组件 -->
          <StockHoldersChart 
            :ts-code="tsCode"
            chart-height="450px"
          />
        </el-card>
      </el-col>
    </el-row>

    <!-- 公司基本信息 -->
    <el-card style="margin-top: 20px;" v-if="stockDetail">
      <template #header>
        <span>公司基本信息</span>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="公司全称">
          {{ stockDetail.fullname || '--' }}
        </el-descriptions-item>
        <el-descriptions-item label="所属行业">
          {{ stockDetail.industry || '--' }}
        </el-descriptions-item>
        <el-descriptions-item label="上市日期">
          {{ stockDetail.list_date || '--' }}
        </el-descriptions-item>
        <el-descriptions-item label="交易所">
          {{ stockDetail.market || '--' }}
        </el-descriptions-item>
        <el-descriptions-item label="地区">
          {{ stockDetail.area || '--' }}
        </el-descriptions-item>
        <el-descriptions-item label="股票代码">
          {{ stockDetail.ts_code || '--' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 交易对话框 -->
    <el-dialog
      v-model="tradeDialogVisible"
      title="股票交易"
      width="500px"
    >
      <el-form :model="tradeForm" label-width="80px">
        <el-form-item label="股票">
          <el-input :value="`${stockDetail?.name} (${tsCode})`" readonly />
        </el-form-item>
        
        <el-form-item label="当前价格">
          <div class="price-display">
            <div class="price-item">
              <span class="price-label">最新价:</span>
              <span class="price-value">{{ stockDetail?.current_price || '--' }}</span>
            </div>
            <div class="price-item">
              <span class="price-label">买一价:</span>
              <span class="price-value price-down">{{ stockDetail?.bid_price || '--' }}</span>
            </div>
            <div class="price-item">
              <span class="price-label">卖一价:</span>
              <span class="price-value price-up">{{ stockDetail?.ask_price || '--' }}</span>
            </div>
          </div>
        </el-form-item>
        
        <el-form-item label="交易数量">
          <el-input-number 
            v-model="tradeForm.shares"
            :min="100"
            :step="100"
            placeholder="请输入交易数量"
            style="width: 100%"
          />
          <div class="trade-tip">最少100股，必须是100的整数倍</div>
        </el-form-item>
        
        <el-form-item label="预估金额">
          <div class="estimated-amount">
            ¥{{ calculateTradeAmount() }}
            <div class="trade-price-note">
              * 买入将按卖一价 {{ stockDetail?.ask_price || '--' }} 执行
            </div>
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="tradeDialogVisible = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="executeTrade"
            :loading="tradeExecuting"
          >
            确认买入
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ArrowLeft, Star, StarFilled } from '@element-plus/icons-vue'
import { getStockDetail, getStockIntradayChart } from '@/api/stock'
import { buyStock } from '@/api/trading'
import KlineChart from '@/components/KlineChart.vue'
import StockHoldersChart from '@/components/StockHoldersChart.vue'
import VChart from "vue-echarts"
import { use } from "echarts/core"
import { CanvasRenderer } from "echarts/renderers"
import { LineChart } from "echarts/charts"
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
  ToolboxComponent
} from "echarts/components"
import { markRaw } from 'vue'

use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
  ToolboxComponent
])

export default {
  name: 'StockDetail',
  components: {
    ArrowLeft,
    Star,
    StarFilled,
    KlineChart,
    StockHoldersChart,
    VChart
  },
  data() {
    return {
      loading: false,
      stockDetail: null,
      chartMode: 'kline', // 'kline' or 'realtime'
      realtimeLoading: false,
      realtimeData: [],
      tradeDialogVisible: false,
      tradeForm: {
        shares: 100
      },
      tradeExecuting: false,
      hasTradePermission: true, // 模拟交易权限
      realtimeTimer: null,
      watchlistLoading: false,
      isInWatchlist: false
    }
  },
  computed: {
    tsCode() {
      return this.$route.params.tsCode
    },
    
    isMarketOpen() {
      const now = new Date()
      const hour = now.getHours()
      const minute = now.getMinutes()
      const currentTime = hour * 100 + minute // 转换为HHMM格式，如 930, 1500
      const day = now.getDay()

      // 周末不开盘
      if (day === 0 || day === 6) {
        return false
      }

      // 工作日交易时间：9:30-11:30, 13:00-15:00
      const isOpenSession = (currentTime >= 930 && currentTime <= 1130) ||
                           (currentTime >= 1300 && currentTime <= 1500)

      return isOpenSession
    },
    
    realtimeChartOption() {
      // 通用的图表基础结构
      const createBaseOption = (title, titleColor = '#999') => markRaw({
        title: {
          text: title,
          left: 'center',
          top: 'middle',
          textStyle: {
            color: titleColor,
            fontSize: 14
          }
        },
        xAxis: {
          type: 'category',
          data: [],
          show: false
        },
        yAxis: {
          type: 'value',
          show: false
        },
        series: [
          {
            name: '股价',
            type: 'line',
            data: [],
            showSymbol: false
          }
        ]
      })

      // 数据验证
      if (!this.realtimeData || !Array.isArray(this.realtimeData) || !this.realtimeData.length) {
        return createBaseOption('暂无分时数据')
      }

      // 过滤和验证数据
      const validPairs = this.realtimeData.filter(item =>
        item &&
        typeof item === 'object' &&
        item.time &&
        item.price != null &&
        !isNaN(parseFloat(item.price))
      )

      if (validPairs.length === 0) {
        return createBaseOption('数据格式异常，请稍后重试', '#ff6b6b')
      }

      // 格式化时间显示：将091505格式转换为09:15格式
      const formatTime = (timeStr) => {
        if (!timeStr) return timeStr
        if (typeof timeStr === 'string' && timeStr.length === 6 && /^\d{6}$/.test(timeStr)) {
          return `${timeStr.substring(0, 2)}:${timeStr.substring(2, 4)}`
        }
        return timeStr
      }

      const times = validPairs.map(item => formatTime(item.time))
      const prices = validPairs.map(item => parseFloat(item.price))

      // 计算价格范围，确保Y轴显示合理
      const minPrice = Math.min(...prices)
      const maxPrice = Math.max(...prices)
      const priceRange = maxPrice - minPrice
      const padding = priceRange * 0.1 // 10%的padding
      const yAxisMin = Math.max(0, minPrice - padding)
      const yAxisMax = maxPrice + padding

      return markRaw({
        title: {
          text: '实时股价',
          left: 'center'
        },
        tooltip: {
          trigger: 'axis',
          position: function (pt) {
            return [pt[0], '10%']
          },
          formatter: function (params) {
            const item = params[0]
            return `时间: ${item.axisValue}<br/>价格: ¥${item.value}`
          }
        },
        toolbox: {
          feature: {
            dataZoom: {
              yAxisIndex: 'none'
            },
            restore: {},
            saveAsImage: {}
          }
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: times,
          axisLabel: {
            interval: Math.max(1, Math.floor(times.length / 8)) // 动态间隔显示时间标签
          }
        },
        yAxis: {
          type: 'value',
          min: yAxisMin,
          max: yAxisMax,
          scale: true,
          axisLabel: {
            formatter: '¥{value}'
          },
          splitLine: {
            show: true,
            lineStyle: {
              color: '#f0f0f0'
            }
          }
        },
        dataZoom: [
          {
            type: 'inside',
            start: 0,
            end: 100
          },
          {
            start: 0,
            end: 100,
            handleIcon: 'M10.7,11.9v-1.3H9.3v1.3c-4.9,0.3-8.8,4.4-8.8,9.4c0,5,3.9,9.1,8.8,9.4v1.3h1.3v-1.3c4.9-0.3,8.8-4.4-8.8-9.4C19.5,16.3,15.6,12.2,10.7,11.9z M13.3,24.4H6.7V23h6.6V24.4z M13.3,19.6H6.7v-1.4h6.6V19.6z',
            handleSize: '80%',
            handleStyle: {
              color: '#fff',
              shadowBlur: 3,
              shadowColor: 'rgba(0, 0, 0, 0.6)',
              shadowOffsetX: 2,
              shadowOffsetY: 2
            }
          }
        ],
        series: [
          {
            name: '股价',
            type: 'line',
            smooth: true,
            symbol: 'none',
            sampling: 'average',
            itemStyle: {
              color: 'rgb(255, 70, 131)'
            },
            areaStyle: {
              color: {
                type: 'linear',
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [
                  { offset: 0, color: 'rgb(255, 158, 68)' },
                  { offset: 1, color: 'rgb(255, 70, 131)' }
                ]
              }
            },
            data: prices
          }
        ]
      })
    }
  },
  async created() {
    await this.getStockDetail()
    this.checkWatchlistStatus()
  },
  beforeUnmount() {
    this.clearRealtimeTimer()
  },
  methods: {
    async getStockDetail() {
      if (!this.tsCode) return

      this.loading = true
      try {
        const response = await getStockDetail(this.tsCode)
        if (response.data.code === 200) {
          this.stockDetail = response.data.data
          // 获取实时价格更新显示
          await this.updateRealtimePrice()
        } else {
          this.$message.error(response.data.msg || '获取股票详情失败')
        }
      } catch (error) {
        console.error('获取股票详情失败:', error)
        this.$message.error('获取股票详情失败')
      } finally {
        this.loading = false
      }
    },

    async updateRealtimePrice() {
      try {
        // 使用新的实时价格API获取买卖价格
        const { getStockRealtimePrice } = await import('@/api/stock')
        const response = await getStockRealtimePrice(this.tsCode)

        if (response.data.code === 200 && response.data.data && this.stockDetail) {
          const priceData = response.data.data

          // 更新所有价格信息
          this.stockDetail.current_price = priceData.current_price
          this.stockDetail.bid_price = priceData.bid_price
          this.stockDetail.ask_price = priceData.ask_price
          this.stockDetail.open_price = priceData.open_price
          this.stockDetail.high_price = priceData.high_price
          this.stockDetail.low_price = priceData.low_price
          this.stockDetail.change = priceData.change
          this.stockDetail.pct_chg = priceData.pct_chg
          this.stockDetail.volume = priceData.volume
          this.stockDetail.amount = priceData.amount

          console.log(`价格已更新: 最新=${priceData.current_price}, 买一=${priceData.bid_price}, 卖一=${priceData.ask_price}`)
        }
      } catch (error) {
        console.error('获取实时价格失败:', error)
        // 回退到分时图数据更新
        try {
          const { getStockIntradayChart } = await import('@/api/stock')
          const response = await getStockIntradayChart(this.tsCode)

          if (response.data.code === 200 && response.data.data && this.stockDetail) {
            const chartData = response.data.data
            if (chartData.price && Array.isArray(chartData.price) && chartData.price.length > 0) {
              const newPrice = parseFloat(chartData.price[chartData.price.length - 1])
              this.stockDetail.current_price = newPrice

              // 计算涨跌幅
              if (this.stockDetail.pre_close) {
                const preClose = parseFloat(this.stockDetail.pre_close)
                this.stockDetail.change = newPrice - preClose
                this.stockDetail.pct_chg = ((newPrice - preClose) / preClose * 100)
              }

              console.log(`回退价格更新: ${newPrice}`)
            }
          }
        } catch (fallbackError) {
          console.error('回退价格更新也失败:', fallbackError)
        }
      }
    },
    
    switchToKline() {
      this.chartMode = 'kline'
      this.clearRealtimeTimer()
    },
    
    switchToRealtime() {
      this.chartMode = 'realtime'
      this.loadRealtimeData()
      this.startRealtimeTimer()
    },
    
    async loadRealtimeData() {
      this.realtimeLoading = true
      try {
        if (typeof getStockIntradayChart === 'function') {
          const response = await getStockIntradayChart(this.tsCode)
          if (response.data.code === 200 && response.data.data) {
            // 分时图数据格式: [{time: '09:30', price: 12.34}, ...]
            this.realtimeData = response.data.data

            // 如果返回了数据日期信息，显示给用户
            if (response.data.date) {
              const dataDate = response.data.date
              const today = new Date().toISOString().split('T')[0]
              if (dataDate !== today) {
                this.$message.info(`当前非交易时间，显示 ${dataDate} 的分时数据`)
              }
            }
          } else {
            console.warn('无分时数据:', response.data.msg)
            this.realtimeData = []
            this.$message.warning(`获取分时数据失败: ${response.data.msg}`)
          }
        } else {
          console.warn('分时数据API未配置')
          this.realtimeData = []
        }
      } catch (error) {
        console.error('获取分时数据失败:', error)
        this.realtimeData = []
        this.$message.error('获取分时数据失败，请稍后重试')
      } finally {
        this.realtimeLoading = false
      }
    },
    
    startRealtimeTimer() {
      this.realtimeTimer = setInterval(() => {
        this.loadRealtimeData()
      }, 5000) // 每5秒更新一次
    },
    
    clearRealtimeTimer() {
      if (this.realtimeTimer) {
        clearInterval(this.realtimeTimer)
        this.realtimeTimer = null
      }
    },
    
    openTradeDialog() {
      this.tradeDialogVisible = true
      this.tradeForm.shares = 100
    },
    
    calculateTradeAmount() {
      // 买入使用卖一价，如果没有卖一价则使用当前价格
      const tradePrice = this.stockDetail?.ask_price || this.stockDetail?.current_price
      if (!tradePrice || !this.tradeForm.shares) {
        return '0.00'
      }
      const amount = tradePrice * this.tradeForm.shares
      return amount.toFixed(2)
    },
    
    async executeTrade() {
      // 交易时间检查
      if (!this.isMarketOpen) {
        this.$message.error('当前非交易时间！交易时间：工作日 9:30-11:30, 13:00-15:00')
        return
      }

      if (!this.tradeForm.shares || this.tradeForm.shares < 100) {
        this.$message.warning('交易数量不能少于100股')
        return
      }

      if (this.tradeForm.shares % 100 !== 0) {
        this.$message.warning('交易数量必须是100的整数倍')
        return
      }

      this.tradeExecuting = true
      try {
        // 买入使用卖一价，确保使用真实的交易价格
        const tradePrice = this.stockDetail.ask_price || this.stockDetail.current_price

        const response = await buyStock({
          ts_code: this.tsCode,
          price: tradePrice,  // 使用卖一价作为买入价格
          shares: this.tradeForm.shares
        })

        if (response.data.flag === 1) {
          this.$message.success(`买入成功！成交价格: ¥${tradePrice}`)
          this.tradeDialogVisible = false
          // 刷新股票信息
          await this.updateRealtimePrice()
        } else {
          this.$message.error(response.data.msg || '买入失败')
        }
      } catch (error) {
        console.error('交易失败:', error)
        this.$message.error('交易失败，请重试')
      } finally {
        this.tradeExecuting = false
      }
    },
    
    goBack() {
      this.$router.go(-1)
    },
    
    getPriceClass(pctChg) {
      if (!pctChg) return ''
      return pctChg > 0 ? 'price-up' : pctChg < 0 ? 'price-down' : ''
    },
    
    formatChange(change) {
      if (!change) return '--'
      const prefix = change > 0 ? '+' : ''
      return prefix + change.toFixed(2)
    },
    
    formatPercent(pct) {
      if (!pct) return '--'
      const prefix = pct > 0 ? '+' : ''
      return prefix + pct.toFixed(2) + '%'
    },
    
    formatVolume(volume) {
      if (!volume) return '--'
      if (volume >= 100000000) {
        return (volume / 100000000).toFixed(2) + '亿'
      } else if (volume >= 10000) {
        return (volume / 10000).toFixed(2) + '万'
      }
      return volume.toString()
    },
    
    formatAmount(amount) {
      if (!amount) return '--'
      if (amount >= 100000000) {
        return (amount / 100000000).toFixed(2) + '亿元'
      } else if (amount >= 10000) {
        return (amount / 10000).toFixed(2) + '万元'
      }
      return amount.toFixed(2) + '元'
    },

    // 自选股票相关方法
    checkWatchlistStatus() {
      const savedCodes = JSON.parse(localStorage.getItem('watchlist_codes') || '[]')
      this.isInWatchlist = savedCodes.includes(this.tsCode)
    },

    async toggleWatchlist() {
      if (!this.stockDetail) {
        this.$message.warning('股票信息未加载完成')
        return
      }

      this.watchlistLoading = true

      try {
        if (this.isInWatchlist) {
          // 从自选中移除
          const { removeFromWatchList } = await import('@/api/trading')
          const response = await removeFromWatchList(this.tsCode)

          if (response.data.code === 200) {
            this.isInWatchlist = false
            this.$message.success(`已将 ${this.stockDetail.name} 从自选股中移除`)

            // 同步更新localStorage（兼容性处理）
            const savedCodes = JSON.parse(localStorage.getItem('watchlist_codes') || '[]')
            const index = savedCodes.indexOf(this.tsCode)
            if (index > -1) {
              savedCodes.splice(index, 1)
              localStorage.setItem('watchlist_codes', JSON.stringify(savedCodes))
            }
          } else {
            throw new Error(response.data.msg || '移除失败')
          }
        } else {
          // 添加到自选
          const { addToWatchList } = await import('@/api/trading')
          const response = await addToWatchList({
            ts_code: this.tsCode
          })

          if (response.data.code === 200) {
            this.isInWatchlist = true
            this.$message.success(`已将 ${this.stockDetail.name} 添加到自选股`)

            // 同步更新localStorage（兼容性处理）
            const savedCodes = JSON.parse(localStorage.getItem('watchlist_codes') || '[]')
            if (!savedCodes.includes(this.tsCode)) {
              savedCodes.unshift(this.tsCode)
              localStorage.setItem('watchlist_codes', JSON.stringify(savedCodes))
            }
          } else {
            throw new Error(response.data.msg || '添加失败')
          }
        }
      } catch (error) {
        console.error('操作自选股失败:', error)
        this.$message.error(`操作失败: ${error.message}`)

        // API失败时回退到localStorage模式
        try {
          const savedCodes = JSON.parse(localStorage.getItem('watchlist_codes') || '[]')

          if (this.isInWatchlist) {
            const index = savedCodes.indexOf(this.tsCode)
            if (index > -1) {
              savedCodes.splice(index, 1)
              localStorage.setItem('watchlist_codes', JSON.stringify(savedCodes))
              this.isInWatchlist = false
              this.$message.success(`已将 ${this.stockDetail.name} 从自选股中移除 (本地模式)`)
            }
          } else {
            savedCodes.unshift(this.tsCode)
            localStorage.setItem('watchlist_codes', JSON.stringify(savedCodes))
            this.isInWatchlist = true
            this.$message.success(`已将 ${this.stockDetail.name} 添加到自选股 (本地模式)`)
          }
        } catch (fallbackError) {
          console.error('localStorage回退也失败:', fallbackError)
          this.$message.error('操作失败，请重试')
        }
      } finally {
        this.watchlistLoading = false
      }
    }
  }
}
</script>

<style scoped>
.app-container {
  padding: 20px;
}

.header-actions {
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stock-actions {
  display: flex;
  gap: 10px;
}

.stock-info {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.info-panel {
  text-align: left;
}

.stock-name {
  margin: 0 0 15px 0;
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.ts-code {
  font-size: 14px;
  color: #666;
  margin-left: 10px;
}

.price-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.current-price {
  font-size: 28px;
  font-weight: bold;
}

.change-info {
  font-size: 16px;
}

.trading-info {
  padding: 10px 0;
}

.info-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  padding: 5px 0;
}

.label {
  color: #666;
  font-size: 14px;
}

.value {
  color: #333;
  font-weight: 500;
}

.price-up {
  color: #dd4b39; /* AdminLTE红色 */
}

.price-down {
  color: #00a65a; /* AdminLTE绿色 */
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-actions {
  display: flex;
  gap: 10px;
}

.chart-card, .holders-card {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.trade-tip {
  font-size: 12px;
  color: #999;
  margin-top: 5px;
}

.estimated-amount {
  font-size: 18px;
  font-weight: bold;
  color: #dd4b39;
}

.trade-price-note {
  font-size: 12px;
  color: #666;
  margin-top: 5px;
  font-weight: normal;
}

.price-display {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 6px;
}

.price-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.price-label {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.price-value {
  font-size: 16px;
  font-weight: bold;
  color: #333;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.realtime-chart {
  width: 100%;
  height: 450px;
}

.realtime-chart-container {
  width: 100%;
  height: 450px;
}
</style>