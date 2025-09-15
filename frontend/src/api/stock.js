import request from '@/utils/request'

// 股票列表
export function getStockList(params) {
  return request({
    url: '/stock/list/',
    method: 'get',
    params
  })
}

// 股票详情
export function getStockDetail(tsCode) {
  return request({
    url: `/stock/detail/${tsCode}/`,
    method: 'get'
  })
}

// 热门股票
export function getHotStocks(params) {
  return request({
    url: '/stock/hot/',
    method: 'get',
    params
  })
}

// 股票搜索
export function searchStocks(params) {
  return request({
    url: '/stock/search/',
    method: 'get',
    params
  })
}

// 行业列表
export function getIndustries() {
  return request({
    url: '/stock/industries/',
    method: 'get'
  })
}

// 股票实时数据
export function getStockRealtimeData(tsCode) {
  return request({
    url: `/stock/realtime/data/${tsCode}/`,
    method: 'get'
  })
}

// 获取实时数据（兼容函数）
export function getRealtimeData(tsCode) {
  return request({
    url: `/stock/realtime/data/${tsCode}/`,
    method: 'get'
  })
}

// 分时图数据
export function getStockIntradayChart(tsCode) {
  return request({
    url: `/stock/realtime/chart/${tsCode}/`,
    method: 'get'
  })
}

// 实时价格
export function getStockRealtimePrice(tsCode) {
  return request({
    url: `/stock/realtime/price/${tsCode}/`,
    method: 'get'
  })
}

// 市场概况
export function getMarketOverview() {
  return request({
    url: '/stock/market/overview/',
    method: 'get'
  })
}

// K线数据
export function getStockKlineData(tsCode, params) {
  return request({
    url: `/stock/kline/${tsCode}/`,
    method: 'get',
    params
  })
}

// 技术分析数据
export function getStockTechnicalAnalysis(tsCode) {
  return request({
    url: `/stock/technical/${tsCode}/`,
    method: 'get'
  })
}

// 股票持股信息
export function getStockHolders(tsCode) {
  return request({
    url: `/stock/holders/${tsCode}/`,
    method: 'get'
  })
}

// 市场新闻列表
export function getMarketNewsList(params) {
  return request({
    url: '/stock/news/',
    method: 'get',
    params
  })
}

// 新闻详情
export function getNewsDetail(newsId) {
  return request({
    url: `/stock/news/${newsId}/`,
    method: 'get'
  })
}

// 最新新闻
export function getLatestNews(params) {
  return request({
    url: '/stock/news/latest/',
    method: 'get',
    params
  })
}

// 新闻分类
export function getNewsCategories() {
  return request({
    url: '/stock/news/categories/',
    method: 'get'
  })
}

// 创建新闻（管理员）
export function createNews(data) {
  return request({
    url: '/stock/news/create/',
    method: 'post',
    data
  })
}

// 同步股票数据（超级管理员）
export function syncStockData(data) {
  return request({
    url: '/stock/sync/',
    method: 'post',
    data
  })
}

// 手动同步新闻（超级管理员）
export function syncNewsManual() {
  return request({
    url: '/stock/news/sync/',
    method: 'post'
  })
}

// 股票实时数据（单个股票）
export function getStockRealtime(tsCode) {
  return request({
    url: `/stock/realtime/${tsCode}/`,
    method: 'get'
  })
}