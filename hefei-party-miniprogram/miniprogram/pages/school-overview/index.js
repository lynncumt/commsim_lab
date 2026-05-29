// 学校概况
const db = wx.cloud.database();

Page({
  data: {
    overview: {},
    colleges: []
  },

  onLoad() {
    this.loadData();
  },

  async loadData() {
    wx.showLoading({ title: '加载中...' });
    try {
      const [overviewRes, collegesRes] = await Promise.all([
        db.collection('school_overview').limit(1).get(),
        db.collection('colleges').orderBy('sortOrder', 'asc').get()
      ]);
      this.setData({
        overview: overviewRes.data[0] || {},
        colleges: collegesRes.data
      });
    } catch (e) {
      console.error(e);
      wx.showToast({ title: '加载失败', icon: 'none' });
    } finally {
      wx.hideLoading();
    }
  },

  goToCollege(e) {
    const { id, name } = e.currentTarget.dataset;
    wx.navigateTo({ url: `/pages/college-detail/index?id=${id}&name=${encodeURIComponent(name)}` });
  }
});
