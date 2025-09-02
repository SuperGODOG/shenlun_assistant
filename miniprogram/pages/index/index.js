// index.js
Page({
  data: {
    question: '',
    answer: '',
    response: '',
    isLoading: false,
    showingAd: false
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

  // 粘贴到题目输入框
  pasteToQuestion: function() {
    wx.getClipboardData({
      success: (res) => {
        const clipboardData = res.data;
        if (clipboardData) {
          this.setData({
            question: clipboardData
          });
          wx.showToast({
            title: '粘贴成功',
            icon: 'success',
            duration: 1500
          });
        } else {
          wx.showToast({
            title: '剪切板为空',
            icon: 'none',
            duration: 1500
          });
        }
      },
      fail: () => {
        wx.showToast({
          title: '获取剪切板失败',
          icon: 'none',
          duration: 1500
        });
      }
    });
  },

  // 粘贴到答案输入框
  pasteToAnswer: function() {
    wx.getClipboardData({
      success: (res) => {
        const clipboardData = res.data;
        if (clipboardData) {
          this.setData({
            answer: clipboardData
          });
          wx.showToast({
            title: '粘贴成功',
            icon: 'success',
            duration: 1500
          });
        } else {
          wx.showToast({
            title: '剪切板为空',
            icon: 'none',
            duration: 1500
          });
        }
      },
      fail: () => {
        wx.showToast({
          title: '获取剪切板失败',
          icon: 'none',
          duration: 1500
        });
      }
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

    // 自动播放广告
    this.playAdAndSubmit();
  },

  // 播放广告并提交
  playAdAndSubmit: function() {
    const videoAd = wx.createRewardedVideoAd({
      adUnitId: 'adunit-xxxxxxxxxxxxxxxx' // 需要替换为真实的广告位ID
    });

    this.setData({
      showingAd: true
    });

    // 显示AI思考提示
    wx.showToast({
      title: 'AI正在思考中，预计10-20秒',
      icon: 'loading',
      duration: 2000
    });

    videoAd.onLoad(() => {
      console.log('激励视频广告加载成功');
    });

    videoAd.onError((err) => {
      console.error('激励视频广告加载失败', err);
      // 广告加载失败，直接提交请求
      this.setData({
        showingAd: false
      });
      this.sendRequest();
    });

    videoAd.onClose((res) => {
      this.setData({
        showingAd: false
      });
      // 无论用户是否看完广告，都继续提交请求
      this.sendRequest();
    });

    // 显示广告
    videoAd.show().catch(() => {
      // 广告显示失败，直接提交
      console.log('广告显示失败，直接提交请求');
      this.setData({
        showingAd: false
      });
      this.sendRequest();
    });
  },

  // 发送请求到后端
  sendRequest: function() {

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