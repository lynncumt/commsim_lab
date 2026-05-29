# 合肥城市学院校企党建互助微信小程序（云开发版）

## 功能模块

| 模块 | 说明 |
|------|------|
| 首页 | 7个主模块 + 3个附设栏目 + 合城动态 |
| 学校概况 | 图文介绍 + 4个二级学院 + 9个系专业 |
| 校企党建互助简介 | 时代背景 + 六大需求 + 5个互助项目 |
| 学校党建思政资源 | 党建/组织/理论/人才 四类资源 |
| 党建思政专家库 | 专家列表 + 详情弹窗 |
| 党建思政精品课程库 | 4类课程（思想引领/政策阐释/责任担当/党务实操） |
| 校企党建互助案例采撷 | 新闻列表 + 全文详情 |
| 党建互助·联系我们 | 需求多选 + 表单提交 + 云数据库存档 |
| 校区地址 | 多校区 + 高德导航 + 电话拨打 |
| 视见合城 | 宣传视频列表 / 关闭后返回首页 |
| 学校媒体链接 | 官网/微信/抖音/小红书 |

## 云数据库集合

| 集合名 | 用途 |
|--------|------|
| `school_overview` | 学校概况图文 |
| `colleges` | 二级学院（4个） |
| `departments` | 系部（9个，含专业） |
| `party_intro` | 党建互助简介 |
| `party_resources` | 党建思政资源 |
| `expert_intro` | 专家库介绍 |
| `experts` | 专家列表 |
| `course_intro` | 课程库介绍 |
| `courses` | 课程列表（category 1-4） |
| `cases` | 案例新闻 |
| `contact_requests` | 用户联系申请（只写） |
| `campuses` | 校区地址 |
| `school_contact` | 联系电话邮编 |
| `videos` | 宣传视频 |
| `media_links` | 媒体链接 |

## 云函数

| 函数名 | 用途 |
|--------|------|
| `submitContact` | 提交联系申请（含服务端写入） |
| `getContent` | 通用内容读取（支持分页） |

## 数据库权限设置

- `contact_requests`：仅创建者可写，管理员可读全部
- 其余集合：所有用户只读，管理员后台可写

## 部署步骤

1. 在微信开发者工具中打开 `hefei-party-miniprogram/` 目录
2. 填写 `project.config.json` 中的 `appid`
3. 填写 `miniprogram/app.js` 中的云环境 ID（`your-cloud-env-id`）
4. 在云开发控制台按 `utils/db-init.js` 中的结构创建数据库集合
5. 上传并部署云函数 `submitContact` 和 `getContent`
6. 将所需图片上传至云存储，更新对应数据库字段

## Tab图标

在 `miniprogram/images/` 目录中放置以下图片（建议 81×81px PNG）：
- `tab-home.png` / `tab-home-active.png`
- `tab-contact.png` / `tab-contact-active.png`
