// 党建思政精品课程库
const db = wx.cloud.database();

Page({
  data: {
    intro: '',
    categories: [],
    showModal: false,
    currentCourse: {}
  },

  onLoad() {
    this.loadData();
  },

  async loadData() {
    wx.showLoading({ title: '加载中...' });
    try {
      const [introRes, coursesRes] = await Promise.all([
        db.collection('course_intro').limit(1).get(),
        db.collection('courses').orderBy('categoryOrder', 'asc').get()
      ]);

      const intro = introRes.data[0]?.content || '';
      const allCourses = coursesRes.data;

      // 按分类分组
      const categoryMap = {};
      const categoryNames = {
        1: { num: '一', name: '思想引领类' },
        2: { num: '二', name: '政策阐释类' },
        3: { num: '三', name: '责任担当类' },
        4: { num: '四', name: '党务实操类' }
      };

      allCourses.forEach(course => {
        const cat = course.category || 1;
        if (!categoryMap[cat]) {
          categoryMap[cat] = {
            key: cat,
            ...categoryNames[cat],
            courses: []
          };
        }
        categoryMap[cat].courses.push(course);
      });

      const categories = Object.values(categoryMap).sort((a, b) => a.key - b.key);

      this.setData({ intro, categories });
    } catch (e) {
      console.error(e);
    } finally {
      wx.hideLoading();
    }
  },

  viewCourse(e) {
    const course = e.currentTarget.dataset.course;
    this.setData({ showModal: true, currentCourse: course });
  },

  closeModal() {
    this.setData({ showModal: false });
  },

  playVideo(e) {
    const url = e.currentTarget.dataset.url;
    wx.navigateTo({ url: `/pages/video/index?url=${encodeURIComponent(url)}` });
  }
});
