<template>
  <div class="market-kline-chart-container">
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
import { getStockKlineData } from '@/api/stock'
import { markRaw } from 'vue'

export default {
  name: 'MarketKlineChart',
  props: {
    tsCode: {
      type: String,
      default: '000001.SH'
    },
    chartType: {
      type: String,
      default: 'kline'
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
      klineData: null,
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
      }
    }
  },
  methods: {
    initChart() {
      if (this.$refs.chartContainer) {
        this.chart = markRaw(echarts.init(this.$refs.chartContainer))
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
          period: 'daily',  // 使用标准参数
          limit: 200
        })

        console.log('大盘K线API响应:', response.data)

        if (response.data.code === 200) {
          this.klineData = {
            dates: response.data.data.dates || [],
            kline: response.data.data.kline || [],
            ma5: response.data.data.ma5 || [],
            ma10: response.data.data.ma10 || [],
            ma20: response.data.data.ma20 || [],
            ma30: response.data.data.ma30 || []
          }

          console.log('处理后的K线数据:', this.klineData)
          this.renderKlineChart()
        } else {
          console.error('大盘K线API错误:', response.data.msg)
          this.$message.error(response.data.msg || '获取大盘K线数据失败')
        }
      } catch (error) {
        console.error('加载大盘K线数据失败:', error)
        this.$message.error('加载大盘K线数据失败')
      } finally {
        this.loading = false
      }
    },

    renderKlineChart() {
      if (!this.chart || !this.klineData) return

      const { dates, kline, ma5, ma10, ma20, ma30 } = this.klineData

      if (!Array.isArray(dates) || !Array.isArray(kline) || dates.length === 0 || kline.length === 0) {
        const emptyOption = {
          title: {
            text: '暂无大盘K线数据',
            left: 'center',
            top: 'middle',
            textStyle: {
              color: '#999',
              fontSize: 14
            }
          }
        }
        this.chart.setOption(emptyOption, true)
        return
      }

      // 数据清洗
      const dataLength = dates.length
      const cleanKlineData = Array.isArray(kline) ?
        kline.filter(item => item && Array.isArray(item) && item.length >= 4).slice(0, dataLength) : []

      // MA 数据清洗
      const cleanMA = (maData) => {
        if (!Array.isArray(maData)) return new Array(dataLength).fill(null)
        const result = new Array(dataLength).fill(null)
        for (let i = 0; i < Math.min(maData.length, dataLength); i++) {
          const value = maData[i]
          result[i] = (value != null && !isNaN(parseFloat(value))) ? parseFloat(value) : null
        }
        return result
      }

      const cleanMA5 = cleanMA(ma5)
      const cleanMA10 = cleanMA(ma10)
      const cleanMA20 = cleanMA(ma20)
      const cleanMA30 = cleanMA(ma30)

      // 计算 MACD
      const macdData = this.calculateMACD(cleanKlineData)

      const option = {
        title: {
          text: '上证指数',
          left: 0,
          textStyle: {
            color: '#333',
            fontSize: 14
          }
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross'
          },
          formatter: function (params) {
            if (!params || !Array.isArray(params) || params.length === 0) return ''

            let result = `${params[0].name}<br/>`

            params.forEach(item => {
              if (!item.seriesName || item.value == null) return

              if (item.seriesType === 'candlestick' && Array.isArray(item.data)) {
                const [open, close, low, high] = item.data
                result += `<span style="color: ${item.color}">${item.seriesName}</span><br/>`
                result += `  开盘：${open}<br/>`
                result += `  收盘：${close}<br/>`
                result += `  最低：${low}<br/>`
                result += `  最高：${high}<br/>`
              } else {
                const value = typeof item.value === 'number' ? item.value.toFixed(2) : item.value
                result += `<span style="color: ${item.color}">${item.seriesName}：${value}</span><br/>`
              }
            })

            return result
          }
        },
        legend: {
          data: ['上证指数', 'MA5', 'MA10', 'MA20', 'MA30', 'MACD'],
          top: 20,
          textStyle: {
            fontSize: 12
          }
        },
        grid: [
          {
            left: '5%',
            right: '5%',
            height: '60%',
            top: '50px'
          },
          {
            left: '5%',
            right: '5%',
            top: '75%',
            height: '15%'
          }
        ],
        xAxis: [
          {
            type: 'category',
            data: dates,
            scale: true,
            boundaryGap: false,
            axisLine: { onZero: false },
            splitLine: { show: false },
            axisLabel: {
              fontSize: 10
            }
          },
          {
            type: 'category',
            gridIndex: 1,
            data: dates,
            scale: true,
            boundaryGap: false,
            axisLine: { onZero: false },
            axisTick: { show: false },
            splitLine: { show: false },
            axisLabel: { show: false }
          }
        ],
        yAxis: [
          {
            scale: true,
            splitArea: {
              show: true
            },
            axisLabel: {
              fontSize: 10
            }
          },
          {
            scale: true,
            gridIndex: 1,
            splitNumber: 2,
            axisLabel: { show: false },
            axisLine: { show: false },
            axisTick: { show: false },
            splitLine: { show: false }
          }
        ],
        dataZoom: [
          {
            type: 'inside',
            xAxisIndex: [0, 1],
            start: 70,
            end: 100
          },
          {
            show: true,
            xAxisIndex: [0, 1],
            type: 'slider',
            top: '92%',
            start: 70,
            end: 100,
            height: 20
          }
        ],
        series: [
          // K线
          {
            name: '上证指数',
            type: 'candlestick',
            data: cleanKlineData,
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
          // MA5
          {
            name: 'MA5',
            type: 'line',
            data: cleanMA5,
            smooth: true,
            lineStyle: {
              opacity: 0.8,
              width: 1,
              color: '#1890ff'
            },
            showSymbol: false,
            connectNulls: false
          },
          // MA10
          {
            name: 'MA10',
            type: 'line',
            data: cleanMA10,
            smooth: true,
            lineStyle: {
              opacity: 0.8,
              width: 1,
              color: '#52c41a'
            },
            showSymbol: false,
            connectNulls: false
          },
          // MA20
          {
            name: 'MA20',
            type: 'line',
            data: cleanMA20,
            smooth: true,
            lineStyle: {
              opacity: 0.8,
              width: 1,
              color: '#faad14'
            },
            showSymbol: false,
            connectNulls: false
          },
          // MA30
          {
            name: 'MA30',
            type: 'line',
            data: cleanMA30,
            smooth: true,
            lineStyle: {
              opacity: 0.8,
              width: 1,
              color: '#f5222d'
            },
            showSymbol: false,
            connectNulls: false
          },
          // MACD
          {
            name: 'MACD',
            type: 'bar',
            xAxisIndex: 1,
            yAxisIndex: 1,
            data: macdData.macd,
            itemStyle: {
              color: function(params) {
                return params.data >= 0 ? '#ec0000' : '#00da3c'
              }
            }
          }
        ]
      }

      this.chart.setOption(option, true)
    },

    // 计算 MACD
    calculateMACD(klineData) {
      if (!Array.isArray(klineData) || klineData.length < 26) {
        const len = klineData.length || 0
        return {
          dif: new Array(len).fill(null),
          dea: new Array(len).fill(null),
          macd: new Array(len).fill(null)
        }
      }

      const closePrices = klineData.map(item => {
        if (Array.isArray(item) && item.length >= 4) {
          return parseFloat(item[1]) // 收盘价
        }
        return null
      }).filter(price => price !== null)

      if (closePrices.length < 26) {
        const len = klineData.length
        return {
          dif: new Array(len).fill(null),
          dea: new Array(len).fill(null),
          macd: new Array(len).fill(null)
        }
      }

      // 计算 EMA
      const calculateEMA = (data, period) => {
        const ema = []
        const multiplier = 2 / (period + 1)

        ema[0] = data[0]
        for (let i = 1; i < data.length; i++) {
          ema[i] = (data[i] * multiplier) + (ema[i - 1] * (1 - multiplier))
        }
        return ema
      }

      const ema12 = calculateEMA(closePrices, 12)
      const ema26 = calculateEMA(closePrices, 26)

      // 计算 DIF
      const dif = []
      for (let i = 0; i < ema12.length; i++) {
        dif[i] = ema12[i] - ema26[i]
      }

      // 计算 DEA
      const dea = calculateEMA(dif, 9)

      // 计算 MACD
      const macd = []
      for (let i = 0; i < dif.length; i++) {
        macd[i] = (dif[i] - dea[i]) * 2
      }

      // 补齐长度
      const dataLength = klineData.length
      const resultMacd = new Array(dataLength).fill(null)

      const startIndex = Math.max(0, dataLength - macd.length)
      for (let i = 0; i < macd.length && startIndex + i < dataLength; i++) {
        resultMacd[startIndex + i] = macd[i]
      }

      return {
        macd: resultMacd
      }
    }
  }
}
</script>

<style scoped>
.market-kline-chart-container {
  width: 100%;
}

.chart-container {
  border: 1px solid #e8e8e8;
  border-radius: 4px;
}
</style>