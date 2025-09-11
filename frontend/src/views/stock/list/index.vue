<template>
  <div class="app-container">
    <el-card>
      <!-- 搜索区域 -->
      <div class="filter-container">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-input
              v-model="queryParams.keyword"
              placeholder="请输入股票名称或代码"
              clearable
              @keyup.enter="handleQuery"
            />
          </el-col>
          <el-col :span="4">
            <el-select v-model="queryParams.industry" placeholder="行业筛选" clearable>
              <el-option
                v-for="industry in industries"
                :key="industry"
                :label="industry"
                :value="industry"
              />
            </el-select>
          </el-col>
          <el-col :span="4">
            <el-select v-model="queryParams.market" placeholder="市场类型" clearable>
              <el-option label="主板" value="主板" />
              <el-option label="创业板" value="创业板" />
              <el-option label="科创板" value="科创板" />
              <el-option label="中小板" value="中小板" />
            </el-select>
          </el-col>
          <el-col :span="6">
            <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
            <el-button icon="Refresh" @click="resetQuery">重置</el-button>
          </el-col>
        </el-row>
      </div>

      <!-- 股票列表 -->
      <el-table
        v-loading="loading"
        :data="stockList"
        style="width: 100%"
        @row-click="handleRowClick"
        row-style="cursor: pointer"
      >
        <el-table-column prop="symbol" label="股票代码" width="100" />
        <el-table-column prop="name" label="股票名称" width="150" />
        <el-table-column prop="current_price" label="现价" width="100" align="right">
          <template #default="scope">
            <span :class="getPriceClass(scope.row.pct_chg)">
              {{ scope.row.current_price || '--' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="change" label="涨跌额" width="100" align="right">
          <template #default="scope">
            <span :class="getPriceClass(scope.row.pct_chg)">
              {{ formatChange(scope.row.change) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="pct_chg" label="涨跌幅" width="100" align="right">
          <template #default="scope">
            <span :class="getPriceClass(scope.row.pct_chg)">
              {{ formatPercent(scope.row.pct_chg) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="volume" label="成交量(手)" width="120" align="right">
          <template #default="scope">
            {{ formatVolume(scope.row.volume) }}
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="成交额(千元)" width="120" align="right">
          <template #default="scope">
            {{ formatAmount(scope.row.amount) }}
          </template>
        </el-table-column>
        <el-table-column prop="industry" label="行业" width="120" />
        <el-table-column prop="market" label="市场" width="100" />
        <el-table-column prop="trade_date" label="交易日期" width="120" />
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button
              type="primary"
              size="small"
              @click.stop="viewDetail(scope.row)"
            >
              详情
            </el-button>
            <el-button
              type="success"
              size="small"
              @click.stop="startTrade(scope.row)"
            >
              交易
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-show="total > 0"
        :current-page="queryParams.page"
        :page-size="queryParams.pageSize"
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
import { getStockList, getIndustries } from '@/api/stock'

export default {
  name: 'StockList',
  data() {
    return {
      loading: false,
      stockList: [],
      total: 0,
      industries: [],
      queryParams: {
        page: 1,
        pageSize: 20,
        keyword: '',
        industry: '',
        market: ''
      }
    }
  },
  created() {
    this.getList()
    this.getIndustriesList()
  },
  methods: {
    async getList() {
      this.loading = true
      try {
        const response = await getStockList(this.queryParams)
        if (response.data.code === 200) {
          this.stockList = response.data.data.list
          this.total = response.data.data.total
        } else {
          this.$message.error(response.data.msg)
        }
      } catch (error) {
        this.$message.error('获取股票列表失败')
      } finally {
        this.loading = false
      }
    },
    async getIndustriesList() {
      try {
        const response = await getIndustries()
        if (response.data.code === 200) {
          this.industries = response.data.data
        }
      } catch (error) {
        console.error('获取行业列表失败:', error)
      }
    },
    handleQuery() {
      this.queryParams.page = 1
      this.getList()
    },
    resetQuery() {
      this.queryParams = {
        page: 1,
        pageSize: 20,
        keyword: '',
        industry: '',
        market: ''
      }
      this.getList()
    },
    handleSizeChange(val) {
      this.queryParams.pageSize = val
      this.queryParams.page = 1
      this.getList()
    },
    handleCurrentChange(val) {
      this.queryParams.page = val
      this.getList()
    },
    handleRowClick(row) {
      this.viewDetail(row)
    },
    viewDetail(row) {
      this.$router.push(`/stock/detail/${row.ts_code}`)
    },
    startTrade(row) {
      this.$router.push(`/stock/trade/${row.ts_code}`)
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
    formatVolume(value) {
      if (!value) return '--'
      if (value >= 10000) {
        return (value / 10000).toFixed(1) + '万'
      }
      return value.toLocaleString()
    },
    formatAmount(value) {
      if (!value) return '--'
      if (value >= 100000) {
        return (value / 100000).toFixed(1) + '亿'
      } else if (value >= 10000) {
        return (value / 10000).toFixed(1) + '万'
      }
      return value.toLocaleString()
    }
  }
}
</script>

<style scoped>
.app-container {
  padding: 20px;
}

.filter-container {
  margin-bottom: 20px;
}

.price-up {
  color: #f56c6c;
}

.price-down {
  color: #67c23a;
}

.el-table .el-table__row:hover {
  background-color: #f5f7fa;
}
</style>