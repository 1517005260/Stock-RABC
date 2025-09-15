import request from '@/utils/request'

// 用户资产相关接口

// 获取用户资产概览
export function getUserAssets() {
  return request({
    url: '/trading/account/',
    method: 'get'
  })
}

// 获取用户持仓
export function getUserPositions() {
  return request({
    url: '/trading/positions/',
    method: 'get'
  })
}

// 获取用户交易记录
export function getTradeRecords(params) {
  return request({
    url: '/trading/records/',
    method: 'get',
    params
  })
}

// 获取用户自选股
export function getUserWatchList() {
  return request({
    url: '/trading/watchlist/',
    method: 'get'
  })
}

// 添加自选股
export function addToWatchList(data) {
  return request({
    url: '/trading/watchlist/add/',
    method: 'post',
    data
  })
}

// 删除自选股
export function removeFromWatchList(tsCode) {
  return request({
    url: `/trading/watchlist/remove/${tsCode}/`,
    method: 'delete'
  })
}

// 交易操作相关接口

// 买入股票
export function buyStock(data) {
  return request({
    url: '/trading/buy/',
    method: 'post',
    data
  })
}

// 卖出股票
export function sellStock(data) {
  return request({
    url: '/trading/sell/',
    method: 'post',
    data
  })
}

// 撤销交易
export function cancelTrade(data) {
  return request({
    url: '/trading/cancel/',
    method: 'post',
    data
  })
}

// 获取交易统计
export function getTradingStats(params) {
  return request({
    url: '/trading/statistics/',
    method: 'get',
    params
  })
}

// 管理员功能

// 获取所有用户交易记录（管理员）
export function getAllTradeRecords(params) {
  return request({
    url: '/trading/admin/records/',
    method: 'get',
    params
  })
}

// 获取用户资产列表（管理员）
export function getAllUserAssets(params) {
  return request({
    url: '/trading/admin/accounts/',
    method: 'get',
    params
  })
}

// 调整用户资产（管理员）
export function adjustUserAssets(data) {
  return request({
    url: '/trading/admin/assets/adjust/',
    method: 'post',
    data
  })
}

// 冻结/解冻用户交易权限（管理员）
export function toggleUserTradingStatus(data) {
  return request({
    url: '/trading/admin/freeze-user/',
    method: 'post',
    data
  })
}

// 新闻相关接口

// 获取新闻列表
export function getNewsList(params) {
  return request({
    url: '/trading/news/',
    method: 'get',
    params
  })
}

// 获取新闻详情
export function getNewsDetail(newsId) {
  return request({
    url: `/trading/news/${newsId}/`,
    method: 'get'
  })
}

// 管理员新闻管理

// 爬取最新新闻（管理员）
export function fetchLatestNews(data) {
  return request({
    url: '/trading/admin/news/fetch/',
    method: 'post',
    data
  })
}

// 删除新闻（管理员）
export function deleteNews(newsId) {
  return request({
    url: `/trading/admin/news/${newsId}/delete/`,
    method: 'delete'
  })
}

// 创建新闻（管理员）
export function createNews(data) {
  return request({
    url: '/trading/admin/news/create/',
    method: 'post',
    data
  })
}

// 更新新闻（管理员）
export function updateNews(newsId, data) {
  return request({
    url: `/trading/admin/news/${newsId}/update/`,
    method: 'put',
    data
  })
}

// 获取管理员新闻列表
export function getAdminNewsList(params) {
  return request({
    url: '/trading/admin/news/',
    method: 'get',
    params
  })
}