// 党建互助·联系我们


Page({
  data: {
    needCategories: [
      {
        key: 1, num: '一', name: '思想引领类',
        items: [
          { id: '1-1', label: '习近平新时代中国特色社会主义思想专题学习' },
          { id: '1-2', label: '党史学习教育' },
          { id: '1-3', label: '爱国主义教育' },
          { id: '1-4', label: '理想信念教育' }
        ]
      },
      {
        key: 2, num: '二', name: '政策阐释类',
        items: [
          { id: '2-1', label: '党的路线方针政策解读' },
          { id: '2-2', label: '党规党纪专题培训' },
          { id: '2-3', label: '习近平法治思想学习' },
          { id: '2-4', label: '乡村振兴与共同富裕政策解读' }
        ]
      },
      {
        key: 3, num: '三', name: '责任担当类',
        items: [
          { id: '3-1', label: '企业党委书记能力提升' },
          { id: '3-2', label: '基层党支部书记培训' },
          { id: '3-3', label: '党员发展与教育管理' },
          { id: '3-4', label: '党建与业务融合发展' }
        ]
      },
      {
        key: 4, num: '四', name: '党务实操类',
        items: [
          { id: '4-1', label: '党员组织关系转接' },
          { id: '4-2', label: '党组织换届选举指导' },
          { id: '4-3', label: '党务档案规范化管理' },
          { id: '4-4', label: '主题党日活动策划' }
        ]
      },
      {
        key: 5, num: '五', name: '产教研合作类',
        items: [
          { id: '5-1', label: '校企联合实训基地共建' },
          { id: '5-2', label: '产学研协同创新项目' },
          { id: '5-3', label: '企业员工学历教育合作' },
          { id: '5-4', label: '党建引领乡村振兴实践' }
        ]
      }
    ],
    selectedNeeds: {},
    form: {
      contactName: '',
      orgName: '',
      contactInfo: '',
      address: '',
      field: '',
      message: ''
    },
    submitting: false
  },

  toggleNeed(e) {
    const id = e.currentTarget.dataset.id;
    const selected = { ...this.data.selectedNeeds };
    if (selected[id]) {
      delete selected[id];
    } else {
      selected[id] = true;
    }
    this.setData({ selectedNeeds: selected });
  },

  onInput(e) {
    const field = e.currentTarget.dataset.field;
    const value = e.detail.value;
    this.setData({ [`form.${field}`]: value });
  },

  async submitForm() {
    const db = wx.cloud.database();
    const { form, selectedNeeds, needCategories } = this.data;

    if (!form.contactName.trim()) {
      return wx.showToast({ title: '请输入联系人姓名', icon: 'none' });
    }
    if (!form.orgName.trim()) {
      return wx.showToast({ title: '请输入单位名称', icon: 'none' });
    }
    if (!form.contactInfo.trim()) {
      return wx.showToast({ title: '请输入联系方式', icon: 'none' });
    }

    // 收集已选需求标签
    const selectedLabels = [];
    needCategories.forEach(cat => {
      cat.items.forEach(item => {
        if (selectedNeeds[item.id]) {
          selectedLabels.push(`${cat.name} - ${item.label}`);
        }
      });
    });

    this.setData({ submitting: true });

    try {
      await db.collection('contact_requests').add({
        data: {
          ...form,
          selectedNeeds: selectedLabels,
          createTime: db.serverDate(),
          status: 'pending', // pending / viewed / archived
          isRead: false
        }
      });

      wx.showModal({
        title: '提交成功',
        content: '感谢您的联系！我们将尽快与您沟通，共同推进党建互助合作。',
        showCancel: false,
        success: () => {
          // 清空表单
          this.setData({
            selectedNeeds: {},
            form: {
              contactName: '',
              orgName: '',
              contactInfo: '',
              address: '',
              field: '',
              message: ''
            }
          });
        }
      });
    } catch (e) {
      console.error(e);
      wx.showToast({ title: '提交失败，请重试', icon: 'none' });
    } finally {
      this.setData({ submitting: false });
    }
  }
});
