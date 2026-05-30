// 首页
Page({
  data: {
    newsList: [],
    loading: true
  },

  onLoad() {
    this.loadNews();
  },

  onShow() {
    // 每次显示页面刷新动态
    this.loadNews();
  },

  async loadNews() {
    this.setData({ loading: true });
    try {
      const db = wx.cloud.database();

      // 优先按 createTime 倒序；若该字段不存在会 fallback
      let res;
      try {
        res = await db.collection('cases')
          .orderBy('createTime', 'desc')
          .limit(5)
          .get();
      } catch (e) {
        // 字段不存在或权限问题时，不带 orderBy 直接取
        res = await db.collection('cases').limit(5).get();
      }

      const newsList = (res.data || []).map(item => ({
        ...item,
        date: this._formatDate(item.createTime || item.date || item.publishTime)
      }));

      this.setData({ newsList, loading: false });
    } catch (e) {
      console.error('加载合城动态失败:', e);
      wx.showToast({ title: '动态加载失败，请检查云环境配置', icon: 'none', duration: 3000 });
      this.setData({ loading: false });
    }
  },

  // 兼容 serverDate 对象、Date 对象、时间戳、字符串
  _formatDate(val) {
    if (!val) return '';
    try {
      // serverDate 返回的是 { $date: timestamp } 或 Date 对象
      const d = (val instanceof Date) ? val
        : (typeof val === 'object' && val.$date) ? new Date(val.$date)
        : new Date(val);
      if (isNaN(d.getTime())) return String(val).slice(0, 10);
      return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
    } catch {
      return '';
    }
  },

  goTo(e) {
    wx.navigateTo({ url: e.currentTarget.dataset.url });
  },

  goToCase(e) {
    wx.navigateTo({ url: `/pages/case-detail/index?id=${e.currentTarget.dataset.id}` });
  }
});
