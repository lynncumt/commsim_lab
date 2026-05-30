// 党建思政专家库
Page({
  data: {
    intro: '',
    experts: [],
    showModal: false,
    currentExpert: {}
  },

  onLoad() {
    this.loadData();
  },

  async loadData() {
    const db = wx.cloud.database();
    wx.showLoading({ title: '加载中...' });
    try {
      let expertsRes;
      try {
        expertsRes = await db.collection('experts').orderBy('sortOrder', 'asc').get();
      } catch (e) {
        expertsRes = await db.collection('experts').get();
      }
      const introRes = await db.collection('expert_intro').limit(1).get();
      console.log('[experts] count:', (expertsRes.data || []).length, expertsRes.data);
      this.setData({
        intro: introRes.data[0]?.content || '',
        experts: expertsRes.data || []
      });
    } catch (e) {
      console.error('[专家库加载失败]', e.errMsg || e);
      wx.showToast({ title: '加载失败', icon: 'none' });
    } finally {
      wx.hideLoading();
    }
  },

  viewExpert(e) {
    const index = e.currentTarget.dataset.index;
    this.setData({
      showModal: true,
      currentExpert: this.data.experts[index]
    });
  },

  closeModal() {
    this.setData({ showModal: false });
  }
});
