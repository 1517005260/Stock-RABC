<template>
  <div class="stock-holders-container">
    <div 
      ref="chartContainer" 
      class="chart-container"
      :style="{ width: '100%', height: chartHeight }"
      v-loading="loading"
    ></div>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import { getStockHolders } from '@/api/stock'
import { markRaw } from 'vue'

export default {
  name: 'StockHoldersChart',
  props: {
    tsCode: {
      type: String,
      required: true
    },
    chartHeight: {
      type: String,
      default: '300px'
    }
  },
  data() {
    return {
      chart: null,
      loading: false,
      holdersData: []
    }
  },
  mounted() {
    this.initChart()
    this.loadHoldersData()
  },
  beforeUnmount() {
    if (this.chart) {
      this.chart.dispose()
    }
  },
  watch: {
    tsCode: {
      handler() {
        this.loadHoldersData()
      },
      immediate: false
    }
  },
  methods: {
    initChart() {
      if (this.$refs.chartContainer) {
        // 使用 markRaw 防止 Vue 反应式系统干扰 ECharts 实例
        this.chart = markRaw(echarts.init(this.$refs.chartContainer))
        window.addEventListener('resize', this.handleResize)
      }
    },
    
    handleResize() {
      if (this.chart) {
        this.chart.resize()
      }
    },
    
    async loadHoldersData() {
      if (!this.tsCode) return
      
      this.loading = true
      try {
        const response = await getStockHolders(this.tsCode)
        
        if (response.data.code === 200) {
          this.holdersData = response.data.data
          this.renderChart()
        } else {
          this.$message.error(response.data.msg || '获取持股数据失败')
        }
      } catch (error) {
        console.error('加载持股数据失败:', error)
        this.$message.error('加载持股数据失败')
      } finally {
        this.loading = false
      }
    },
    
    renderChart() {
      if (!this.chart || !this.holdersData || !Array.isArray(this.holdersData) || !this.holdersData.length) return
      
      // 过滤和验证数据
      const validData = this.holdersData.filter(item => 
        item && 
        typeof item === 'object' && 
        item.name && 
        typeof item.percentage === 'number' && 
        !isNaN(item.percentage)
      )
      
      if (validData.length === 0) {
        // 如果没有有效数据，显示空状态
        const emptyOption = {
          title: {
            text: '暂无持股数据',
            left: 'center',
            top: 'middle',
            textStyle: {
              color: '#999',
              fontSize: 14
            }
          },
          series: []
        }
        this.chart.setOption(emptyOption, true)
        return
      }
      
      const option = {
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: {c}% ({d}%)'
        },
        legend: {
          orient: 'vertical',
          left: '10px',
          top: '20px',
          data: validData.map(item => item.name),
          textStyle: {
            fontSize: 12
          },
          itemWidth: 14,
          itemHeight: 14,
          itemGap: 8
        },
        series: [
          {
            name: '持股比例',
            type: 'pie',
            radius: ['20%', '40%'],
            center: ['65%', '80%'],
            data: validData.map(item => ({
              name: item.name,
              value: parseFloat(item.percentage) || 0
            })),
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            },
            label: {
              show: true,
              formatter: '{c}%',
              fontSize: 12
            },
            labelLine: {
              show: true,
              length: 10,
              length2: 10
            }
          }
        ],
        color: [
          '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de',
          '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#ffb64d'
        ]
      }
      
      this.chart.setOption(option, true)
    }
  }
}
</script>

<style scoped>
.stock-holders-container {
  width: 100%;
  background: #fff;
  border-radius: 4px;
  padding: 10px;
}

.chart-container {
  border-radius: 4px;
}
</style>