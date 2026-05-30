// app.js
// ============================================================
// ⚠️  必填：将下方 CLOUD_ENV_ID 替换为你的云开发环境ID
// 查找方式：微信开发者工具 → 顶部「云开发」按钮 → 环境ID（格式如 hefei-party-xxxxxx）
// ============================================================
const CLOUD_ENV_ID = '';  // 👈 填入环境ID，例如: 'hefei-party-a1b2c3'

App({
  onLaunch: function () {
    if (!wx.cloud) {
      console.error('请使用 2.2.3 或以上的基础库以使用云能力');
      return;
    }
    const initOpts = { traceUser: true };
    if (CLOUD_ENV_ID) {
      initOpts.env = CLOUD_ENV_ID;
    }
    wx.cloud.init(initOpts);
    console.log('云开发初始化完成，环境:', CLOUD_ENV_ID || '（默认环境）');
  },
  globalData: {
    cloudEnvId: CLOUD_ENV_ID
  }
});
