// 首页
const db = wx.cloud.database();

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

  // 加载合城动态（取最新5条案例）
  async loadNews() {
    try {
      const res = await db.collection('cases')
        .orderBy('createTime', 'desc')
        .limit(5)
        .get();
      this.setData({
        newsList: res.data.map(item => ({
          ...item,
          date: item.createTime
            ? new Date(item.createTime).toLocaleDateString('zh-CN')
            : ''
        })),
        loading: false
      });
    } catch (e) {
      console.error('加载动态失败', e);
      this.setData({ loading: false });
    }
  },

  goTo(e) {
    const url = e.currentTarget.dataset.url;
    wx.navigateTo({ url });
  },

  goToCase(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/case-detail/index?id=${id}` });
  }
});
