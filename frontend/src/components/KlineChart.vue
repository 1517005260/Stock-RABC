<template>
  <div class="kline-chart-container">
    <!-- 切换按钮 -->
    <div class="chart-controls">
      <el-button-group>
        <el-button 
          :type="chartType === 'kline' ? 'primary' : 'default'" 
          size="small"
          @click="switchToKline"
        >
          股票日K
        </el-button>
        <el-button 
          :type="chartType === 'realtime' ? 'primary' : 'default'" 
          size="small"
          @click="switchToRealtime"
        >
          实时股价
        </el-button>
      </el-button-group>
    </div>

    <!-- K线图容器 -->
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
import { getStockKlineData, getStockIntradayChart } from '@/api/stock'

export default {
  name: 'KlineChart',
  props: {
    tsCode: {
      type: String,
      required: true
    },
    stockName: {
      type: String,
      default: ''
    },
    chartHeight: {
      type: String,
      default: '400px'
    }
  },
  data() {
    return {
      chart: null,
      loading: false,
      chartType: 'kline', // 'kline' 或 'realtime'
      klineData: null,
      realtimeData: null,
      upColor: '#ec0000',
      upBorderColor: '#8A0000', 
      downColor: '#00da3c',
      downBorderColor: '#008F28'
    }
  },
  mounted() {
    this.initChart()
    this.loadKlineData()
  },
  beforeUnmount() {
    if (this.chart) {
      this.chart.dispose()
    }
  },
  watch: {
    tsCode: {
      handler() {
        this.loadKlineData()
      },
      immediate: false
    }
  },
  methods: {
    initChart() {
      if (this.$refs.chartContainer) {
        this.chart = echarts.init(this.$refs.chartContainer)
        
        // 监听窗口大小变化
        window.addEventListener('resize', this.handleResize)
      }
    },
    
    handleResize() {
      if (this.chart) {
        this.chart.resize()
      }
    },
    
    async loadKlineData() {
      if (!this.tsCode) return
      
      this.loading = true
      try {
        const response = await getStockKlineData(this.tsCode, {
          start_date: '20230101'
        })
        
        if (response.data.code === 200) {
          this.klineData = response.data.data
          if (this.chartType === 'kline') {
            this.renderKlineChart()
          }
        } else {
          this.$message.error(response.data.msg || '获取K线数据失败')
        }
      } catch (error) {
        console.error('加载K线数据失败:', error)
        this.$message.error('加载K线数据失败')
      } finally {
        this.loading = false
      }
    },
    
    async loadRealtimeData() {
      if (!this.tsCode) return
      
      this.loading = true
      try {
        const response = await getStockIntradayChart(this.tsCode)
        
        if (response.data.code === 200) {
          this.realtimeData = response.data.data
          this.renderRealtimeChart()
        } else {
          this.$message.error(response.data.msg || '获取分时数据失败')
        }
      } catch (error) {
        console.error('加载分时数据失败:', error)
        this.$message.error('加载分时数据失败')
      } finally {
        this.loading = false
      }
    },
    
    switchToKline() {
      this.chartType = 'kline'
      if (this.klineData) {
        this.renderKlineChart()
      } else {
        this.loadKlineData()
      }
    },
    
    switchToRealtime() {
      this.chartType = 'realtime'
      this.loadRealtimeData()
    },
    
    renderKlineChart() {
      if (!this.chart || !this.klineData) return
      
      const { dates, kline, ma5, ma10, ma20, ma30 } = this.klineData

      const option = {
        title: {
          text: this.stockName || this.tsCode,
          left: 0,
          textStyle: {
            color: '#333',
            fontSize: 16
          }
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross'
          },
          formatter: function (params) {
            const data = params[0]
            const [open, close, low, high] = data.data
            return `${data.name}<br/>
                   开盘：${open}<br/>
                   收盘：${close}<br/>
                   最低：${low}<br/>
                   最高：${high}`
          }
        },
        legend: {
          data: ['日K', 'MA5', 'MA10', 'MA20', 'MA30'],
          top: 30
        },
        grid: {
          left: '10%',
          right: '10%',
          bottom: '15%',
          top: '80px'
        },
        xAxis: {
          type: 'category',
          data: dates,
          scale: true,
          boundaryGap: false,
          axisLine: { onZero: false },
          splitLine: { show: false },
          splitNumber: 20,
          min: 'dataMin',
          max: 'dataMax'
        },
        yAxis: {
          scale: true,
          splitArea: {
            show: true
          }
        },
        dataZoom: [
          {
            type: 'inside',
            start: 50,
            end: 100
          },
          {
            show: true,
            type: 'slider',
            top: '90%',
            start: 50,
            end: 100
          }
        ],
        series: [
          {
            name: '日K',
            type: 'candlestick',
            data: kline,
            itemStyle: {
              color: this.upColor,
              color0: this.downColor,
              borderColor: this.upBorderColor,
              borderColor0: this.downBorderColor
            },
            markPoint: {
              label: {
                formatter: function (param) {
                  return param != null ? Math.round(param.value) : ''
                }
              },
              data: [
                {
                  name: 'highest value',
                  type: 'max',
                  valueDim: 'highest'
                },
                {
                  name: 'lowest value', 
                  type: 'min',
                  valueDim: 'lowest'
                },
                {
                  name: 'average value on close',
                  type: 'average',
                  valueDim: 'close'
                }
              ]
            },
            markLine: {
              symbol: ['none', 'none'],
              data: [
                {
                  name: 'min line on close',
                  type: 'min',
                  valueDim: 'close'
                },
                {
                  name: 'max line on close',
                  type: 'max', 
                  valueDim: 'close'
                }
              ]
            }
          },
          {
            name: 'MA5',
            type: 'line',
            data: ma5,
            smooth: true,
            lineStyle: {
              opacity: 0.5,
              width: 1
            },
            showSymbol: false
          },
          {
            name: 'MA10',
            type: 'line',
            data: ma10,
            smooth: true,
            lineStyle: {
              opacity: 0.5,
              width: 1
            },
            showSymbol: false
          },
          {
            name: 'MA20',
            type: 'line',
            data: ma20,
            smooth: true,
            lineStyle: {
              opacity: 0.5,
              width: 1
            },
            showSymbol: false
          },
          {
            name: 'MA30',
            type: 'line',
            data: ma30,
            smooth: true,
            lineStyle: {
              opacity: 0.5,
              width: 1
            },
            showSymbol: false
          }
        ]
      }
      
      this.chart.setOption(option, true)
    },
    
    renderRealtimeChart() {
      if (!this.chart || !this.realtimeData) return
      
      const { time, price } = this.realtimeData
      
      // 分时图配置
      const option = {
        title: {
          text: `${this.stockName || this.tsCode} - 分时图`,
          left: 0,
          textStyle: {
            color: '#333',
            fontSize: 16
          }
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross'
          }
        },
        grid: {
          left: '10%',
          right: '10%',
          bottom: '15%',
          top: '80px'
        },
        xAxis: {
          type: 'category',
          data: time,
          boundaryGap: false
        },
        yAxis: {
          type: 'value',
          scale: true
        },
        series: [
          {
            type: 'line',
            data: price,
            smooth: true,
            symbol: 'none',
            lineStyle: {
              color: '#1890ff',
              width: 2
            },
            areaStyle: {
              color: {
                type: 'linear',
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [{
                  offset: 0, color: 'rgba(24, 144, 255, 0.3)'
                }, {
                  offset: 1, color: 'rgba(24, 144, 255, 0.1)'
                }]
              }
            }
          }
        ]
      }
      
      this.chart.setOption(option, true)
    }
  }
}
</script>

<style scoped>
.kline-chart-container {
  width: 100%;
}

.chart-controls {
  margin-bottom: 10px;
  text-align: left;
}

.chart-container {
  border: 1px solid #e8e8e8;
  border-radius: 4px;
}
</style>