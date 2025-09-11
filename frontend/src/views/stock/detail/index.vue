<template>
  <div class="app-container">
    <!-- 返回按钮 -->
    <div class="header-actions">
      <el-button @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        返回股票列表
      </el-button>
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
              <span>{{ stockDetail?.name || '' }} - K线图</span>
              <div class="chart-actions">
                <el-button 
                  type="primary" 
                  size="small" 
                  @click="openTradeDialog"
                  :disabled="!hasTradePermission"
                >
                  买入
                </el-button>
              </div>
            </div>
          </template>
          
          <!-- 使用我们新创建的K线图组件 -->
          <KlineChart 
            :ts-code="tsCode" 
            :stock-name="stockDetail?.name || ''"
            chart-height="450px"
          />
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
          <el-input :value="stockDetail?.current_price" readonly />
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
import { ArrowLeft } from '@element-plus/icons-vue'
import { getStockDetail } from '@/api/stock'
import { buyStock } from '@/api/trading'
import KlineChart from '@/components/KlineChart.vue'
import StockHoldersChart from '@/components/StockHoldersChart.vue'

export default {
  name: 'StockDetail',
  components: {
    ArrowLeft,
    KlineChart,
    StockHoldersChart
  },
  data() {
    return {
      loading: false,
      stockDetail: null,
      tradeDialogVisible: false,
      tradeForm: {
        shares: 100
      },
      tradeExecuting: false,
      hasTradePermission: true // 模拟交易权限
    }
  },
  computed: {
    tsCode() {
      return this.$route.params.tsCode
    }
  },
  async created() {
    await this.getStockDetail()
  },
  methods: {
    async getStockDetail() {
      if (!this.tsCode) return
      
      this.loading = true
      try {
        const response = await getStockDetail(this.tsCode)
        if (response.data.code === 200) {
          this.stockDetail = response.data.data
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
    
    openTradeDialog() {
      this.tradeDialogVisible = true
      this.tradeForm.shares = 100
    },
    
    calculateTradeAmount() {
      if (!this.stockDetail?.current_price || !this.tradeForm.shares) {
        return '0.00'
      }
      const amount = this.stockDetail.current_price * this.tradeForm.shares
      return amount.toFixed(2)
    },
    
    async executeTrade() {
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
        const response = await buyStock({
          ts_code: this.tsCode,
          price: this.stockDetail.current_price,
          shares: this.tradeForm.shares
        })
        
        if (response.data.flag === 1) {
          this.$message.success('买入成功！')
          this.tradeDialogVisible = false
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

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>