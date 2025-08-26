// index.js
Page({
  data: {
    question: '',
    answer: '',
    response: '',
    isLoading: false
  },

  onLoad: function() {
    // 页面加载时执行的逻辑
  },

  // 题目输入事件处理
  onQuestionInput: function(e) {
    this.setData({
      question: e.detail.value
    });
  },

  // 答案输入事件处理
  onAnswerInput: function(e) {
    this.setData({
      answer: e.detail.value
    });
  },

  // 提交内容到后端
  submitContent: function() {
    // 检查题目是否为空
    if (!this.data.question.trim()) {
      wx.showToast({
        title: '请输入题目内容',
        icon: 'none',
        duration: 2000
      });
      return;
    }

    // 设置加载状态
    this.setData({
      isLoading: true
    });

    // 构建请求数据
    const requestData = {
      题目: this.data.question,
      答案: this.data.answer.trim() || null
    };

    // 获取全局数据
    const app = getApp();
    const apiBaseUrl = app.globalData.apiBaseUrl;

    // 发送请求到后端
    wx.request({
      url: `${apiBaseUrl}/api/chat`,
      method: 'POST',
      timeout: 60000,
      data: {
        prompt: JSON.stringify(requestData),
        format: 'text'
      },
      success: (res) => {
        console.log('API响应状态:', res.statusCode);
        console.log('API响应数据长度:', res.data && res.data.response ? res.data.response.length : 0);
        console.log('API响应数据前100字符:', res.data && res.data.response ? res.data.response.substring(0, 100) : 'null');
        
        if (res.statusCode === 200 && res.data) {
          const responseText = res.data.response || '服务器返回数据格式错误';
          console.log('设置响应文本长度:', responseText.length);
          
          this.setData({
            response: responseText
          });
        } else {
          this.setData({
            response: '请求失败，请稍后再试'
          });
        }
      },
      fail: (error) => {
        console.error('请求失败', error);
        this.setData({
          response: '网络错误，请检查网络连接'
        });
      },
      complete: () => {
        this.setData({
          isLoading: false
        });
      }
    });
  }
});