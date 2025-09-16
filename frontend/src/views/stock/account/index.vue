<template>
  <div class="account-container">
    <el-row :gutter="20">
      <!-- 账户概览卡片 -->
      <el-col :span="24">
        <el-card class="overview-card">
          <template #header>
            <div class="card-header">
              <span>账户概览</span>
              <el-button @click="refreshAccount" :loading="loading">刷新</el-button>
            </div>
          </template>
          
          <el-row :gutter="20">
            <el-col :span="4">
              <div class="account-item">
                <div class="account-value">¥{{ accountInfo.account_balance?.toFixed(2) || '0.00' }}</div>
                <div class="account-label">可用资金</div>
              </div>
            </el-col>
            <el-col :span="4">
              <div class="account-item">
                <div class="account-value">¥{{ accountInfo.frozen_balance?.toFixed(2) || '0.00' }}</div>
                <div class="account-label">冻结资金</div>
              </div>
            </el-col>
            <el-col :span="4">
              <div class="account-item">
                <div class="account-value">¥{{ accountInfo.market_value?.toFixed(2) || '0.00' }}</div>
                <div class="account-label">持仓市值</div>
              </div>
            </el-col>
            <el-col :span="4">
              <div class="account-item">
                <div class="account-value">¥{{ accountInfo.total_value?.toFixed(2) || '0.00' }}</div>
                <div class="account-label">总资产</div>
              </div>
            </el-col>
            <el-col :span="4">
              <div class="account-item">
                <div class="account-value" :class="{
                  'text-success': accountInfo.total_profit > 0,
                  'text-danger': accountInfo.total_profit < 0
                }">
                  {{ accountInfo.total_profit > 0 ? '+' : '' }}¥{{ accountInfo.total_profit?.toFixed(2) || '0.00' }}
                </div>
                <div class="account-label">总盈亏</div>
              </div>
            </el-col>
            <el-col :span="4">
              <div class="account-item">
                <div class="account-value">{{ accountInfo.position_count || 0 }}</div>
                <div class="account-label">持仓品种</div>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 资产分布饼图 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>资产分布</span>
          </template>
          <div ref="assetChart" style="height: 300px;"></div>
        </el-card>
      </el-col>
      
      <!-- 近期交易趋势 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>近期交易趋势</span>
          </template>
          <div ref="tradeChart" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 持仓概览表格 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>持仓概览</span>
              <el-button size="small" @click="goToPositions">查看全部</el-button>
            </div>
          </template>
          
          <el-table :data="positionList.slice(0, 5)" style="width: 100%" v-loading="loading">
            <el-table-column prop="ts_code" label="股票代码" width="120">
              <template #default="scope">
                <el-link @click="goToStockDetail(scope.row.ts_code)">{{ scope.row.ts_code }}</el-link>
              </template>
            </el-table-column>
            <el-table-column prop="stock_name" label="股票名称" width="150"></el-table-column>
            <el-table-column prop="position_shares" label="持仓数量" width="120" align="right"></el-table-column>
            <el-table-column prop="cost_price" label="成本价" width="120" align="right">
              <template #default="scope">
                ¥{{ scope.row.cost_price?.toFixed(2) || '--' }}
              </template>
            </el-table-column>
            <el-table-column prop="current_price" label="现价" width="120" align="right">
              <template #default="scope">
                ¥{{ scope.row.current_price?.toFixed(2) || '--' }}
              </template>
            </el-table-column>
            <el-table-column prop="market_value" label="市值" width="120" align="right">
              <template #default="scope">
                ¥{{ scope.row.market_value?.toFixed(2) || '--' }}
              </template>
            </el-table-column>
            <el-table-column prop="profit_loss" label="盈亏" width="120" align="right">
              <template #default="scope">
                <span :class="{
                  'text-success': scope.row.profit_loss > 0,
                  'text-danger': scope.row.profit_loss < 0
                }">
                  {{ scope.row.profit_loss > 0 ? '+' : '' }}{{ scope.row.profit_loss?.toFixed(2) || '--' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="scope">
                <el-button size="small" type="primary" @click="goToTrade(scope.row.ts_code, 'sell')">卖出</el-button>
              </template>
            </el-table-column>
            
            <template #empty>
              <div class="empty-data">
                <el-empty description="暂无持仓" :image-size="80"></el-empty>
              </div>
            </template>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 最近交易记录 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>最近交易</span>
              <el-button size="small" @click="goToRecords">查看全部</el-button>
            </div>
          </template>
          
          <el-table :data="recentTrades.slice(0, 5)" style="width: 100%" v-loading="loading">
            <el-table-column prop="trade_time" label="交易时间" width="180">
              <template #default="scope">
                {{ scope.row.trade_time || '--' }}
              </template>
            </el-table-column>
            <el-table-column prop="ts_code" label="股票代码" width="120">
              <template #default="scope">
                <el-link @click="goToStockDetail(scope.row.ts_code)">{{ scope.row.ts_code }}</el-link>
              </template>
            </el-table-column>
            <el-table-column prop="stock_name" label="股票名称" width="150"></el-table-column>
            <el-table-column prop="trade_type_display" label="类型" width="80" align="center">
              <template #default="scope">
                <el-tag :type="scope.row.trade_type === 'BUY' ? 'danger' : 'success'" size="small">
                  {{ scope.row.trade_type_display || scope.row.trade_type }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="trade_price" label="价格" width="120" align="right">
              <template #default="scope">
                ¥{{ scope.row.trade_price?.toFixed(2) || '--' }}
              </template>
            </el-table-column>
            <el-table-column prop="trade_shares" label="数量" width="100" align="right">
              <template #default="scope">
                {{ scope.row.trade_shares || '--' }}
              </template>
            </el-table-column>
            <el-table-column prop="trade_amount" label="金额" width="140" align="right">
              <template #default="scope">
                ¥{{ scope.row.trade_amount?.toFixed(2) || '--' }}
              </template>
            </el-table-column>
            <el-table-column prop="status_display" label="状态" width="100" align="center">
              <template #default="scope">
                <el-tag 
                  :type="getStatusType(scope.row.status)" 
                  size="small">
                  {{ scope.row.status_display || scope.row.status }}
                </el-tag>
              </template>
            </el-table-column>
            
            <template #empty>
              <div class="empty-data">
                <el-empty description="暂无交易记录" :image-size="80"></el-empty>
              </div>
            </template>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { getUserAssets, getUserPositions, getTradeRecords } from '@/api/trading'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

export default {
  name: 'StockAccount',
  data() {
    return {
      loading: false,
      accountInfo: {
        account_balance: 0,
        frozen_balance: 0,
        market_value: 0,
        total_value: 0,
        total_profit: 0,
        position_count: 0
      },
      positionList: [],
      recentTrades: [],
      assetChartInstance: null,
      tradeChartInstance: null
    }
  },
  mounted() {
    this.loadAccountData()
    this.$nextTick(() => {
      this.initCharts()
    })
  },
  beforeUnmount() {
    if (this.assetChartInstance) {
      this.assetChartInstance.dispose()
    }
    if (this.tradeChartInstance) {
      this.tradeChartInstance.dispose()
    }
  },
  methods: {
    async loadAccountData() {
      this.loading = true
      try {
        // 并行加载数据
        const [accountResponse, positionsResponse, tradesResponse] = await Promise.all([
          this.loadAccountInfo(),
          this.loadPositions(),
          this.loadRecentTrades()
        ])
        
        // 更新图表
        this.$nextTick(() => {
          this.updateAssetChart()
          this.updateTradeChart()
        })
        
      } catch (error) {
        console.error('加载账户数据失败:', error)
      }
      this.loading = false
    },
    
    async loadAccountInfo() {
      try {
        const response = await getUserAssets()
        if (response.data.code === 200) {
          this.accountInfo = response.data.data
        } else {
          ElMessage.error(response.data.msg || '加载账户信息失败')
        }
      } catch (error) {
        console.error('加载账户信息失败:', error)
        ElMessage.error('加载账户信息失败，请稍后重试')
      }
    },
    
    async loadPositions() {
      try {
        const response = await getUserPositions({ pageSize: 10 })
        if (response.data.code === 200) {
          this.positionList = response.data.data.list || []
        }
      } catch (error) {
        console.error('加载持仓数据失败:', error)
      }
    },
    
    async loadRecentTrades() {
      try {
        const response = await getTradeRecords({ pageSize: 10 })
        if (response.data.code === 200) {
          this.recentTrades = response.data.data.list || []
        }
      } catch (error) {
        console.error('加载交易记录失败:', error)
      }
    },
    
    initCharts() {
      // 初始化资产分布饼图
      if (this.$refs.assetChart) {
        this.assetChartInstance = echarts.init(this.$refs.assetChart)
        this.updateAssetChart()
      }
      
      // 初始化交易趋势图
      if (this.$refs.tradeChart) {
        this.tradeChartInstance = echarts.init(this.$refs.tradeChart)
        this.updateTradeChart()
      }
    },
    
    updateAssetChart() {
      if (!this.assetChartInstance) return
      
      const option = {
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: ¥{c} ({d}%)'
        },
        series: [
          {
            name: '资产分布',
            type: 'pie',
            radius: '50%',
            data: [
              {
                value: this.accountInfo.account_balance || 0,
                name: '可用资金'
              },
              {
                value: this.accountInfo.frozen_balance || 0,
                name: '冻结资金'
              },
              {
                value: this.accountInfo.market_value || 0,
                name: '持仓市值'
              }
            ],
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            }
          }
        ]
      }
      
      this.assetChartInstance.setOption(option)
    },
    
    updateTradeChart() {
      if (!this.tradeChartInstance || !this.recentTrades.length) {
        // 如果没有数据，显示空图表
        const emptyOption = {
          title: {
            text: '暂无交易数据',
            subtext: '完成交易后将显示趋势',
            left: 'center',
            top: 'center',
            textStyle: {
              color: '#999',
              fontSize: 14
            },
            subtextStyle: {
              color: '#ccc',
              fontSize: 12
            }
          }
        }
        this.tradeChartInstance.setOption(emptyOption)
        return
      }

      // 按日期分组交易数据
      const tradesByDate = {}
      const buyAmountsByDate = {}
      const sellAmountsByDate = {}

      this.recentTrades.forEach(trade => {
        const date = new Date(trade.trade_time)
        const dateStr = `${date.getMonth() + 1}/${date.getDate()}`

        if (!tradesByDate[dateStr]) {
          tradesByDate[dateStr] = 0
          buyAmountsByDate[dateStr] = 0
          sellAmountsByDate[dateStr] = 0
        }

        tradesByDate[dateStr] += trade.trade_amount

        if (trade.trade_type === 'BUY') {
          buyAmountsByDate[dateStr] += trade.trade_amount
        } else if (trade.trade_type === 'SELL') {
          sellAmountsByDate[dateStr] += trade.trade_amount
        }
      })

      const dates = Object.keys(tradesByDate).sort()
      const buyAmounts = dates.map(date => buyAmountsByDate[date] || 0)
      const sellAmounts = dates.map(date => sellAmountsByDate[date] || 0)
      const totalAmounts = dates.map(date => tradesByDate[date] || 0)

      const option = {
        title: {
          text: '交易金额趋势',
          left: 'left',
          textStyle: {
            fontSize: 14,
            fontWeight: 'normal'
          }
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross',
            label: {
              backgroundColor: '#6a7985'
            }
          },
          formatter: function(params) {
            let result = params[0].axisValue + '<br/>'
            params.forEach(param => {
              result += `${param.marker}${param.seriesName}: ¥${param.value.toFixed(2)}<br/>`
            })
            return result
          }
        },
        legend: {
          data: ['买入金额', '卖出金额', '总交易额'],
          top: 'bottom',
          textStyle: {
            fontSize: 12
          }
        },
        grid: {
          left: '8%',
          right: '4%',
          bottom: '20%',
          top: '20%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: dates,
          axisLabel: {
            fontSize: 11
          },
          name: '交易日期',
          nameLocation: 'middle',
          nameGap: 25,
          nameTextStyle: {
            fontSize: 12,
            color: '#666'
          }
        },
        yAxis: {
          type: 'value',
          axisLabel: {
            formatter: function(value) {
              if (value >= 10000) {
                return '¥' + (value / 10000).toFixed(1) + 'w'
              }
              return '¥' + value.toFixed(0)
            },
            fontSize: 11
          },
          name: '交易金额',
          nameLocation: 'middle',
          nameGap: 50,
          nameTextStyle: {
            fontSize: 12,
            color: '#666'
          },
          splitLine: {
            lineStyle: {
              type: 'dashed',
              color: '#e6e6e6'
            }
          }
        },
        series: [
          {
            name: '买入金额',
            type: 'line',
            data: buyAmounts,
            smooth: true,
            symbol: 'circle',
            symbolSize: 6,
            lineStyle: {
              width: 2,
              color: '#67c23a' // 买入用绿色（支出）
            },
            itemStyle: {
              color: '#67c23a'
            },
            areaStyle: {
              color: {
                type: 'linear',
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [{
                  offset: 0, color: 'rgba(103, 194, 58, 0.3)'
                }, {
                  offset: 1, color: 'rgba(103, 194, 58, 0.1)'
                }]
              }
            }
          },
          {
            name: '卖出金额',
            type: 'line',
            data: sellAmounts,
            smooth: true,
            symbol: 'circle',
            symbolSize: 6,
            lineStyle: {
              width: 2,
              color: '#f56c6c' // 卖出用红色（收入）
            },
            itemStyle: {
              color: '#f56c6c'
            },
            areaStyle: {
              color: {
                type: 'linear',
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [{
                  offset: 0, color: 'rgba(245, 108, 108, 0.3)'
                }, {
                  offset: 1, color: 'rgba(245, 108, 108, 0.1)'
                }]
              }
            }
          },
          {
            name: '总交易额',
            type: 'line',
            data: totalAmounts,
            smooth: true,
            symbol: 'diamond',
            symbolSize: 8,
            lineStyle: {
              width: 3,
              color: '#409eff',
              type: 'dashed'
            },
            itemStyle: {
              color: '#409eff'
            }
          }
        ]
      }

      this.tradeChartInstance.setOption(option)
    },
    
    getStatusType(status) {
      const statusTypes = {
        'COMPLETED': 'success',
        'PENDING': 'warning',
        'CANCELLED': 'info',
        'FAILED': 'danger'
      }
      return statusTypes[status] || 'default'
    },
    
    refreshAccount() {
      this.loadAccountData()
    },
    
    goToPositions() {
      this.$router.push('/stock/positions')
    },
    
    goToRecords() {
      this.$router.push('/stock/records')
    },
    
    goToStockDetail(tsCode) {
      this.$router.push(`/stock/detail/${tsCode}`)
    },
    
    goToTrade(tsCode, type = 'buy') {
      this.$router.push(`/stock/trade/${tsCode}?type=${type}`)
    }
  }
}
</script>

<style scoped>
.account-container {
  padding: 20px;
}

.overview-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.account-item {
  text-align: center;
  padding: 15px;
}

.account-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 8px;
}

.account-label {
  font-size: 14px;
  color: #999;
}

.empty-data {
  padding: 20px 0;
}

.text-success {
  color: #f56c6c; /* A股红涨 */
}

.text-danger {
  color: #67c23a; /* A股绿跌 */
}

.el-link {
  color: #409eff;
  text-decoration: none;
}

.el-link:hover {
  color: #66b1ff;
}
</style>