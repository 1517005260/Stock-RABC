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

      <!-- 技术指标控制 -->
      <div class="indicator-controls" v-if="chartType === 'kline'">
        <el-dropdown @command="handleIndicatorChange">
          <el-button size="small">
            技术指标 <el-icon><arrow-down /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item
                v-for="indicator in availableIndicators"
                :key="indicator.value"
                :command="indicator.value"
                :class="{ 'is-active': activeIndicators.includes(indicator.value) }"
              >
                <el-checkbox
                  :model-value="activeIndicators.includes(indicator.value)"
                  @change="() => toggleIndicator(indicator.value)"
                >
                  {{ indicator.label }}
                </el-checkbox>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
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
import { ArrowDown } from '@element-plus/icons-vue'
import { markRaw } from 'vue'

export default {
  name: 'KlineChart',
  components: {
    ArrowDown
  },
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
      downBorderColor: '#008F28',
      // 技术指标控制
      activeIndicators: ['MA5', 'MA10', 'MA20', 'MA30', 'MACD'], // 默认显示的指标
      availableIndicators: [
        { label: 'MA5', value: 'MA5' },
        { label: 'MA10', value: 'MA10' },
        { label: 'MA20', value: 'MA20' },
        { label: 'MA30', value: 'MA30' },
        { label: 'MACD', value: 'MACD' },
        { label: 'DIF', value: 'DIF' },
        { label: 'DEA', value: 'DEA' }
      ]
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
        // 使用 markRaw 防止 Vue 反应式系统干扰 ECharts 实例
        this.chart = markRaw(echarts.init(this.$refs.chartContainer))

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
          start_date: '20220101', // 修改为两年前
          limit: 500
        })

        console.log('K线数据响应:', response.data) // 调试日志

        if (response.data.code === 200) {
          // 后端返回的数据结构现在包含 dates, kline, ma5, ma10, ma20, ma30
          this.klineData = {
            dates: response.data.data.dates || [],
            kline: response.data.data.kline || [],
            ma5: response.data.data.ma5 || [],
            ma10: response.data.data.ma10 || [],
            ma20: response.data.data.ma20 || [],
            ma30: response.data.data.ma30 || []
          }

          console.log('解析后的K线数据:', this.klineData) // 调试日志

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

      // 验证数据结构
      const { dates, kline, ma5, ma10, ma20, ma30 } = this.klineData

      if (!Array.isArray(dates) || !Array.isArray(kline) || dates.length === 0 || kline.length === 0) {
        // 如果没有有效数据，显示空状态
        const emptyOption = {
          title: {
            text: '暂无K线数据',
            left: 'center',
            top: 'middle',
            textStyle: {
              color: '#999',
              fontSize: 16
            }
          },
          xAxis: {
            type: 'category',
            data: [],
            show: false
          },
          yAxis: {
            type: 'value',
            show: false
          },
          series: [
            {
              name: '暂无数据',
              type: 'candlestick',
              data: [],
              showSymbol: false
            }
          ]
        }
        this.chart.setOption(emptyOption, true)
        return
      }

      // 数据清洗和对齐 - 保持索引一致性
      const dataLength = dates.length
      const cleanKlineData = Array.isArray(kline) ?
        kline.filter(item => item && Array.isArray(item) && item.length >= 4).slice(0, dataLength) : []

      // MA 数据处理：保持长度一致，用 null 替换无效值
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

      // 计算 MACD 指标
      const macdData = this.calculateMACD(cleanKlineData)

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
            if (!params || !Array.isArray(params) || params.length === 0) return ''

            let result = `${params[0].name}<br/>`

            params.forEach(item => {
              if (!item.seriesName || item.value == null) return

              // 处理不同系列类型的数据
              if (item.seriesType === 'candlestick' && Array.isArray(item.data)) {
                // K线数据：[open, close, low, high]
                const [open, close, low, high] = item.data
                result += `<span style="color: ${item.color}">${item.seriesName}</span><br/>`
                result += `  开盘：${open}<br/>`
                result += `  收盘：${close}<br/>`
                result += `  最低：${low}<br/>`
                result += `  最高：${high}<br/>`
              } else {
                // 线性数据：MA、MACD、DIF、DEA
                const value = typeof item.value === 'number' ? item.value.toFixed(4) : item.value
                result += `<span style="color: ${item.color}">${item.seriesName}：${value}</span><br/>`
              }
            })

            return result
          }
        },
        legend: {
          data: ['日K'].concat(this.activeIndicators),
          top: 30
        },
        grid: [
          {
            left: '10%',
            right: '10%',
            height: '50%',
            top: '80px'
          },
          {
            left: '10%',
            right: '10%',
            top: '65%',
            height: '20%'
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
            splitNumber: 20,
            min: 'dataMin',
            max: 'dataMax'
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
            axisLabel: { show: false },
            min: 'dataMin',
            max: 'dataMax'
          }
        ],
        yAxis: [
          {
            scale: true,
            splitArea: {
              show: true
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
            start: 50,
            end: 100
          },
          {
            show: true,
            xAxisIndex: [0, 1],
            type: 'slider',
            top: '90%',
            start: 50,
            end: 100
          }
        ],
        series: this.generateSeries(cleanKlineData, cleanMA5, cleanMA10, cleanMA20, cleanMA30, macdData)
      }

      this.chart.setOption(option, true)
    },

    // 计算 MACD 指标
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

      // 计算 DEA (DIF 的 9 日 EMA)
      const dea = calculateEMA(dif, 9)

      // 计算 MACD
      const macd = []
      for (let i = 0; i < dif.length; i++) {
        macd[i] = (dif[i] - dea[i]) * 2
      }

      // 补齐数组长度以匹配原始数据
      const dataLength = klineData.length
      const resultDif = new Array(dataLength).fill(null)
      const resultDea = new Array(dataLength).fill(null)
      const resultMacd = new Array(dataLength).fill(null)

      // 从第26个数据点开始填充（MACD需要至少26个周期）
      const startIndex = Math.max(0, dataLength - dif.length)
      for (let i = 0; i < dif.length && startIndex + i < dataLength; i++) {
        resultDif[startIndex + i] = dif[i]
        resultDea[startIndex + i] = dea[i]
        resultMacd[startIndex + i] = macd[i]
      }

      return {
        dif: resultDif,
        dea: resultDea,
        macd: resultMacd
      }
    },
    
    renderRealtimeChart() {
      if (!this.chart || !this.realtimeData) return
      
      const { time, price } = this.realtimeData
      
      // 验证数据结构
      if (!Array.isArray(time) || !Array.isArray(price) || time.length === 0 || price.length === 0) {
        // 按照sample项目的方式处理空数据情况
        const emptyOption = {
          title: {
            text: '暂无分时数据',
            left: 'center',
            top: 'middle',
            textStyle: {
              color: '#999',
              fontSize: 16
            }
          },
          xAxis: {
            type: 'category',
            data: [],
            show: false
          },
          yAxis: {
            type: 'value',
            show: false
          },
          series: [
            {
              name: '暂无数据',
              type: 'line',
              data: [],
              showSymbol: false
            }
          ]
        }
        this.chart.setOption(emptyOption, true)
        return
      }
      
      // 格式化时间显示：将091505格式转换为09:15格式
      const formatTimeDisplay = (timeStr) => {
        if (!timeStr) return timeStr
        
        // 如果是091505这种6位格式，转换为09:15
        if (typeof timeStr === 'string' && timeStr.length === 6 && /^\d{6}$/.test(timeStr)) {
          const hours = timeStr.substring(0, 2)
          const minutes = timeStr.substring(2, 4)
          return `${hours}:${minutes}`
        }
        
        // 如果是09:15这种格式，直接返回
        if (typeof timeStr === 'string' && timeStr.includes(':')) {
          return timeStr
        }
        
        // 其他格式尝试转换
        return timeStr
      }
      
      // 格式化时间数据
      const formattedTimes = time.map(item => formatTimeDisplay(item))
      
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
          data: formattedTimes,
          boundaryGap: false
        },
        yAxis: {
          type: 'value',
          scale: true
        },
        series: [
          {
            name: '分时价格',
            type: 'line',
            data: Array.isArray(price) ? price.filter(item => item != null && !isNaN(item)) : [],
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
    },

    // 动态生成系列配置
    generateSeries(cleanKlineData, cleanMA5, cleanMA10, cleanMA20, cleanMA30, macdData) {
      const series = []

      // K线图（始终显示）
      series.push({
        name: '日K',
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
      })

      // MA 系列（根据用户选择）
      const maConfigs = {
        'MA5': { data: cleanMA5, color: '#1890ff' },
        'MA10': { data: cleanMA10, color: '#52c41a' },
        'MA20': { data: cleanMA20, color: '#faad14' },
        'MA30': { data: cleanMA30, color: '#f5222d' }
      }

      Object.keys(maConfigs).forEach(key => {
        if (this.activeIndicators.includes(key)) {
          series.push({
            name: key,
            type: 'line',
            data: maConfigs[key].data,
            smooth: true,
            lineStyle: {
              opacity: 0.8,
              width: 1,
              color: maConfigs[key].color
            },
            showSymbol: false,
            connectNulls: false
          })
        }
      })

      // MACD 指标（根据用户选择）
      if (this.activeIndicators.includes('MACD')) {
        series.push({
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
        })
      }

      if (this.activeIndicators.includes('DIF')) {
        series.push({
          name: 'DIF',
          type: 'line',
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: macdData.dif,
          lineStyle: {
            color: '#da6200',
            width: 1
          },
          itemStyle: {
            color: '#da6200'
          },
          showSymbol: false,
          connectNulls: false
        })
      }

      if (this.activeIndicators.includes('DEA')) {
        series.push({
          name: 'DEA',
          type: 'line',
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: macdData.dea,
          lineStyle: {
            color: '#0000da',
            width: 1
          },
          itemStyle: {
            color: '#0000da'
          },
          showSymbol: false,
          connectNulls: false
        })
      }

      return series
    },

    // 技术指标控制方法
    handleIndicatorChange(indicator) {
      this.toggleIndicator(indicator)
    },

    toggleIndicator(indicator) {
      const index = this.activeIndicators.indexOf(indicator)
      if (index > -1) {
        this.activeIndicators.splice(index, 1)
      } else {
        this.activeIndicators.push(indicator)
      }
      // 重新渲染图表
      if (this.chartType === 'kline' && this.klineData) {
        this.renderKlineChart()
      }
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
  display: flex;
  align-items: center;
  gap: 15px;
}

.indicator-controls {
  margin-left: auto;
}

.chart-container {
  border: 1px solid #e8e8e8;
  border-radius: 4px;
}

/* 指标下拉菜单样式 */
:deep(.el-dropdown-menu__item.is-active) {
  background-color: #f5f7fa;
}

:deep(.el-checkbox) {
  pointer-events: none;
}

:deep(.el-checkbox__input) {
  pointer-events: auto;
}
</style>