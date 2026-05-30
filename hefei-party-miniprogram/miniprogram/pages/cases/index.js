// 校企党建互助案例采撷

const PAGE_SIZE = 10;

Page({
  data: {
    cases: [],
    loading: true,
    hasMore: false,
    page: 0
  },

  onLoad() {
    this.loadCases(true);
  },

  async loadCases(reset = false) {
    const db = wx.cloud.database();
    const page = reset ? 0 : this.data.page;
    try {
      const res = await db.collection('cases')
        .orderBy('createTime', 'desc')
        .skip(page * PAGE_SIZE)
        .limit(PAGE_SIZE)
        .get();

      const newCases = res.data.map(item => ({
        ...item,
        dateStr: item.createTime
          ? new Date(item.createTime).toLocaleDateString('zh-CN')
          : ''
      }));

      this.setData({
        cases: reset ? newCases : [...this.data.cases, ...newCases],
        loading: false,
        hasMore: newCases.length === PAGE_SIZE,
        page: page + 1
      });
    } catch (e) {
      console.error(e);
      this.setData({ loading: false });
    }
  },

  loadMore() {
    this.loadCases(false);
  },

  goToDetail(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/case-detail/index?id=${id}` });
  }
});
