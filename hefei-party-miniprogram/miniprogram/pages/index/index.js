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
    this.loadNews();
  },

  async loadNews() {
    this.setData({ loading: true });
    try {
      const db = wx.cloud.database();
      let res;
      try {
        res = await db.collection('cases')
          .orderBy('createTime', 'desc')
          .limit(5)
          .get();
      } catch (e) {
        // orderBy 失败时（字段不存在等）直接取前5条
        res = await db.collection('cases').limit(5).get();
      }

      const newsList = (res.data || []).map(item => ({
        ...item,
        date: this._formatDate(item.createTime || item.date || item.publishTime)
      }));
      this.setData({ newsList, loading: false });
    } catch (e) {
      // 静默失败，显示"暂无动态"，控制台输出详情供排查
      console.error('[合城动态加载失败]', e.errMsg || e);
      this.setData({ loading: false });
    }
  },

  // 兼容 serverDate / Date / 时间戳 / 字符串
  _formatDate(val) {
    if (!val) return '';
    try {
      const d = (val instanceof Date) ? val
        : (val && val.$date) ? new Date(val.$date)
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
