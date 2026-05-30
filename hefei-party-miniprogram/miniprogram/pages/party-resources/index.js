// 学校党建思政资源


Page({
  data: {
    resourceSections: [
      { key: 'party', title: '党建资源', content: '', images: [] },
      { key: 'org', title: '组织资源', content: '', images: [] },
      { key: 'theory', title: '理论资源', content: '', images: [] },
      { key: 'talent', title: '人才资源', content: '', images: [] }
    ]
  },

  onLoad() {
    this.loadData();
  },

  async loadData() {
    const db = wx.cloud.database();
    wx.showLoading({ title: '加载中...' });
    try {
      const res = await db.collection('party_resources').limit(1).get();
      const data = res.data[0];
      if (data) {
        const sections = this.data.resourceSections.map(s => ({
          ...s,
          content: data[s.key + 'Content'] || '',
          images: data[s.key + 'Images'] || []
        }));
        this.setData({ resourceSections: sections });
      }
    } catch (e) {
      console.error(e);
    } finally {
      wx.hideLoading();
    }
  }
});
