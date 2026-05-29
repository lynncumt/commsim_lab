// 云函数：通用内容获取（支持分页）
const cloud = require('wx-server-sdk');
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV });
const db = cloud.database();

exports.main = async (event, context) => {
  const { collection, id, page = 0, pageSize = 10, orderBy = 'createTime', orderDir = 'desc' } = event;

  try {
    if (id) {
      const res = await db.collection(collection).doc(id).get();
      return { success: true, data: res.data };
    }

    const query = db.collection(collection)
      .orderBy(orderBy, orderDir)
      .skip(page * pageSize)
      .limit(pageSize);

    const res = await query.get();
    return { success: true, data: res.data, total: res.data.length };
  } catch (e) {
    return { success: false, error: e.message };
  }
};
