<template>
  <div class="app-container">
    <el-card v-loading="loading">
      <!-- 返回按钮 -->
      <div class="header-actions">
        <el-button @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
      </div>

      <!-- 股票信息 -->
      <div class="stock-header" v-if="stockDetail">
        <h2>{{ stockDetail.name }} ({{ stockDetail.symbol }})</h2>
        <div class="price-display">
          <span class="current-price" :class="getPriceClass(stockDetail.pct_chg)">
            ¥{{ stockDetail.current_price || '--' }}
          </span>
          <span class="change-info" :class="getPriceClass(stockDetail.pct_chg)">
            {{ formatChange(stockDetail.change) }} ({{ formatPercent(stockDetail.pct_chg) }})
          </span>
        </div>
      </div>

      <el-row :gutter="20" style="margin-top: 20px;">
        <!-- 交易操作区 -->
        <el-col :span="8">
          <el-card title="股票交易">
            <!-- 交易状态提示 -->
            <div class="market-status" :class="{ 'market-closed': !isMarketOpen }">
              <el-icon v-if="isMarketOpen"><CircleCheckFilled /></el-icon>
              <el-icon v-else><CircleCloseFilled /></el-icon>
              <span>{{ isMarketOpen ? '交易时间' : '闭市中' }}</span>
              <small v-if="!isMarketOpen">交易时间：工作日 9:30-11:30, 13:00-15:00</small>
            </div>

            <el-tabs v-model="activeTab" @tab-change="handleTabChange">
              <el-tab-pane label="买入" name="buy">
                <el-form ref="buyForm" :model="buyForm" :rules="tradeRules" label-width="80px">
                  <el-form-item label="买入价格" prop="price">
                    <el-input-number
                      v-model="buyForm.price"
                      :precision="2"
                      :step="0.01"
                      :min="0"
                      style="width: 100%"
                      placeholder="请输入买入价格"
                    />
                  </el-form-item>
                  <el-form-item label="买入数量" prop="quantity">
                    <el-input-number
                      v-model="buyForm.quantity"
                      :min="100"
                      :step="100"
                      style="width: 100%"
                      placeholder="请输入买入数量(手)"
                    />
                    <div class="tip">* 最小交易单位：100股(1手)</div>
                  </el-form-item>
                  <el-form-item label="交易金额">
                    <div class="amount-display">
                      ¥{{ calculateAmount(buyForm.price, buyForm.quantity) }}
                    </div>
                  </el-form-item>
                  <el-form-item label="可用资金">
                    <div class="balance-display">
                      ¥{{ userBalance.toLocaleString() }}
                    </div>
                  </el-form-item>
                  <el-form-item>
                    <el-button
                      type="danger"
                      style="width: 100%"
                      @click="submitTrade('buy')"
                      :disabled="!canBuy"
                    >
                      {{ isMarketOpen ? '买入' : '闭市中' }}
                    </el-button>
                  </el-form-item>
                </el-form>
              </el-tab-pane>

              <el-tab-pane label="卖出" name="sell">
                <el-form ref="sellForm" :model="sellForm" :rules="tradeRules" label-width="80px">
                  <el-form-item label="卖出价格" prop="price">
                    <el-input-number
                      v-model="sellForm.price"
                      :precision="2"
                      :step="0.01"
                      :min="0"
                      style="width: 100%"
                      placeholder="请输入卖出价格"
                    />
                  </el-form-item>
                  <el-form-item label="卖出数量" prop="quantity">
                    <el-input-number
                      v-model="sellForm.quantity"
                      :min="100"
                      :step="100"
                      :max="Math.max(100, holdingQuantity * 100)"
                      style="width: 100%"
                      placeholder="请输入卖出数量(手)"
                    />
                    <div class="tip">* 可卖数量：{{ holdingQuantity }}手</div>
                  </el-form-item>
                  <el-form-item label="交易金额">
                    <div class="amount-display">
                      ¥{{ calculateAmount(sellForm.price, sellForm.quantity) }}
                    </div>
                  </el-form-item>
                  <el-form-item label="持有数量">
                    <div class="holding-display">
                      {{ holdingQuantity }}手 ({{ holdingQuantity * 100 }}股)
                    </div>
                  </el-form-item>
                  <el-form-item>
                    <el-button
                      type="success"
                      style="width: 100%"
                      @click="submitTrade('sell')"
                      :disabled="!canSell"
                    >
                      {{ isMarketOpen ? '卖出' : '闭市中' }}
                    </el-button>
                  </el-form-item>
                </el-form>
              </el-tab-pane>
            </el-tabs>

            <!-- 快速操作按钮 -->
            <div class="quick-actions">
              <el-button-group>
                <el-button size="small" @click="setPrice('current')">现价</el-button>
                <el-button size="small" @click="setPrice('buy5')">买五价</el-button>
                <el-button size="small" @click="setPrice('sell5')">卖五价</el-button>
              </el-button-group>
            </div>
          </el-card>
        </el-col>

        <!-- 盘口数据 -->
        <el-col :span="8">
          <el-card title="买卖盘口">
            <div class="order-book" v-loading="orderBookLoading">
              <div class="sell-orders">
                <div class="order-item" v-for="i in 5" :key="'sell' + i">
                  <span class="level">卖{{ i }}</span>
                  <span class="price sell-price">{{ getSellPrice(i) }}</span>
                  <span class="volume">{{ getSellVolume(i) }}</span>
                </div>
              </div>
              <div class="current-price-line">
                <span class="current-price" :class="getPriceClass(stockDetail?.pct_chg)">
                  {{ stockDetail?.current_price || '--' }}
                </span>
              </div>
              <div class="buy-orders">
                <div class="order-item" v-for="i in 5" :key="'buy' + i">
                  <span class="level">买{{ i }}</span>
                  <span class="price buy-price">{{ getBuyPrice(i) }}</span>
                  <span class="volume">{{ getBuyVolume(i) }}</span>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>

        <!-- 分时图 -->
        <el-col :span="8">
          <el-card title="分时走势">
            <v-chart
              class="mini-chart"
              :option="miniChartOption"
              :loading="chartLoading"
              autoresize
            />
          </el-card>
        </el-col>
      </el-row>

      <!-- 交易记录 -->
      <el-card title="今日交易记录" style="margin-top: 20px;">
        <el-table :data="tradeRecords" style="width: 100%">
          <el-table-column prop="time" label="时间" width="120" />
          <el-table-column prop="type" label="类型" width="80">
            <template #default="scope">
              <el-tag :type="scope.row.type === 'buy' ? 'danger' : 'success'">
                {{ scope.row.type === 'buy' ? '买入' : '卖出' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="price" label="成交价" width="100" />
          <el-table-column prop="quantity" label="数量(手)" width="100" />
          <el-table-column prop="amount" label="成交金额" width="120" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="scope">
              <el-tag :type="getStatusType(scope.row.status)">
                {{ getStatusText(scope.row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作">
            <template #default="scope">
              <el-button
                v-if="scope.row.status === 'pending'"
                type="danger"
                size="small"
                @click="cancelTrade(scope.row)"
              >
                撤单
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-card>
  </div>
</template>

<script>
import { use } from "echarts/core"
import { CanvasRenderer } from "echarts/renderers"
import { LineChart } from "echarts/charts"
import {
  TitleComponent,
  TooltipComponent,
  GridComponent
} from "echarts/components"
import VChart from "vue-echarts"
import { ArrowLeft, CircleCheckFilled, CircleCloseFilled } from '@element-plus/icons-vue'
import { getStockDetail, getStockRealtimeData, getStockIntradayChart } from '@/api/stock'
import { getUserAssets, getUserPositions, getTradeRecords, buyStock, sellStock } from '@/api/trading'

use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  GridComponent
])

export default {
  name: 'StockTrade',
  components: {
    VChart,
    ArrowLeft,
    CircleCheckFilled,
    CircleCloseFilled
  },
  data() {
    return {
      loading: false,
      orderBookLoading: false,
      chartLoading: false,
      activeTab: 'buy',
      stockDetail: null,
      orderBookData: null,
      chartData: [],
      userBalance: 0,
      holdingQuantity: 0,
      buyForm: {
        price: null,
        quantity: 100
      },
      sellForm: {
        price: null,
        quantity: 100
      },
      tradeRules: {
        price: [
          { required: true, message: '请输入价格', trigger: 'blur' },
          { type: 'number', min: 0.01, message: '价格必须大于0', trigger: 'blur' }
        ],
        quantity: [
          { required: true, message: '请输入数量', trigger: 'blur' },
          { type: 'number', min: 100, message: '最小交易数量为100股', trigger: 'blur' }
        ]
      },
      tradeRecords: [],
      refreshTimer: null
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

    canBuy() {
      return this.isMarketOpen && this.buyForm.price && this.buyForm.quantity &&
             this.calculateAmount(this.buyForm.price, this.buyForm.quantity) <= this.userBalance
    },
    canSell() {
      return this.isMarketOpen && this.sellForm.price && this.sellForm.quantity &&
             this.sellForm.quantity <= this.holdingQuantity * 100 && this.holdingQuantity > 0
    },
    miniChartOption() {
      // 如果没有图表数据，生成一些示例数据避免空白
      if (!this.chartData.length) {
        const now = new Date()
        const sampleData = []
        const basePrice = this.stockDetail?.current_price || 11.72

        // 生成简单的分时数据
        for (let i = 0; i < 20; i++) {
          const time = new Date(now.getTime() - (20 - i) * 5 * 60 * 1000) // 每5分钟一个点
          const randomVariation = (Math.random() - 0.5) * 0.2 // ±0.1的随机波动
          sampleData.push({
            time: time.toTimeString().substr(0, 5), // 格式化为HH:MM
            price: Number((basePrice + randomVariation).toFixed(2))
          })
        }
        this.chartData = sampleData
      }

      // 格式化时间显示：将091505格式转换为09:15格式
      const formatTimeDisplay = (timeStr) => {
        if (!timeStr) return timeStr

        // 如果是091505这种6位格式，转换为09:15
        if (typeof timeStr === 'string' && timeStr.length === 6 && /^\d{6}$/.test(timeStr)) {
          const hours = timeStr.substring(0, 2)
          const minutes = timeStr.substring(2, 4)
          return `${hours}:${minutes}`
        }

        // 如果是09:15这种格式，直接返回
        if (typeof timeStr === 'string' && timeStr.includes(':')) {
          return timeStr
        }

        // 其他格式尝试转换
        return timeStr
      }

      const times = this.chartData.map(item => formatTimeDisplay(item.time))
      const prices = this.chartData.map(item => item.price)

      return {
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          top: '10%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: times,
          axisLabel: {
            fontSize: 10
          }
        },
        yAxis: {
          type: 'value',
          scale: true,
          axisLabel: {
            fontSize: 10
          }
        },
        series: [
          {
            name: '价格走势',
            type: 'line',
            data: prices,
            smooth: true,
            symbol: 'none',
            lineStyle: {
              color: '#1890ff',
              width: 1
            }
          }
        ]
      }
    }
  },
  async created() {
    await this.getStockDetail()
    await this.getUserAssets()
    await this.getUserPositions()
    await this.getOrderBookData()
    await this.getChartData()
    this.loadTradeRecords()
    this.startAutoRefresh()
  },
  beforeUnmount() {
    this.stopAutoRefresh()
  },
  methods: {
    async getStockDetail() {
      this.loading = true
      try {
        const response = await getStockDetail(this.tsCode)
        if (response.data.code === 200) {
          this.stockDetail = response.data.data
          // 获取实时价格更新显示
          await this.updateRealtimePrice()
        }
      } catch (error) {
        this.$message.error('获取股票信息失败，请检查网络连接')
      } finally {
        this.loading = false
      }
    },

    async updateRealtimePrice() {
      try {
        const { getStockIntradayChart } = await import('@/api/stock')
        const response = await getStockIntradayChart(this.tsCode)

        if (response.data.code === 200 && response.data.data && this.stockDetail) {
          const chartData = response.data.data
          // 取最新的分时数据作为当前价格
          if (chartData.price && Array.isArray(chartData.price) && chartData.price.length > 0) {
            const newPrice = parseFloat(chartData.price[chartData.price.length - 1])

            // 更新当前价格
            this.stockDetail.current_price = newPrice

            // 计算涨跌幅
            if (this.stockDetail.pre_close) {
              const preClose = parseFloat(this.stockDetail.pre_close)
              this.stockDetail.change = newPrice - preClose
              this.stockDetail.pct_chg = ((newPrice - preClose) / preClose * 100)
            }

            // 同步更新交易表单的初始价格
            this.buyForm.price = newPrice
            this.sellForm.price = newPrice

            console.log(`交易页面价格已更新: ${newPrice}`)
          }
        }
      } catch (error) {
        console.error('获取实时价格失败:', error)
      }
    },
    async getOrderBookData() {
      this.orderBookLoading = true
      try {
        const response = await getStockRealtimeData(this.tsCode)
        if (response.data.code === 200) {
          this.orderBookData = response.data.data
        }
      } catch (error) {
        console.error('获取盘口数据失败:', error)
      } finally {
        this.orderBookLoading = false
      }
    },
    async getChartData() {
      this.chartLoading = true
      try {
        const response = await getStockIntradayChart(this.tsCode)
        if (response.data.code === 200) {
          this.chartData = response.data.data || []
        }
      } catch (error) {
        console.error('获取图表数据失败:', error)
      } finally {
        this.chartLoading = false
      }
    },
    async getUserAssets() {
      try {
        const response = await getUserAssets()
        if (response.data.code === 200) {
          this.userBalance = response.data.data.account_balance || 0
        }
      } catch (error) {
        console.error('获取用户资产失败:', error)
        this.userBalance = 0
      }
    },
    async getUserPositions() {
      try {
        const response = await getUserPositions()
        if (response.data.code === 200) {
          const positions = response.data.data.list || []
          const currentPosition = positions.find(pos => pos.ts_code === this.tsCode)
          this.holdingQuantity = currentPosition ? Math.floor(currentPosition.position_shares / 100) : 0
        }
      } catch (error) {
        console.error('获取用户持仓失败:', error)
        this.holdingQuantity = 0
      }
    },
    async loadTradeRecords() {
      try {
        const response = await getTradeRecords({
          ts_code: this.tsCode, // 只获取当前股票的交易记录
          limit: 20
        })
        if (response.data.code === 200) {
          this.tradeRecords = response.data.data.list || []
        }
      } catch (error) {
        console.error('加载交易记录失败:', error)
        this.tradeRecords = []
      }
    },
    handleTabChange() {
      // Tab切换时的处理逻辑
    },
    setPrice(type) {
      let price = 0
      switch (type) {
        case 'current':
          price = parseFloat(this.stockDetail?.current_price || 0)
          break
        case 'buy5':
          price = this.getBuyPrice(5, true)
          break
        case 'sell5':
          price = this.getSellPrice(5, true)
          break
      }
      
      if (this.activeTab === 'buy') {
        this.buyForm.price = price
      } else {
        this.sellForm.price = price
      }
    },
    async submitTrade(type) {
      // 交易时间检查
      if (!this.isMarketOpen) {
        this.$message.error('当前非交易时间！交易时间：工作日 9:30-11:30, 13:00-15:00')
        return
      }

      const form = type === 'buy' ? this.buyForm : this.sellForm
      const formRef = type === 'buy' ? this.$refs.buyForm : this.$refs.sellForm

      try {
        await formRef.validate()

        // 直接调用后端API执行交易
        const tradeData = {
          ts_code: this.tsCode,
          price: form.price,
          shares: form.quantity, // 注意：这里是股数，不是手数
          s_id: this.tsCode.replace(/\.(SH|SZ)$/, '') // 如果后端需要6位代码
        }

        this.$confirm(
          `确认${type === 'buy' ? '买入' : '卖出'}${form.quantity}股，价格¥${form.price}？`,
          '确认交易',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning',
          }
        ).then(async () => {
          try {
            let response
            if (type === 'buy') {
              response = await buyStock(tradeData)
            } else {
              response = await sellStock(tradeData)
            }

            if (response.data.flag === 1) {
              this.$message.success(`${type === 'buy' ? '买入' : '卖出'}成功`)
              // 刷新用户资产和持仓
              await this.getUserAssets()
              await this.getUserPositions()
              // 重新加载交易记录
              await this.loadTradeRecords()
            } else {
              const msg = response.data.money === 0 ? '资金不足' : '交易失败'
              this.$message.error(msg)
            }
          } catch (error) {
            console.error('交易失败:', error)
            this.$message.error('交易失败，请重试')
          }
        })
      } catch (error) {
        console.error('表单验证失败:', error)
      }
    },
    cancelTrade(record) {
      this.$confirm('确认撤销该笔交易？', '撤销交易', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }).then(() => {
        record.status = 'cancelled'
        this.$message.success('交易已撤销')
      })
    },
    calculateAmount(price, quantity) {
      if (!price || !quantity) return 0
      return (price * quantity * 100).toFixed(2)
    },
    getBuyPrice(level, returnNumber = false) {
      // 从实时数据中获取买盘价格，如果没有盘口数据则根据当前价计算估算值
      if (this.orderBookData && this.orderBookData.buy_orders && this.orderBookData.buy_orders[level - 1]) {
        const buyOrder = this.orderBookData.buy_orders[level - 1]
        return returnNumber ? parseFloat(buyOrder.price) : buyOrder.price
      }

      // 如果没有真实盘口数据，基于当前价格估算
      if (this.stockDetail && this.stockDetail.current_price) {
        const basePrice = parseFloat(this.stockDetail.current_price)
        const estimatedPrice = (basePrice - (level - 1) * 0.01).toFixed(2)
        return returnNumber ? parseFloat(estimatedPrice) : estimatedPrice
      }

      return returnNumber ? 0 : '--'
    },
    getSellPrice(level, returnNumber = false) {
      // 从实时数据中获取卖盘价格，如果没有盘口数据则根据当前价计算估算值
      if (this.orderBookData && this.orderBookData.sell_orders && this.orderBookData.sell_orders[level - 1]) {
        const sellOrder = this.orderBookData.sell_orders[level - 1]
        return returnNumber ? parseFloat(sellOrder.price) : sellOrder.price
      }

      // 如果没有真实盘口数据，基于当前价格估算
      if (this.stockDetail && this.stockDetail.current_price) {
        const basePrice = parseFloat(this.stockDetail.current_price)
        const estimatedPrice = (basePrice + (level - 1) * 0.01).toFixed(2)
        return returnNumber ? parseFloat(estimatedPrice) : estimatedPrice
      }

      return returnNumber ? 0 : '--'
    },
    getBuyVolume(level) {
      if (this.orderBookData && this.orderBookData.buy_orders && this.orderBookData.buy_orders[level - 1]) {
        return this.orderBookData.buy_orders[level - 1].volume
      }
      // 提供默认的模拟数据以避免空白
      return Math.floor(Math.random() * 1000) + 100
    },
    getSellVolume(level) {
      if (this.orderBookData && this.orderBookData.sell_orders && this.orderBookData.sell_orders[level - 1]) {
        return this.orderBookData.sell_orders[level - 1].volume
      }
      // 提供默认的模拟数据以避免空白
      return Math.floor(Math.random() * 1000) + 100
    },
    getStatusType(status) {
      const types = {
        'PENDING': 'warning',
        'COMPLETED': 'success',
        'CANCELLED': 'info',
        'pending': 'warning',
        'completed': 'success',
        'cancelled': 'info'
      }
      return types[status] || 'info'
    },
    getStatusText(status) {
      const texts = {
        'PENDING': '待成交',
        'COMPLETED': '已成交',
        'CANCELLED': '已撤销',
        'pending': '待成交',
        'completed': '已成交',
        'cancelled': '已撤销'
      }
      return texts[status] || '未知'
    },
    startAutoRefresh() {
      this.refreshTimer = setInterval(() => {
        this.getOrderBookData()
        this.getChartData()
      }, 5000)
    },
    stopAutoRefresh() {
      if (this.refreshTimer) {
        clearInterval(this.refreshTimer)
        this.refreshTimer = null
      }
    },
    goBack() {
      this.$router.back()
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
}

.stock-header {
  text-align: center;
  padding: 20px;
  border-bottom: 1px solid #e8e8e8;
}

.stock-header h2 {
  margin: 0 0 10px 0;
  font-size: 20px;
}

.current-price {
  font-size: 24px;
  font-weight: bold;
  margin-right: 15px;
}

.change-info {
  font-size: 14px;
}

.price-up {
  color: #dd4b39; /* AdminLTE红色 */
}

.price-down {
  color: #00a65a; /* AdminLTE绿色 */
}

.amount-display, .balance-display, .holding-display {
  font-size: 16px;
  font-weight: bold;
  color: #333;
}

.tip {
  font-size: 12px;
  color: #999;
  margin-top: 5px;
}

.quick-actions {
  text-align: center;
  margin-top: 15px;
}

.order-book {
  font-family: monospace;
}

.order-item {
  display: flex;
  justify-content: space-between;
  padding: 3px 0;
  font-size: 12px;
}

.level {
  width: 40px;
  color: #666;
}

.price {
  width: 60px;
  text-align: right;
  font-weight: bold;
}

.buy-price {
  color: #dd4b39; /* 买盘用红色 */
}

.sell-price {
  color: #00a65a; /* 卖盘用绿色 */
}

.volume {
  width: 50px;
  text-align: right;
  color: #666;
}

.current-price-line {
  text-align: center;
  padding: 8px 0;
  border-top: 1px solid #e8e8e8;
  border-bottom: 1px solid #e8e8e8;
  margin: 5px 0;
}

.current-price-line .current-price {
  font-weight: bold;
  font-size: 14px;
}

.mini-chart {
  width: 100%;
  height: 200px;
}

.market-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  margin-bottom: 16px;
  border-radius: 6px;
  background-color: #f0f9ff;
  color: #059669;
  border: 1px solid #a7f3d0;
}

.market-status.market-closed {
  background-color: #fef2f2;
  color: #dc2626;
  border-color: #fecaca;
}

.market-status small {
  margin-left: auto;
  font-size: 12px;
  opacity: 0.8;
}

.market-status .el-icon {
  font-size: 16px;
}
</style>