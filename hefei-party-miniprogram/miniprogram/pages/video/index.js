// 视见合城
const db = wx.cloud.database();

Page({
  data: {
    videos: [],
    singleUrl: '',
    showPlayer: false,
    currentVideoUrl: ''
  },

  onLoad(options) {
    if (options.url) {
      // 从课程页跳入，直接播放
      this.setData({ singleUrl: decodeURIComponent(options.url) });
      wx.setNavigationBarTitle({ title: '课程视频' });
    } else {
      this.loadVideos();
    }
  },

  onHide() {
    // 页面隐藏时暂停视频
    const videoCtx = wx.createVideoContext('myVideo');
    if (videoCtx) videoCtx.pause();
    const popupCtx = wx.createVideoContext('popupVideo');
    if (popupCtx) popupCtx.pause();
  },

  async loadVideos() {
    wx.showLoading({ title: '加载中...' });
    try {
      const res = await db.collection('videos').orderBy('sortOrder', 'asc').get();
      this.setData({ videos: res.data });
    } catch (e) {
      console.error(e);
    } finally {
      wx.hideLoading();
    }
  },

  playVideo(e) {
    const url = e.currentTarget.dataset.url;
    this.setData({ showPlayer: true, currentVideoUrl: url });
  },

  closePlayer() {
    const ctx = wx.createVideoContext('popupVideo');
    if (ctx) ctx.stop();
    this.setData({ showPlayer: false });
    // 关闭后返回首页（文档要求）
    if (!this.data.singleUrl) {
      // 视频列表模式：只关闭弹窗
    } else {
      wx.navigateBack();
    }
  },

  onVideoEnd() {
    // 单视频播放结束返回
    wx.navigateBack();
  }
});
