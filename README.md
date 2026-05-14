# 通信原理仿真软件 v1.0

基于 Python/PyQt5 的交互式通信原理仿真平台，面向高校通信工程/电子信息专业本科教学，覆盖《通信原理》课程全部实验大纲。

---

## 功能总览

### 基础实验模块

| 模块 | 对应实验 | 主要内容 |
|------|----------|---------|
| 信号源与基础分析 | 实验1 | 正弦/方波/NRZ/三角/锯齿波，实时功率谱，AWGN叠加 |
| 模拟调制解调 | 实验2 | AM/DSB/SSB-USB/SSB-LSB/FM/PM，相干/包络解调，时域+频域 |
| 信号数字化与复用 | 实验3/4/6 | 抽样定理验证，PCM量化SQNR，ΔM增量调制，TDM时分复用 |
| 基带传输与码型变换 | 实验7/8 | NRZ/RZ/AMI/HDB3码型，升余弦滤波，眼图，奈奎斯特准则 |
| 数字频带调制 | 实验5 | 2ASK/2FSK/2PSK/2DPSK，相干/非相干解调，BER vs SNR |

### 扩展功能模块

| 模块 | 主要内容 |
|------|---------|
| 新型频带调制 | QPSK星座图，16QAM灰码映射，MSK连续相位轨迹，BER曲线 |
| 差错控制编码 | Hamming(7,4) 纠错，卷积码+Viterbi译码，LDPC/极化码BER近似，Shannon极限 |
| 现代通信系统 | OFDM（PAPR/CP/多径）、MIMO Alamouti STBC、FHSS跳频、LS信道估计、DVB-T链路 |

### 综合分析工具（独立面板）

| 工具 | 功能 |
|------|------|
| 示波器 | 双通道时域显示，李萨如图，Vpp/Vrms/Vdc测量 |
| 频谱分析仪 | PSD/幅度谱/相位谱，多窗函数（Hann/Blackman/Flattop），单/双边谱 |
| 误码率测试仪 | 8种调制方式理论BER曲线，5种编码方案，Shannon极限参考线 |
| 星座图/眼图 | BPSK至64QAM星座，相位/频率偏差模拟，RC滤波眼图分析 |

---

## 快速开始

### 环境要求

- Python **3.9+**（推荐 3.11）
- Windows 10/11（也支持 Linux/macOS 直接运行源码）

### 安装依赖

```bash
pip install -r requirements.txt
```

`requirements.txt` 包含：
```
PyQt5>=5.15.0
numpy>=1.21.0
scipy>=1.7.0
matplotlib>=3.4.0
pyinstaller>=5.0.0
```

### 直接运行（开发模式）

```bash
python main.py
```

### 构建 Windows .exe

**方式1：双击运行**

```
build_exe.bat
```

**方式2：手动执行**

```bash
pip install -r requirements.txt
python -m PyInstaller commsim.spec --noconfirm --clean
# 输出位置: dist\通信原理仿真软件.exe
```

构建完成后，`dist\通信原理仿真软件.exe` 为单文件可执行程序，**无需安装 Python 环境**，双击即可在 Windows 上运行。

---

## 默认账号

| 用户名 | 密码 | 说明 |
|--------|------|------|
| `admin` | `admin123` | 内置管理员账号 |

首次运行自动创建，也可在登录界面注册新账号（支持填写真实姓名和学号）。

---

## 项目结构

```
commsim_lab/
├── main.py                    # 程序入口（PyQt5 Application）
├── requirements.txt
├── commsim.spec               # PyInstaller 打包配置
├── build_exe.bat              # Windows 一键构建脚本
├── build_exe.sh               # Linux/macOS 构建脚本
└── src/
    ├── auth/
    │   ├── user_manager.py    # SQLite 用户管理（SHA-256 密码）
    │   └── login_window.py    # 无边框登录/注册对话框
    ├── ui/
    │   ├── styles.py          # 全局深色主题 QSS
    │   ├── main_window.py     # 主窗口（侧边栏导航 + 进度统计）
    │   └── base_module.py     # 模块基类（左参数面板 + 右 matplotlib 图区）
    ├── modules/
    │   ├── signal_sources.py       # 实验1
    │   ├── analog_modulation.py    # 实验2
    │   ├── digitization.py         # 实验3/4/6
    │   ├── baseband.py             # 实验7/8
    │   ├── digital_modulation.py   # 实验5
    │   ├── advanced_modulation.py  # QPSK/16QAM/MSK
    │   ├── error_coding.py         # 差错控制编码
    │   └── modern_systems.py       # OFDM/MIMO/FHSS/DVB-T
    └── tools/
        └── analysis_panel.py       # 综合分析工具（4个子选项卡）
```

---

## 技术架构

| 层次 | 技术选型 | 说明 |
|------|----------|------|
| GUI 框架 | PyQt5 5.15+ | 跨平台原生窗口，支持 High-DPI |
| 信号处理 | NumPy + SciPy | FFT、滤波器、Welch PSD、Hilbert变换 |
| 可视化 | Matplotlib Qt5Agg | 嵌入式交互图表，支持缩放/保存 |
| 数据库 | SQLite3（内置） | 用户账号与实验进度持久化 |
| 安全 | hashlib SHA-256 | 密码哈希存储，不明文保存 |
| 打包 | PyInstaller 5+ | 单文件 .exe，无需 Python 运行时 |

---

## 仿真算法说明

### 基带编码
- **NRZ-L / RZ / AMI**：逐比特极性映射
- **HDB3**：AMI + 四连零替换（B00V / 000V 规则），符合 ITU G.703

### 调制解调
- **AM/DSB/SSB**：基于 Hilbert 变换的解析信号法生成 SSB
- **FM/PM**：累积相位积分调制，瞬时频率微分解调
- **QPSK/16QAM**：I/Q 正交双路，Gray 码映射，相干检测
- **MSK**：连续相位 CPFSK，调制指数 h=0.5

### 差错控制
- **Hamming(7,4)**：生成矩阵 G、校验矩阵 H，伴随式单比特纠错
- **卷积码**：约束长度 K=3，生成多项式 g1=111, g2=101（八进制 7,5）
- **Viterbi 译码**：硬判决最大似然，格图回溯
- **LDPC/Polar**：基于 Shannon 极限的近似 BER 曲线（教学展示用）

### 现代系统
- **OFDM**：IFFT/FFT 调制，循环前缀插入/删除，Welch PSD，PAPR CCDF
- **MIMO Alamouti**：2×N_R Alamouti STBC，MRC 接收，分集增益分析
- **OFDM 信道估计**：LS 最小二乘导频估计，线性插值，频域单抽头均衡

---

## 使用说明

1. 运行 `main.py` 或双击 `dist\通信原理仿真软件.exe`
2. 使用默认账号 `admin / admin123` 登录，或注册新账号
3. 从左侧导航栏选择实验模块
4. 在左侧参数面板调整仿真参数
5. 点击 **▶ 运行仿真** 按钮刷新图形
6. 使用 matplotlib 工具栏进行缩放、平移、保存图像
7. 点击 **📊 实验进度** 查看已访问模块统计

---

## 依赖说明

所有依赖均为开源 Python 包，可通过 `pip install -r requirements.txt` 一键安装。PyInstaller 将所有依赖打包进单一 `.exe`，最终用户无需额外安装任何软件。