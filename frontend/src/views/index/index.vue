<template>
  <div class="home">
    <!-- 欢迎区域 -->
    <div class="welcome-section">
      <h1>欢迎使用股票交易模拟系统</h1>
      <p>基于RBAC权限管理的金融软件项目管理实践平台</p>
    </div>

    <!-- 功能导航 -->
    <el-row :gutter="20" class="feature-nav">
      <el-col :span="6">
        <el-card class="feature-card" shadow="hover" @click="goToStockDashboard">
          <div class="feature-content">
            <el-icon size="48" color="#409EFF"><TrendCharts /></el-icon>
            <h3>股票交易首页</h3>
            <p>查看市场行情、热门股票和实时数据</p>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="feature-card" shadow="hover" @click="goToStockList">
          <div class="feature-content">
            <el-icon size="48" color="#67C23A"><List /></el-icon>
            <h3>股票列表</h3>
            <p>浏览所有上市股票，支持搜索和筛选</p>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="feature-card" shadow="hover" @click="goToUserCenter">
          <div class="feature-content">
            <el-icon size="48" color="#E6A23C"><User /></el-icon>
            <h3>个人中心</h3>
            <p>管理个人信息和账户设置</p>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="feature-card" shadow="hover" @click="goToSystemManagement">
          <div class="feature-content">
            <el-icon size="48" color="#F56C6C"><Setting /></el-icon>
            <h3>系统管理</h3>
            <p>用户权限管理和系统配置</p>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 系统特色 -->
    <div class="features-section">
      <h2>系统特色</h2>
      <el-row :gutter="30">
        <el-col :span="8">
          <div class="feature-item">
            <el-icon size="32" color="#409EFF"><DataAnalysis /></el-icon>
            <h4>实时数据</h4>
            <p>提供实时股票行情、K线图表和技术分析指标</p>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="feature-item">
            <el-icon size="32" color="#67C23A"><Lock /></el-icon>
            <h4>权限管理</h4>
            <p>基于RBAC模型的完整权限管理体系</p>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="feature-item">
            <el-icon size="32" color="#E6A23C"><Monitor /></el-icon>
            <h4>模拟交易</h4>
            <p>安全的模拟交易环境，零风险学习投资</p>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 快速链接 -->
    <div class="quick-links">
      <h3>快速链接</h3>
      <el-button-group>
        <el-button type="primary" @click="goToStockDashboard">
          <el-icon><TrendCharts /></el-icon>
          进入交易系统
        </el-button>
        <el-button type="success" @click="goToStockList">
          <el-icon><Search /></el-icon>
          浏览股票
        </el-button>
        <el-button type="info" @click="goToChat">
          <el-icon><ChatDotSquare /></el-icon>
          AI助手
        </el-button>
      </el-button-group>
    </div>
  </div>
</template>

<script>
import {
  TrendCharts,
  List,
  User,
  Setting,
  DataAnalysis,
  Lock,
  Monitor,
  Search,
  ChatDotSquare
} from '@element-plus/icons-vue'

export default {
  name: "index",
  components: {
    TrendCharts,
    List,
    User,
    Setting,
    DataAnalysis,
    Lock,
    Monitor,
    Search,
    ChatDotSquare
  },
  methods: {
    goToStockDashboard() {
      this.$router.push('/stock/dashboard')
    },
    goToStockList() {
      this.$router.push('/stock/list')
    },
    goToUserCenter() {
      this.$router.push('/userCenter')
    },
    goToSystemManagement() {
      // 检查用户权限
      const currentUser = JSON.parse(sessionStorage.getItem('currentUser') || '{}')
      const userRoles = currentUser.roles || ''
      const isAdmin = userRoles.includes('超级管理员') || userRoles.includes('管理员')
      
      if (isAdmin) {
        this.$router.push('/sys/user')
      } else {
        this.$message.warning('权限不足，无法访问系统管理')
      }
    },
    goToChat() {
      this.$router.push('/chat')
    }
  }
};
</script>

<style lang="scss" scoped>
.home {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.welcome-section {
  text-align: center;
  padding: 40px 0 60px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
  margin-bottom: 40px;

  h1 {
    font-size: 36px;
    font-weight: bold;
    margin-bottom: 15px;
  }

  p {
    font-size: 18px;
    opacity: 0.9;
  }
}

.feature-nav {
  margin-bottom: 50px;
}

.feature-card {
  cursor: pointer;
  transition: all 0.3s ease;
  height: 200px;

  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15) !important;
  }
}

.feature-content {
  text-align: center;
  padding: 20px;

  h3 {
    margin: 15px 0 10px;
    font-size: 18px;
    font-weight: bold;
    color: #333;
  }

  p {
    color: #666;
    font-size: 14px;
    line-height: 1.5;
  }
}

.features-section {
  text-align: center;
  padding: 40px 0;
  background: #f8f9fa;
  border-radius: 12px;
  margin-bottom: 40px;

  h2 {
    font-size: 28px;
    font-weight: bold;
    margin-bottom: 40px;
    color: #333;
  }
}

.feature-item {
  text-align: center;
  padding: 20px;

  h4 {
    margin: 15px 0 10px;
    font-size: 18px;
    font-weight: bold;
    color: #333;
  }

  p {
    color: #666;
    font-size: 14px;
    line-height: 1.6;
  }
}

.quick-links {
  text-align: center;
  padding: 30px 0;

  h3 {
    font-size: 20px;
    font-weight: bold;
    margin-bottom: 20px;
    color: #333;
  }

  .el-button-group .el-button {
    margin: 0 5px;
    padding: 12px 20px;
    font-size: 14px;
  }
}

@media (max-width: 768px) {
  .home {
    padding: 10px;
  }

  .welcome-section {
    padding: 30px 20px 40px;

    h1 {
      font-size: 24px;
    }

    p {
      font-size: 16px;
    }
  }

  .feature-card {
    margin-bottom: 20px;
  }

  .features-section {
    padding: 30px 20px;
  }

  .quick-links .el-button-group .el-button {
    margin: 5px;
    display: block;
    width: 200px;
  }
}
</style>
