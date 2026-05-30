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
      const experts = expertsRes.data || [];
      // 将 cloud:// 路径转为可访问的 HTTPS URL
      const cloudFileIds = experts.map(e => e.avatar).filter(a => a && a.startsWith('cloud://'));
      if (cloudFileIds.length > 0) {
        try {
          const { fileList } = await wx.cloud.getTempFileURL({ fileList: cloudFileIds });
          const urlMap = {};
          fileList.forEach(f => { urlMap[f.fileID] = f.tempFileURL; });
          experts.forEach(e => { if (urlMap[e.avatar]) e.avatar = urlMap[e.avatar]; });
        } catch (e) {
          console.error('[头像URL转换失败]', e);
        }
      }
      this.setData({
        intro: introRes.data[0]?.content || '',
        experts
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
