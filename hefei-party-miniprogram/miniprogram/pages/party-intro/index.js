// 校企党建互助简介
const db = wx.cloud.database();

Page({
  data: {
    data: {},
    projects: [
      { num: '01', name: '组织互助联建', desc: '' },
      { num: '02', name: '理论互助联学', desc: '' },
      { num: '03', name: '活动互助联办', desc: '' },
      { num: '04', name: '人才互助联育', desc: '' },
      { num: '05', name: '发展互助联动', desc: '' }
    ]
  },

  onLoad() {
    this.loadData();
  },

  async loadData() {
    wx.showLoading({ title: '加载中...' });
    try {
      const res = await db.collection('party_intro').limit(1).get();
      const introData = res.data[0] || {};
      this.setData({
        data: introData,
        projects: introData.projects || this.data.projects
      });
    } catch (e) {
      console.error(e);
    } finally {
      wx.hideLoading();
    }
  }
});
