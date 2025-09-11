<template>
  <div class="trade-records-container">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>交易记录</span>
          <div class="header-controls">
            <el-select v-model="filterType" placeholder="交易类型" clearable @change="loadRecords">
              <el-option label="全部" value=""></el-option>
              <el-option label="买入" value="BUY"></el-option>
              <el-option label="卖出" value="SELL"></el-option>
            </el-select>
            <el-select v-model="filterStatus" placeholder="交易状态" clearable @change="loadRecords">
              <el-option label="全部" value=""></el-option>
              <el-option label="已完成" value="COMPLETED"></el-option>
              <el-option label="待成交" value="PENDING"></el-option>
              <el-option label="已撤销" value="CANCELLED"></el-option>
            </el-select>
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              @change="loadRecords">
            </el-date-picker>
            <el-button @click="refreshRecords" :loading="loading">刷新</el-button>
          </div>
        </div>
      </template>
      
      <el-table :data="recordsList" style="width: 100%" v-loading="loading" @sort-change="handleSortChange">
        <el-table-column prop="trade_time" label="交易时间" width="180" sortable="custom">
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
        <el-table-column prop="trade_type_display" label="交易类型" width="100" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.trade_type === 'BUY' ? 'danger' : 'success'" size="small">
              {{ scope.row.trade_type_display || scope.row.trade_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="trade_price" label="交易价格" width="120" align="right" sortable="custom">
          <template #default="scope">
            ¥{{ scope.row.trade_price?.toFixed(2) || '--' }}
          </template>
        </el-table-column>
        <el-table-column prop="trade_shares" label="交易数量" width="120" align="right" sortable="custom">
          <template #default="scope">
            {{ scope.row.trade_shares || '--' }}
          </template>
        </el-table-column>
        <el-table-column prop="trade_amount" label="交易金额" width="140" align="right" sortable="custom">
          <template #default="scope">
            ¥{{ scope.row.trade_amount?.toFixed(2) || '--' }}
          </template>
        </el-table-column>
        <el-table-column prop="commission" label="手续费" width="100" align="right">
          <template #default="scope">
            ¥{{ scope.row.commission?.toFixed(2) || '--' }}
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
        <el-table-column prop="remark" label="备注" width="200" show-overflow-tooltip></el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="scope">
            <el-button 
              v-if="scope.row.status === 'PENDING'" 
              size="small" 
              type="warning" 
              @click="cancelTrade(scope.row)">
              撤销
            </el-button>
            <el-button size="small" @click="goToStockDetail(scope.row.ts_code)">详情</el-button>
          </template>
        </el-table-column>
        
        <template #empty>
          <div class="empty-data">
            <el-empty description="暂无交易记录"></el-empty>
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
    
    <!-- 交易统计卡片 -->
    <el-card class="stats-card">
      <template #header>
        <span>交易统计</span>
      </template>
      <el-row :gutter="20">
        <el-col :span="4">
          <div class="stat-item">
            <div class="stat-value">{{ tradeStats.total_trades || 0 }}</div>
            <div class="stat-label">总交易笔数</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="stat-item">
            <div class="stat-value">{{ tradeStats.buy_count || 0 }}</div>
            <div class="stat-label">买入笔数</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="stat-item">
            <div class="stat-value">{{ tradeStats.sell_count || 0 }}</div>
            <div class="stat-label">卖出笔数</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="stat-item">
            <div class="stat-value">¥{{ tradeStats.buy_amount?.toFixed(2) || '0.00' }}</div>
            <div class="stat-label">买入金额</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="stat-item">
            <div class="stat-value">¥{{ tradeStats.sell_amount?.toFixed(2) || '0.00' }}</div>
            <div class="stat-label">卖出金额</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="stat-item">
            <div class="stat-value">¥{{ tradeStats.total_commission?.toFixed(2) || '0.00' }}</div>
            <div class="stat-label">总手续费</div>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script>
import { getTradeRecords, cancelTrade, getTradingStats } from '@/api/trading'
import { ElMessage, ElMessageBox } from 'element-plus'

export default {
  name: 'TradeRecords',
  data() {
    return {
      loading: false,
      recordsList: [],
      currentPage: 1,
      pageSize: 20,
      total: 0,
      sortField: '',
      sortOrder: '',
      filterType: '',
      filterStatus: '',
      dateRange: null,
      tradeStats: {
        total_trades: 0,
        buy_count: 0,
        sell_count: 0,
        buy_amount: 0,
        sell_amount: 0,
        total_commission: 0
      }
    }
  },
  mounted() {
    this.loadRecords()
    this.loadStats()
  },
  methods: {
    async loadRecords() {
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
        
        if (this.filterType) {
          params.trade_type = this.filterType
        }
        
        if (this.filterStatus) {
          params.status = this.filterStatus
        }
        
        if (this.dateRange && this.dateRange.length === 2) {
          params.start_date = this.dateRange[0].toISOString().split('T')[0]
          params.end_date = this.dateRange[1].toISOString().split('T')[0]
        }
        
        const response = await getTradeRecords(params)
        
        if (response.data.code === 200) {
          this.recordsList = response.data.data.list || []
          this.total = response.data.data.total || 0
        } else {
          ElMessage.error(response.data.msg || '加载交易记录失败')
        }
      } catch (error) {
        console.error('加载交易记录失败:', error)
        ElMessage.error('加载交易记录失败，请稍后重试')
        this.recordsList = []
        this.total = 0
      }
      this.loading = false
    },
    
    async loadStats() {
      try {
        const response = await getTradingStats()
        
        if (response.data.code === 200) {
          this.tradeStats = response.data.data
        }
      } catch (error) {
        console.error('加载交易统计失败:', error)
      }
    },
    
    async cancelTrade(trade) {
      try {
        await ElMessageBox.confirm(
          `确定要撤销这笔交易吗？\n股票: ${trade.stock_name} (${trade.ts_code})\n类型: ${trade.trade_type_display}\n价格: ¥${trade.trade_price}\n数量: ${trade.trade_shares}`,
          '确认撤销',
          {
            confirmButtonText: '确定撤销',
            cancelButtonText: '取消',
            type: 'warning',
          }
        )
        
        const response = await cancelTrade({
          trade_id: trade.id
        })
        
        if (response.data.code === 200) {
          ElMessage.success('撤销成功')
          this.loadRecords()
          this.loadStats()
        } else {
          ElMessage.error(response.data.msg || '撤销失败')
        }
      } catch (error) {
        if (error !== 'cancel') {
          console.error('撤销交易失败:', error)
          ElMessage.error('撤销失败，请稍后重试')
        }
      }
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
    
    refreshRecords() {
      this.currentPage = 1
      this.loadRecords()
      this.loadStats()
    },
    
    handleSortChange({ prop, order }) {
      this.sortField = prop
      this.sortOrder = order === 'ascending' ? 'asc' : (order === 'descending' ? 'desc' : '')
      this.loadRecords()
    },
    
    handleSizeChange(val) {
      this.pageSize = val
      this.currentPage = 1
      this.loadRecords()
    },
    
    handleCurrentChange(val) {
      this.currentPage = val
      this.loadRecords()
    },
    
    goToStockDetail(tsCode) {
      this.$router.push(`/stock/detail/${tsCode}`)
    }
  }
}
</script>

<style scoped>
.trade-records-container {
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

.header-controls {
  display: flex;
  align-items: center;
  gap: 10px;
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
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: #999;
}

.el-link {
  color: #409eff;
  text-decoration: none;
}

.el-link:hover {
  color: #66b1ff;
}
</style>