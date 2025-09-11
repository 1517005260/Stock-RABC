<template>
  <div class="stock-holders-container">
    <div class="chart-header">
      <h3>股权占比</h3>
    </div>
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
        this.chart = echarts.init(this.$refs.chartContainer)
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
      if (!this.chart || !this.holdersData.length) return
      
      const option = {
        title: {
          text: '股权占比',
          left: 'center',
          textStyle: {
            color: '#333',
            fontSize: 14
          }
        },
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: {c}% ({d}%)'
        },
        legend: {
          orient: 'vertical',
          left: 'left',
          data: this.holdersData.map(item => item.name),
          textStyle: {
            fontSize: 12
          }
        },
        series: [
          {
            name: '持股比例',
            type: 'pie',
            radius: '55%',
            center: ['60%', '60%'],
            data: this.holdersData.map(item => ({
              name: item.name,
              value: item.percentage
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
              formatter: '{b}: {c}%'
            },
            labelLine: {
              show: true
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

.chart-header {
  text-align: center;
  margin-bottom: 10px;
}

.chart-header h3 {
  margin: 0;
  color: #333;
  font-size: 16px;
  font-weight: 500;
}

.chart-container {
  border-radius: 4px;
}
</style>