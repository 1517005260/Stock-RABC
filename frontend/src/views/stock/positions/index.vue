<template>
  <div class="positions-container">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>我的持仓</span>
          <el-button @click="refreshPositions" :loading="loading">刷新</el-button>
        </div>
      </template>
      
      <el-table :data="positionList" style="width: 100%" v-loading="loading" @sort-change="handleSortChange">
        <el-table-column prop="ts_code" label="股票代码" width="120" sortable="custom">
          <template #default="scope">
            <el-link @click="goToStockDetail(scope.row.ts_code)">{{ scope.row.ts_code }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="stock_name" label="股票名称" width="150"></el-table-column>
        <el-table-column prop="position_shares" label="持仓数量" width="120" align="right"></el-table-column>
        <el-table-column prop="available_shares" label="可卖数量" width="120" align="right"></el-table-column>
        <el-table-column prop="cost_price" label="成本价" width="120" align="right" sortable="custom">
          <template #default="scope">
            ¥{{ scope.row.cost_price?.toFixed(2) || '--' }}
          </template>
        </el-table-column>
        <el-table-column prop="current_price" label="现价" width="120" align="right" sortable="custom">
          <template #default="scope">
            ¥{{ scope.row.current_price?.toFixed(2) || '--' }}
          </template>
        </el-table-column>
        <el-table-column prop="market_value" label="市值" width="120" align="right" sortable="custom">
          <template #default="scope">
            ¥{{ scope.row.market_value?.toFixed(2) || '--' }}
          </template>
        </el-table-column>
        <el-table-column prop="profit_loss" label="盈亏" width="120" align="right" sortable="custom">
          <template #default="scope">
            <span :class="{
              'text-success': scope.row.profit_loss > 0,
              'text-danger': scope.row.profit_loss < 0,
              'text-muted': scope.row.profit_loss === 0
            }">
              {{ scope.row.profit_loss > 0 ? '+' : '' }}{{ scope.row.profit_loss?.toFixed(2) || '--' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="profit_rate" label="盈亏比例" width="120" align="right" sortable="custom">
          <template #default="scope">
            <span :class="{
              'text-success': scope.row.profit_rate > 0,
              'text-danger': scope.row.profit_rate < 0,
              'text-muted': scope.row.profit_rate === 0
            }">
              {{ scope.row.profit_rate > 0 ? '+' : '' }}{{ scope.row.profit_rate?.toFixed(2) || '--' }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="scope">
            <el-button size="small" type="primary" @click="goToTrade(scope.row.ts_code, 'sell')">卖出</el-button>
            <el-button size="small" @click="goToStockDetail(scope.row.ts_code)">详情</el-button>
          </template>
        </el-table-column>
        
        <template #empty>
          <div class="empty-data">
            <el-empty description="暂无持仓数据"></el-empty>
          </div>
        </template>
      </el-table>
      
      <div class="pagination-wrapper" v-if="total > 0">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange">
        </el-pagination>
      </div>
    </el-card>
    
    <!-- 持仓统计卡片 -->
    <el-card class="stats-card">
      <template #header>
        <span>持仓统计</span>
      </template>
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value">{{ positionStats.total_positions || 0 }}</div>
            <div class="stat-label">持仓品种</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value">¥{{ positionStats.total_market_value?.toFixed(2) || '0.00' }}</div>
            <div class="stat-label">总市值</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value" :class="{
              'text-success': positionStats.total_profit_loss > 0,
              'text-danger': positionStats.total_profit_loss < 0
            }">
              {{ positionStats.total_profit_loss > 0 ? '+' : '' }}¥{{ positionStats.total_profit_loss?.toFixed(2) || '0.00' }}
            </div>
            <div class="stat-label">总盈亏</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value" :class="{
              'text-success': positionStats.total_profit_rate > 0,
              'text-danger': positionStats.total_profit_rate < 0
            }">
              {{ positionStats.total_profit_rate > 0 ? '+' : '' }}{{ positionStats.total_profit_rate?.toFixed(2) || '0.00' }}%
            </div>
            <div class="stat-label">总盈亏比例</div>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script>
import { getUserPositions } from '@/api/trading'
import { ElMessage } from 'element-plus'

export default {
  name: 'StockPositions',
  data() {
    return {
      loading: false,
      positionList: [],
      currentPage: 1,
      pageSize: 20,
      total: 0,
      sortField: '',
      sortOrder: '',
      positionStats: {
        total_positions: 0,
        total_market_value: 0,
        total_profit_loss: 0,
        total_profit_rate: 0
      }
    }
  },
  mounted() {
    this.loadPositions()
  },
  methods: {
    async loadPositions() {
      this.loading = true
      try {
        const params = {
          page: this.currentPage,
          pageSize: this.pageSize
        }
        
        if (this.sortField && this.sortOrder) {
          params.sort_field = this.sortField
          params.sort_order = this.sortOrder
        }
        
        const response = await getUserPositions(params)
        
        if (response.data.code === 200) {
          this.positionList = response.data.data.list || []
          this.total = response.data.data.total || 0
          this.calculateStats()
        } else {
          ElMessage.error(response.data.msg || '加载持仓数据失败')
        }
      } catch (error) {
        console.error('加载持仓数据失败:', error)
        ElMessage.error('加载持仓数据失败，请稍后重试')
        this.positionList = []
        this.total = 0
      }
      this.loading = false
    },
    
    calculateStats() {
      if (!this.positionList || this.positionList.length === 0) {
        this.positionStats = {
          total_positions: 0,
          total_market_value: 0,
          total_profit_loss: 0,
          total_profit_rate: 0
        }
        return
      }
      
      const totalPositions = this.positionList.length
      const totalMarketValue = this.positionList.reduce((sum, pos) => sum + (pos.market_value || 0), 0)
      const totalProfitLoss = this.positionList.reduce((sum, pos) => sum + (pos.profit_loss || 0), 0)
      const totalCostValue = this.positionList.reduce((sum, pos) => {
        return sum + ((pos.cost_price || 0) * (pos.position_shares || 0))
      }, 0)
      
      this.positionStats = {
        total_positions: totalPositions,
        total_market_value: totalMarketValue,
        total_profit_loss: totalProfitLoss,
        total_profit_rate: totalCostValue > 0 ? (totalProfitLoss / totalCostValue) * 100 : 0
      }
    },
    
    refreshPositions() {
      this.currentPage = 1
      this.loadPositions()
    },
    
    handleSortChange({ prop, order }) {
      this.sortField = prop
      this.sortOrder = order === 'ascending' ? 'asc' : (order === 'descending' ? 'desc' : '')
      this.loadPositions()
    },
    
    handleSizeChange(val) {
      this.pageSize = val
      this.currentPage = 1
      this.loadPositions()
    },
    
    handleCurrentChange(val) {
      this.currentPage = val
      this.loadPositions()
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
.positions-container {
  padding: 20px;
}

.box-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.empty-data {
  padding: 40px 0;
}

.pagination-wrapper {
  margin-top: 20px;
  text-align: right;
}

.stats-card {
  margin-top: 20px;
}

.stat-item {
  text-align: center;
  padding: 10px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: #999;
}

.text-success {
  color: #67c23a;
}

.text-danger {
  color: #f56c6c;
}

.text-muted {
  color: #909399;
}

.el-link {
  color: #409eff;
  text-decoration: none;
}

.el-link:hover {
  color: #66b1ff;
}
</style>