// 学院详情


Page({
  data: {
    college: {},
    departments: []
  },

  onLoad(options) {
    const { id, name } = options;
    wx.setNavigationBarTitle({ title: decodeURIComponent(name || '学院详情') });
    this.loadData(id);
  },

  async loadData(collegeId) {
    const db = wx.cloud.database();
    wx.showLoading({ title: '加载中...' });
    try {
      const [collegeRes, deptRes] = await Promise.all([
        db.collection('colleges').doc(collegeId).get(),
        db.collection('departments')
          .where({ collegeId })
          .orderBy('sortOrder', 'asc')
          .get()
      ]);
      this.setData({
        college: collegeRes.data,
        departments: deptRes.data
      });
    } catch (e) {
      console.error(e);
      wx.showToast({ title: '加载失败', icon: 'none' });
    } finally {
      wx.hideLoading();
    }
  }
});
