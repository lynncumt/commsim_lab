// 校区地址


Page({
  data: {
    campuses: [],
    contactInfo: {
      postCode: '',
      phones: []
    }
  },

  onLoad() {
    this.loadData();
  },

  async loadData() {
    const db = wx.cloud.database();
    wx.showLoading({ title: '加载中...' });
    try {
      const [campusRes, contactRes] = await Promise.all([
        db.collection('campuses').orderBy('sortOrder', 'asc').get(),
        db.collection('school_contact').limit(1).get()
      ]);
      this.setData({
        campuses: campusRes.data,
        contactInfo: contactRes.data[0] || { postCode: '', phones: [] }
      });
    } catch (e) {
      console.error(e);
    } finally {
      wx.hideLoading();
    }
  },

  openMap(e) {
    const { lat, lng, name, address } = e.currentTarget.dataset;
    if (lat && lng) {
      wx.openLocation({
        latitude: parseFloat(lat),
        longitude: parseFloat(lng),
        name,
        address,
        scale: 16
      });
    } else {
      // 没有坐标时用高德地图搜索
      wx.showToast({ title: '暂无导航数据', icon: 'none' });
    }
  },

  callPhone(e) {
    const phone = e.currentTarget.dataset.phone;
    wx.makePhoneCall({ phoneNumber: phone });
  }
});
