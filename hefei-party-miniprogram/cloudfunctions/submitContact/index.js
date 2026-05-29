// 云函数：提交联系申请（服务端写入，可配合消息推送）
const cloud = require('wx-server-sdk');
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV });
const db = cloud.database();

exports.main = async (event, context) => {
  const { form, selectedNeeds } = event;

  try {
    const result = await db.collection('contact_requests').add({
      data: {
        ...form,
        selectedNeeds: selectedNeeds || [],
        createTime: db.serverDate(),
        status: 'pending',
        isRead: false,
        openid: cloud.getWXContext().OPENID
      }
    });

    // 可在此处调用 sendUniformMessage 向管理员推送模板消息通知
    // await cloud.openapi.uniformMessage.send({ ... })

    return { success: true, id: result._id };
  } catch (e) {
    return { success: false, error: e.message };
  }
};
