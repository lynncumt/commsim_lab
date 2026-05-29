/**
 * 云数据库初始化脚本
 * 在微信开发者工具云开发控制台执行，或通过云函数调用
 *
 * 数据库集合说明：
 *
 * school_overview   - 学校概况（图文）
 * colleges          - 二级学院（4个）
 * departments       - 系部（9个，关联collegeId）
 * party_intro       - 校企党建互助简介
 * party_resources   - 学校党建思政资源
 * expert_intro      - 专家库介绍文字
 * experts           - 专家列表
 * course_intro      - 课程库介绍文字
 * courses           - 课程列表（category: 1-4）
 * cases             - 案例新闻列表
 * contact_requests  - 联系申请（用户提交）
 * campuses          - 校区地址
 * school_contact    - 学校联系信息（邮编、电话）
 * videos            - 宣传视频列表
 * media_links       - 媒体链接
 */

// 示例数据结构

const sampleData = {
  // 学校概况
  school_overview: {
    content: '<p>合肥城市学院是一所以工科为主...</p>',
    images: ['cloud://env-id.xxxx/school1.jpg', 'cloud://env-id.xxxx/school2.jpg'],
    updateTime: new Date()
  },

  // 二级学院
  colleges: [
    { name: '智能建造与能源学院', brief: '涵盖土木工程、建筑学等专业', sortOrder: 1, images: [], content: '' },
    { name: '空间设计与规划学院', brief: '涵盖城乡规划、环境设计等专业', sortOrder: 2, images: [], content: '' },
    { name: '数字经济与管理学院', brief: '涵盖工商管理、会计学等专业', sortOrder: 3, images: [], content: '' },
    { name: '现代机电工程学院', brief: '涵盖机械工程、电气工程等专业', sortOrder: 4, images: [], content: '' }
  ],

  // 系部（示例）
  departments: [
    { name: '智能建造系', collegeId: 'college-1-id', majors: ['土木工程', '智能建造'], sortOrder: 1, intro: '' },
    { name: '材料与新能源系', collegeId: 'college-1-id', majors: ['新能源材料', '建筑材料'], sortOrder: 2, intro: '' }
    // ... 共9个系
  ],

  // 专家
  experts: [
    {
      name: '张XX',
      title: '教授 / 党建理论研究专家',
      brief: '长期从事党史党建研究，主持多项省级科研项目...',
      content: '<p>详细介绍...</p>',
      avatar: 'cloud://env-id.xxxx/expert1.jpg',
      sortOrder: 1
    }
  ],

  // 课程
  courses: [
    { title: '习近平新时代中国特色社会主义思想概论', teacher: '张XX', category: 1, categoryOrder: 1, description: '', videoUrl: '' },
    { title: '党史学习教育专题讲座', teacher: '李XX', category: 1, categoryOrder: 2, description: '', videoUrl: '' },
    { title: '全面从严治党政策解读', teacher: '王XX', category: 2, categoryOrder: 1, description: '', videoUrl: '' }
  ],

  // 案例新闻
  cases: [
    {
      title: '合肥城市学院与XX集团签署党建共建协议',
      summary: '为深入推进校企党建互助工作，合肥城市学院与XX集团...',
      content: '<p>正文内容...</p>',
      coverImage: 'cloud://env-id.xxxx/case1.jpg',
      images: [],
      source: '党委办公室',
      createTime: new Date()
    }
  ],

  // 校区
  campuses: [
    { name: '滨湖校区', address: '安徽省合肥市包河区XX路XX号', lat: 31.74, lng: 117.29, sortOrder: 1, image: '' },
    { name: '舒城校区', address: '安徽省六安市舒城县XX路XX号', lat: 31.46, lng: 116.94, sortOrder: 2, image: '' }
  ],

  // 学校联系信息
  school_contact: {
    postCode: '230000',
    phones: ['0551-XXXXXXXX', '0551-XXXXXXXX']
  },

  // 视频
  videos: [
    { title: '合肥城市学院宣传片', description: '展示学校风貌与教学成果', url: 'cloud://env-id.xxxx/promo.mp4', coverImage: '', sortOrder: 1 }
  ],

  // 媒体链接
  media_links: [
    { name: '校园官网', description: '合肥城市学院官方网站', type: 'web', url: 'https://www.hfcu.edu.cn', sortOrder: 1 },
    { name: '微信官号', description: '搜索关注"合肥城市学院"', type: 'wechat', url: '', sortOrder: 2 },
    { name: '抖音官号', description: '抖音搜索"合肥城市学院"', type: 'douyin', url: '', sortOrder: 3 },
    { name: '小红书官号', description: '小红书搜索"合肥城市学院"', type: 'xiaohongshu', url: '', sortOrder: 4 }
  ]
};

module.exports = sampleData;
