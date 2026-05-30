// app.js
App({
  onLaunch: function () {
    if (!wx.cloud) {
      console.error('请使用 2.2.3 或以上的基础库以使用云能力');
    } else {
      wx.cloud.init({
        // ⚠️ 将下方引号内替换为云开发控制台的环境ID（如 hefei-party-xxxxx）
        // 开发调试期间可留空，自动读取开发者工具右上角选择的环境
        // env: 'your-env-id',
        traceUser: true,
      });
    }
  },
  globalData: {}
});
