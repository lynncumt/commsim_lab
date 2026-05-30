// 案例详情


Page({
  data: {
    article: {},
    loading: true
  },

  onLoad(options) {
    const { id } = options;
    this.loadArticle(id);
  },

  async loadArticle(id) {
    const db = wx.cloud.database();
    try {
      const res = await db.collection('cases').doc(id).get();
      const data = res.data;
      this.setData({
        article: {
          ...data,
          dateStr: data.createTime
            ? new Date(data.createTime).toLocaleDateString('zh-CN')
            : ''
        },
        loading: false
      });
      wx.setNavigationBarTitle({ title: data.title || '案例详情' });
    } catch (e) {
      console.error(e);
      this.setData({ loading: false });
      wx.showToast({ title: '加载失败', icon: 'none' });
    }
  },

  previewImage(e) {
    const { src, list } = e.currentTarget.dataset;
    wx.previewImage({ current: src, urls: list });
  }
});
