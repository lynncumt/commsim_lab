// 学校媒体链接


Page({
  data: {
    mediaLinks: []
  },

  onLoad() {
    this.loadData();
  },

  async loadData() {
    const db = wx.cloud.database();
    wx.showLoading({ title: '加载中...' });
    try {
      const res = await db.collection('media_links').orderBy('sortOrder', 'asc').get();
      this.setData({ mediaLinks: res.data });
    } catch (e) {
      console.error(e);
      // 使用默认数据
      this.setData({
        mediaLinks: [
          { _id: '1', name: '校园官网', description: '合肥城市学院官方网站', type: 'web', url: 'https://www.hfcu.edu.cn', icon: '' },
          { _id: '2', name: '微信官号', description: '合肥城市学院官方微信公众号', type: 'wechat', url: '', icon: '' },
          { _id: '3', name: '抖音官号', description: '合肥城市学院抖音官方账号', type: 'douyin', url: '', icon: '' },
          { _id: '4', name: '小红书官号', description: '合肥城市学院小红书官方账号', type: 'xiaohongshu', url: '', icon: '' }
        ]
      });
    } finally {
      wx.hideLoading();
    }
  },

  openLink(e) {
    const { url, type } = e.currentTarget.dataset;
    if (type === 'web' && url) {
      wx.navigateTo({
        url: `/pages/webview/index?url=${encodeURIComponent(url)}`
      });
    } else if (!url) {
      wx.showToast({ title: '链接暂未配置', icon: 'none' });
    } else {
      // 其他类型（微信、抖音等）显示提示
      wx.showModal({
        title: '提示',
        content: '请在相应平台搜索"合肥城市学院"关注官方账号',
        showCancel: false
      });
    }
  }
});
