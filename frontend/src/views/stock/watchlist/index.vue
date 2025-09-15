<template>
  <div class="app-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>我的自选股</span>
          <div class="header-actions">
            <el-button @click="showAddDialog = true">
              <el-icon><Plus /></el-icon>
              添加自选股
            </el-button>
            <el-button @click="refreshWatchlist">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <!-- 统计信息 -->
      <el-row :gutter="20" class="stats-row">
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-number">{{ watchlist.length }}</div>
            <div class="stat-label">自选股票</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-number up">{{ upCount }}</div>
            <div class="stat-label">上涨</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-number down">{{ downCount }}</div>
            <div class="stat-label">下跌</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-number">{{ flatCount }}</div>
            <div class="stat-label">平盘</div>
          </div>
        </el-col>
      </el-row>

      <!-- 自选股列表 -->
      <div class="watchlist-container" v-loading="loading">
        <el-table
          :data="watchlist"
          style="width: 100%"
          @row-click="goToStock"
          row-style="cursor: pointer"
        >
          <el-table-column prop="name" label="股票名称" width="120">
            <template #default="scope">
              <div class="stock-name">
                <strong>{{ scope.row.name || scope.row.stock_name || scope.row.ts_code }}</strong>
                <div class="stock-code">{{ scope.row.ts_code }}</div>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column prop="current_price" label="现价" width="100" align="right">
            <template #default="scope">
              <span :class="getPriceClass(scope.row.pct_chg)">
                {{ formatPrice(scope.row.current_price) }}
              </span>
            </template>
          </el-table-column>

          <el-table-column prop="change" label="涨跌" width="100" align="right">
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

          <el-table-column prop="volume" label="成交量" width="120" align="right">
            <template #default="scope">
              {{ formatVolume(scope.row.volume) }}
            </template>
          </el-table-column>

          <el-table-column prop="turnover_rate" label="换手率" width="100" align="right">
            <template #default="scope">
              {{ scope.row.turnover_rate && scope.row.turnover_rate > 0 ? scope.row.turnover_rate.toFixed(2) + '%' : '--' }}
            </template>
          </el-table-column>

          <el-table-column prop="pe_ratio" label="市盈率" width="100" align="right">
            <template #default="scope">
              {{ scope.row.pe_ratio && scope.row.pe_ratio > 0 ? scope.row.pe_ratio.toFixed(2) : '--' }}
            </template>
          </el-table-column>

          <el-table-column prop="market_cap" label="市值" width="120" align="right">
            <template #default="scope">
              {{ formatMarketCap(scope.row.market_cap) }}
            </template>
          </el-table-column>

          <el-table-column label="操作" width="150" align="center">
            <template #default="scope">
              <el-button text size="small" @click.stop="goToStock(scope.row)">
                详情
              </el-button>
              <el-button text size="small" @click.stop="goToTrade(scope.row)">
                交易
              </el-button>
              <el-button text size="small" type="danger" @click.stop="removeFromWatchlist(scope.row)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 空状态 -->
        <el-empty v-if="!loading && !watchlist.length" description="还没有添加自选股">
          <el-button type="primary" @click="showAddDialog = true">
            添加自选股
          </el-button>
        </el-empty>
      </div>
    </el-card>

    <!-- 添加自选股对话框 -->
    <el-dialog
      v-model="showAddDialog"
      title="添加自选股"
      width="600px"
      @close="resetAddForm"
    >
      <div class="add-stock-form">
        <el-input
          v-model="searchKeyword"
          placeholder="请输入股票代码或名称搜索"
          @input="searchStocks"
          clearable
        >
          <template #append>
            <el-button @click="searchStocks">
              <el-icon><Search /></el-icon>
            </el-button>
          </template>
        </el-input>

        <div class="search-results" v-if="searchResults.length">
          <div class="results-header">搜索结果:</div>
          <div
            v-for="stock in searchResults"
            :key="stock.ts_code"
            class="result-item"
            @click="addToWatchlist(stock)"
          >
            <div class="stock-info">
              <span class="stock-name">{{ stock.name }}</span>
              <span class="stock-code">{{ stock.ts_code }}</span>
            </div>
            <div class="stock-price">
              <span>{{ formatPrice(stock.current_price) }}</span>
              <span :class="getPriceClass(stock.pct_chg)">
                {{ formatPercent(stock.pct_chg) }}
              </span>
            </div>
          </div>
        </div>

        <div class="popular-stocks">
          <div class="popular-header">热门股票:</div>
          <el-row :gutter="10">
            <el-col :span="12" v-for="stock in popularStocks" :key="stock.ts_code">
              <div class="popular-item" @click="addToWatchlist(stock)">
                <div class="stock-info">
                  <span class="stock-name">{{ stock.name }}</span>
                  <span class="stock-code">{{ stock.ts_code }}</span>
                </div>
                <div class="stock-price">
                  <span class="current-price">{{ formatPrice(stock.close || stock.current_price) }}</span>
                  <span :class="getPriceClass(stock.pct_chg)" class="price-change">
                    {{ formatPercent(stock.pct_chg) }}
                  </span>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
      </div>

      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { Plus, Refresh, Search } from '@element-plus/icons-vue'
import { getStockList, getStockRealtime, getHotStocks } from '@/api/stock'
import { getUserWatchList, addToWatchList, removeFromWatchList } from '@/api/trading'

export default {
  name: 'StockWatchlist',
  components: {
    Plus,
    Refresh,
    Search
  },
  data() {
    return {
      loading: false,
      watchlist: [],
      showAddDialog: false,
      searchKeyword: '',
      searchResults: [],
      popularStocks: []
    }
  },
  computed: {
    upCount() {
      return this.watchlist.filter(stock => stock.pct_chg > 0).length
    },
    downCount() {
      return this.watchlist.filter(stock => stock.pct_chg < 0).length
    },
    flatCount() {
      return this.watchlist.filter(stock => stock.pct_chg === 0).length
    }
  },
  async created() {
    await this.loadWatchlist()
    this.loadPopularStocks()
  },
  methods: {
    async loadWatchlist() {
      this.loading = true
      try {
        // 从后端API获取自选股
        const response = await getUserWatchList()

        if (response.data.code === 200) {
          this.watchlist = response.data.data || []
          console.log('从API获取自选股成功:', this.watchlist)
        } else {
          console.error('API获取自选股失败:', response.data.msg)

          // 如果API失败，回退到localStorage方式
          const savedCodes = JSON.parse(localStorage.getItem('watchlist_codes') || '[]')

          if (savedCodes.length === 0) {
            this.watchlist = []
          } else {
            // 获取实时数据
            const promises = savedCodes.map(code => this.getStockData(code))
            const results = await Promise.allSettled(promises)

            this.watchlist = results
              .filter(result => result.status === 'fulfilled' && result.value)
              .map(result => {
                const stock = result.value
                return {
                  ...stock,
                  name: stock.name || stock.stock_name || '未知股票',
                  stock_name: stock.name || stock.stock_name || '未知股票'
                }
              })

            console.log('从localStorage获取自选股:', this.watchlist)
          }
        }
      } catch (error) {
        console.error('加载自选股失败:', error)
        this.watchlist = []
      } finally {
        this.loading = false
      }
    },
    async getStockData(code) {
      try {
        const response = await getStockRealtime(code)
        if (response.data.code === 200) {
          return response.data.data
        }
        return null
      } catch (error) {
        console.error(`获取股票 ${code} 数据失败:`, error)
        return null
      }
    },
    async loadPopularStocks() {
      try {
        const response = await getHotStocks({ limit: 8 })
        if (response.data.code === 200) {
          this.popularStocks = response.data.data.list || response.data.data || []
          console.log('热门股票加载成功:', this.popularStocks.length, '只')
        }
      } catch (error) {
        console.error('加载热门股票失败:', error)
        this.popularStocks = []
      }
    },
    async searchStocks() {
      if (!this.searchKeyword.trim()) {
        this.searchResults = []
        return
      }

      try {
        const response = await getStockList({
          keyword: this.searchKeyword,
          limit: 10
        })
        
        if (response.data.code === 200) {
          this.searchResults = response.data.data
        } else {
          this.searchResults = []
        }
      } catch (error) {
        console.error('搜索股票失败:', error)
        this.searchResults = []
      }
    },
    async refreshWatchlist() {
      await this.loadWatchlist()
      this.$message.success('自选股已刷新')
    },
    async addToWatchlist(stock) {
      // 检查是否已存在
      const exists = this.watchlist.find(item => item.ts_code === stock.ts_code)
      if (exists) {
        this.$message.warning('该股票已在自选列表中')
        return
      }

      try {
        // 调用后端API添加自选股
        const response = await addToWatchList({
          ts_code: stock.ts_code
        })

        if (response.data.code === 200) {
          // API添加成功后更新前端列表
          this.watchlist.unshift({
            ts_code: stock.ts_code,
            stock_name: stock.name || stock.stock_name || '未知股票',
            name: stock.name || stock.stock_name || '未知股票',
            current_price: stock.current_price || stock.close || 0,
            change: stock.change || 0,
            pct_chg: stock.pct_chg || 0,
            volume: stock.volume || stock.vol || 0,
            amount: stock.amount || 0,
            turnover_rate: stock.turnover_rate || 0,
            pe_ratio: stock.pe_ratio || 0,
            market_cap: stock.market_cap || 0
          })

          this.$message.success(`已添加 ${stock.name} 到自选股`)
          this.showAddDialog = false
          this.resetAddForm()
        } else {
          throw new Error(response.data.msg || '添加失败')
        }
      } catch (error) {
        console.error('添加自选股失败:', error)

        // API失败时回退到localStorage
        this.watchlist.unshift({
          ts_code: stock.ts_code,
          stock_name: stock.name || stock.stock_name || '未知股票',
          name: stock.name || stock.stock_name || '未知股票',
          current_price: stock.current_price || stock.close || 0,
          change: stock.change || 0,
          pct_chg: stock.pct_chg || 0,
          volume: stock.volume || stock.vol || 0,
          amount: stock.amount || 0,
          turnover_rate: stock.turnover_rate || 0,
          pe_ratio: stock.pe_ratio || 0,
          market_cap: stock.market_cap || 0
        })
        const codes = this.watchlist.map(item => item.ts_code)
        localStorage.setItem('watchlist_codes', JSON.stringify(codes))

        this.$message.success(`已添加 ${stock.name} 到自选股 (本地存储)`)
        this.showAddDialog = false
        this.resetAddForm()
      }
    },
    removeFromWatchlist(stock) {
      this.$confirm(`确定要从自选股中删除 ${stock.name} 吗？`, '确认删除', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(async () => {
        try {
          // 调用后端API删除自选股
          const response = await removeFromWatchList(stock.ts_code)

          if (response.data.code === 200) {
            // API删除成功后更新前端列表
            const index = this.watchlist.findIndex(item => item.ts_code === stock.ts_code)
            if (index > -1) {
              this.watchlist.splice(index, 1)
            }
            this.$message.success(`已删除 ${stock.name}`)
          } else {
            throw new Error(response.data.msg || '删除失败')
          }
        } catch (error) {
          console.error('删除自选股失败:', error)

          // API失败时回退到localStorage
          const index = this.watchlist.findIndex(item => item.ts_code === stock.ts_code)
          if (index > -1) {
            this.watchlist.splice(index, 1)

            // 更新本地存储
            const codes = this.watchlist.map(item => item.ts_code)
            localStorage.setItem('watchlist_codes', JSON.stringify(codes))

            this.$message.success(`已删除 ${stock.name} (本地存储)`)
          }
        }
      }).catch(() => {
        // 取消删除
      })
    },
    resetAddForm() {
      this.searchKeyword = ''
      this.searchResults = []
    },
    goToStock(stock) {
      this.$router.push(`/stock/detail/${stock.ts_code}`)
    },
    goToTrade(stock) {
      this.$router.push(`/stock/trade/${stock.ts_code}`)
    },
    getPriceClass(pctChg) {
      if (!pctChg) return ''
      return pctChg > 0 ? 'price-up' : pctChg < 0 ? 'price-down' : ''
    },
    formatPrice(price) {
      if (!price || price === 0) return '--'
      return parseFloat(price).toFixed(2)
    },
    formatChange(value) {
      if (!value || value === 0) return '--'
      const formatted = parseFloat(value).toFixed(2)
      return value > 0 ? `+${formatted}` : formatted
    },
    formatPercent(value) {
      if (!value || value === 0) return '--'
      const formatted = parseFloat(value).toFixed(2)
      return value > 0 ? `+${formatted}%` : `${formatted}%`
    },
    formatVolume(volume) {
      if (!volume || volume === 0) return '--'
      if (volume >= 100000000) {
        return (volume / 100000000).toFixed(2) + '亿手'
      } else if (volume >= 10000) {
        return (volume / 10000).toFixed(0) + '万手'
      }
      return volume.toLocaleString() + '手'
    },
    formatMarketCap(marketCap) {
      if (!marketCap || marketCap === 0) return '--'
      if (marketCap >= 1000000000000) {
        return (marketCap / 1000000000000).toFixed(2) + '万亿'
      } else if (marketCap >= 100000000) {
        return (marketCap / 100000000).toFixed(0) + '亿'
      }
      return (marketCap / 100000000).toFixed(2) + '亿'
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
  gap: 10px;
}

.stats-row {
  margin-bottom: 20px;
  padding: 20px 0;
  background-color: #f9f9f9;
  border-radius: 8px;
}

.stat-item {
  text-align: center;
}

.stat-number {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 5px;
}

.stat-number.up {
  color: #dd4b39;
}

.stat-number.down {
  color: #00a65a;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.watchlist-container {
  min-height: 400px;
}

.stock-name {
  line-height: 1.2;
}

.stock-code {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.add-stock-form {
  padding: 10px 0;
}

.search-results {
  margin: 20px 0;
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
}

.results-header {
  padding: 10px 15px;
  background-color: #f5f7fa;
  font-weight: bold;
  border-bottom: 1px solid #e4e7ed;
}

.result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.3s;
}

.result-item:hover {
  background-color: #f9f9f9;
}

.result-item:last-child {
  border-bottom: none;
}

.stock-info {
  display: flex;
  flex-direction: column;
}

.stock-price {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.popular-stocks {
  margin-top: 20px;
}

.popular-header {
  margin-bottom: 10px;
  font-weight: bold;
}

.popular-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  margin-bottom: 8px;
  background-color: #f5f7fa;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.popular-item:hover {
  background-color: #e6f7ff;
}

.popular-item .stock-info {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.popular-item .stock-price {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.popular-item .current-price {
  font-size: 12px;
  font-weight: bold;
}

.popular-item .price-change {
  font-size: 11px;
  margin-top: 2px;
}

.price-up {
  color: #dd4b39;
}

.price-down {
  color: #00a65a;
}
</style>